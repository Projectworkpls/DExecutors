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
    """Parent dashboard showing all their projects categorized by status"""
    try:
        # Get parent's projects
        projects = current_app.supabase_service.get_projects_by_parent(current_user.id)
        project_objects = [Project.from_dict(p) for p in projects] if projects else []

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
    except Exception as e:
        flash('Error loading dashboard. Please try again.', 'error')
        print(f"Dashboard error: {e}")
        return render_template('parent/dashboard.html',
                               pending_projects=[],
                               approved_projects=[],
                               in_progress_projects=[],
                               completed_projects=[])


@parent_bp.route('/post-idea', methods=['GET', 'POST'])
@login_required
@role_required('parent')
def post_idea():
    """Handle project idea submission with AI evaluation"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        suggested_credits = request.form.get('suggested_credits', '10')
        target_age = request.form.get('target_age', '').strip()

        # Validation
        if not all([title, description, target_age]):
            flash('Please fill in all required fields.', 'error')
            return render_template('parent/post_idea.html')

        try:
            suggested_credits = int(suggested_credits)
        except ValueError:
            suggested_credits = 10

        # Access Gemini service from app context
        gemini_service = current_app.gemini_service

        # Start AI evaluation chat
        print(f"Starting AI evaluation for project: {title}")
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

            print("AI evaluation started successfully, redirecting to chat")
            return render_template('parent/ai_evaluation_chat.html',
                                   initial_response=chat_result['response'],
                                   project_title=title)
        else:
            print(f"AI evaluation failed: {chat_result.get('error')}")
            flash(
                f'AI evaluation unavailable: {chat_result.get("error", "Unknown error")}. Project saved without AI evaluation.',
                'warning')

            # Save project without AI evaluation
            supabase_service = current_app.supabase_service
            project_data = {
                'title': title,
                'description': description,
                'credits': suggested_credits,  # Use 'credits' instead of 'suggested_credits'
                'target_age': target_age,
                'parent_id': current_user.id,
                'status': 'pending',
                'ai_evaluation': {},
                'evaluation_parameters': {},
                'created_at': None  # Let Supabase handle this
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
    """Handle AI chat conversation during project evaluation"""
    try:
        user_response = request.json.get('message', '').strip()
        chat_session = session.get('chat_session')

        if not user_response:
            return jsonify({'error': 'Message cannot be empty'}), 400

        if not chat_session:
            return jsonify({'error': 'Chat session not found. Please start over.'}), 400

        # Access Gemini service from app context
        gemini_service = current_app.gemini_service

        # Continue conversation
        print(f"Continuing AI chat with message: {user_response[:50]}...")
        result = gemini_service.continue_project_evaluation_chat(chat_session, user_response)

        if result['success']:
            return jsonify({'response': result['response']})
        else:
            print(f"AI chat error: {result['error']}")
            return jsonify({'error': f"AI response error: {result['error']}"}), 500

    except Exception as e:
        print(f"AI chat exception: {e}")
        return jsonify({'error': 'An error occurred during chat. Please try again.'}), 500


@parent_bp.route('/finalize-evaluation', methods=['POST'])
@login_required
@role_required('parent')
def finalize_evaluation():
    """Finalize AI evaluation and create project with evaluation data"""
    try:
        chat_session = session.get('chat_session')
        temp_project = session.get('temp_project')

        if not chat_session or not temp_project:
            return jsonify({'error': 'Session data not found. Please start over.'}), 400

        # Get final evaluation from Gemini
        print("Finalizing AI evaluation...")
        evaluation_result = current_app.gemini_service.finalize_project_evaluation(chat_session)

        if evaluation_result['success']:
            # Create project with AI evaluation
            project_data = temp_project.copy()

            # Extract credits from AI evaluation
            ai_evaluation = evaluation_result['evaluation']
            recommended_credits = ai_evaluation.get('recommended_credits', {})
            max_credits = recommended_credits.get('max_credits', temp_project.get('suggested_credits', 10))

            project_data.update({
                'status': 'pending',
                'credits': max_credits,  # Use the AI recommended credits
                'ai_evaluation': ai_evaluation,
                'evaluation_parameters': ai_evaluation.get('evaluation_parameters', {}),
                'created_at': None  # Let Supabase handle this
            })

            # Remove suggested_credits if it exists (use credits instead)
            project_data.pop('suggested_credits', None)

            print(f"Creating project with AI evaluation: {project_data['title']}")
            created_project = current_app.supabase_service.create_project(project_data)

            if created_project:
                # Clear session data
                session.pop('temp_project', None)
                session.pop('chat_session', None)

                print("Project created successfully with AI evaluation")
                flash('Project idea submitted successfully with AI evaluation! It will be reviewed by an admin.',
                      'success')
                return jsonify({'success': True, 'redirect': url_for('parent.dashboard')})
            else:
                print("Failed to create project in database")
                return jsonify({'error': 'Failed to create project in database'}), 500
        else:
            print(f"AI evaluation finalization failed: {evaluation_result['error']}")
            return jsonify({'error': f"AI evaluation failed: {evaluation_result['error']}"}), 500

    except Exception as e:
        print(f"Finalize evaluation exception: {e}")
        return jsonify({'error': 'An error occurred while finalizing evaluation. Please try again.'}), 500


@parent_bp.route('/project/<int:project_id>')
@login_required
@role_required('parent')
def view_project(project_id):
    """View detailed project information and submissions"""
    try:
        # Get project details
        response = current_app.supabase_service.get_client().table('projects').select('*').eq('id', project_id).eq(
            'parent_id', current_user.id).execute()

        if not response.data:
            flash('Project not found.', 'error')
            return redirect(url_for('parent.dashboard'))

        project = Project.from_dict(response.data[0])

        # Get submissions if project is claimed
        submissions = []
        if project.status in ['claimed', 'in_progress', 'completed']:
            try:
                submissions_response = current_app.supabase_service.get_client().table('submissions').select(
                    '*, users(full_name)').eq('project_id', project_id).execute()
                submissions = submissions_response.data if submissions_response.data else []
            except Exception as e:
                print(f"Error fetching submissions: {e}")
                submissions = []

        return render_template('parent/project_detail.html', project=project, submissions=submissions)

    except Exception as e:
        print(f"Error loading project details: {e}")
        flash('Error loading project details.', 'error')
        return redirect(url_for('parent.dashboard'))


@parent_bp.route('/cancel-evaluation', methods=['POST'])
@login_required
@role_required('parent')
def cancel_evaluation():
    """Cancel AI evaluation and save project without evaluation"""
    try:
        temp_project = session.get('temp_project')

        if not temp_project:
            return jsonify({'error': 'No project data found'}), 400

        # Save project without AI evaluation
        project_data = temp_project.copy()
        project_data.update({
            'status': 'pending',
            'credits': temp_project.get('suggested_credits', 10),
            'ai_evaluation': {},
            'evaluation_parameters': {},
            'created_at': None
        })

        # Remove suggested_credits
        project_data.pop('suggested_credits', None)

        created_project = current_app.supabase_service.create_project(project_data)

        if created_project:
            # Clear session data
            session.pop('temp_project', None)
            session.pop('chat_session', None)

            flash('Project idea submitted successfully! It will be reviewed by an admin.', 'success')
            return jsonify({'success': True, 'redirect': url_for('parent.dashboard')})
        else:
            return jsonify({'error': 'Failed to create project'}), 500

    except Exception as e:
        print(f"Cancel evaluation error: {e}")
        return jsonify({'error': 'An error occurred while saving project'}), 500
