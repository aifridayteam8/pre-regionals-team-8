"""Azure Infrastructure incident log parser (block + hierarchical formats).

Ported from incidentiq/services/parser.py. Handles two shapes:

* Single-incident file: a ``=`` banner with metadata, then timestamped event
  blocks separated by dashed rules (see logs/Subscription Provisioning Failed).
* Multi-incident file: a parent banner + framing sections (WORKFLOW STARTED,
  AZURE MONITOR ALERTS, ROLLBACK), several ``INCIDENT N`` child sections, and
  parent-level analysis sections (ROOT CAUSE ANALYSIS, BUSINESS IMPACT,
  RECOMMENDATIONS, INCIDENT STATUS). See logs/multiple incidents 1.

Two entry points:

* ``AzureParser`` — BaseParser-compatible; ``parse``/``parse_content`` return a
  flat list of normalized event dicts (level lowercase per backend convention).
* ``parse_file(raw, filename)`` — hierarchical ``IncidentFile`` with parent
  metadata/events, ``INCIDENT N`` children, and analysis text, used by the
  incident upload route to create parent/child Incident rows.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Dict, List

from .base_parser import BaseParser

# --- regexes -----------------------------------------------------------------

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Event header: "<ISO8601 ts> <SEVERITY> [service (free text)]". Service optional
# so bare alert lines ("<ts> ALERT") still parse.
_HEADER_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)"
    r"\s+(?P<sev>FATAL|CRITICAL|ERROR|WARN|WARNING|INFO|DEBUG|ALERT|ALARM)"
    r"(?:\s+(?P<svc>.+?))?\s*$"
)

# A "Key: value" detail line. Key is letters/digits/spaces/()._- but NOT slashes,
# so URLs ("https://...") don't get mistaken for keys.
_KV_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9 _().\-]*?)\s*:\s*(?P<val>.*)$")

_SEPARATOR_RE = re.compile(r"^(?:-{3,}|={3,})\s*$")
_FENCE_RE = re.compile(r"^={3,}\s*$")  # '=' fences delimit banner sections
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_REQUEST_RE = re.compile(r"^(GET|POST|PUT|DELETE|PATCH|HEAD)\s+\S", re.IGNORECASE)
_STATUS_CODE_RE = re.compile(r"\s*(\d{3})")

# Raw log token -> backend internal level (lowercase, matches services/ filters)
_LEVEL_MAP = {
    "FATAL": "critical",
    "CRITICAL": "critical",
    "ERROR": "error",
    "ALERT": "error",
    "ALARM": "error",
    "WARN": "warning",
    "WARNING": "warning",
    "INFO": "info",
    "DEBUG": "debug",
}

_LEVEL_RANK = {"critical": 1, "error": 2, "warning": 3, "info": 4, "debug": 4}

_BANNER_TITLE = "AZURE INFRASTRUCTURE INCIDENT LOG"
_FRAMING_TITLES = {"WORKFLOW STARTED", "AZURE MONITOR ALERTS", "ROLLBACK"}
_ANALYSIS_KEYS = {
    "ROOT CAUSE ANALYSIS": "root_cause",
    "BUSINESS IMPACT": "business_impact",
    "RECOMMENDATIONS": "recommendations",
    "FINAL INCIDENT SUMMARY": "final_summary",
    "INCIDENT STATUS": "status",
}
_INCIDENT_MARKER_RE = re.compile(r"^INCIDENT\s+(\d+)", re.IGNORECASE)


# --- data shapes -------------------------------------------------------------


@dataclass
class ParsedEvent:
    ts: datetime | None
    level: str  # lowercase internal level
    service: str
    message: str
    details: dict
    line_no: int
    ref: str = ""  # "E-0001"
    section: str | None = None


@dataclass
class ChildIncident:
    index: int  # 1, 2, 3 ...
    name: str  # e.g. "AZURE SUBSCRIPTION PROVISIONING FAILED"
    title: str  # full banner title
    events: List[ParsedEvent] = field(default_factory=list)


@dataclass
class IncidentFile:
    metadata: dict  # parent banner fields
    parent_severity: str | None  # stated banner severity (SEVn) if present
    parent_events: List[ParsedEvent] = field(default_factory=list)
    children: List[ChildIncident] = field(default_factory=list)
    analysis: dict = field(default_factory=dict)
    format: str = "block"


# --- low-level helpers -------------------------------------------------------


def _prep(raw: bytes | str) -> list[str]:
    text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
    text = _ANSI_RE.sub("", text)
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _parse_ts(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _collect_json(lines: list[str], i: int) -> tuple[object, int]:
    """Accumulate a brace-balanced block starting at line i; return (parsed, next_i)."""
    depth = 0
    buf: list[str] = []
    n = len(lines)
    while i < n:
        s = lines[i]
        buf.append(s)
        depth += s.count("{") - s.count("}")
        i += 1
        if depth <= 0:
            break
    text = "\n".join(buf)
    try:
        return json.loads(text), i
    except (json.JSONDecodeError, ValueError):
        return text, i


def _extract_details(body_lines: list[str]) -> dict:
    """Best-effort structuring of a body block into key/value pairs + payloads."""
    details: dict = {}
    i, n = 0, len(body_lines)
    while i < n:
        line = body_lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("{"):
            payload, i = _collect_json(body_lines, i)
            details.setdefault("_payloads", []).append(payload)
            continue
        if _URL_RE.match(line):
            details.setdefault("_urls", []).append(line)
            i += 1
            continue
        if _REQUEST_RE.match(line):
            details.setdefault("_requests", []).append(line)
            i += 1
            continue
        m = _KV_RE.match(line)
        if m:
            key, val = m.group("key").strip(), m.group("val").strip()
            if val:
                details[key] = val
                i += 1
                continue
            # Empty inline value: value lives on the following non-empty line(s).
            j = i + 1
            collected: list[str] = []
            while j < n:
                nxt = body_lines[j].strip()
                if not nxt:
                    break
                if nxt.startswith("{"):
                    payload, j = _collect_json(body_lines, j)
                    details.setdefault("_payloads", []).append(payload)
                    continue
                if _KV_RE.match(nxt) and not (_URL_RE.match(nxt) or _REQUEST_RE.match(nxt)):
                    break
                collected.append(nxt)
                j += 1
            if collected:
                details[key] = collected[0] if len(collected) == 1 else " ".join(collected)
            i = j
            continue
        i += 1
    return details


def _parse_banner(lines: list[str]) -> dict:
    """Pull key/value fields out of a banner block."""
    meta: dict = {}
    for line in lines:
        s = line.strip()
        if not s or _SEPARATOR_RE.match(s):
            continue
        m = _KV_RE.match(s)
        if m and m.group("val").strip():
            meta[m.group("key").strip()] = m.group("val").strip()
    return meta


def _join(lines: list[str]) -> str:
    return " | ".join(s.strip() for s in lines if s.strip())


def normalize_severity(raw: str | None) -> str | None:
    """'SEV-1' / 'SEV 1' / 'sev1' -> 'SEV1'. Returns None if no digit found."""
    if not raw:
        return None
    digits = re.sub(r"[^0-9]", "", raw)
    return f"SEV{digits}" if digits else None


def compute_severity(events: List[ParsedEvent]) -> str:
    """BR-1 mapping: critical->SEV1, error->SEV2, warning->SEV3, info-only->SEV4."""
    ranks = [_LEVEL_RANK.get(e.level, 4) for e in events] or [4]
    return f"SEV{min(ranks)}"


def _extract_events(
    lines: list[str], line_offset: int = 0, section: str | None = None
) -> List[ParsedEvent]:
    """Parse a block of lines into ParsedEvents (refs restart at E-0001)."""
    header_idxs = [k for k, ln in enumerate(lines) if _HEADER_RE.match(ln)]
    events: List[ParsedEvent] = []
    for n, start in enumerate(header_idxs):
        end = header_idxs[n + 1] if n + 1 < len(header_idxs) else len(lines)
        m = _HEADER_RE.match(lines[start])
        assert m is not None
        body_lines = [
            ln for ln in lines[start + 1 : end] if not _SEPARATOR_RE.match(ln.strip())
        ]
        body_nonempty = [ln.strip() for ln in body_lines if ln.strip()]

        raw_sev = m.group("sev").upper()
        details = _extract_details(body_lines)
        details["_severity_raw"] = raw_sev

        events.append(
            ParsedEvent(
                ts=_parse_ts(m.group("ts")),
                level=_LEVEL_MAP.get(raw_sev, "info"),
                service=(m.group("svc") or "").strip(),
                message=_join(body_nonempty),
                details=details,
                line_no=line_offset + start + 1,
                ref=f"E-{n + 1:04d}",
                section=section,
            )
        )
    return events


# --- section splitting -------------------------------------------------------


@dataclass
class _RawSection:
    title: str
    offset: int  # line index where the body starts
    body: list[str] = field(default_factory=list)


def _split_sections(lines: list[str]) -> list[_RawSection]:
    """Split a file into ``=``-fenced banner sections.

    A banner is a fence line, one or more title lines, then (optionally) a
    closing fence. Everything up to the next fence is that section's body.
    Titles stop at the first "Key: value" line — single-incident banners put
    metadata between the title and the closing fence.
    """
    sections: list[_RawSection] = []
    i, n = 0, len(lines)
    current: _RawSection | None = None
    while i < n:
        if _FENCE_RE.match(lines[i].strip()):
            j = i + 1
            title_parts: list[str] = []
            while j < n:
                s = lines[j].strip()
                if not s or _FENCE_RE.match(s) or _HEADER_RE.match(lines[j]) or _KV_RE.match(s):
                    break
                title_parts.append(s)
                j += 1
            if title_parts:
                i = j
                if i < n and _FENCE_RE.match(lines[i].strip()):
                    i += 1  # consume the closing fence of a fence/title/fence banner
                current = _RawSection(title=" / ".join(title_parts), offset=i)
                sections.append(current)
                continue
            i += 1
            continue
        if current is not None:
            current.body.append(lines[i])
        i += 1
    return sections


# --- hierarchical API --------------------------------------------------------


def parse_file(raw: bytes | str, filename: str = "") -> IncidentFile:
    """Hierarchical parse: parent metadata/events + INCIDENT N children + analysis."""
    lines = _prep(raw)

    if not any(_FENCE_RE.match(ln.strip()) for ln in lines):
        # No banners at all — every event belongs to the parent.
        events = _extract_events(lines)
        if not events:
            events = _flat_lines_as_events(lines)
        return IncidentFile(
            metadata={},
            parent_severity=None,
            parent_events=events,
            format="block" if events and events[0].ref else "flat",
        )

    metadata: dict = {}
    parent_events: List[ParsedEvent] = []
    children: List[ChildIncident] = []
    analysis: dict = {}

    for sec in _split_sections(lines):
        head = sec.title.split(" / ")[0].strip().upper()

        if head == _BANNER_TITLE:
            first = next(
                (k for k, ln in enumerate(sec.body) if _HEADER_RE.match(ln)), len(sec.body)
            )
            metadata.update(_parse_banner(sec.body[:first]))
            parent_events += _extract_events(sec.body[first:], sec.offset + first, section="Main")
            continue

        marker = _INCIDENT_MARKER_RE.match(head)
        if marker:
            name = sec.title.split(" / ", 1)[1].strip() if " / " in sec.title else ""
            children.append(
                ChildIncident(
                    index=int(marker.group(1)),
                    name=name,
                    title=sec.title,
                    events=_extract_events(sec.body, sec.offset, section=sec.title),
                )
            )
            continue

        if head in _FRAMING_TITLES:
            parent_events += _extract_events(sec.body, sec.offset, section=head.title())
            continue

        if head in _ANALYSIS_KEYS:
            analysis[_ANALYSIS_KEYS[head]] = _join(sec.body)
            continue

        # END OF LOG and anything else: ignore for structure.

    # Renumber the parent's own events sequentially across its sections.
    parent_events = [replace(ev, ref=f"E-{k + 1:04d}") for k, ev in enumerate(parent_events)]

    return IncidentFile(
        metadata=metadata,
        parent_severity=normalize_severity(metadata.get("Severity")),
        parent_events=parent_events,
        children=children,
        analysis=analysis,
        format="block-hier" if children else "block",
    )


def _flat_lines_as_events(lines: list[str]) -> List[ParsedEvent]:
    """Fallback: no event headers found — one info event per non-empty line."""
    events: List[ParsedEvent] = []
    n = 0
    for idx, ln in enumerate(lines):
        s = ln.strip()
        if not s or _SEPARATOR_RE.match(s):
            continue
        n += 1
        events.append(
            ParsedEvent(
                ts=None,
                level="info",
                service="",
                message=s,
                details={},
                line_no=idx + 1,
                ref="",
            )
        )
    return events


# --- helpers shared with routes ----------------------------------------------


def derive_status(parsed: IncidentFile) -> str:
    """Status keyword from the INCIDENT STATUS section or event details."""
    raw = parsed.analysis.get("status")
    if not raw:
        for ev in parsed.parent_events:
            if ev.details.get("Incident Status"):
                raw = ev.details["Incident Status"]
                break
    if not raw:
        return "Open"
    up = raw.upper()
    for keyword in ("OPEN", "CLOSED", "RESOLVED", "MITIGATED", "INVESTIGATING", "ACKNOWLEDGED"):
        if keyword in up:
            return keyword.title()
    first = raw.strip().split("|")[0].strip()
    return first.title() if first else "Open"


def derive_category(parsed: IncidentFile) -> str:
    """Category from banner metadata, else any event's Category detail."""
    if parsed.metadata.get("Category"):
        return parsed.metadata["Category"]
    for ev in parsed.parent_events + [e for c in parsed.children for e in c.events]:
        if ev.details.get("Category"):
            return ev.details["Category"]
    return "Unknown"


def event_error_code(details: dict) -> str | None:
    for key in ("Error", "Error Code", "Failure Code", "code"):
        if details.get(key):
            return str(details[key])
    http_status = details.get("HTTP Status")
    if http_status:
        m = _STATUS_CODE_RE.match(str(http_status))
        if m:
            return m.group(1)
    return None


# --- BaseParser-compatible flat interface ------------------------------------


class AzureParser(BaseParser):
    """Parser for Azure Infrastructure log format (flat event-dict interface)."""

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return self.parse_content(f.read())

    def parse_content(self, content: str) -> List[Dict[str, Any]]:
        parsed = parse_file(content)
        correlation_id = parsed.metadata.get("Correlation ID")

        flat: List[Dict[str, Any]] = []
        all_events = list(parsed.parent_events) + [
            e for child in parsed.children for e in child.events
        ]
        for ev in all_events:
            flat.append(
                {
                    "timestamp": ev.ts,
                    "level": ev.level,
                    "source": ev.section or "azure",
                    "message": ev.message,
                    "raw_data": json.dumps(ev.details, default=str),
                    "host": None,
                    "service": ev.service or None,
                    "error_code": event_error_code(ev.details),
                    "correlation_id": ev.details.get("CorrelationId") or correlation_id,
                }
            )
        return flat
