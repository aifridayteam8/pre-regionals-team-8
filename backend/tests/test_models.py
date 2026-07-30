from datetime import datetime

from backend.database import db
from backend.models.user import User
from backend.models.incident import Incident, IncidentEvent
from backend.models.report import Report

# The `app` fixture already pushes an application context, so tests operate
# directly on db.session rather than pushing nested contexts.


class TestUser:
    """Test User model."""

    def test_create_user(self, app):
        """Test user creation."""
        user = User(
            username='alice',
            email='alice@example.com',
            first_name='Alice',
            last_name='Analyst'
        )
        user.set_password('password123')

        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == 'alice'
        assert user.check_password('password123')
        assert not user.check_password('wrongpassword')

    def test_user_to_dict(self, app):
        """Test user serialization omits the password hash."""
        user = User(username='bob', email='bob@example.com')
        user.set_password('password123')

        db.session.add(user)
        db.session.commit()

        user_dict = user.to_dict()
        assert 'id' in user_dict
        assert 'username' in user_dict
        assert 'password_hash' not in user_dict


class TestIncident:
    """Test Incident model."""

    def test_create_incident(self, app, test_user):
        """Test incident creation."""
        incident = Incident(
            title='Test Incident',
            description='Test description',
            severity='SEV2',
            status='Open',
            incident_type='Security',
            kind='parent',
            user_id=test_user.id
        )

        db.session.add(incident)
        db.session.commit()

        assert incident.id is not None
        assert incident.title == 'Test Incident'
        assert incident.severity == 'SEV2'
        assert incident.status == 'Open'

    def test_incident_to_dict(self, app, test_user):
        """Test incident serialization uses the API field names."""
        incident = Incident(
            title='Test Incident',
            incident_code='INC-20260730-99',
            severity='SEV3',
            user_id=test_user.id
        )

        db.session.add(incident)
        db.session.commit()

        incident_dict = incident.to_dict()
        assert incident_dict['incident_id'] == 'INC-20260730-99'
        assert incident_dict['severity'] == 'SEV3'
        assert incident_dict['event_count'] == 0
        assert 'category' in incident_dict

    def test_parent_child_hierarchy(self, app, test_user):
        """A parent incident exposes its children and they link back."""
        parent = Incident(
            title='Parent', incident_code='INC-20260730-50',
            severity='SEV1', status='Open', kind='parent', user_id=test_user.id
        )
        child = Incident(
            title='Child 1', incident_code='INC-20260730-50-C1',
            severity='SEV2', status='Open', kind='child', child_index=1,
            user_id=test_user.id
        )
        parent.children.append(child)

        db.session.add(parent)
        db.session.commit()

        data = parent.to_dict(include_children=True)
        assert len(data['children']) == 1
        assert data['children'][0]['incident_id'] == 'INC-20260730-50-C1'
        assert child.to_dict()['parent_id'] == 'INC-20260730-50'


class TestIncidentEvent:
    """Test IncidentEvent model."""

    def test_create_event(self, app, test_incident):
        """Test event creation."""
        event = IncidentEvent(
            incident_id=test_incident.id,
            timestamp=datetime(2026, 7, 30, 12, 0, 0),
            level='error',
            source='application',
            message='Test error message',
            raw_data='{"HTTP Status": "500 Internal Server Error"}',
            event_ref='E-0001',
            line_no=12,
        )

        db.session.add(event)
        db.session.commit()

        assert event.id is not None
        assert event.level == 'error'
        assert event.message == 'Test error message'

    def test_event_to_dict(self, app, test_incident):
        """Serialized events carry the fields the timeline UI reads."""
        event = IncidentEvent(
            incident_id=test_incident.id,
            timestamp=datetime(2026, 7, 30, 12, 0, 0),
            level='error',
            message='boom',
            raw_data='{"Error": "Boom"}',
            event_ref='E-0001',
            section='Main',
            line_no=7,
        )
        db.session.add(event)
        db.session.commit()

        data = event.to_dict()
        assert data['ts'] == '2026-07-30T12:00:00'
        assert data['severity'] == 'ERROR'
        assert data['section'] == 'Main'
        assert data['details'] == {'Error': 'Boom'}


class TestReport:
    """Test Report model."""

    def test_create_report(self, app, test_user, test_incident):
        """Test report creation."""
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
        report = Report(
            incident_id=test_incident.id,
            user_id=test_user.id,
            title='Test Report'
        )

        db.session.add(report)
        db.session.commit()

        report_dict = report.to_dict()
        assert 'id' in report_dict
        assert report_dict['title'] == 'Test Report'
