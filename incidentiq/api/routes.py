from flask import Blueprint, jsonify, request

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify(status="ok", service="incidentiq")


@api.post("/incidents")
def create_incident():
    # Phase 1 equivalent of the old Streamlit uploader: accept a file and echo
    # its name + size. The full ingest -> parse -> mask -> correlate -> timeline
    # -> pipeline -> validator -> store flow is wired in here in Phase 5.
    file = request.files.get("file")
    if file is None:
        return jsonify(error="no file uploaded (expected multipart form field 'file')"), 400
    data = file.read()
    return jsonify(filename=file.filename, size_bytes=len(data)), 201
