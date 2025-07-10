from supabase import create_client, Client
import os

class SupabaseService:
    def __init__(self):
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_ANON_KEY')
        self.supabase: Client = create_client(url, key)

    def create_user(self, user_data):
        return self.supabase.table('users').insert(user_data).execute()

    def get_user(self, user_id):
        return self.supabase.table('users').select('*').eq('id', user_id).execute()

    def create_project(self, project_data):
        return self.supabase.table('projects').insert(project_data).execute()

    def get_projects(self, filters=None):
        query = self.supabase.table('projects').select('*')
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        return query.execute()

    # New: Create a submission (student submits work)
    def create_submission(self, submission_data):
        return self.supabase.table('work_submissions').insert(submission_data).execute()

    # New: Get submissions (student's submissions or all)
    def get_submissions(self, filters=None):
        query = self.supabase.table('work_submissions').select('*')
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        return query.execute()

supabase_service = SupabaseService()
