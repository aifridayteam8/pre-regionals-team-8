from flask import request, current_app, send_file
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import json
from datetime import datetime
from backend.models.report import Report, db
from backend.models.incident import Incident, IncidentEvent
from backend.models.user import User
from backend.utils.schemas import report_create_schema, report_update_schema, report_generate_schema
from backend.ai.report_generator import ReportGenerator
from backend.config import get_config
from marshmallow import ValidationError

report_ns = Namespace('reports', description='Report operations')

# DTOs
report_model = report_ns.model('Report', {
    'id': fields.Integer,
    'incident_id': fields.Integer,
    'user_id': fields.Integer,
    'title': fields.String,
    'executive_summary': fields.String,
    'incident_overview': fields.String,
    'timeline': fields.String,
    'root_cause_analysis': fields.String,
    'impact_assessment': fields.String,
    'systems_affected': fields.String,
    'resolution_steps': fields.String,
    'recommendations': fields.String,
    'preventive_actions': fields.String,
    'lessons_learned': fields.String,
    'ai_model_used': fields.String,
    'confidence_score': fields.Float,
    'generation_time': fields.Float,
    'status': fields.String,
    'version': fields.Integer,
    'report_file_path': fields.String,
    'report_format': fields.String,
    'created_at': fields.String,
    'updated_at': fields.String
})

report_create_model = report_ns.model('ReportCreate', {
    'incident_id': fields.Integer(required=True),
    'title': fields.String(required=True)
})

report_update_model = report_ns.model('ReportUpdate', {
    'title': fields.String,
    'executive_summary': fields.String,
    'incident_overview': fields.String,
    'timeline': fields.String,
    'root_cause_analysis': fields.String,
    'impact_assessment': fields.String,
    'systems_affected': fields.String,
    'resolution_steps': fields.String,
    'recommendations': fields.String,
    'preventive_actions': fields.String,
    'lessons_learned': fields.String,
    'status': fields.String
})

report_generate_model = report_ns.model('ReportGenerate', {
    'incident_id': fields.Integer(required=True),
    'title': fields.String(required=True)
})


@report_ns.route('')
class ReportList(Resource):
    @report_ns.doc('list_reports')
    @jwt_required()
    def get(self):
        """List all reports."""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        incident_id = request.args.get('incident_id', type=int)
        
        query = Report.query
        
        if status:
            query = query.filter_by(status=status)
        
        if incident_id:
            query = query.filter_by(incident_id=incident_id)
        
        query = query.order_by(Report.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'reports': [report.to_summary_dict() for report in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }


@report_ns.route('/<int:report_id>')
class ReportDetail(Resource):
    @report_ns.doc('get_report')
    @jwt_required()
    @report_ns.marshal_with(report_model)
    def get(self, report_id):
        """Get report by ID."""
        report = Report.query.get_or_404(report_id)
        return report.to_dict()
    
    @report_ns.doc('update_report')
    @jwt_required()
    @report_ns.expect(report_update_model)
    @report_ns.marshal_with(report_model)
    def put(self, report_id):
        """Update report."""
        try:
            data = report_update_schema.load(request.json)
        except ValidationError as err:
            return {'message': 'Validation error', 'errors': err.messages}, 400
        
        report = Report.query.get_or_404(report_id)
        
        if 'title' in data:
            report.title = data['title']
        if 'executive_summary' in data:
            report.executive_summary = data['executive_summary']
        if 'incident_overview' in data:
            report.incident_overview = data['incident_overview']
        if 'timeline' in data:
            report.timeline = data['timeline']
        if 'root_cause_analysis' in data:
            report.root_cause_analysis = data['root_cause_analysis']
        if 'impact_assessment' in data:
            report.impact_assessment = data['impact_assessment']
        if 'systems_affected' in data:
            report.systems_affected = data['systems_affected']
        if 'resolution_steps' in data:
            report.resolution_steps = data['resolution_steps']
        if 'recommendations' in data:
            report.recommendations = data['recommendations']
        if 'preventive_actions' in data:
            report.preventive_actions = data['preventive_actions']
        if 'lessons_learned' in data:
            report.lessons_learned = data['lessons_learned']
        if 'status' in data:
            report.status = data['status']
        
        report.updated_at = datetime.utcnow()
        db.session.commit()
        
        return report.to_dict()
    
    @report_ns.doc('delete_report')
    @jwt_required()
    def delete(self, report_id):
        """Delete report."""
        report = Report.query.get_or_404(report_id)
        db.session.delete(report)
        db.session.commit()
        return {'message': 'Report deleted successfully'}, 200


@report_ns.route('/generate')
class ReportGenerate(Resource):
    @report_ns.doc('generate_report')
    @jwt_required()
    @report_ns.expect(report_generate_model)
    @report_ns.marshal_with(report_model, code=201)
    def post(self):
        """Generate AI-powered report."""
        try:
            data = report_generate_schema.load(request.json)
        except ValidationError as err:
            return {'message': 'Validation error', 'errors': err.messages}, 400
        
        current_user_id = get_jwt_identity()
        
        # Get incident
        incident = Incident.query.get_or_404(data['incident_id'])
        
        # Get events
        events = IncidentEvent.query.filter_by(incident_id=data['incident_id']).all()
        
        if not events:
            return {'message': 'No events found for this incident. Please upload log files first.'}, 400
        
        # Generate report
        config = get_config()
        generator = ReportGenerator(config)
        
        try:
            report_data = generator.generate_report(
                incident.to_dict(),
                [event.to_dict() for event in events]
            )
            
            # Create report record
            report = Report(
                incident_id=data['incident_id'],
                user_id=current_user_id,
                title=data['title'],
                executive_summary=report_data.get('executive_summary'),
                incident_overview=report_data.get('incident_overview'),
                timeline=report_data.get('timeline'),
                root_cause_analysis=report_data.get('root_cause_analysis'),
                impact_assessment=report_data.get('impact_assessment'),
                systems_affected=report_data.get('systems_affected'),
                resolution_steps=report_data.get('resolution_steps'),
                recommendations=report_data.get('recommendations'),
                preventive_actions=report_data.get('preventive_actions'),
                lessons_learned=report_data.get('lessons_learned'),
                ai_model_used=report_data.get('ai_model_used'),
                confidence_score=report_data.get('confidence_score'),
                generation_time=report_data.get('generation_time'),
                status='draft'
            )
            
            db.session.add(report)
            db.session.commit()
            
            return report.to_dict(), 201
            
        except Exception as e:
            return {'message': f'Error generating report: {str(e)}'}, 500


@report_ns.route('/<int:report_id>/download')
class ReportDownload(Resource):
    @report_ns.doc('download_report')
    @jwt_required()
    def get(self, report_id):
        """Download report in specified format."""
        report = Report.query.get_or_404(report_id)
        format_type = request.args.get('format', 'json')
        
        if format_type not in ['json', 'markdown', 'pdf']:
            return {'message': 'Invalid format. Supported: json, markdown, pdf'}, 400
        
        if format_type == 'json':
            return report.to_dict()
        
        elif format_type == 'markdown':
            markdown_content = self._generate_markdown(report)
            
            # Save to file
            filename = f"report_{report_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
            file_path = os.path.join(current_app.config['REPORTS_FOLDER'], filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Update report
            report.report_file_path = file_path
            report.report_format = 'markdown'
            db.session.commit()
            
            return send_file(file_path, as_attachment=True, download_name=filename)
        
        elif format_type == 'pdf':
            # PDF generation would require additional libraries
            # For now, return markdown and suggest conversion
            return {'message': 'PDF generation not implemented. Please download as markdown and convert.'}, 400
    
    def _generate_markdown(self, report) -> str:
        """Generate markdown content from report."""
        md = f"# {report.title}\n\n"
        md += f"**Generated by:** {report.ai_model_used}\n"
        md += f"**Confidence Score:** {report.confidence_score}\n"
        md += f"**Generated:** {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        md += "---\n\n"
        
        if report.executive_summary:
            md += "## Executive Summary\n\n"
            md += f"{report.executive_summary}\n\n"
        
        if report.incident_overview:
            md += "## Incident Overview\n\n"
            md += f"{report.incident_overview}\n\n"
        
        if report.timeline:
            md += "## Timeline\n\n"
            md += f"{report.timeline}\n\n"
        
        if report.root_cause_analysis:
            md += "## Root Cause Analysis\n\n"
            md += f"{report.root_cause_analysis}\n\n"
        
        if report.impact_assessment:
            md += "## Impact Assessment\n\n"
            md += f"{report.impact_assessment}\n\n"
        
        if report.systems_affected:
            md += "## Systems Affected\n\n"
            md += f"{report.systems_affected}\n\n"
        
        if report.resolution_steps:
            md += "## Resolution Steps\n\n"
            md += f"{report.resolution_steps}\n\n"
        
        if report.recommendations:
            md += "## Recommendations\n\n"
            md += f"{report.recommendations}\n\n"
        
        if report.preventive_actions:
            md += "## Preventive Actions\n\n"
            md += f"{report.preventive_actions}\n\n"
        
        if report.lessons_learned:
            md += "## Lessons Learned\n\n"
            md += f"{report.lessons_learned}\n\n"
        
        return md
