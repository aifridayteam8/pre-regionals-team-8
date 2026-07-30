from flask import Blueprint, jsonify, request

from services import parser, store

api = Blueprint("api", __name__)

MAX_BYTES = 5 * 1024 * 1024  # 5 MB upload cap


@api.get("/health")
def health():
    return jsonify(status="ok", service="incidentiq")


@api.post("/incidents")
def create_incident():
    """Upload a log file: parse unstructured text into structured events and store."""
    file = request.files.get("file")
    if file is None:
        return jsonify(error="no file uploaded (expected multipart form field 'file')"), 400

    data = file.read()
    if not data:
        return jsonify(error="uploaded file is empty"), 400
    if len(data) > MAX_BYTES:
        return jsonify(error=f"file too large (> {MAX_BYTES} bytes)"), 413

    result = parser.parse(data, filename=file.filename or "upload.log")
    incident_id = store.save(result, filename=file.filename or "upload.log")
    incident = store.get_incident(incident_id)

    return (
        jsonify(
            incident_id=incident_id,
            format=result.format,
            event_count=len(result.events),
            incident=incident,
        ),
        201,
    )


@api.get("/incidents")
def list_incidents():
    return jsonify(incidents=store.list_incidents())


@api.get("/incidents/<incident_id>")
def get_incident(incident_id: str):
    incident = store.get_incident(incident_id)
    if incident is None:
        return jsonify(error=f"incident {incident_id} not found"), 404
    return jsonify(incident=incident, events=store.get_events(incident_id))
