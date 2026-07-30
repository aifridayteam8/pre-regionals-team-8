from datetime import datetime
from backend.database import db


class Report(db.Model):
    """Report model for storing AI-generated incident reports."""
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Report content
    title = db.Column(db.String(200), nullable=False)
    executive_summary = db.Column(db.Text)
    incident_overview = db.Column(db.Text)
    timeline = db.Column(db.Text)
    root_cause_analysis = db.Column(db.Text)
    impact_assessment = db.Column(db.Text)
    systems_affected = db.Column(db.Text)
    resolution_steps = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    preventive_actions = db.Column(db.Text)
    lessons_learned = db.Column(db.Text)
    
    # AI metadata
    ai_model_used = db.Column(db.String(100))
    confidence_score = db.Column(db.Float)  # 0.0 to 1.0
    generation_time = db.Column(db.Float)  # seconds
    
    # Report status
    status = db.Column(db.String(20), default='draft')  # draft, final, archived
    version = db.Column(db.Integer, default=1)
    
    # File paths
    report_file_path = db.Column(db.String(500))
    report_format = db.Column(db.String(20))  # json, markdown, pdf
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert report to dictionary."""
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'user_id': self.user_id,
            'title': self.title,
            'executive_summary': self.executive_summary,
            'incident_overview': self.incident_overview,
            'timeline': self.timeline,
            'root_cause_analysis': self.root_cause_analysis,
            'impact_assessment': self.impact_assessment,
            'systems_affected': self.systems_affected,
            'resolution_steps': self.resolution_steps,
            'recommendations': self.recommendations,
            'preventive_actions': self.preventive_actions,
            'lessons_learned': self.lessons_learned,
            'ai_model_used': self.ai_model_used,
            'confidence_score': self.confidence_score,
            'generation_time': self.generation_time,
            'status': self.status,
            'version': self.version,
            'report_file_path': self.report_file_path,
            'report_format': self.report_format,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_summary_dict(self):
        """Convert report to summary dictionary (without full content)."""
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'user_id': self.user_id,
            'title': self.title,
            'executive_summary': self.executive_summary,
            'ai_model_used': self.ai_model_used,
            'confidence_score': self.confidence_score,
            'status': self.status,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Report {self.title}>'
