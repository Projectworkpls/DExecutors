from flask import current_app
from app.services.supabase_service import SupabaseService
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class NotificationService:
    def __init__(self):
        self.supabase_service = SupabaseService()

    def create_notification(self, user_id, title, message, notification_type='info'):
        """Create a new notification for a user"""
        try:
            notification_data = {
                'user_id': user_id,
                'title': title,
                'message': message,
                'type': notification_type,
                'read': False,
                'created_at': datetime.utcnow().isoformat()
            }

            response = self.supabase_service.get_client().table('notifications').insert(notification_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating notification: {e}")
            return None

    def get_user_notifications(self, user_id, limit=10):
        """Get notifications for a user"""
        try:
            response = self.supabase_service.get_client().table('notifications').select('*').eq('user_id',
                                                                                                user_id).order(
                'created_at', desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching notifications: {e}")
            return []

    def mark_notification_read(self, notification_id):
        """Mark a notification as read"""
        try:
            response = self.supabase_service.get_client().table('notifications').update({'read': True}).eq('id',
                                                                                                           notification_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return None

    def send_email_notification(self, to_email, subject, body):
        """Send email notification (placeholder implementation)"""
        try:
            # This is a placeholder - implement with your preferred email service
            print(f"Email notification sent to {to_email}")
            print(f"Subject: {subject}")
            print(f"Body: {body}")
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def notify_project_approved(self, project_data):
        """Notify parent when project is approved"""
        try:
            # Create in-app notification
            self.create_notification(
                user_id=project_data['parent_id'],
                title="Project Approved!",
                message=f"Your project '{project_data['title']}' has been approved and is now available for students.",
                notification_type='success'
            )

            # Send email notification
            parent_email = self.get_user_email(project_data['parent_id'])
            if parent_email:
                self.send_email_notification(
                    to_email=parent_email,
                    subject="Project Approved - Student Project Platform",
                    body=f"Great news! Your project '{project_data['title']}' has been approved and is now available for students to claim."
                )

            return True
        except Exception as e:
            print(f"Error sending project approval notification: {e}")
            return False

    def notify_project_claimed(self, project_data, student_data):
        """Notify parent when project is claimed by student"""
        try:
            # Create in-app notification
            self.create_notification(
                user_id=project_data['parent_id'],
                title="Project Claimed!",
                message=f"Your project '{project_data['title']}' has been claimed by {student_data['full_name']}.",
                notification_type='info'
            )

            return True
        except Exception as e:
            print(f"Error sending project claimed notification: {e}")
            return False

    def notify_submission_approved(self, submission_data, project_data):
        """Notify student when submission is approved"""
        try:
            # Create in-app notification
            self.create_notification(
                user_id=submission_data['student_id'],
                title="Submission Approved!",
                message=f"Your submission for '{project_data['title']}' has been approved! You earned {submission_data.get('points_awarded', 0)} points.",
                notification_type='success'
            )

            return True
        except Exception as e:
            print(f"Error sending submission approval notification: {e}")
            return False

    def notify_deadline_approaching(self, project_data, student_id):
        """Notify student when project deadline is approaching"""
        try:
            # Create in-app notification
            self.create_notification(
                user_id=student_id,
                title="Deadline Approaching",
                message=f"Your project '{project_data['title']}' is due soon. Don't forget to submit your work!",
                notification_type='warning'
            )

            return True
        except Exception as e:
            print(f"Error sending deadline notification: {e}")
            return False

    def get_user_email(self, user_id):
        """Get user email by ID"""
        try:
            response = self.supabase_service.get_client().table('users').select('email').eq('id', user_id).execute()
            return response.data[0]['email'] if response.data else None
        except Exception as e:
            print(f"Error fetching user email: {e}")
            return None
