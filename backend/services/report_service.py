from typing import List, Dict, Optional
from datetime import datetime
from backend.models.report import Report, db
from backend.models.incident import Incident


class ReportService:
    """Service layer for report operations."""
    
    @staticmethod
    def create_report(user_id: int, incident_id: int, title: str) -> Report:
        """Create a new report."""
        report = Report(
            incident_id=incident_id,
            user_id=user_id,
            title=title,
            status='draft'
        )
        
        db.session.add(report)
        db.session.commit()
        
        return report
    
    @staticmethod
    def get_report(report_id: int) -> Optional[Report]:
        """Get report by ID."""
        return Report.query.get(report_id)
    
    @staticmethod
    def get_reports(user_id: Optional[int] = None, **filters) -> List[Report]:
        """Get reports with optional filters."""
        query = Report.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if 'incident_id' in filters:
            query = query.filter_by(incident_id=filters['incident_id'])
        
        if 'status' in filters:
            query = query.filter_by(status=filters['status'])
        
        return query.order_by(Report.created_at.desc()).all()
    
    @staticmethod
    def update_report(report_id: int, data: Dict) -> Optional[Report]:
        """Update report."""
        report = Report.query.get(report_id)
        
        if not report:
            return None
        
        updateable_fields = [
            'title', 'executive_summary', 'incident_overview', 'timeline',
            'root_cause_analysis', 'impact_assessment', 'systems_affected',
            'resolution_steps', 'recommendations', 'preventive_actions',
            'lessons_learned', 'status'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(report, field, data[field])
        
        report.updated_at = datetime.utcnow()
        db.session.commit()
        
        return report
    
    @staticmethod
    def delete_report(report_id: int) -> bool:
        """Delete report."""
        report = Report.query.get(report_id)
        
        if not report:
            return False
        
        db.session.delete(report)
        db.session.commit()
        
        return True
    
    @staticmethod
    def finalize_report(report_id: int) -> Optional[Report]:
        """Finalize a report (increment version and set status to final)."""
        report = Report.query.get(report_id)
        
        if not report:
            return None
        
        report.status = 'final'
        report.version += 1
        report.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return report
    
    @staticmethod
    def get_report_history(incident_id: int) -> List[Report]:
        """Get all reports for an incident."""
        return Report.query.filter_by(incident_id=incident_id).order_by(
            Report.version.desc()
        ).all()
