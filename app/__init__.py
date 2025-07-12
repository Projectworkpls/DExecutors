from flask import Flask, redirect, url_for, send_from_directory, jsonify
from flask_login import LoginManager
from app.config import Config
import os

login_manager = LoginManager()


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

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.parent import parent_bp
    from app.routes.student import student_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(parent_bp, url_prefix='/parent')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Main route
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # Favicon route - return empty response to prevent 404s
    @app.route('/favicon.ico')
    def favicon():
        return '', 204

    # File upload route
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        upload_dir = os.path.join(app.root_path, 'uploads')
        return send_from_directory(upload_dir, filename)

    # Simple error handlers that don't rely on templates
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
