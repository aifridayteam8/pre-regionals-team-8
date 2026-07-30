import pytest
from backend.app import create_app
from backend.models.user import db as user_db
from backend.models.incident import db as incident_db
from backend.models.report import db as report_db


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        user_db.create_all()
        incident_db.create_all()
        report_db.create_all()
        yield app
        user_db.drop_all()
        incident_db.drop_all()
        report_db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create test user."""
    with app.app_context():
        from backend.models.user import User
        user = User(
            username='testuser',
            email='test@example.com',
            role='analyst'
        )
        user.set_password('password123')
        user_db.session.add(user)
        user_db.session.commit()
        return user


@pytest.fixture
def test_incident(app, test_user):
    """Create test incident."""
    with app.app_context():
        from backend.models.incident import Incident
        incident = Incident(
            title='Test Incident',
            description='Test description',
            severity='medium',
            user_id=test_user.id
        )
        incident_db.session.add(incident)
        incident_db.session.commit()
        return incident


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers."""
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    token = response.json['access_token']
    return {'Authorization': f'Bearer {token}'}
