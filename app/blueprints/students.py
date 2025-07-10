from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.supabase_client import supabase_service
from app.services.gemini_ai import gemini_service
import uuid
from datetime import datetime
from app.utils.auth import login_required
import json

students_bp = Blueprint('students', __name__, url_prefix='/students')

# Student Dashboard: My Submissions and Recent Opportunities
@students_bp.route('/dashboard')
@login_required
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'executor':
        flash('Access denied: Student account required.', 'error')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user_data = supabase_service.get_user(user_id)
    user = user_data.data[0] if user_data.data else None

    my_submissions = supabase_service.get_submissions({'student_id': user_id})
    recent_projects = supabase_service.get_projects({'status': 'open'})

    return render_template(
        'dashboard/student_dashboard.html',
        user=user,
        my_submissions=my_submissions.data if my_submissions and my_submissions.data else [],
        recent_projects=recent_projects.data[:5] if recent_projects and recent_projects.data else []
    )

# Submit a New Idea (Student)
@students_bp.route('/submit_idea', methods=['GET', 'POST'])
@login_required
def submit_idea():
    if 'user_id' not in session or session.get('role') != 'executor':
        flash('Access denied: Student account required.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        submission_data = {
            'id': str(uuid.uuid4()),
            'student_id': session['user_id'],
            'title': request.form['title'],
            'description': request.form['description'],
            'budget': float(request.form['budget']),
            'deadline': request.form['deadline'],
            'submitted_at': datetime.utcnow().isoformat(),
            'status': 'pending_review'
        }

        # AI Analysis of the project feasibility
        ai_analysis = gemini_service.analyze_project_feasibility(
            submission_data['title'],
            submission_data['description'],
            submission_data['budget'],
            submission_data['deadline']
        )
        submission_data['ai_analysis'] = ai_analysis

        # Save submission to the database
        result = supabase_service.create_submission(submission_data)

        if result.data:
            flash('Submission created and analyzed by AI!', 'success')
            return redirect(url_for('students.submission_analysis', submission_id=submission_data['id']))
        else:
            flash('Error creating submission', 'error')

    return render_template('students/submit_idea.html')

# View Submission AI Analysis Result
@students_bp.route('/submission_analysis/<submission_id>')
@login_required
def submission_analysis(submission_id):
    if 'user_id' not in session or session.get('role') != 'executor':
        flash('Access denied: Student account required.', 'error')
        return redirect(url_for('auth.login'))

    submission_resp = supabase_service.get_submissions({'id': submission_id})
    submission = submission_resp.data[0] if submission_resp.data else None
    ai_analysis = submission.get('ai_analysis', {}) if submission else {}
    return render_template('students/submission_analysis.html', submission=submission, analysis=ai_analysis)

# Browse Projects (for Students) with AI Analysis and Submission
@students_bp.route('/browse', methods=['GET', 'POST'])
@login_required
def browse_projects():
    if 'user_id' not in session or session.get('role') != 'executor':
        flash('Access denied: Student account required.', 'error')
        return redirect(url_for('auth.login'))

    analysis = None
    projects = supabase_service.get_projects({'status': 'open'})
    if request.method == 'POST':
        selected_title = request.form['project_title']
        selected_project = next((p for p in projects.data if p['title'] == selected_title), {})
        budget = selected_project.get('budget', 0)
        deadline = selected_project.get('deadline', '')
        description = request.form['submission_description']

        if request.form.get('action') == 'analyze':
            analysis = gemini_service.analyze_project_feasibility(
                selected_title,
                description,
                budget,
                deadline
            )
            # Store analysis and project in session for the result page
            session['analysis'] = analysis
            # Add student submission description to the project for context
            project_for_session = dict(selected_project)
            project_for_session['description'] = description
            session['analysis_project'] = project_for_session
            return redirect(url_for('students.analysis_results'))

        elif request.form.get('action') == 'submit':
            # Retrieve the analysis from the hidden field or session if needed
            ai_analysis = request.form.get('ai_analysis_json')
            if ai_analysis:
                try:
                    ai_analysis = json.loads(ai_analysis)
                except Exception:
                    ai_analysis = None
            else:
                ai_analysis = session.get('analysis')

            submission_data = {
                'id': str(uuid.uuid4()),
                'student_id': session['user_id'],
                'project_id': selected_project.get('id'),
                'title': selected_title,
                'description': description,
                'budget': budget,
                'deadline': deadline,
                'submitted_at': datetime.utcnow().isoformat(),
                'status': 'pending_review',
                'ai_analysis': ai_analysis
            }
            result = supabase_service.create_submission(submission_data)
            # Clear analysis from session after submission
            session.pop('analysis', None)
            session.pop('analysis_project', None)
            if result.data:
                flash('Project submitted for admin approval!', 'success')
            else:
                flash('Error submitting project.', 'error')
            return redirect(url_for('students.student_dashboard'))

    return render_template('students/browse_projects.html', projects=projects.data, analysis=analysis)

# Show AI Analysis Results (after Analyze with AI)
@students_bp.route('/analysis_results')
@login_required
def analysis_results():
    analysis = session.get('analysis')
    project = session.get('analysis_project')
    if not analysis or not project:
        flash("No analysis found. Please analyze a project first.", "error")
        return redirect(url_for('students.browse_projects'))
    return render_template('students/analysis_results.html', analysis=analysis, project=project)

# Apply for a Project (separate POST endpoint for "Apply" button)
@students_bp.route('/apply/<project_id>', methods=['POST'])
@login_required
def apply_for_project(project_id):
    if 'user_id' not in session or session.get('role') != 'executor':
        flash('Access denied: Student account required.', 'error')
        return redirect(url_for('auth.login'))

    application_data = {
        'id': str(uuid.uuid4()),
        'student_id': session['user_id'],
        'project_id': project_id,
        'applied_at': datetime.utcnow().isoformat(),
        'status': 'applied'
    }
    result = supabase_service.apply_for_project(application_data)
    if result.data:
        flash('Applied for project successfully!', 'success')
    else:
        flash('Error applying for project.', 'error')
    return redirect(url_for('students.browse_projects'))

