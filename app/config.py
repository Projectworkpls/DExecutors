import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

    # Debug environment loading
    @classmethod
    def validate_config(cls):
        print("=== Configuration Validation ===")
        print(f"SECRET_KEY: {'✓' if cls.SECRET_KEY else '✗'}")
        print(f"SUPABASE_URL: {'✓' if cls.SUPABASE_URL else '✗'}")
        print(f"SUPABASE_KEY: {'✓' if cls.SUPABASE_KEY else '✗'}")
        print(f"GEMINI_API_KEY: {'✓' if cls.GEMINI_API_KEY else '✗'}")
        print("================================")
