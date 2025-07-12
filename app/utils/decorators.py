from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def role_required(role):
    """Decorator to require specific user role"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('auth.login'))

            if current_user.role != role:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('auth.login'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def anonymous_required(f):
    """Decorator to require anonymous user (not logged in)"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            # Redirect based on user role
            if current_user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif current_user.is_parent():
                return redirect(url_for('parent.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        return f(*args, **kwargs)

    return decorated_function
