from app import create_app
import os

print("SUPABASE_URL:", os.environ.get("SUPABASE_URL"))
print("SUPABASE_KEY present:", bool(os.environ.get("SUPABASE_KEY")))

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
