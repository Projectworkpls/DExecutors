from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.supabase_client import supabase_service
import os
import uuid
from datetime import datetime
from postgrest.exceptions import APIError

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Load admin credentials from environment variables
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin123')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Admin login check
        if email == ADMIN_USER and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Admin logged in successfully!', 'success')
            return redirect(url_for('admin.dashboard'))

        # User login (parent/student)
        user_resp = supabase_service.supabase.table('users').select('*').eq('email', email).execute()
        if user_resp.data and len(user_resp.data) > 0:
            user = user_resp.data[0]
            # WARNING: In production, use hashed passwords!
            if password == user.get('password'):
                session['user_id'] = user['id']
                # Store user_type as role in session
                session['role'] = user.get('user_type')  # 'ideator', 'executor', or 'both'
                flash('Logged in successfully!', 'success')
                # Redirect based on user_type
                if session['role'] == 'ideator':
                    return redirect(url_for('dashboard.parent_dashboard'))
                elif session['role'] == 'executor':
                    return redirect(url_for('dashboard.student_dashboard'))
                elif session['role'] == 'both':
                    # Customize as needed
                    return redirect(url_for('dashboard.parent_dashboard'))
                else:
                    flash('Unknown user role. Contact support.', 'error')
                    return redirect(url_for('auth.login'))
        flash('Invalid credentials', 'error')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Collect form data
        user_data = {
            'id': str(uuid.uuid4()),
            'username': request.form['username'],
            'email': request.form['email'],
            'password': request.form['password'],  # Hash in production!
            'user_type': request.form.get('user_type', 'executor'),  # Default to 'executor' (student)
            'created_at': datetime.utcnow().isoformat()
        }
        try:
            result = supabase_service.create_user(user_data)
            if result.data:
                flash('Account created! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Registration failed.', 'error')
        except APIError as e:
            # Handle duplicate username or email
            if hasattr(e, 'code') and e.code == '23505':
                flash('Username or email already exists. Please choose a different one.', 'error')
            else:
                print(f"APIError during registration: {e}")  # Debugging
                flash('An unexpected error occurred.', 'error')
        except Exception as e:
            print(f"Unexpected error during registration: {e}")  # Debugging
            flash('An unexpected error occurred.', 'error')
    return render_template('auth/register.html')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('admin_logged_in', None)
    session.pop('role', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.index'))
