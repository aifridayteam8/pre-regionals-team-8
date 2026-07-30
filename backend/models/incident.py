from datetime import datetime
from backend.database import db


class Incident(db.Model):
    """Incident model for storing incident information."""
    __tablename__ = 'incidents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='open')  # open, investigating, resolved, closed
    incident_type = db.Column(db.String(50))  # security, performance, network, application, etc.
    source = db.Column(db.String(100))  # where the incident was detected
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # File information
    log_file_path = db.Column(db.String(500))
    log_file_type = db.Column(db.String(20))  # json, txt, csv, syslog
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    events = db.relationship('IncidentEvent', backref='incident', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='incident', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert incident to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'status': self.status,
            'incident_type': self.incident_type,
            'source': self.source,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'user_id': self.user_id,
            'log_file_path': self.log_file_path,
            'log_file_type': self.log_file_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'event_count': len(self.events)
        }
    
    def __repr__(self):
        return f'<Incident {self.title}>'


class IncidentEvent(db.Model):
    """IncidentEvent model for storing individual log events."""
    __tablename__ = 'incident_events'
    
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    
    # Event details
    timestamp = db.Column(db.DateTime)
    level = db.Column(db.String(20))  # info, warning, error, critical, debug
    source = db.Column(db.String(100))
    message = db.Column(db.Text)
    raw_data = db.Column(db.Text)  # Original raw log line
    
    # Parsed fields
    host = db.Column(db.String(100))
    service = db.Column(db.String(100))
    error_code = db.Column(db.String(50))
    correlation_id = db.Column(db.String(100))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert event to dictionary."""
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level,
            'source': self.source,
            'message': self.message,
            'raw_data': self.raw_data,
            'host': self.host,
            'service': self.service,
            'error_code': self.error_code,
            'correlation_id': self.correlation_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<IncidentEvent {self.id}>'
