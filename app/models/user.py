from flask_login import UserMixin
from flask import current_app


class User(UserMixin):
    def __init__(self, id, email, role, full_name=None, grade_level=None, points=0):
        self.id = id
        self.email = email
        self.role = role
        self.full_name = full_name
        self.grade_level = grade_level
        self.points = points

    @staticmethod
    def get_by_id(user_id):
        try:
            supabase_service = current_app.supabase_service
            user_data = supabase_service.get_user_profile(user_id)

            if user_data:
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    role=user_data['role'],
                    full_name=user_data.get('full_name'),
                    grade_level=user_data.get('grade_level'),
                    points=user_data.get('points', 0)
                )
        except Exception as e:
            print(f"Error in get_by_id: {e}")
        return None

    @staticmethod
    def get_by_email(email):
        try:
            supabase_service = current_app.supabase_service
            response = supabase_service.get_client().table('users').select('*').eq('email', email).execute()
            if response.data:
                user_data = response.data[0]
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    role=user_data['role'],
                    full_name=user_data.get('full_name'),
                    grade_level=user_data.get('grade_level'),
                    points=user_data.get('points', 0)
                )
        except Exception as e:
            print(f"Error fetching user by email: {e}")
        return None

    def is_parent(self):
        return self.role == 'parent'

    def is_student(self):
        return self.role == 'student'

    def is_admin(self):
        return self.role == 'admin'
