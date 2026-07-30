import json
from typing import List, Dict, Optional
from datetime import datetime
from backend.models.incident import Incident, IncidentEvent, db
from backend.models.user import User
from backend.parsers.azure_parser import (
    ParsedEvent,
    parse_file,
    compute_severity,
    derive_status,
    derive_category,
    event_error_code,
)


def _next_incident_code() -> str:
    """INC-YYYYMMDD-NN with NN = daily counter over parent incidents."""
    day = datetime.utcnow().strftime('%Y%m%d')
    prefix = f'INC-{day}-'
    count = Incident.query.filter(
        Incident.kind == 'parent',
        Incident.incident_code.like(prefix + '%'),
    ).count()
    return f'{prefix}{count + 1:02d}'


def _make_events(parsed_events: List[ParsedEvent], correlation_id: Optional[str]) -> List[IncidentEvent]:
    return [
        IncidentEvent(
            timestamp=ev.ts.replace(tzinfo=None) if ev.ts else None,
            level=ev.level,
            source=ev.section or 'azure',
            message=ev.message,
            raw_data=json.dumps(ev.details, default=str),
            host=None,
            service=ev.service or None,
            error_code=event_error_code(ev.details),
            correlation_id=ev.details.get('CorrelationId') or correlation_id,
            event_ref=ev.ref,
            section=ev.section,
            line_no=ev.line_no,
        )
        for ev in parsed_events
    ]


def _timing(events: List[ParsedEvent]) -> dict:
    stamps = [e.ts for e in events if e.ts is not None]
    started = min(stamps).replace(tzinfo=None) if stamps else None
    ended = max(stamps).replace(tzinfo=None) if stamps else None
    duration = int((ended - started).total_seconds()) if started and ended else None
    return {
        'started_at': started,
        'ended_at': ended,
        'duration_s': duration,
        'error_count': sum(1 for e in events if e.level in ('error', 'critical')),
        'warn_count': sum(1 for e in events if e.level == 'warning'),
    }


def create_incident_from_log(user_id: int, raw: bytes, filename: str) -> Incident:
    """Parse a log file into a parent Incident (+ child Incidents) with events.

    Children inherit the parent's status and category — an open parent means
    its children are open too.
    """
    parsed = parse_file(raw, filename)
    meta = parsed.metadata
    correlation_id = meta.get('Correlation ID')
    all_events = list(parsed.parent_events) + [e for c in parsed.children for e in c.events]

    status = derive_status(parsed)
    category = derive_category(parsed)
    code = _next_incident_code()

    parent = Incident(
        incident_code=code,
        title=meta.get('Subscription Name') or filename,
        severity=parsed.parent_severity or compute_severity(all_events),
        status=status,
        incident_type=category,
        kind='parent',
        environment=meta.get('Environment'),
        region=meta.get('Region'),
        correlation_id=correlation_id,
        log_incident_id=meta.get('Incident ID'),
        format=parsed.format,
        root_cause=parsed.analysis.get('root_cause'),
        business_impact=parsed.analysis.get('business_impact'),
        recommendations=parsed.analysis.get('recommendations'),
        final_summary=parsed.analysis.get('final_summary'),
        user_id=user_id,
        source_filename=filename,
        source='upload',
        **_timing(all_events),
    )
    parent.events = _make_events(parsed.parent_events, correlation_id)

    for child_data in parsed.children:
        child = Incident(
            incident_code=f'{code}-C{child_data.index}',
            title=child_data.name or child_data.title,
            severity=compute_severity(child_data.events),
            status=status,  # inherit parent status
            incident_type=category,  # inherit parent category
            kind='child',
            child_index=child_data.index,
            environment=meta.get('Environment'),
            region=meta.get('Region'),
            correlation_id=correlation_id,
            log_incident_id=meta.get('Incident ID'),
            format='block',
            user_id=user_id,
            source_filename=filename,
            source='upload',
            **_timing(child_data.events),
        )
        child.events = _make_events(child_data.events, correlation_id)
        parent.children.append(child)

    db.session.add(parent)
    db.session.commit()
    return parent


def resolve_incident(identifier: str) -> Optional[Incident]:
    """Look up an incident by incident_code (INC-...) or numeric id."""
    incident = Incident.query.filter_by(incident_code=identifier).first()
    if incident is None and identifier.isdigit():
        incident = Incident.query.get(int(identifier))
    return incident


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
