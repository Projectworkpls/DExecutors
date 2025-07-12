from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_required, current_user
from app.models.project import Project
from app.utils.decorators import role_required
import json

parent_bp = Blueprint('parent', __name__)


@parent_bp.route('/dashboard')
@login_required
@role_required('parent')
def dashboard():
    # Get parent's projects
    projects = current_app.supabase_service.get_projects_by_parent(current_user.id)
    project_objects = [Project.from_dict(p) for p in projects]

    # Categorize projects by status
    pending_projects = [p for p in project_objects if p.status == 'pending']
    approved_projects = [p for p in project_objects if p.status == 'approved']
    in_progress_projects = [p for p in project_objects if p.status in ['claimed', 'in_progress']]
    completed_projects = [p for p in project_objects if p.status == 'completed']

    return render_template('parent/dashboard.html',
                           pending_projects=pending_projects,
                           approved_projects=approved_projects,
                           in_progress_projects=in_progress_projects,
                           completed_projects=completed_projects)


@parent_bp.route('/post-idea', methods=['GET', 'POST'])
@login_required
@role_required('parent')
def post_idea():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        suggested_credits = int(request.form.get('suggested_credits', 10))
        target_age = request.form.get('target_age')

        if not all([title, description, target_age]):
            flash('Please fill in all required fields.', 'error')
            return render_template('parent/post_idea.html')

        # Access Gemini service from app context
        gemini_service = current_app.gemini_service

        # Start AI evaluation chat
        chat_result = gemini_service.start_project_evaluation_chat(title, description)

        if chat_result['success']:
            # Store project data and chat session in session
            session['temp_project'] = {
                'title': title,
                'description': description,
                'suggested_credits': suggested_credits,
                'target_age': target_age,
                'parent_id': current_user.id
            }
            session['chat_session'] = chat_result['chat_session']

            return render_template('parent/ai_evaluation_chat.html',
                                   initial_response=chat_result['response'],
                                   project_title=title)
        else:
            flash(
                f'AI evaluation unavailable: {chat_result.get("error", "Unknown error")}. Project saved without AI evaluation.',
                'warning')

            # Save project without AI evaluation
            supabase_service = current_app.supabase_service
            project_data = {
                'title': title,
                'description': description,
                'suggested_credits': suggested_credits,
                'target_age': target_age,
                'parent_id': current_user.id,
                'status': 'pending',
                'ai_evaluation': {},
                'evaluation_parameters': {}
            }

            created_project = supabase_service.create_project(project_data)

            if created_project:
                flash('Project idea submitted successfully! It will be reviewed by an admin.', 'success')
                return redirect(url_for('parent.dashboard'))
            else:
                flash('Failed to create project. Please try again.', 'error')

    return render_template('parent/post_idea.html')


@parent_bp.route('/ai-chat', methods=['POST'])
@login_required
@role_required('parent')
def ai_chat():
    user_response = request.json.get('message')
    chat_session = session.get('chat_session')

    if not chat_session:
        return jsonify({'error': 'Chat session not found'}), 400

    # Access Gemini service from app context
    gemini_service = current_app.gemini_service

    # Continue conversation
    result = gemini_service.continue_project_evaluation_chat(chat_session, user_response)

    if result['success']:
        return jsonify({'response': result['response']})
    else:
        return jsonify({'error': result['error']}), 500


@parent_bp.route('/finalize-evaluation', methods=['POST'])
@login_required
@role_required('parent')
def finalize_evaluation():
    chat_session = session.get('chat_session')
    temp_project = session.get('temp_project')

    if not chat_session or not temp_project:
        return jsonify({'error': 'Session data not found'}), 400

    # Get final evaluation
    evaluation_result = current_app.gemini_service.finalize_project_evaluation(chat_session)

    if evaluation_result['success']:
        # Create project with AI evaluation
        project_data = temp_project.copy()
        project_data.update({
            'status': 'pending',
            'ai_evaluation': evaluation_result['evaluation'],
            'evaluation_parameters': evaluation_result['evaluation'].get('evaluation_parameters', {}),
            'credits': evaluation_result['evaluation']['recommended_credits']['max_credits']
        })

        created_project = current_app.supabase_service.create_project(project_data)

        if created_project:
            # Clear session data
            session.pop('temp_project', None)
            session.pop('chat_session', None)

            flash('Project idea submitted successfully with AI evaluation! It will be reviewed by an admin.', 'success')
            return jsonify({'success': True, 'redirect': url_for('parent.dashboard')})
        else:
            return jsonify({'error': 'Failed to create project'}), 500
    else:
        return jsonify({'error': evaluation_result['error']}), 500


@parent_bp.route('/project/<int:project_id>')
@login_required
@role_required('parent')
def view_project(project_id):
    # Get project details
    try:
        response = current_app.supabase_service.get_client().table('projects').select('*').eq('id', project_id).eq('parent_id', current_user.id).execute()
        if not response.data:
            flash('Project not found.', 'error')
            return redirect(url_for('parent.dashboard'))

        project = Project.from_dict(response.data[0])

        # Get submissions if project is claimed
        submissions = []
        if project.status in ['claimed', 'in_progress', 'completed']:
            submissions_response = current_app.supabase_service.get_client().table('submissions').select('*, users(full_name)').eq('project_id', project_id).execute()
            submissions = submissions_response.data

        return render_template('parent/project_detail.html', project=project, submissions=submissions)

    except Exception as e:
        flash('Error loading project details.', 'error')
        return redirect(url_for('parent.dashboard'))
