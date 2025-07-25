from flask import Flask, redirect, url_for, send_from_directory, jsonify, render_template , current_app
from flask_login import LoginManager
from app.config import Config
import os
import json



login_manager = LoginManager()


def from_json_filter(value):
    """Custom Jinja filter to safely parse JSON strings into dictionaries."""
    try:
        return json.loads(value)
    except Exception:
        return {}


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Validate configuration
    Config.validate_config()

    # Initialize extensions
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Initialize services WITHIN app context
    from app.services.supabase_service import SupabaseService
    from app.services.gemini_service import GeminiService
    from app.services.notification_service import NotificationService

    supabase_service = SupabaseService()
    gemini_service = GeminiService()
    notification_service = NotificationService()

    supabase_service.init_app(app)
    gemini_service.init_app(app)

    # Store services in app context for global access
    app.supabase_service = supabase_service
    app.gemini_service = gemini_service
    app.notification_service = notification_service

    # Register custom Jinja filter
    app.jinja_env.filters['from_json'] = from_json_filter

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.parent import parent_bp
    from app.routes.student import student_bp
    from app.routes.admin import admin_bp
    from app.routes.ideas import ideas_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(parent_bp, url_prefix='/parent')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ideas_bp)

    # Main route - landing page
    @app.route('/')
    def index():
    # Fetch all approved submissions with related project info
        submissions_response = current_app.supabase_service.get_client().table('submissions') \
            .select('*, projects(*)') \
            .eq('status', 'approved') \
            .execute()

        submissions = submissions_response.data or []

        # Filter submissions whose projects are marked show_on_landing_page = True
        visible_submissions = [s for s in submissions if s.get('projects') and s['projects'].get('show_on_landing_page')]

        return render_template('index.html', projectsVisible=visible_submissions)

        




    # Favicon route (prevent 404s)
    @app.route('/favicon.ico')
    def favicon():
        return '', 204

    # Serve uploaded files
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        upload_dir = os.path.join(app.root_path, 'uploads')
        return send_from_directory(upload_dir, filename)

    # Error handlers

    @app.errorhandler(404)
    def not_found_error(error):
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>404 - Page Not Found</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>404 - Page Not Found</h1>
            <p>The page you're looking for doesn't exist.</p>
            <a href="/auth/login">Go to Login</a>
        </body>
        </html>
        ''', 404

    @app.errorhandler(500)
    def internal_error(error):
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>500 - Server Error</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>500 - Internal Server Error</h1>
            <p>Something went wrong on our end.</p>
            <a href="/auth/login">Go to Login</a>
        </body>
        </html>
        ''', 500

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.get_by_id(user_id)
