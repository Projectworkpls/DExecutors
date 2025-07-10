from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.services.supabase_client import supabase_service

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Parent Dashboard Route
@dashboard_bp.route('/parent')
def parent_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user_data = supabase_service.get_user(user_id)
    user = user_data.data[0] if user_data.data else None

    # Update: Use 'user_type' to match your schema (ideator = parent)
    if not user or user.get('user_type') != 'ideator':
        flash('Access denied: Parent account required.', 'error')
        return redirect(url_for('auth.login'))

    my_projects = supabase_service.get_projects({'ideator_id': user_id})
    recent_projects = supabase_service.get_projects()

    return render_template(
        'dashboard/parent_dashboard.html',
        user=user,
        my_projects=my_projects.data if my_projects and my_projects.data else [],
        recent_projects=recent_projects.data[:5] if recent_projects and recent_projects.data else []
    )

# Student Dashboard Route
@dashboard_bp.route('/student')
def student_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user_data = supabase_service.get_user(user_id)
    user = user_data.data[0] if user_data.data else None

    # Update: Use 'user_type' to match your schema (executor = student)
    if not user or user.get('user_type') != 'executor':
        flash('Access denied: Student account required.', 'error')
        return redirect(url_for('auth.login'))

    my_submissions = supabase_service.get_submissions({'student_id': user_id})
    recent_projects = supabase_service.get_projects()

    return render_template(
        'dashboard/student_dashboard.html',
        user=user,
        my_submissions=my_submissions.data if my_submissions and my_submissions.data else [],
        recent_projects=recent_projects.data[:5] if recent_projects and recent_projects.data else []
    )
