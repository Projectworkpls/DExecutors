from flask import Blueprint, render_template, current_app

ideas_bp = Blueprint('ideas', __name__)

@ideas_bp.route('/ideas')
def ideas():
    # Fetch all approved ideas/projects
    projects = current_app.supabase_service.get_projects_by_status('approved')
    return render_template('ideas.html', ideas=projects)

@ideas_bp.route('/ideas/<int:project_id>')
def idea_detail(project_id):
    project = current_app.supabase_service.get_client().table('projects').select('*').eq('id', project_id).execute()
    if not project.data:
        return render_template('404.html'), 404
    project = project.data[0]
    return render_template('idea_detail.html', project=project)
