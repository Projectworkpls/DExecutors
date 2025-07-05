from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Dummy data stores for demonstration (replace with DB queries in real app)
parents_ideas = [
    {'id': 1, 'title': 'Eco-friendly school project', 'status': 'pending', 'submitted_by': 'parent1'},
    {'id': 2, 'title': 'Recycling awareness campaign', 'status': 'approved', 'submitted_by': 'parent2'}
]
students_submissions = [
    {'id': 1, 'idea_id': 1, 'student': 'student1', 'video_url': 'http://example.com/video1', 'status': 'pending'},
    {'id': 2, 'idea_id': 2, 'student': 'student2', 'video_url': 'http://example.com/video2', 'status': 'approved'}
]

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))  # Redirect to the unified login page

@admin_bp.before_request
def check_admin_login():
    # Only restrict dashboard and approval routes, not logout
    if request.endpoint and request.endpoint.startswith('admin.') and \
       request.endpoint not in ('admin.logout',) and \
       not session.get('admin_logged_in'):
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('auth.login'))

@admin_bp.route('/dashboard')
def dashboard():
    # Show parents' ideas and students' submissions pending approval
    pending_parents_ideas = [idea for idea in parents_ideas if idea['status'] == 'pending']
    pending_students_submissions = [sub for sub in students_submissions if sub['status'] == 'pending']
    return render_template(
        'admin_dashboard.html',
        parents_ideas=pending_parents_ideas,
        students_submissions=pending_students_submissions
    )

@admin_bp.route('/approve_parent_idea/<int:idea_id>', methods=['POST'])
def approve_parent_idea(idea_id):
    for idea in parents_ideas:
        if idea['id'] == idea_id:
            idea['status'] = 'approved'
            flash(f'Parent idea "{idea["title"]}" approved.', 'success')
            break
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/approve_student_submission/<int:submission_id>', methods=['POST'])
def approve_student_submission(submission_id):
    for sub in students_submissions:
        if sub['id'] == submission_id:
            sub['status'] = 'approved'
            flash(f'Student submission for idea ID {sub["idea_id"]} approved.', 'success')
            break
    return redirect(url_for('admin.dashboard'))
