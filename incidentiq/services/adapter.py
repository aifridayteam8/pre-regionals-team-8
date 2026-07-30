"""Adapt incidentiq's rich parser output to the flat event-dict shape backend/ expects.

backend/'s routes build IncidentEvent rows from dicts shaped like
``base_parser.normalize_event()``. This lets the backend team import incidentiq's
parser (multi-incident + parent/child + structured details) as a drop-in
replacement for its AzureParser, without changing route code:

    from services.adapter import parse_azure_log
    events = parse_azure_log(raw_bytes, filename)   # -> list[dict]

Each dict carries the backend contract keys (timestamp, level, source, message,
raw_data, host, service, error_code, correlation_id). The full structured detail
map is preserved as JSON in ``raw_data`` so nothing is lost; parent/child context
is carried in ``source`` for teams that later add hierarchy to their model.
"""

from __future__ import annotations

import json
import re

from services.parser import IncidentFile, parse_file

# incidentiq severities -> backend's normalized levels (debug/info/warning/error/critical)
_LEVEL_MAP = {
    "FATAL": "critical",
    "CRITICAL": "critical",
    "ERROR": "error",
    "ALERT": "critical",
    "ALARM": "critical",
    "WARN": "warning",
    "WARNING": "warning",
    "INFO": "info",
    "DEBUG": "debug",
}

_STATUS_CODE_RE = re.compile(r"\s*(\d{3})")


def _level(severity: str | None) -> str:
    return _LEVEL_MAP.get((severity or "").upper(), "info")


def _error_code(details: dict) -> str | None:
    for key in ("Error", "Error Code", "Failure Code", "Failure Code", "code"):
        if details.get(key):
            return str(details[key])
    http_status = details.get("HTTP Status")
    if http_status:
        m = _STATUS_CODE_RE.match(str(http_status))
        if m:
            return m.group(1)
    return None


def _to_dicts(events, details, correlation_id, source):
    out = []
    for ev, det in zip(events, details):
        clean = {k: v for k, v in det.items() if k != "_section"}
        out.append(
            {
                "timestamp": ev.ts.isoformat() if ev.ts else None,
                "level": _level(ev.severity),
                "source": det.get("_section") or source,
                "message": ev.message_masked,
                "service": ev.service or None,
                "host": ev.host_token or None,
                "error_code": _error_code(det),
                "correlation_id": det.get("CorrelationId") or correlation_id,
                "raw_data": json.dumps(clean, default=str),
            }
        )
    return out


def to_backend_events(parsed: IncidentFile) -> list[dict]:
    """Flatten a parsed IncidentFile (parent + children) into backend event dicts."""
    correlation_id = parsed.metadata.get("Correlation ID")
    source = parsed.metadata.get("Incident ID") or "azure"

    events = _to_dicts(parsed.parent_events, parsed.parent_details, correlation_id, source)
    for child in parsed.children:
        events += _to_dicts(child.events, child.details, correlation_id, child.title)
    return events


def parse_azure_log(raw: bytes, filename: str = "") -> list[dict]:
    """Parse raw log bytes -> list of backend-shaped event dicts."""
    return to_backend_events(parse_file(raw, filename))


def parse_azure_content(text: str) -> list[dict]:
    """Parse log text -> list of backend-shaped event dicts."""
    return parse_azure_log(text.encode("utf-8"))
