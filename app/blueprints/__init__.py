from .main import main_bp
from .auth import auth_bp
from .projects import projects_bp
from .dashboard import dashboard_bp
from .api import api_bp
from .admin import admin_bp
from .students import students_bp  # Make sure this file exists!

__all__ = [
    'main_bp',
    'auth_bp',
    'projects_bp',
    'dashboard_bp',
    'api_bp',
    'admin_bp',
    'students_bp',
]
