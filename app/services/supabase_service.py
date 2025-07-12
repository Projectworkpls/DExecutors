from supabase import create_client, Client
from flask import current_app
import json
from datetime import datetime
import uuid
import hashlib


class SupabaseService:
    def __init__(self):
        self.client = None
        self._url = None
        self._key = None

    def init_app(self, app):
        try:
            self._url = app.config.get('SUPABASE_URL')
            self._key = app.config.get('SUPABASE_KEY')

            print(f"Initializing Supabase with URL: {self._url[:30]}..." if self._url else "No URL found")
            print(f"Supabase key present: {bool(self._key)}")

            if not self._url or not self._key:
                print("ERROR: Missing Supabase credentials in environment")
                self.client = None
                return

            self.client = create_client(self._url, self._key)
            print("Supabase client initialized successfully")

        except Exception as e:
            print(f"Failed to initialize Supabase client: {e}")
            self.client = None

    def get_client(self):
        if self.client is None:
            print("ERROR: Supabase client is None - reinitializing...")
            if self._url and self._key:
                try:
                    self.client = create_client(self._url, self._key)
                    print("Supabase client reinitialized successfully")
                except Exception as e:
                    print(f"Failed to reinitialize: {e}")
            return self.client
        return self.client

    def hash_password(self, password):
        """Simple password hashing"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, email, password, user_data):
        """Create user directly in database - bypass Supabase auth completely"""
        try:
            client = self.get_client()
            if client is None:
                print("Error: Supabase client is None")
                return None, None

            print(f"Creating user directly in database: {email}")

            # Generate a UUID for the user
            user_id = str(uuid.uuid4())

            # Hash the password
            password_hash = self.hash_password(password)

            # Create user profile directly in database using service role
            user_profile = {
                "id": user_id,
                "email": email,
                "role": user_data.get('role', 'student'),
                "full_name": user_data.get('full_name'),
                "grade_level": user_data.get('grade_level'),
                "points": 0,
                "password_hash": password_hash,
                "created_at": datetime.utcnow().isoformat()
            }

            # Use service role client to bypass RLS
            service_client = create_client(self._url, self._key)

            # Insert directly using service role
            response = service_client.table('users').insert(user_profile).execute()

            if response.data:
                print(f"User created successfully in database: {user_id}")

                # Create a mock user object
                class MockUser:
                    def __init__(self, user_id, email):
                        self.id = user_id
                        self.email = email

                mock_user = MockUser(user_id, email)
                return mock_user, response.data
            else:
                print("Failed to create user in database")
                return None, None

        except Exception as e:
            print(f"Error creating user: {e}")
            return None, None

    def authenticate_user(self, email, password):
        """Authenticate user using database only"""
        try:
            client = self.get_client()
            if client is None:
                return None

            # Hash the provided password
            password_hash = self.hash_password(password)

            # Check database directly
            response = client.table('users').select('*').eq('email', email).eq('password_hash', password_hash).execute()

            if response.data:
                user_data = response.data[0]

                # Create a mock user object
                class MockUser:
                    def __init__(self, user_data):
                        self.id = user_data['id']
                        self.email = user_data['email']

                return MockUser(user_data)

            return None

        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    def get_user_profile(self, user_id):
        """Get user profile by ID"""
        try:
            client = self.get_client()
            if client is None:
                return None

            response = client.table('users').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching user profile: {e}")
            return None

    # Project operations
    def create_project(self, project_data):
        """Create a new project"""
        try:
            client = self.get_client()
            if client is None:
                return None

            response = client.table('projects').insert(project_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating project: {e}")
            return None

    def get_projects_by_status(self, status):
        """Get projects by status"""
        try:
            client = self.get_client()
            if client is None:
                return []

            response = client.table('projects').select('*').eq('status', status).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching projects: {e}")
            return []

    def get_projects_by_parent(self, parent_id):
        """Get projects by parent ID"""
        try:
            client = self.get_client()
            if client is None:
                return []

            response = client.table('projects').select('*').eq('parent_id', parent_id).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching parent projects: {e}")
            return []

    def update_project_status(self, project_id, status, additional_data=None):
        """Update project status"""
        try:
            client = self.get_client()
            if client is None:
                return None

            update_data = {"status": status}
            if additional_data:
                update_data.update(additional_data)

            response = client.table('projects').update(update_data).eq('id', project_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating project: {e}")
            return None

    # Submission operations
    def create_submission(self, submission_data):
        """Create a new submission"""
        try:
            client = self.get_client()
            if client is None:
                return None

            response = client.table('submissions').insert(submission_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating submission: {e}")
            return None

    def get_submissions_by_student(self, student_id):
        """Get submissions by student ID"""
        try:
            client = self.get_client()
            if client is None:
                return []

            response = client.table('submissions').select('*, projects(*)').eq('student_id', student_id).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching submissions: {e}")
            return []

    def get_pending_submissions(self):
        """Get pending submissions"""
        try:
            client = self.get_client()
            if client is None:
                return []

            response = client.table('submissions').select('*, projects(*), users(*)').eq('status', 'pending').execute()
            return response.data
        except Exception as e:
            print(f"Error fetching pending submissions: {e}")
            return []

    def update_submission_status(self, submission_id, status, admin_feedback=None):
        """Update submission status"""
        try:
            client = self.get_client()
            if client is None:
                return None

            update_data = {"status": status}
            if admin_feedback:
                update_data["admin_feedback"] = admin_feedback

            response = client.table('submissions').update(update_data).eq('id', submission_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating submission: {e}")
            return None
