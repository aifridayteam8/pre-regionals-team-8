from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from datetime import datetime, timedelta
from backend.models.incident import Incident, IncidentEvent, db
from backend.models.report import Report

analytics_ns = Namespace('analytics', description='Analytics operations')

# DTOs
analytics_model = analytics_ns.model('Analytics', {
    'total_incidents': fields.Integer,
    'incidents_by_severity': fields.Raw,
    'incidents_by_status': fields.Raw,
    'incidents_by_type': fields.Raw,
    'total_reports': fields.Integer,
    'avg_confidence_score': fields.Float,
    'recent_incidents': fields.List(fields.Raw),
    'incident_trend': fields.List(fields.Raw)
})


@analytics_ns.route('/dashboard')
class DashboardAnalytics(Resource):
    @analytics_ns.doc('get_dashboard_analytics')
    @jwt_required()
    @analytics_ns.marshal_with(analytics_model)
    def get(self):
        """Get dashboard analytics."""
        # Time range
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total incidents
        total_incidents = Incident.query.filter(
            Incident.created_at >= start_date
        ).count()
        
        # Incidents by severity
        incidents_by_severity = db.session.query(
            Incident.severity,
            func.count(Incident.id)
        ).filter(
            Incident.created_at >= start_date
        ).group_by(Incident.severity).all()
        
        severity_data = {severity: count for severity, count in incidents_by_severity}
        
        # Incidents by status
        incidents_by_status = db.session.query(
            Incident.status,
            func.count(Incident.id)
        ).filter(
            Incident.created_at >= start_date
        ).group_by(Incident.status).all()
        
        status_data = {status: count for status, count in incidents_by_status}
        
        # Incidents by type
        incidents_by_type = db.session.query(
            Incident.incident_type,
            func.count(Incident.id)
        ).filter(
            Incident.created_at >= start_date,
            Incident.incident_type.isnot(None)
        ).group_by(Incident.incident_type).all()
        
        type_data = {itype: count for itype, count in incidents_by_type}
        
        # Total reports
        total_reports = Report.query.filter(
            Report.created_at >= start_date
        ).count()
        
        # Average confidence score
        avg_confidence = db.session.query(
            func.avg(Report.confidence_score)
        ).filter(
            Report.created_at >= start_date
        ).scalar()
        
        # Recent incidents
        recent_incidents = Incident.query.filter(
            Incident.created_at >= start_date
        ).order_by(Incident.created_at.desc()).limit(5).all()
        
        # Incident trend (daily)
        incident_trend = db.session.query(
            func.date(Incident.created_at).label('date'),
            func.count(Incident.id).label('count')
        ).filter(
            Incident.created_at >= start_date
        ).group_by(func.date(Incident.created_at)).all()
        
        trend_data = [
            {'date': str(date), 'count': count}
            for date, count in incident_trend
        ]
        
        return {
            'total_incidents': total_incidents,
            'incidents_by_severity': severity_data,
            'incidents_by_status': status_data,
            'incidents_by_type': type_data,
            'total_reports': total_reports,
            'avg_confidence_score': float(avg_confidence) if avg_confidence else 0.0,
            'recent_incidents': [incident.to_dict() for incident in recent_incidents],
            'incident_trend': trend_data
        }


@analytics_ns.route('/incidents/timeline')
class IncidentTimeline(Resource):
    @analytics_ns.doc('get_incident_timeline')
    @jwt_required()
    def get(self):
        """Get incident timeline data."""
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        timeline = db.session.query(
            func.date(Incident.created_at).label('date'),
            func.count(Incident.id).label('count'),
            Incident.severity
        ).filter(
            Incident.created_at >= start_date
        ).group_by(
            func.date(Incident.created_at),
            Incident.severity
        ).all()
        
        result = {}
        for date, count, severity in timeline:
            date_str = str(date)
            if date_str not in result:
                result[date_str] = {}
            result[date_str][severity] = count
        
        return result


@analytics_ns.route('/reports/performance')
class ReportPerformance(Resource):
    @analytics_ns.doc('get_report_performance')
    @jwt_required()
    def get(self):
        """Get report generation performance metrics."""
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        reports = Report.query.filter(
            Report.created_at >= start_date
        ).all()
        
        if not reports:
            return {
                'total_reports': 0,
                'avg_generation_time': 0,
                'avg_confidence_score': 0,
                'reports_by_model': {},
                'reports_by_status': {}
            }
        
        avg_generation_time = sum(r.generation_time or 0 for r in reports) / len(reports)
        avg_confidence = sum(r.confidence_score or 0 for r in reports) / len(reports)
        
        # Reports by model
        reports_by_model = {}
        for report in reports:
            model = report.ai_model_used or 'unknown'
            reports_by_model[model] = reports_by_model.get(model, 0) + 1
        
        # Reports by status
        reports_by_status = {}
        for report in reports:
            status = report.status
            reports_by_status[status] = reports_by_status.get(status, 0) + 1
        
        return {
            'total_reports': len(reports),
            'avg_generation_time': round(avg_generation_time, 2),
            'avg_confidence_score': round(avg_confidence, 2),
            'reports_by_model': reports_by_model,
            'reports_by_status': reports_by_status
        }


@analytics_ns.route('/events/summary')
class EventsSummary(Resource):
    @analytics_ns.doc('get_events_summary')
    @jwt_required()
    def get(self):
        """Get events summary analytics."""
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total events
        total_events = IncidentEvent.query.filter(
            IncidentEvent.created_at >= start_date
        ).count()
        
        # Events by level
        events_by_level = db.session.query(
            IncidentEvent.level,
            func.count(IncidentEvent.id)
        ).filter(
            IncidentEvent.created_at >= start_date
        ).group_by(IncidentEvent.level).all()
        
        level_data = {level: count for level, count in events_by_level}
        
        # Events by source
        events_by_source = db.session.query(
            IncidentEvent.source,
            func.count(IncidentEvent.id)
        ).filter(
            IncidentEvent.created_at >= start_date,
            IncidentEvent.source.isnot(None)
        ).group_by(IncidentEvent.source).limit(10).all()
        
        source_data = {source: count for source, count in events_by_source}
        
        # Events by service
        events_by_service = db.session.query(
            IncidentEvent.service,
            func.count(IncidentEvent.id)
        ).filter(
            IncidentEvent.created_at >= start_date,
            IncidentEvent.service.isnot(None)
        ).group_by(IncidentEvent.service).limit(10).all()
        
        service_data = {service: count for service, count in events_by_service}
        
        return {
            'total_events': total_events,
            'events_by_level': level_data,
            'events_by_source': source_data,
            'events_by_service': service_data
        }
