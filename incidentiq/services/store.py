"""SQLite persistence for parsed incidents (parent/child) and their events.

Auto-creates the schema on import. The database lives at ``data/incidents.db``
(gitignored). Tables:

- incidents: one row per incident. A file becomes one *parent* row plus one
  *child* row per ``INCIDENT N`` section (parent_id links children to parent).
- events:    the structured, queryable event rows, owned by whichever incident
  (parent or child) they belong to.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from services.models import Event
from services.parser import IncidentFile

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "incidents.db"

_SEVERITY_RANK = {
    "FATAL": 1, "CRITICAL": 1, "ERROR": 2, "ALERT": 2, "ALARM": 2,
    "WARN": 3, "INFO": 4, "DEBUG": 4,
}


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def _db():
    """Connection context that commits on success and always CLOSES.

    sqlite3's own `with conn:` commits but leaves the connection open; this
    wrapper closes it so we don't leak connections / hold locks.
    """
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with _db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id      TEXT PRIMARY KEY,
                parent_id        TEXT,               -- NULL for top-level parents
                kind             TEXT,               -- 'parent' | 'child'
                child_index      INTEGER,
                title            TEXT,
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
                duration_s       INTEGER,
                root_cause       TEXT,
                business_impact  TEXT,
                recommendations  TEXT,
                final_summary    TEXT,
                FOREIGN KEY (parent_id) REFERENCES incidents (incident_id)
            );

            CREATE TABLE IF NOT EXISTS events (
                db_id        INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id  TEXT NOT NULL,
                event_ref    TEXT,
                section      TEXT,
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
            CREATE INDEX IF NOT EXISTS idx_incidents_parent ON incidents (parent_id);
            """
        )


def _next_incident_id(conn: sqlite3.Connection) -> str:
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"INC-{day}-"
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM incidents WHERE kind = 'parent' AND incident_id LIKE ?",
        (prefix + "%",),
    ).fetchone()
    return f"{prefix}{row['c'] + 1:02d}"


def _summarize(events: list[Event]) -> dict:
    """Compute severity / counts / timing from a set of events."""
    ranks = [_SEVERITY_RANK.get(e.severity, 4) for e in events] or [4]
    stamps = [e.ts for e in events if e.ts is not None]
    started = min(stamps) if stamps else None
    ended = max(stamps) if stamps else None
    return {
        "severity": f"SEV{min(ranks)}",
        "error_count": sum(1 for e in events if _SEVERITY_RANK.get(e.severity, 4) <= 2),
        "warn_count": sum(1 for e in events if e.severity == "WARN"),
        "started_at": started.isoformat() if started else None,
        "ended_at": ended.isoformat() if ended else None,
        "duration_s": int((ended - started).total_seconds()) if started and ended else None,
    }


_KNOWN_STATUSES = (
    "OPEN", "CLOSED", "RESOLVED", "MITIGATED", "INVESTIGATING",
    "ACKNOWLEDGED", "IN PROGRESS",
)


def _normalize_status(raw: str | None) -> str:
    """Reduce a status blob ('OPEN | Awaiting recovery...') to a keyword ('Open')."""
    if not raw:
        return "Unknown"
    up = raw.upper()
    for keyword in _KNOWN_STATUSES:
        if keyword in up:
            return keyword.title()
    first = raw.strip().split("|")[0].strip()
    return first.title() if first else "Unknown"


def _derive_parent_status(parsed: IncidentFile) -> str:
    """Status from the INCIDENT STATUS section, else an 'Incident Status' event field."""
    raw = parsed.analysis.get("status")
    if not raw:
        for det in parsed.parent_details:
            if det.get("Incident Status"):
                raw = det["Incident Status"]
                break
    return _normalize_status(raw)


def _derive_category(parsed: IncidentFile) -> str:
    """Category from banner metadata, else the Incident Recorder event details."""
    if parsed.metadata.get("Category"):
        return parsed.metadata["Category"]
    all_details = list(parsed.parent_details) + [d for c in parsed.children for d in c.details]
    for det in all_details:
        if det.get("Category"):
            return det["Category"]
    return "Unknown"


def _insert_incident(conn, **cols) -> None:
    keys = list(cols)
    conn.execute(
        f"INSERT INTO incidents ({', '.join(keys)}) VALUES ({', '.join('?' for _ in keys)})",
        [cols[k] for k in keys],
    )


def _insert_events(conn, incident_id: str, events: list[Event], details: list[dict]) -> None:
    conn.executemany(
        """
        INSERT INTO events (
            incident_id, event_ref, section, line_no, ts, severity, service, message, details_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                incident_id,
                ev.id,
                det.get("_section"),
                ev.raw_line_no,
                ev.ts.isoformat() if ev.ts else None,
                ev.severity,
                ev.service,
                ev.message_masked,
                json.dumps(det, default=str),
            )
            for ev, det in zip(events, details)
        ],
    )


def save_file(parsed: IncidentFile, filename: str) -> dict:
    """Persist a parsed file as a parent incident plus its child incidents.

    Returns {"parent_id": ..., "child_ids": [...]}.
    """
    meta = parsed.metadata
    all_events = list(parsed.parent_events) + [e for c in parsed.children for e in c.events]
    agg = _summarize(all_events)
    now = datetime.now(timezone.utc).isoformat()
    # Children are sub-incidents of the parent workflow, so they inherit the
    # parent's status — an open parent means its children are open too.
    parent_status = _derive_parent_status(parsed)

    with _db() as conn:
        parent_id = _next_incident_id(conn)
        _insert_incident(
            conn,
            incident_id=parent_id,
            parent_id=None,
            kind="parent",
            child_index=None,
            title=meta.get("Subscription Name") or filename,
            source_filename=filename,
            created_at=now,
            format=parsed.format,
            environment=meta.get("Environment"),
            region=meta.get("Region"),
            correlation_id=meta.get("Correlation ID"),
            log_incident_id=meta.get("Incident ID"),
            severity=parsed.parent_severity or agg["severity"],
            category=_derive_category(parsed),
            status=parent_status,
            event_count=len(all_events),
            error_count=agg["error_count"],
            warn_count=agg["warn_count"],
            started_at=agg["started_at"],
            ended_at=agg["ended_at"],
            duration_s=agg["duration_s"],
            root_cause=parsed.analysis.get("root_cause"),
            business_impact=parsed.analysis.get("business_impact"),
            recommendations=parsed.analysis.get("recommendations"),
            final_summary=parsed.analysis.get("final_summary"),
        )
        _insert_events(conn, parent_id, parsed.parent_events, parsed.parent_details)

        child_ids: list[str] = []
        for child in parsed.children:
            child_id = f"{parent_id}-C{child.index}"
            child_ids.append(child_id)
            csum = _summarize(child.events)
            _insert_incident(
                conn,
                incident_id=child_id,
                parent_id=parent_id,
                kind="child",
                child_index=child.index,
                title=child.name or child.title,
                source_filename=filename,
                created_at=now,
                format="block",
                environment=meta.get("Environment"),
                region=meta.get("Region"),
                correlation_id=meta.get("Correlation ID"),
                log_incident_id=meta.get("Incident ID"),
                severity=csum["severity"],
                category=_derive_category(parsed),  # child inherits parent category
                status=parent_status,  # child inherits parent status
                event_count=len(child.events),
                error_count=csum["error_count"],
                warn_count=csum["warn_count"],
                started_at=csum["started_at"],
                ended_at=csum["ended_at"],
                duration_s=csum["duration_s"],
                root_cause=None,
                business_impact=None,
                recommendations=None,
                final_summary=None,
            )
            _insert_events(conn, child_id, child.events, child.details)

    return {"parent_id": parent_id, "child_ids": child_ids}


# --- read helpers ------------------------------------------------------------


def list_parents() -> list[dict]:
    """Top-level incidents, each with a nested list of child summaries."""
    with _db() as conn:
        parents = conn.execute(
            "SELECT * FROM incidents WHERE kind = 'parent' ORDER BY created_at DESC, incident_id DESC"
        ).fetchall()
        result = []
        for p in parents:
            d = dict(p)
            kids = conn.execute(
                "SELECT * FROM incidents WHERE parent_id = ? ORDER BY child_index",
                (p["incident_id"],),
            ).fetchall()
            d["children"] = [dict(k) for k in kids]
            result.append(d)
        return result


def get_incident(incident_id: str) -> dict | None:
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)
        ).fetchone()
        return dict(row) if row else None


def get_children(parent_id: str) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM incidents WHERE parent_id = ? ORDER BY child_index", (parent_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_events(incident_id: str) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM events WHERE incident_id = ? ORDER BY db_id", (incident_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            raw = d.pop("details_json", None)
            try:
                d["details"] = json.loads(raw) if raw else {}
            except (json.JSONDecodeError, TypeError):
                d["details"] = {}
            result.append(d)
        return result


# Create the schema as soon as the module is imported.
init_db()
