import json
from datetime import datetime

from backend.database import db

# Internal lowercase level -> API display form (matches frontend log-level styles)
_LEVEL_DISPLAY = {
    "critical": "CRITICAL",
    "error": "ERROR",
    "warning": "WARN",
    "info": "INFO",
    "debug": "DEBUG",
}


class Incident(db.Model):
    """Incident model. A log file becomes one *parent* incident plus one *child*
    incident per ``INCIDENT N`` section (parent_id links children to parent)."""
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    incident_code = db.Column(db.String(40), unique=True, index=True)  # INC-YYYYMMDD-NN[-Cn]
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), default='SEV4')  # SEV1..SEV4
    status = db.Column(db.String(20), default='Open')  # Open, Investigating, Mitigated, Resolved, Closed
    incident_type = db.Column(db.String(100))  # category (Database, Key Vault, ...)
    source = db.Column(db.String(100))  # where the incident was detected

    # Hierarchy
    parent_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=True)
    kind = db.Column(db.String(10), default='parent')  # 'parent' | 'child'
    child_index = db.Column(db.Integer)

    # Parsed log context
    environment = db.Column(db.String(50))
    region = db.Column(db.String(50))
    correlation_id = db.Column(db.String(100))
    log_incident_id = db.Column(db.String(100))  # the log's own Incident ID
    format = db.Column(db.String(20))  # block | block-hier | flat

    # Timing / counts
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    duration_s = db.Column(db.Integer)
    error_count = db.Column(db.Integer, default=0)
    warn_count = db.Column(db.Integer, default=0)

    # Analysis sections extracted from the log
    root_cause = db.Column(db.Text)
    business_impact = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    final_summary = db.Column(db.Text)

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # File information
    log_file_path = db.Column(db.String(500))
    log_file_type = db.Column(db.String(20))
    source_filename = db.Column(db.String(255))

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    events = db.relationship('IncidentEvent', backref='incident', lazy=True,
                             cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='incident', lazy=True,
                              cascade='all, delete-orphan')
    children = db.relationship('Incident', backref=db.backref('parent', remote_side=[id]),
                               lazy=True, cascade='all, delete-orphan',
                               order_by='Incident.child_index')

    def to_dict(self, include_children=False):
        """Serialize with the field names the React frontend consumes."""
        data = {
            'id': self.id,
            'incident_id': self.incident_code or str(self.id),
            'parent_id': self.parent.incident_code if self.parent_id and self.parent else None,
            'kind': self.kind or 'parent',
            'child_index': self.child_index,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'status': self.status,
            'category': self.incident_type or 'Unknown',
            'source': self.source,
            'environment': self.environment,
            'region': self.region,
            'correlation_id': self.correlation_id,
            'log_incident_id': self.log_incident_id,
            'format': self.format,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'duration_s': self.duration_s,
            'event_count': len(self.events),
            'error_count': self.error_count or 0,
            'warn_count': self.warn_count or 0,
            'root_cause': self.root_cause,
            'business_impact': self.business_impact,
            'recommendations': self.recommendations,
            'final_summary': self.final_summary,
            'user_id': self.user_id,
            'source_filename': self.source_filename,
            'log_file_type': self.log_file_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_children:
            data['children'] = [child.to_dict() for child in self.children]
        return data

    def __repr__(self):
        return f'<Incident {self.incident_code or self.title}>'


class IncidentEvent(db.Model):
    """IncidentEvent model for storing individual log events."""
    __tablename__ = 'incident_events'

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)

    # Event details
    timestamp = db.Column(db.DateTime)
    level = db.Column(db.String(20))  # info, warning, error, critical, debug (lowercase)
    source = db.Column(db.String(100))
    message = db.Column(db.Text)
    raw_data = db.Column(db.Text)  # structured details as JSON

    # Parsed fields
    host = db.Column(db.String(100))
    service = db.Column(db.String(100))
    error_code = db.Column(db.String(50))
    correlation_id = db.Column(db.String(100))
    event_ref = db.Column(db.String(20))  # "E-0001" within its incident
    section = db.Column(db.String(120))  # log section (Main, INCIDENT 1 / ..., Rollback)
    line_no = db.Column(db.Integer)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def details(self):
        try:
            return json.loads(self.raw_data) if self.raw_data else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def to_dict(self):
        """Serialize with the field names the React frontend consumes."""
        details = self.details
        display_level = details.get('_severity_raw') or _LEVEL_DISPLAY.get(self.level, 'INFO')
        return {
            'db_id': self.id,
            'incident_id': self.incident.incident_code if self.incident else self.incident_id,
            'event_ref': self.event_ref,
            'ts': self.timestamp.isoformat() if self.timestamp else None,
            'severity': display_level,
            'level': self.level,
            'source': self.source,
            'service': self.service,
            'message': self.message,
            'host': self.host,
            'error_code': self.error_code,
            'correlation_id': self.correlation_id,
            'section': self.section,
            'line_no': self.line_no,
            'details': details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<IncidentEvent {self.id}>'
