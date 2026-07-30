from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from backend.models.incident import Incident, IncidentEvent, db
from backend.models.user import User
from backend.utils.schemas import incident_create_schema, incident_update_schema
from backend.utils.validators import validate_file
from backend.parsers.parser_factory import ParserFactory
from marshmallow import ValidationError

incident_ns = Namespace('incidents', description='Incident operations')

# DTOs
incident_model = incident_ns.model('Incident', {
    'id': fields.Integer,
    'title': fields.String,
    'description': fields.String,
    'severity': fields.String,
    'status': fields.String,
    'incident_type': fields.String,
    'source': fields.String,
    'detected_at': fields.String,
    'resolved_at': fields.String,
    'user_id': fields.Integer,
    'log_file_path': fields.String,
    'log_file_type': fields.String,
    'created_at': fields.String,
    'updated_at': fields.String,
    'event_count': fields.Integer
})

incident_create_model = incident_ns.model('IncidentCreate', {
    'title': fields.String(required=True),
    'description': fields.String,
    'severity': fields.String,
    'status': fields.String,
    'incident_type': fields.String,
    'source': fields.String
})

incident_text_model = incident_ns.model('IncidentText', {
    'log_text': fields.String(required=True),
    'log_type': fields.String(required=True, description='File type: azure, json, csv, txt, syslog')
})

incident_update_model = incident_ns.model('IncidentUpdate', {
    'title': fields.String,
    'description': fields.String,
    'severity': fields.String,
    'status': fields.String,
    'incident_type': fields.String,
    'source': fields.String,
    'resolved_at': fields.String
})


@incident_ns.route('')
class IncidentList(Resource):
    @incident_ns.doc('list_incidents')
    @jwt_required()
    @incident_ns.marshal_list_with(incident_model)
    def get(self):
        """List all incidents."""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        severity = request.args.get('severity')
        status = request.args.get('status')
        search = request.args.get('search')
        
        query = Incident.query
        
        if severity:
            query = query.filter_by(severity=severity)
        
        if status:
            query = query.filter_by(status=status)
        
        if search:
            query = query.filter(
                Incident.title.ilike(f'%{search}%') |
                Incident.description.ilike(f'%{search}%')
            )
        
        query = query.order_by(Incident.created_at.desc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return pagination.items
    
    @incident_ns.doc('create_incident')
    @jwt_required()
    @incident_ns.expect(incident_create_model)
    @incident_ns.marshal_with(incident_model, code=201)
    def post(self):
        """Create a new incident."""
        try:
            data = incident_create_schema.load(request.json)
        except ValidationError as err:
            return {'message': 'Validation error', 'errors': err.messages}, 400
        
        current_user_id = get_jwt_identity()
        
        incident = Incident(
            title=data['title'],
            description=data.get('description'),
            severity=data.get('severity', 'medium'),
            status=data.get('status', 'open'),
            incident_type=data.get('incident_type'),
            source=data.get('source'),
            user_id=current_user_id
        )
        
        db.session.add(incident)
        db.session.commit()
        
        return incident.to_dict(), 201


@incident_ns.route('/<int:incident_id>')
class IncidentDetail(Resource):
    @incident_ns.doc('get_incident')
    @jwt_required()
    @incident_ns.marshal_with(incident_model)
    def get(self, incident_id):
        """Get incident by ID."""
        incident = Incident.query.get_or_404(incident_id)
        return incident.to_dict()
    
    @incident_ns.doc('update_incident')
    @jwt_required()
    @incident_ns.expect(incident_update_model)
    @incident_ns.marshal_with(incident_model)
    def put(self, incident_id):
        """Update incident."""
        try:
            data = incident_update_schema.load(request.json)
        except ValidationError as err:
            return {'message': 'Validation error', 'errors': err.messages}, 400
        
        incident = Incident.query.get_or_404(incident_id)
        
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
        
        db.session.commit()
        
        return incident.to_dict()
    
    @incident_ns.doc('delete_incident')
    @jwt_required()
    def delete(self, incident_id):
        """Delete incident."""
        incident = Incident.query.get_or_404(incident_id)
        db.session.delete(incident)
        db.session.commit()
        return {'message': 'Incident deleted successfully'}, 200


@incident_ns.route('/<int:incident_id>/upload')
class IncidentUpload(Resource):
    @incident_ns.doc('upload_log_file')
    @jwt_required()
    def post(self, incident_id):
        """Upload log file for incident."""
        incident = Incident.query.get_or_404(incident_id)
        
        if 'file' not in request.files:
            return {'message': 'No file provided'}, 400
        
        file = request.files['file']
        
        is_valid, message = validate_file(file)
        if not is_valid:
            return {'message': message}, 400
        
        # Save file
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"incident_{incident_id}_{timestamp}.{file_ext}"
        
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)
        
        # Update incident
        incident.log_file_path = upload_path
        incident.log_file_type = file_ext
        
        # Parse and store events
        try:
            parser = ParserFactory.get_parser(file_ext)
            events = parser.parse(upload_path)
            
            # Clear existing events
            IncidentEvent.query.filter_by(incident_id=incident_id).delete()
            
            # Store new events
            for event_data in events:
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
            
            return {
                'message': 'File uploaded and parsed successfully',
                'file_path': upload_path,
                'events_count': len(events)
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error parsing file: {str(e)}'}, 500


@incident_ns.route('/<int:incident_id>/events')
class IncidentEvents(Resource):
    @incident_ns.doc('get_incident_events')
    @jwt_required()
    def get(self, incident_id):
        """Get events for an incident."""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        level = request.args.get('level')
        
        query = IncidentEvent.query.filter_by(incident_id=incident_id)
        
        if level:
            query = query.filter_by(level=level)
        
        query = query.order_by(IncidentEvent.timestamp.asc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'events': [event.to_dict() for event in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }


@incident_ns.route('/from-text')
class IncidentFromText(Resource):
    @incident_ns.doc('create_incident_from_text')
    @jwt_required()
    @incident_ns.expect(incident_text_model)
    @incident_ns.marshal_with(incident_model, code=201)
    def post(self):
        """Create incident from log text."""
        data = request.json
        
        if not data or 'log_text' not in data or 'log_type' not in data:
            return {'message': 'log_text and log_type are required'}, 400
        
        log_text = data['log_text']
        log_type = data['log_type']
        
        current_user_id = get_jwt_identity()
        
        # Parse the text
        try:
            parser = ParserFactory.get_parser(log_type)
            
            # Use parse_content if available, otherwise create temp file
            if hasattr(parser, 'parse_content'):
                events = parser.parse_content(log_text)
            else:
                # Fallback: create temp file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{log_type}', delete=False, encoding='utf-8') as f:
                    f.write(log_text)
                    temp_path = f.name
                
                try:
                    events = parser.parse(temp_path)
                finally:
                    import os
                    os.unlink(temp_path)
            
            if not events:
                return {'message': 'No events parsed from the provided text'}, 400
            
            # Create incident
            incident = Incident(
                title=data.get('title', f'Incident from {log_type} log'),
                description=data.get('description', f'Incident created from {log_type} log text'),
                severity=data.get('severity', 'medium'),
                status=data.get('status', 'open'),
                incident_type=data.get('incident_type'),
                source=data.get('source', log_type),
                user_id=current_user_id,
                log_file_type=log_type
            )
            
            db.session.add(incident)
            db.session.flush()
            
            # Store events
            for event_data in events:
                event = IncidentEvent(
                    incident_id=incident.id,
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
            
            return incident.to_dict(), 201
            
        except ValueError as e:
            return {'message': f'Unsupported log type: {str(e)}'}, 400
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error processing log text: {str(e)}'}, 500
