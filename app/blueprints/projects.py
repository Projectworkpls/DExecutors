from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.supabase_client import supabase_service
from app.services.gemini_ai import gemini_service
import uuid
from datetime import datetime
from app.utils.auth import login_required

projects_bp = Blueprint('projects', __name__)

# Create Project (Parent posts an idea)
@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        project_data = {
            'id': str(uuid.uuid4()),
            'title': request.form['title'],
            'description': request.form['description'],
            'budget': float(request.form['budget']),
            'deadline': request.form['deadline'],
            'ideator_id': session['user_id'],
            'status': 'analyzing',
            'created_at': datetime.utcnow().isoformat()
        }

        # AI Analysis
        ai_analysis = gemini_service.analyze_project_feasibility(
            project_data['title'],
            project_data['description'],
            project_data['budget'],
            project_data['deadline']
        )

        # Store AI analysis and key fields
        project_data['ai_feasibility_analysis'] = ai_analysis
        project_data['ai_feasibility_score'] = ai_analysis.get('feasibility_score')
        project_data['milestones'] = ai_analysis.get('suggested_milestones', [])
        project_data['status'] = 'open'

        # Save to database
        result = supabase_service.create_project(project_data)

        if result.data:
            flash('Project created and analyzed successfully!', 'success')
            return redirect(url_for('projects.analysis_result', project_id=project_data['id']))
        else:
            flash('Error creating project', 'error')

    return render_template('projects/create.html')

# Browse Projects (for both parents and students)
@projects_bp.route('/browse')
def browse_projects():
    projects = supabase_service.get_projects({'status': 'open'})
    return render_template('projects/browse.html', projects=projects.data)

# Project Detail Page
@projects_bp.route('/<id>')
def project_detail(id):
    project_resp = supabase_service.get_projects({'id': id})
    project = project_resp.data[0] if project_resp.data else None
    return render_template('projects/detail.html', project=project)

# AI Analysis Result Page (after posting idea)
@projects_bp.route('/analysis_result/<project_id>')
@login_required
def analysis_result(project_id):
    project_resp = supabase_service.get_projects({'id': project_id})
    project = project_resp.data[0] if project_resp.data else None
    ai_analysis = project.get('ai_feasibility_analysis', {}) if project else {}
    return render_template('projects/analysis_result.html', project=project, analysis=ai_analysis)

# Confirm and Post Project (after parent reviews AI analysis)
@projects_bp.route('/confirm/<project_id>', methods=['POST'])
@login_required
def confirm_project(project_id):
    update_result = supabase_service.update_project_status(project_id, 'open')
    if update_result:
        flash('Project confirmed and posted!', 'success')
    else:
        flash('Error confirming project.', 'error')
    # Redirect to the correct dashboard based on user role
    role = session.get('role')
    if role == 'parent':
        return redirect(url_for('dashboard.parent_dashboard'))
    elif role == 'student':
        return redirect(url_for('dashboard.student_dashboard'))
    else:
        return redirect(url_for('auth.login'))
