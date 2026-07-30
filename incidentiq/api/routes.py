from flask import Blueprint, jsonify, request

from services import parser, store

api = Blueprint("api", __name__)

MAX_BYTES = 5 * 1024 * 1024  # 5 MB upload cap


@api.get("/health")
def health():
    return jsonify(status="ok", service="incidentiq")


@api.post("/incidents")
def create_incident():
    """Upload a log file: parse into a parent incident + child incidents, then store."""
    file = request.files.get("file")
    if file is None:
        return jsonify(error="no file uploaded (expected multipart form field 'file')"), 400

    data = file.read()
    if not data:
        return jsonify(error="uploaded file is empty"), 400
    if len(data) > MAX_BYTES:
        return jsonify(error=f"file too large (> {MAX_BYTES} bytes)"), 413

    filename = file.filename or "upload.log"
    parsed = parser.parse_file(data, filename=filename)
    saved = store.save_file(parsed, filename=filename)
    parent = store.get_incident(saved["parent_id"])

    return (
        jsonify(
            parent_id=saved["parent_id"],
            child_ids=saved["child_ids"],
            format=parsed.format,
            child_count=len(saved["child_ids"]),
            incident=parent,
        ),
        201,
    )


@api.get("/incidents")
def list_incidents():
    """List top-level incidents, each with nested child summaries."""
    return jsonify(incidents=store.list_parents())


@api.get("/incidents/<incident_id>")
def get_incident(incident_id: str):
    """Full detail. Parents include their children + own events; children include events."""
    incident = store.get_incident(incident_id)
    if incident is None:
        return jsonify(error=f"incident {incident_id} not found"), 404

    payload = {"incident": incident, "events": store.get_events(incident_id)}
    if incident.get("kind") == "parent":
        payload["children"] = store.get_children(incident_id)
    return jsonify(payload)
