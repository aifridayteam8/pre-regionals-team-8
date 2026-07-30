import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app, db
from backend.models.user import User
from backend.models.incident import Incident, IncidentEvent
from backend.models.report import Report

def init_db():
    """Initialize the database tables."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Create a default user for testing
        existing_user = User.query.filter_by(username='testuser').first()
        if not existing_user:
            user = User(
                username='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                role='user',
                is_active=True
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            print("Default test user created!")
            print("Username: testuser")
            print("Password: password123")
        else:
            print("Test user already exists.")

if __name__ == '__main__':
    init_db()
