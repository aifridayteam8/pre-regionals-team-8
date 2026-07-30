from flask import request, current_app, g
from flask_restx import Namespace, Resource, fields
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from backend.models.incident import Incident, IncidentEvent, db
from backend.utils.schemas import incident_create_schema, incident_update_schema
from backend.parsers.parser_factory import ParserFactory
from backend.auth.decorators import jwt_optional
from backend.services.incident_service import create_incident_from_log, resolve_incident
from marshmallow import ValidationError

incident_ns = Namespace('incidents', description='Incident operations')

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

# DTOs (documentation only — responses are returned as plain dicts so the
# parent/child + events envelope the frontend expects passes through intact).
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
    @jwt_optional
    def get(self):
        """List top-level incidents, each with nested child summaries."""
        severity = request.args.get('severity')
        status = request.args.get('status')
        search = request.args.get('search')

        query = Incident.query.filter(Incident.kind == 'parent')

        if severity:
            query = query.filter_by(severity=severity)
        if status:
            query = query.filter_by(status=status)
        if search:
            query = query.filter(
                Incident.title.ilike(f'%{search}%') |
                Incident.description.ilike(f'%{search}%')
            )

        parents = query.order_by(Incident.created_at.desc(), Incident.id.desc()).all()
        return {'incidents': [p.to_dict(include_children=True) for p in parents]}

    @incident_ns.doc('create_incident')
    @jwt_optional
    def post(self):
        """Create an incident.

        Two modes:
        * multipart form field ``file`` — parse the log into a parent incident
          plus one child per ``INCIDENT N`` section (the path the UI uses).
        * JSON body — create an empty incident from explicit fields.
        """
        uploaded = request.files.get('file')

        if uploaded is not None:
            data = uploaded.read()
            if not data:
                return {'message': 'Uploaded file is empty'}, 400
            if len(data) > MAX_UPLOAD_BYTES:
                return {'message': f'File too large (> {MAX_UPLOAD_BYTES} bytes)'}, 413

            filename = secure_filename(uploaded.filename or '') or 'upload.log'

            try:
                parent = create_incident_from_log(g.current_user_id, data, filename)
            except Exception as e:  # noqa: BLE001 - surface parse failures as 400
                db.session.rollback()
                return {'message': f'Error parsing log file: {e}'}, 400

            return {
                'parent_id': parent.incident_code,
                'child_ids': [c.incident_code for c in parent.children],
                'child_count': len(parent.children),
                'format': parent.format,
                'event_count': len(parent.events),
                'incident': parent.to_dict(include_children=True),
            }, 201

        try:
            data = incident_create_schema.load(request.json or {})
        except ValidationError as err:
            return {'message': 'Validation error', 'errors': err.messages}, 400

        incident = Incident(
            title=data['title'],
            description=data.get('description'),
            severity=data.get('severity', 'SEV4'),
            status=data.get('status', 'Open'),
            incident_type=data.get('incident_type'),
            source=data.get('source'),
            kind='parent',
            user_id=g.current_user_id
        )

        db.session.add(incident)
        db.session.commit()

        return incident.to_dict(), 201


@incident_ns.route('/<string:incident_id>')
class IncidentDetail(Resource):
    @incident_ns.doc('get_incident')
    @jwt_optional
    def get(self, incident_id):
        """Get one incident with its events (and children, for a parent)."""
        incident = resolve_incident(incident_id)
        if incident is None:
            return {'message': f'Incident {incident_id} not found'}, 404

        payload = {
            'incident': incident.to_dict(),
            'events': [e.to_dict() for e in sorted(
                incident.events, key=lambda e: (e.timestamp is None, e.timestamp, e.id)
            )],
        }
        if incident.kind == 'parent':
            payload['children'] = [c.to_dict() for c in incident.children]
        return payload

    @incident_ns.doc('update_incident')
    @jwt_optional
    @incident_ns.expect(incident_update_model)
    def put(self, incident_id):
        """Update incident."""
        try:
            data = incident_update_schema.load(request.json or {})
        except ValidationError as err:
            return {'message': 'Validation error', 'errors': err.messages}, 400

        incident = resolve_incident(incident_id)
        if incident is None:
            return {'message': f'Incident {incident_id} not found'}, 404

        for attr in ('title', 'description', 'severity', 'incident_type', 'source'):
            if attr in data:
                setattr(incident, attr, data[attr])

        if 'status' in data:
            incident.status = data['status']
            if data['status'].lower() in ('resolved', 'closed') and not incident.resolved_at:
                incident.resolved_at = datetime.utcnow()
            # Children track the parent's status.
            for child in incident.children:
                child.status = incident.status

        db.session.commit()
        return incident.to_dict(include_children=True)

    @incident_ns.doc('delete_incident')
    @jwt_optional
    def delete(self, incident_id):
        """Delete incident (cascades to children and events)."""
        incident = resolve_incident(incident_id)
        if incident is None:
            return {'message': f'Incident {incident_id} not found'}, 404
        db.session.delete(incident)
        db.session.commit()
        return {'message': 'Incident deleted successfully'}, 200


@incident_ns.route('/<string:incident_id>/upload')
class IncidentUpload(Resource):
    @incident_ns.doc('upload_log_file')
    @jwt_optional
    def post(self, incident_id):
        """Attach and parse a log file for an existing incident."""
        incident = resolve_incident(incident_id)
        if incident is None:
            return {'message': f'Incident {incident_id} not found'}, 404

        if 'file' not in request.files:
            return {'message': 'No file provided'}, 400

        file = request.files['file']
        data = file.read()
        if not data:
            return {'message': 'Uploaded file is empty'}, 400
        if len(data) > MAX_UPLOAD_BYTES:
            return {'message': f'File too large (> {MAX_UPLOAD_BYTES} bytes)'}, 413

        filename = secure_filename(file.filename or '') or 'upload.log'
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'log'

        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        with open(upload_path, 'wb') as f:
            f.write(data)

        incident.log_file_path = upload_path
        incident.log_file_type = file_ext
        incident.source_filename = filename

        try:
            parser = ParserFactory.get_parser(file_ext)
            events = parser.parse_content(data.decode('utf-8', errors='replace'))

            IncidentEvent.query.filter_by(incident_id=incident.id).delete()

            for event_data in events:
                db.session.add(IncidentEvent(
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
                ))

            db.session.commit()

            return {
                'message': 'File uploaded and parsed successfully',
                'file_path': upload_path,
                'events_count': len(events)
            }, 200

        except Exception as e:  # noqa: BLE001
            db.session.rollback()
            return {'message': f'Error parsing file: {str(e)}'}, 500


@incident_ns.route('/<string:incident_id>/events')
class IncidentEvents(Resource):
    @incident_ns.doc('get_incident_events')
    @jwt_optional
    def get(self, incident_id):
        """Get events for an incident."""
        incident = resolve_incident(incident_id)
        if incident is None:
            return {'message': f'Incident {incident_id} not found'}, 404

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 200, type=int)
        level = request.args.get('level')

        query = IncidentEvent.query.filter_by(incident_id=incident.id)
        if level:
            query = query.filter_by(level=level)
        query = query.order_by(IncidentEvent.timestamp.asc(), IncidentEvent.id.asc())

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
    @jwt_optional
    @incident_ns.expect(incident_text_model)
    def post(self):
        """Create incident from pasted log text."""
        data = request.json or {}

        if 'log_text' not in data:
            return {'message': 'log_text is required'}, 400

        log_text = data['log_text']
        log_type = data.get('log_type', 'azure')
        filename = data.get('filename', f'pasted.{log_type}')

        if log_type in ('azure', 'log', 'txt'):
            try:
                parent = create_incident_from_log(
                    g.current_user_id, log_text.encode('utf-8'), filename
                )
            except Exception as e:  # noqa: BLE001
                db.session.rollback()
                return {'message': f'Error processing log text: {e}'}, 400

            return {
                'parent_id': parent.incident_code,
                'child_ids': [c.incident_code for c in parent.children],
                'incident': parent.to_dict(include_children=True),
            }, 201

        # Other formats keep the flat parser path.
        try:
            parser = ParserFactory.get_parser(log_type)
            events = parser.parse_content(log_text)
        except ValueError as e:
            return {'message': f'Unsupported log type: {str(e)}'}, 400

        if not events:
            return {'message': 'No events parsed from the provided text'}, 400

        incident = Incident(
            title=data.get('title', f'Incident from {log_type} log'),
            description=data.get('description'),
            severity=data.get('severity', 'SEV3'),
            status=data.get('status', 'Open'),
            incident_type=data.get('incident_type'),
            source=log_type,
            kind='parent',
            user_id=g.current_user_id,
            log_file_type=log_type,
            source_filename=filename,
        )
        db.session.add(incident)
        db.session.flush()

        for event_data in events:
            db.session.add(IncidentEvent(
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
            ))

        db.session.commit()
        return incident.to_dict(), 201
