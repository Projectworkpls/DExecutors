from flask import Blueprint, render_template, session, redirect, url_for
from app.services.supabase_client import supabase_service

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def unified_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    # Get user data
    user_data = supabase_service.get_user(user_id)

    # Get user's projects (both created and applied to)
    my_projects = supabase_service.get_projects({'ideator_id': user_id})
    applied_projects = supabase_service.get_projects({'executor_id': user_id})

    # Get recent activity and leaderboard data
    recent_projects = supabase_service.get_projects()

    return render_template('dashboard/unified_dashboard.html',
                         user=user_data.data[0] if user_data.data else None,
                         my_projects=my_projects.data,
                         applied_projects=applied_projects.data,
                         recent_projects=recent_projects.data[:5]) 