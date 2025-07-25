from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models.project import Project
from app.models.submission import Submission
from app.utils.decorators import role_required
from datetime import datetime
import json
from httpx import ReadTimeout

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    pending_projects = current_app.supabase_service.get_projects_by_status('pending')
    pending_submissions = current_app.supabase_service.get_pending_submissions()

    # Parse submitted_at as datetime objects where needed
    for submission in pending_submissions:
        if submission.get('submitted_at') and isinstance(submission['submitted_at'], str):
            try:
                submission['submitted_at'] = datetime.fromisoformat(submission['submitted_at'].replace('Z', '+00:00'))
            except Exception:
                submission['submitted_at'] = None

    stats = {
        'total_projects': len(current_app.supabase_service.get_client().table('projects').select('id').execute().data),
        'total_students': len(
            current_app.supabase_service.get_client().table('users').select('id').eq('role', 'student').execute().data),
        'total_parents': len(
            current_app.supabase_service.get_client().table('users').select('id').eq('role', 'parent').execute().data),
        'pending_approvals': len(pending_projects) + len(pending_submissions)
    }

    return render_template(
        'admin/dashboard.html',
        pending_projects=pending_projects,
        pending_submissions=pending_submissions,
        stats=stats
    )


@admin_bp.route('/approve-ideas')
@login_required
@role_required('admin')
def approve_ideas():
    pending_projects = current_app.supabase_service.get_projects_by_status('pending')
    project_objects = [Project.from_dict(p) for p in pending_projects]

    # Parse ai_evaluation JSON for each project to access problem_statement and solution_overview
    for p in project_objects:
        if p.ai_evaluation and isinstance(p.ai_evaluation, str):
            try:
                p.ai_evaluation = json.loads(p.ai_evaluation)
            except Exception:
                p.ai_evaluation = {}

        # Debug print to verify data availability
        print(f"Project {p.title} - Problem Statement: {p.ai_evaluation.get('problem_statement', 'None')}")

    return render_template('admin/approve_ideas.html', projects=project_objects)


@admin_bp.route('/approve-project/<int:project_id>', methods=['POST'])
@login_required
@role_required('admin')
def approve_project(project_id):
    action = request.form.get('action')  # approve or reject
    admin_notes = request.form.get('admin_notes', '')
    rejection_reason = request.form.get('rejection_reason', '').strip() or admin_notes

    if action == 'approve':
        result = current_app.supabase_service.update_project_status(project_id, 'approved', {
            'approved_at': datetime.utcnow().isoformat(),
            'approved_by': current_user.id,
            'admin_notes': admin_notes
        })
        print(f"[ADMIN] Attempted to approve project {project_id}. Update result: {result}")

        project_after = current_app.supabase_service.get_client().table('projects').select('*').eq('id', project_id).execute()
        print(f"[ADMIN] Project {project_id} after approval: {project_after.data[0] if project_after.data else 'None found'}")

        if result:
            flash('Project approved successfully!', 'success')
        else:
            flash('Failed to approve project.', 'error')

    elif action == 'reject':
        update_data = {
            'rejected_at': datetime.utcnow().isoformat(),
            'rejected_by': current_user.id,
            'admin_notes': admin_notes,
            'rejection_reason': rejection_reason
        }
        result = current_app.supabase_service.get_client().table('projects').update(update_data).eq('id', project_id).execute()
        print(f"[ADMIN] Attempted to reject project {project_id}. Update result: {result}")
        if result.data:
            flash('Project rejected.', 'info')
        else:
            flash('Failed to reject project.', 'error')

    return redirect(url_for('admin.approve_ideas'))


@admin_bp.route('/approve-submissions')
@login_required
@role_required('admin')
def approve_submissions():
    pending_submissions_resp = current_app.supabase_service.get_client().table('submissions') \
        .select('*, projects(*), users(*)') \
        .eq('status', 'pending') \
        .execute()
    pending_submissions = pending_submissions_resp.data or []

    # Parse datetime as needed
    for sub in pending_submissions:
        if sub.get('submitted_at') and isinstance(sub['submitted_at'], str):
            try:
                sub['submitted_at'] = datetime.fromisoformat(sub['submitted_at'].replace('Z', '+00:00'))
            except Exception:
                sub['submitted_at'] = None

    return render_template('admin/approve_submissions.html', submissions=pending_submissions)



@admin_bp.route('/approve-submission/<int:submission_id>', methods=['POST'])
@login_required
@role_required('admin')
def approve_submission(submission_id):
    action = request.form.get('action')  # approve, reject, request_revision
    admin_feedback = request.form.get('admin_feedback', '')
    points_awarded = int(request.form.get('points_awarded', 0))

    try:
        # Fetch the submission along with its related project data
        submission_response = current_app.supabase_service.get_client().table('submissions') \
            .select('*, projects(*)') \
            .eq('id', submission_id).execute()

        if not submission_response.data:
            flash('Submission not found.', 'error')
            return redirect(url_for('admin.approve_submissions'))

        submission_data = submission_response.data[0]
        project_data = submission_data.get('projects', {})

        if action == 'approve':
            # Update submission status to approved
            result = current_app.supabase_service.update_submission_status(
                submission_id, 'approved', admin_feedback
            )
            print("Approval result:", result)
            if not result or getattr(result, 'error', None):
                flash('Submission approved.', 'error')
            else:
                # Mark project as completed
                current_app.supabase_service.update_project_status(project_data['id'], 'completed')

                # Update user points
                user_response = current_app.supabase_service.get_client().table('users') \
                    .select('points') \
                    .eq('id', submission_data['student_id']) \
                    .execute()
                current_points = user_response.data[0]['points'] if user_response.data else 0
                new_points = current_points + points_awarded

                current_app.supabase_service.get_client().table('users') \
                    .update({'points': new_points}) \
                    .eq('id', submission_data['student_id']) \
                    .execute()

                # Update points awarded for this submission
                current_app.supabase_service.get_client().table('submissions') \
                    .update({'points_awarded': points_awarded}) \
                    .eq('id', submission_id) \
                    .execute()

                flash(f'Submission approved! {points_awarded} points awarded to student.', 'success')

        elif action == 'reject':
            print(f"👉 Rejecting submission {submission_id}")

            result = current_app.supabase_service.update_submission_status(
                submission_id, 'rejected', admin_feedback
            )
            print("🔥 update_submission_status result:", result)

            if not result or getattr(result, 'error', None):
                flash('Failed to reject submission.', 'error')
            else:
                # Reset project claim to approved and clear claimed_by and claimed_at
                current_app.supabase_service.update_project_status(project_data['id'], 'approved', {
                    'claimed_by': None,
                    'claimed_at': None
                })
                flash('Submission rejected. Project is now available for other students.', 'info')

        elif action == 'request_revision':
            print(f"📝 Requesting revision for submission {submission_id}")

            result = current_app.supabase_service.update_submission_status(
                submission_id, 'revision_requested', admin_feedback
            )
            print("🔥 update_submission_status result:", result)

            if not result or getattr(result, 'error', None):
                flash('Failed to request revision.', 'error')
            else:
                flash('Revision requested. Student will be notified.', 'info')

        else:
            flash('Invalid action.', 'warning')

    except Exception as e:
        print(f"❌ Exception in approve_submission route: {e}")
        flash('An error occurred while processing the submission.', 'error')

    return redirect(url_for('admin.approve_submissions'))



@admin_bp.route('/users')
@login_required
@role_required('admin')
def manage_users():
    users_response = current_app.supabase_service.get_client().table('users').select('*').execute()
    users = users_response.data if users_response.data else []

    for user in users:
        if user.get('created_at') and isinstance(user['created_at'], str):
            try:
                user['created_at'] = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
            except Exception:
                user['created_at'] = None

    return render_template('admin/manage_users.html', users=users)


@admin_bp.route('/analytics')
@login_required
@role_required('admin')
def analytics():
    try:
        top_students = current_app.supabase_service.get_client().table('users') \
            .select('full_name, points').eq('role', 'student').order('points', desc=True).limit(10).execute()

        total_projects = current_app.supabase_service.get_client().table('projects').select('status').execute()
        project_stats = {}
        for project in total_projects.data:
            status = project['status']
            project_stats[status] = project_stats.get(status, 0) + 1

        submissions_response = current_app.supabase_service.get_client().table('submissions').select('submitted_at, status').execute()

        analytics_data = {
            'top_students': top_students.data if top_students.data else [],
            'project_stats': project_stats,
            'total_submissions': len(submissions_response.data) if submissions_response.data else 0
        }

        return render_template('admin/analytics.html', analytics=analytics_data)

    except Exception as e:
        flash('Error loading analytics data.', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/toggle-project-visibility/<int:project_id>', methods=['POST'])
@login_required
@role_required('admin')
def toggle_project_visibility(project_id):
    visible = request.form.get('visible') == 'true'
    result = current_app.supabase_service.get_client().table('projects').update({
        'show_on_landing_page': visible,
        'updated_at': datetime.utcnow().isoformat()
    }).eq('id', project_id).execute()

    if not result or result.data is None:
        flash('Failed to update project visibility.', 'error')
    else:
        flash('Project visibility updated successfully.', 'success')

    return redirect(request.referrer or url_for('admin.approve_submissions'))


