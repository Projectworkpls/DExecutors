from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.project import Project
from app.models.submission import Submission
from app.utils.decorators import role_required
from app.utils.helpers import allowed_file, upload_file_to_storage
import os
from datetime import datetime
import json

student_bp = Blueprint('student', __name__)


@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    # Get student's submissions
    submissions = current_app.supabase_service.get_submissions_by_student(current_user.id)

    # Get available opportunities (approved projects not claimed)
    available_projects = current_app.supabase_service.get_projects_by_status('approved')

    # Filter out projects already claimed by this student
    claimed_project_ids = [s['project_id'] for s in submissions]
    available_projects = [p for p in available_projects if p['id'] not in claimed_project_ids]

    return render_template('student/dashboard.html',
                           submissions=submissions,
                           available_projects=available_projects[:5],  # Show latest 5
                           total_points=current_user.points)


@student_bp.route('/opportunities')
@login_required
@role_required('student')
def opportunities():
    # Get all approved projects
    all_projects = current_app.supabase_service.get_projects_by_status('approved')

    # Get student's claimed projects
    submissions = current_app.supabase_service.get_submissions_by_student(current_user.id)
    claimed_project_ids = [s['project_id'] for s in submissions]

    # Filter and search
    search_query = request.args.get('search', '')
    grade_filter = request.args.get('grade', '')
    sort_by = request.args.get('sort', 'created_at')

    filtered_projects = []
    for project in all_projects:
        if project['id'] in claimed_project_ids:
            continue

        # Apply search filter
        if search_query:
            if search_query.lower() not in project['title'].lower() and \
                    search_query.lower() not in project['description'].lower():
                continue

        # Apply grade filter
        if grade_filter:
            ai_eval = project.get('ai_evaluation', {})
            if isinstance(ai_eval, str):
                try:
                    ai_eval = json.loads(ai_eval)
                except:
                    ai_eval = {}

            age_info = ai_eval.get('age_appropriateness', {})
            grade_levels = age_info.get('grade_levels', [])
            if grade_filter not in grade_levels:
                continue

        filtered_projects.append(project)

    # Sort projects
    if sort_by == 'credits':
        filtered_projects.sort(key=lambda x: x.get('credits', 0), reverse=True)
    elif sort_by == 'title':
        filtered_projects.sort(key=lambda x: x.get('title', ''))
    else:  # created_at
        filtered_projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return render_template('student/opportunities.html',
                           projects=filtered_projects,
                           search_query=search_query,
                           grade_filter=grade_filter,
                           sort_by=sort_by)


@student_bp.route('/claim-project/<int:project_id>', methods=['POST'])
@login_required
@role_required('student')
def claim_project(project_id):
    try:
        supabase_service = current_app.supabase_service

        # Check if project exists and is available
        response = supabase_service.get_client().table('projects').select('*').eq('id', project_id).eq('status',
                                                                                                       'approved').execute()

        if not response.data:
            flash('Project not found or not available.', 'error')
            return redirect(url_for('student.opportunities'))

        project_data = response.data[0]

        # Check if student already claimed this project
        existing_submission = supabase_service.get_client().table('submissions').select('*').eq('project_id',
                                                                                                project_id).eq(
            'student_id', current_user.id).execute()

        if existing_submission.data:
            flash('You have already claimed this project.', 'warning')
            return redirect(url_for('student.opportunities'))

        # Create submission record with all required fields
        submission_data = {
            'project_id': project_id,
            'student_id': current_user.id,
            'status': 'claimed',
            'description': '',  # Empty initially
            'submission_type': 'text',  # Default type
            'submitted_at': datetime.utcnow().isoformat(),
            'points_awarded': 0
        }

        submission = supabase_service.create_submission(submission_data)

        if submission:
            # Update project status
            supabase_service.update_project_status(project_id, 'claimed', {
                'claimed_by': current_user.id,
                'claimed_at': datetime.utcnow().isoformat()
            })

            flash('Project claimed successfully! You can now work on it.', 'success')
        else:
            flash('Failed to claim project. Please try again.', 'error')

    except Exception as e:
        print(f"Error in claim_project: {e}")
        flash('An error occurred while claiming the project.', 'error')

    return redirect(url_for('student.opportunities'))


@student_bp.route('/submit-project', methods=['GET', 'POST'])
@login_required
@role_required('student')
def submit_project():
    if request.method == 'GET':
        # Get student's claimed projects that haven't been submitted
        submissions = current_app.supabase_service.get_submissions_by_student(current_user.id)
        claimed_projects = [s for s in submissions if s['status'] == 'claimed']

        return render_template('student/submit_project.html', claimed_projects=claimed_projects)

    # Handle POST request
    project_id = request.form.get('project_id')
    description = request.form.get('description')
    submission_type = request.form.get('submission_type')

    if not all([project_id, description, submission_type]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('student.submit_project'))

    try:
        # Get project details
        project_response = current_app.supabase_service.get_client().table('projects').select('*').eq('id', project_id).execute()
        if not project_response.data:
            flash('Project not found.', 'error')
            return redirect(url_for('student.submit_project'))

        project_data = project_response.data[0]

        # Handle file upload
        file_url = None
        file_content = None

        if submission_type in ['image', 'video']:
            file = request.files.get('file')
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_url = upload_file_to_storage(file, filename)

                if submission_type == 'image':
                    file_content = current_app.gemini_service.process_image_for_evaluation(file)

        elif submission_type == 'url':
            file_url = request.form.get('url')
            if not file_url:
                flash('Please provide a URL.', 'error')
                return redirect(url_for('student.submit_project'))

        # Prepare submission data
        submission_data = {
            'project_id': project_id,
            'student_id': current_user.id,
            'description': description,
            'submission_type': submission_type,
            'file_url': file_url,
            'status': 'pending',
            'submitted_at': datetime.utcnow().isoformat()
        }

        # Get AI evaluation
        ai_evaluation = current_app.gemini_service.evaluate_student_submission(
            project_data, submission_data, file_content
        )

        if ai_evaluation['success']:
            submission_data['ai_evaluation'] = ai_evaluation['evaluation']

                # Update submission
        update_result = current_app.supabase_service.get_client().table('submissions').update(submission_data).eq('project_id',
                                                                                                       project_id).eq(
            'student_id', current_user.id).execute()

        if update_result.data:
            # Update project status
            current_app.supabase_service.update_project_status(project_id, 'in_progress')

            flash('Project submitted successfully! It will be reviewed by an admin.', 'success')
            return redirect(url_for('student.dashboard'))
        else:
            flash('Failed to submit project. Please try again.', 'error')

    except Exception as e:
        flash('An error occurred while submitting the project.', 'error')

    return redirect(url_for('student.submit_project'))


@student_bp.route('/my-submissions')
@login_required
@role_required('student')
def my_submissions():
    submissions = current_app.supabase_service.get_submissions_by_student(current_user.id)
    # Convert submitted_at from string to datetime
    for s in submissions:
        if isinstance(s.get('submitted_at'), str):
            try:
                # Handles ISO format with or without 'Z'
                s['submitted_at'] = datetime.fromisoformat(s['submitted_at'].replace('Z', '+00:00'))
            except Exception:
                s['submitted_at'] = None
    return render_template('student/my_submissions.html', submissions=submissions)