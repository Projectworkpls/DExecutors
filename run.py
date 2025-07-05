from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app import create_app
from app.blueprints.admin import admin_bp

app = create_app()

# Register the admin blueprint (and any others) AFTER app is created
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
