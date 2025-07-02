from flask import Blueprint, render_template
from app.services.supabase_client import supabase_service

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Fetch open ideas/projects from Supabase
    projects_resp = supabase_service.get_projects({'status': 'open'})
    projects = projects_resp.data if projects_resp.data else []
    return render_template('index.html', projects=projects) 