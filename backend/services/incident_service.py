from typing import List, Dict, Optional
from datetime import datetime
from backend.models.incident import Incident, IncidentEvent, db
from backend.models.user import User


class IncidentService:
    """Service layer for incident operations."""
    
    @staticmethod
    def create_incident(user_id: int, data: Dict) -> Incident:
        """Create a new incident."""
        incident = Incident(
            title=data['title'],
            description=data.get('description'),
            severity=data.get('severity', 'medium'),
            status=data.get('status', 'open'),
            incident_type=data.get('incident_type'),
            source=data.get('source'),
            user_id=user_id
        )
        
        db.session.add(incident)
        db.session.commit()
        
        return incident
    
    @staticmethod
    def get_incident(incident_id: int) -> Optional[Incident]:
        """Get incident by ID."""
        return Incident.query.get(incident_id)
    
    @staticmethod
    def get_incidents(user_id: Optional[int] = None, **filters) -> List[Incident]:
        """Get incidents with optional filters."""
        query = Incident.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if 'severity' in filters:
            query = query.filter_by(severity=filters['severity'])
        
        if 'status' in filters:
            query = query.filter_by(status=filters['status'])
        
        if 'search' in filters:
            search = filters['search']
            query = query.filter(
                Incident.title.ilike(f'%{search}%') |
                Incident.description.ilike(f'%{search}%')
            )
        
        return query.order_by(Incident.created_at.desc()).all()
    
    @staticmethod
    def update_incident(incident_id: int, data: Dict) -> Optional[Incident]:
        """Update incident."""
        incident = Incident.query.get(incident_id)
        
        if not incident:
            return None
        
        if 'title' in data:
            incident.title = data['title']
        if 'description' in data:
            incident.description = data['description']
        if 'severity' in data:
            incident.severity = data['severity']
        if 'status' in data:
            incident.status = data['status']
            if data['status'] == 'resolved' and not incident.resolved_at:
                incident.resolved_at = datetime.utcnow()
        if 'incident_type' in data:
            incident.incident_type = data['incident_type']
        if 'source' in data:
            incident.source = data['source']
        
        incident.updated_at = datetime.utcnow()
        db.session.commit()
        
        return incident
    
    @staticmethod
    def delete_incident(incident_id: int) -> bool:
        """Delete incident."""
        incident = Incident.query.get(incident_id)
        
        if not incident:
            return False
        
        db.session.delete(incident)
        db.session.commit()
        
        return True
    
    @staticmethod
    def correlate_events(incident_id: int) -> Dict:
        """Correlate events for an incident."""
        events = IncidentEvent.query.filter_by(incident_id=incident_id).all()
        
        correlation_data = {
            'total_events': len(events),
            'error_count': len([e for e in events if e.level in ['error', 'critical']]),
            'warning_count': len([e for e in events if e.level == 'warning']),
            'unique_sources': len(set(e.source for e in events if e.source)),
            'unique_services': len(set(e.service for e in events if e.service)),
            'time_span': None
        }
        
        if events:
            timestamps = [e.timestamp for e in events if e.timestamp]
            if timestamps:
                correlation_data['time_span'] = (max(timestamps) - min(timestamps)).total_seconds()
        
        return correlation_data
