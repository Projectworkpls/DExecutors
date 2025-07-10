from flask import Flask
from flask_session import Session
from dotenv import load_dotenv
import os
from datetime import datetime

def create_app():
    # Load environment variables
    load_dotenv()

    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SESSION_TYPE'] = 'filesystem'

    # Initialize extensions
    Session(app)

    # Register blueprints (import from the blueprints package)
    from app.blueprints import (
        main_bp,
        auth_bp,
        projects_bp,
        dashboard_bp,
        api_bp,
        admin_bp,
        students_bp,
    )

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(students_bp)

    # Robust custom Jinja2 filter for date formatting
    @app.template_filter('date')
    def format_date(value, format='%d %b %Y'):
        """
        Formats a date for Jinja2 templates.
        - If value is a datetime, formats directly.
        - If value is a string, tries to parse as ISO format or Y-m-d.
        - Returns '' if value is None or empty.
        """
        if not value:
            return ''
        if isinstance(value, datetime):
            return value.strftime(format)
        if isinstance(value, str):
            # Try ISO format first
            try:
                dt = datetime.fromisoformat(value)
                return dt.strftime(format)
            except ValueError:
                # Try common date string format (customize as needed)
                try:
                    dt = datetime.strptime(value, "%Y-%m-%d")
                    return dt.strftime(format)
                except ValueError:
                    return value  # Return as is if parsing fails
        return str(value)

    return app
