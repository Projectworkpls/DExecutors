from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.supabase_client import supabase_service
from app.services.gemini_ai import gemini_service
import uuid
from datetime import datetime
from app.utils.auth import login_required

projects_bp = Blueprint('projects', __name__)

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

        project_data['ai_feasibility_score'] = ai_analysis['feasibility_score']
        project_data['milestones'] = ai_analysis['suggested_milestones']
        project_data['status'] = 'open'

        # Save to database
        result = supabase_service.create_project(project_data)

        if result.data:
            flash('Project created successfully!', 'success')
            return redirect(url_for('dashboard.unified_dashboard'))
        else:
            flash('Error creating project', 'error')

    return render_template('projects/create.html')

@projects_bp.route('/browse')
def browse_projects():
    projects = supabase_service.get_projects({'status': 'open'})
    return render_template('projects/browse.html', projects=projects.data)

@projects_bp.route('/<id>')
def project_detail(id):
    project_resp = supabase_service.supabase.table('projects').select('*').eq('id', id).execute()
    project = project_resp.data[0] if project_resp.data else None
    return render_template('projects/detail.html', project=project) 