"""SQLite persistence for parsed incidents and their structured events.

Auto-creates the schema on import. The database lives at ``data/incidents.db``
(gitignored). Tables:

- incidents: one row per processed log, with computed + banner metadata.
- events:    the structured, queryable event rows (ts, severity, service, ...).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from services.parser import ParseResult

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "incidents.db"

_SEVERITY_RANK = {"FATAL": 1, "CRITICAL": 1, "ERROR": 2, "WARN": 3, "INFO": 4, "DEBUG": 4}


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id      TEXT PRIMARY KEY,
                source_filename  TEXT,
                created_at       TEXT,
                format           TEXT,
                environment      TEXT,
                region           TEXT,
                correlation_id   TEXT,
                log_incident_id  TEXT,
                severity         TEXT,
                category         TEXT,
                status           TEXT,
                event_count      INTEGER,
                error_count      INTEGER,
                warn_count       INTEGER,
                started_at       TEXT,
                ended_at         TEXT,
                duration_s       INTEGER
            );

            CREATE TABLE IF NOT EXISTS events (
                db_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id  TEXT NOT NULL,
                event_ref    TEXT,
                line_no      INTEGER,
                ts           TEXT,
                severity     TEXT,
                service      TEXT,
                message      TEXT,
                details_json TEXT,
                FOREIGN KEY (incident_id) REFERENCES incidents (incident_id)
            );

            CREATE INDEX IF NOT EXISTS idx_events_incident ON events (incident_id);
            CREATE INDEX IF NOT EXISTS idx_events_severity ON events (severity);
            """
        )


def _next_incident_id(conn: sqlite3.Connection) -> str:
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"INC-{day}-"
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM incidents WHERE incident_id LIKE ?", (prefix + "%",)
    ).fetchone()
    return f"{prefix}{row['c'] + 1:02d}"


def _summarize(result: ParseResult) -> dict:
    """Compute incident-level fields from the parsed events + metadata."""
    events = result.events
    ranks = [_SEVERITY_RANK.get(e.severity, 4) for e in events] or [4]
    worst = min(ranks)
    severity = f"SEV{worst}"

    error_count = sum(1 for e in events if _SEVERITY_RANK.get(e.severity, 4) <= 2)
    warn_count = sum(1 for e in events if e.severity == "WARN")

    stamps = [e.ts for e in events if e.ts is not None]
    started = min(stamps) if stamps else None
    ended = max(stamps) if stamps else None
    duration = int((ended - started).total_seconds()) if started and ended else None

    # Pull the log's own incident summary if an "Incident Recorder" block exists.
    log_incident_id = category = status = None
    for ev, det in zip(events, result.details):
        if "Incident Recorder" in ev.service or "Incident" in det.get("Incident ID", ""):
            log_incident_id = det.get("Incident ID", log_incident_id)
            category = det.get("Category", category)
            status = det.get("Incident Status", status)

    return {
        "severity": severity,
        "category": category or "Unknown",
        "status": status or "Unknown",
        "log_incident_id": log_incident_id,
        "error_count": error_count,
        "warn_count": warn_count,
        "started_at": started.isoformat() if started else None,
        "ended_at": ended.isoformat() if ended else None,
        "duration_s": duration,
    }


def save(result: ParseResult, filename: str) -> str:
    """Persist a parsed incident and its events; returns the generated incident_id."""
    summary = _summarize(result)
    meta = result.metadata
    with _connect() as conn:
        incident_id = _next_incident_id(conn)
        conn.execute(
            """
            INSERT INTO incidents (
                incident_id, source_filename, created_at, format,
                environment, region, correlation_id, log_incident_id,
                severity, category, status,
                event_count, error_count, warn_count,
                started_at, ended_at, duration_s
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident_id,
                filename,
                datetime.now(timezone.utc).isoformat(),
                result.format,
                meta.get("Environment"),
                meta.get("Region"),
                meta.get("Correlation ID"),
                summary["log_incident_id"],
                summary["severity"],
                summary["category"],
                summary["status"],
                len(result.events),
                summary["error_count"],
                summary["warn_count"],
                summary["started_at"],
                summary["ended_at"],
                summary["duration_s"],
            ),
        )
        conn.executemany(
            """
            INSERT INTO events (
                incident_id, event_ref, line_no, ts, severity, service, message, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    incident_id,
                    ev.id,
                    ev.raw_line_no,
                    ev.ts.isoformat() if ev.ts else None,
                    ev.severity,
                    ev.service,
                    ev.message_masked,
                    json.dumps(det, default=str),
                )
                for ev, det in zip(result.events, result.details)
            ],
        )
    return incident_id


def list_incidents() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM incidents ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_incident(incident_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)
        ).fetchone()
        return dict(row) if row else None


def get_events(incident_id: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM events WHERE incident_id = ? ORDER BY db_id", (incident_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("details_json"):
                try:
                    d["details"] = json.loads(d["details_json"])
                except (json.JSONDecodeError, TypeError):
                    d["details"] = {}
            del d["details_json"]
            result.append(d)
        return result


# Create the schema as soon as the module is imported.
init_db()
