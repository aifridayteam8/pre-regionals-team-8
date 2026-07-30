from typing import List, Dict, Optional
from backend.models.incident import IncidentEvent, db


class EventService:
    """Service layer for event operations."""
    
    @staticmethod
    def create_event(incident_id: int, event_data: Dict) -> IncidentEvent:
        """Create a new event."""
        event = IncidentEvent(
            incident_id=incident_id,
            timestamp=event_data.get('timestamp'),
            level=event_data.get('level'),
            source=event_data.get('source'),
            message=event_data.get('message'),
            raw_data=event_data.get('raw_data'),
            host=event_data.get('host'),
            service=event_data.get('service'),
            error_code=event_data.get('error_code'),
            correlation_id=event_data.get('correlation_id')
        )
        
        db.session.add(event)
        db.session.commit()
        
        return event
    
    @staticmethod
    def bulk_create_events(incident_id: int, events_data: List[Dict]) -> int:
        """Bulk create events for an incident."""
        # Clear existing events
        IncidentEvent.query.filter_by(incident_id=incident_id).delete()
        
        # Create new events
        for event_data in events_data:
            event = IncidentEvent(
                incident_id=incident_id,
                timestamp=event_data.get('timestamp'),
                level=event_data.get('level'),
                source=event_data.get('source'),
                message=event_data.get('message'),
                raw_data=event_data.get('raw_data'),
                host=event_data.get('host'),
                service=event_data.get('service'),
                error_code=event_data.get('error_code'),
                correlation_id=event_data.get('correlation_id')
            )
            db.session.add(event)
        
        db.session.commit()
        
        return len(events_data)
    
    @staticmethod
    def get_events(incident_id: int, **filters) -> List[IncidentEvent]:
        """Get events with optional filters."""
        query = IncidentEvent.query.filter_by(incident_id=incident_id)
        
        if 'level' in filters:
            query = query.filter_by(level=filters['level'])
        
        if 'source' in filters:
            query = query.filter_by(source=filters['source'])
        
        return query.order_by(IncidentEvent.timestamp.asc()).all()
    
    @staticmethod
    def get_event(event_id: int) -> Optional[IncidentEvent]:
        """Get event by ID."""
        return IncidentEvent.query.get(event_id)
    
    @staticmethod
    def get_events_by_correlation(correlation_id: str) -> List[IncidentEvent]:
        """Get events by correlation ID."""
        return IncidentEvent.query.filter_by(
            correlation_id=correlation_id
        ).order_by(IncidentEvent.timestamp.asc()).all()
    
    @staticmethod
    def get_error_events(incident_id: int) -> List[IncidentEvent]:
        """Get error and critical events."""
        return IncidentEvent.query.filter(
            IncidentEvent.incident_id == incident_id,
            IncidentEvent.level.in_(['error', 'critical'])
        ).order_by(IncidentEvent.timestamp.asc()).all()
    
    @staticmethod
    def get_event_statistics(incident_id: int) -> Dict:
        """Get statistics for events."""
        events = IncidentEvent.query.filter_by(incident_id=incident_id).all()
        
        stats = {
            'total': len(events),
            'by_level': {},
            'by_source': {},
            'by_service': {}
        }
        
        for event in events:
            # Count by level
            level = event.level or 'unknown'
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
            
            # Count by source
            source = event.source or 'unknown'
            stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
            
            # Count by service
            service = event.service or 'unknown'
            stats['by_service'][service] = stats['by_service'].get(service, 0) + 1
        
        return stats
