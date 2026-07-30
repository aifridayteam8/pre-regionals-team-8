import pytest
from backend.app import create_app
from backend.database import db


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create test user.

    Yields inside the app context so the instance stays bound to a live
    session for the duration of the test (returning it would detach it).
    """
    from backend.models.user import User

    user = User(
        username='testuser',
        email='test@example.com',
        role='analyst'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    yield user


@pytest.fixture
def test_incident(app, test_user):
    """Create test incident."""
    from backend.models.incident import Incident

    incident = Incident(
        title='Test Incident',
        description='Test description',
        severity='SEV3',
        status='Open',
        kind='parent',
        user_id=test_user.id
    )
    db.session.add(incident)
    db.session.commit()
    yield incident


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers."""
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    token = response.json['access_token']
    return {'Authorization': f'Bearer {token}'}
