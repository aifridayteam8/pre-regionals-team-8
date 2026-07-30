import pytest
from backend.models.user import User, db
from backend.models.incident import Incident, IncidentEvent
from backend.models.report import Report
from datetime import datetime


class TestUser:
    """Test User model."""
    
    def test_create_user(self, app):
        """Test user creation."""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User'
            )
            user.set_password('password123')
            
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.check_password('password123')
            assert not user.check_password('wrongpassword')
    
    def test_user_to_dict(self, app):
        """Test user serialization."""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com'
            )
            user.set_password('password123')
            
            db.session.add(user)
            db.session.commit()
            
            user_dict = user.to_dict()
            assert 'id' in user_dict
            assert 'username' in user_dict
            assert 'email' in user_dict
            assert 'password_hash' not in user_dict


class TestIncident:
    """Test Incident model."""
    
    def test_create_incident(self, app, test_user):
        """Test incident creation."""
        with app.app_context():
            incident = Incident(
                title='Test Incident',
                description='Test description',
                severity='high',
                status='open',
                incident_type='security',
                user_id=test_user.id
            )
            
            db.session.add(incident)
            db.session.commit()
            
            assert incident.id is not None
            assert incident.title == 'Test Incident'
            assert incident.severity == 'high'
            assert incident.status == 'open'
    
    def test_incident_to_dict(self, app, test_user):
        """Test incident serialization."""
        with app.app_context():
            incident = Incident(
                title='Test Incident',
                user_id=test_user.id
            )
            
            db.session.add(incident)
            db.session.commit()
            
            incident_dict = incident.to_dict()
            assert 'id' in incident_dict
            assert 'title' in incident_dict
            assert 'severity' in incident_dict


class TestIncidentEvent:
    """Test IncidentEvent model."""
    
    def test_create_event(self, app, test_incident):
        """Test event creation."""
        with app.app_context():
            event = IncidentEvent(
                incident_id=test_incident.id,
                timestamp=datetime.utcnow(),
                level='error',
                source='application',
                message='Test error message',
                raw_data='Raw log line'
            )
            
            db.session.add(event)
            db.session.commit()
            
            assert event.id is not None
            assert event.level == 'error'
            assert event.message == 'Test error message'


class TestReport:
    """Test Report model."""
    
    def test_create_report(self, app, test_user, test_incident):
        """Test report creation."""
        with app.app_context():
            report = Report(
                incident_id=test_incident.id,
                user_id=test_user.id,
                title='Test Report',
                executive_summary='Test summary',
                confidence_score=0.85
            )
            
            db.session.add(report)
            db.session.commit()
            
            assert report.id is not None
            assert report.title == 'Test Report'
            assert report.confidence_score == 0.85
            assert report.status == 'draft'
    
    def test_report_to_dict(self, app, test_user, test_incident):
        """Test report serialization."""
        with app.app_context():
            report = Report(
                incident_id=test_incident.id,
                user_id=test_user.id,
                title='Test Report'
            )
            
            db.session.add(report)
            db.session.commit()
            
            report_dict = report.to_dict()
            assert 'id' in report_dict
            assert 'title' in report_dict
            assert 'confidence_score' in report_dict
