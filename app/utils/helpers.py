import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'pdf', 'doc', 'docx'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_file_to_storage(file, filename):
    """Upload file to local storage"""
    try:
        # Create unique filename
        unique_filename = f"{uuid.uuid4()}_{secure_filename(filename)}"

        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # Return URL (for local development)
        return f"/uploads/{unique_filename}"

    except Exception as e:
        print(f"Error uploading file: {e}")
        return None


def format_datetime(dt):
    """Format datetime for display"""
    if dt:
        if isinstance(dt, str):
            # Handle string datetime
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except:
                return dt
        return dt.strftime('%B %d, %Y at %I:%M %p')
    return 'N/A'


def calculate_points_with_bonus(base_points, submission_date, due_date, quality_score):
    """Calculate points with bonuses and penalties"""
    points = base_points

    # Convert string dates to datetime if needed
    if isinstance(submission_date, str):
        submission_date = datetime.fromisoformat(submission_date.replace('Z', '+00:00'))
    if isinstance(due_date, str):
        due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))

    # Early submission bonus
    if submission_date < due_date:
        days_early = (due_date - submission_date).days
        if days_early >= 3:
            points += int(base_points * 0.1)  # 10% bonus for early submission

    # Late submission penalty
    elif submission_date > due_date:
        days_late = (submission_date - due_date).days
        penalty = min(days_late * 0.05, 0.5)  # 5% per day, max 50% penalty
        points = int(points * (1 - penalty))

    # Quality bonus
    if quality_score >= 90:
        points += int(base_points * 0.2)  # 20% bonus for exceptional work
    elif quality_score >= 80:
        points += int(base_points * 0.1)  # 10% bonus for good work

    return max(points, 1)  # Minimum 1 point


def send_notification_email(to_email, subject, body):
    """Send notification email (placeholder)"""
    # This would integrate with your email service
    print(f"Email notification sent to {to_email}: {subject}")
    return True


def generate_project_summary(project_data):
    """Generate a summary of project for display"""
    ai_eval = project_data.get('ai_evaluation', {})

    # Handle JSON string conversion
    if isinstance(ai_eval, str):
        try:
            import json
            ai_eval = json.loads(ai_eval)
        except:
            ai_eval = {}

    summary = {
        'difficulty': ai_eval.get('feasibility', {}).get('difficulty_level', 'Unknown'),
        'estimated_hours': ai_eval.get('feasibility', {}).get('estimated_time_hours', 'Unknown'),
        'age_range': ai_eval.get('age_appropriateness', {}).get('recommended_age_range', 'Unknown'),
        'complexity_score': ai_eval.get('age_appropriateness', {}).get('complexity_score', 'Unknown')
    }

    return summary
