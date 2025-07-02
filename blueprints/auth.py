from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.supabase_client import supabase_service
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']  # In real app, hash and verify
        user_resp = supabase_service.supabase.table('users').select('*').eq('email', email).execute()
        if user_resp.data and len(user_resp.data) > 0:
            user = user_resp.data[0]
            # Simplified password check (replace with real auth)
            if password == user.get('password'):
                session['user_id'] = user['id']
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard.unified_dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']  # In real app, hash password
        user_data = {
            'id': str(uuid.uuid4()),
            'email': email,
            'username': username,
            'password': password,
            'user_type': 'ideator',
            'reputation_xp': 0,
            'level': 1
        }
        result = supabase_service.create_user(user_data)
        if result.data:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registration failed', 'error')
    return render_template('auth/register.html')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.index')) 