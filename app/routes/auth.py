from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.utils.decorators import anonymous_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('auth/login.html')

        # Access service from app context
        supabase_service = current_app.supabase_service
        auth_user = supabase_service.authenticate_user(email, password)

        if auth_user:
            user = User.get_by_id(auth_user.id)
            if user:
                login_user(user)
                flash('Login successful!', 'success')

                if user.is_admin():
                    return redirect(url_for('admin.dashboard'))
                elif user.is_parent():
                    return redirect(url_for('parent.dashboard'))
                else:
                    return redirect(url_for('student.dashboard'))
            else:
                flash('User profile not found.', 'error')
        else:
            flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')



@auth_bp.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        grade_level = request.form.get('grade_level')

        # Basic validation
        if not all([email, password, confirm_password, full_name, role]):
            flash('Please fill in all required fields.', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/register.html')

        supabase_service = current_app.supabase_service
        user_data = {
            'full_name': full_name,
            'role': role,
            'grade_level': grade_level if role == 'student' else None
        }

        try:
            auth_user, profile_data = supabase_service.create_user(email, password, user_data)
        except Exception as e:
            print("ERROR creating user:", e)
            flash(f"Registration error: {str(e)}", 'error')
            return render_template('auth/register.html')

        if auth_user and profile_data:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registration failed. Possible duplicate, invalid fields, or backend problem.', 'error')
            # Optionally: print more debug info
            print("Registration returned:", auth_user, profile_data)
            return render_template('auth/register.html')

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
