import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    INSTAMOJO_API_KEY = os.environ.get('INSTAMOJO_API_KEY')
    INSTAMOJO_AUTH_TOKEN = os.environ.get('INSTAMOJO_AUTH_TOKEN') 