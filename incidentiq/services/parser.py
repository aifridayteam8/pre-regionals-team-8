"""Turn an unstructured incident log into structured Event records.

Built for block-structured Azure infrastructure logs. Two shapes are handled:

* Single-incident file: a banner, then event blocks (see logs/Subscription
  Provisioning Failed).
* Multi-incident file: a parent banner + framing sections (WORKFLOW STARTED,
  AZURE MONITOR ALERTS, ROLLBACK), several ``INCIDENT N`` child sections, and
  parent-level analysis sections (ROOT CAUSE ANALYSIS, BUSINESS IMPACT,
  RECOMMENDATIONS, INCIDENT STATUS). See logs/multiple incidents 1.

``parse()`` returns a flat ParseResult (one incident). ``parse_file()`` returns
an IncidentFile with a parent + child hierarchy.

Each event is a header line

    2026-07-30T09:19:12.108Z WARN Azure AD Graph API

followed by a free-form body of ``Key: value`` pairs and JSON payloads.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime

from services.models import Event

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

_SEVERITY_NORMALIZE = {"WARNING": "WARN"}

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
class ParseResult:
    events: list[Event]
    details: list[dict]  # parallel to events: structured key/values per event
    metadata: dict  # banner fields (Environment, Region, Correlation ID, ...)
    unparsed: list[str]
    format: str


@dataclass
class ChildIncident:
    index: int  # 1, 2, 3 ...
    name: str  # e.g. "AZURE SUBSCRIPTION PROVISIONING FAILED"
    title: str  # full banner title
    events: list[Event]
    details: list[dict]


@dataclass
class IncidentFile:
    metadata: dict  # parent banner fields
    parent_severity: str | None  # stated banner severity (SEVn) if present
    parent_events: list[Event]  # framing / direct events owned by the parent
    parent_details: list[dict]
    children: list[ChildIncident]
    analysis: dict  # root_cause, business_impact, recommendations, final_summary, status
    format: str


# --- low-level helpers -------------------------------------------------------


def _prep(raw: bytes) -> list[str]:
    text = raw.decode("utf-8", errors="replace")
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


def _extract_events(
    lines: list[str], line_offset: int = 0, section: str | None = None
) -> tuple[list[Event], list[dict]]:
    """Parse a block of lines into Events (event refs restart at E-0001)."""
    header_idxs = [k for k, ln in enumerate(lines) if _HEADER_RE.match(ln)]
    events: list[Event] = []
    details_list: list[dict] = []
    for n, start in enumerate(header_idxs):
        end = header_idxs[n + 1] if n + 1 < len(header_idxs) else len(lines)
        m = _HEADER_RE.match(lines[start])
        assert m is not None
        body_lines = [
            ln for ln in lines[start + 1 : end] if not _SEPARATOR_RE.match(ln.strip())
        ]
        body_nonempty = [ln.strip() for ln in body_lines if ln.strip()]

        severity = m.group("sev").upper()
        severity = _SEVERITY_NORMALIZE.get(severity, severity)

        details = _extract_details(body_lines)
        if section:
            details["_section"] = section

        events.append(
            Event(
                id=f"E-{n + 1:04d}",
                ts=_parse_ts(m.group("ts")),
                severity=severity,
                host_token="",  # cloud log — no per-event host; masking is Phase 3
                service=(m.group("svc") or "").strip(),
                message_masked=_join(body_nonempty),
                raw_line_no=line_offset + start + 1,
            )
        )
        details_list.append(details)
    return events, details_list


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
                # Stop the title at a blank, a fence, an event header, or the
                # first "Key: value" metadata line — single-incident banners put
                # metadata between the title and the closing fence.
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


# --- public API --------------------------------------------------------------


def parse(raw: bytes, filename: str = "") -> ParseResult:
    """Flat single-incident parse (kept for direct use / backward compatibility)."""
    lines = _prep(raw)
    header_idxs = [i for i, ln in enumerate(lines) if _HEADER_RE.match(ln)]
    if not header_idxs:
        return _parse_flat(lines)
    metadata = _parse_banner(lines[: header_idxs[0]])
    events, details = _extract_events(lines)
    return ParseResult(events=events, details=details, metadata=metadata, unparsed=[], format="block")


def parse_file(raw: bytes, filename: str = "") -> IncidentFile:
    """Hierarchical parse: parent metadata/events + INCIDENT N children + analysis."""
    lines = _prep(raw)

    if not any(_FENCE_RE.match(ln.strip()) for ln in lines):
        # No banners at all — treat the whole thing as one parent, no children.
        pr = parse(raw, filename)
        return IncidentFile(
            metadata=pr.metadata,
            parent_severity=None,
            parent_events=pr.events,
            parent_details=pr.details,
            children=[],
            analysis={},
            format=pr.format,
        )

    metadata: dict = {}
    parent_events: list[Event] = []
    parent_details: list[dict] = []
    children: list[ChildIncident] = []
    analysis: dict = {}

    for sec in _split_sections(lines):
        head = sec.title.split(" / ")[0].strip().upper()

        if head == _BANNER_TITLE:
            # Metadata before the first event header; any events after belong to
            # the parent (single-incident files put all events here).
            first = next(
                (k for k, ln in enumerate(sec.body) if _HEADER_RE.match(ln)), len(sec.body)
            )
            metadata.update(_parse_banner(sec.body[:first]))
            ev, det = _extract_events(sec.body[first:], sec.offset + first, section="Main")
            parent_events += ev
            parent_details += det
            continue

        marker = _INCIDENT_MARKER_RE.match(head)
        if marker:
            name = sec.title.split(" / ", 1)[1].strip() if " / " in sec.title else ""
            ev, det = _extract_events(sec.body, sec.offset, section=sec.title)
            children.append(
                ChildIncident(
                    index=int(marker.group(1)),
                    name=name,
                    title=sec.title,
                    events=ev,
                    details=det,
                )
            )
            continue

        if head in _FRAMING_TITLES:
            ev, det = _extract_events(sec.body, sec.offset, section=head.title())
            parent_events += ev
            parent_details += det
            continue

        if head in _ANALYSIS_KEYS:
            analysis[_ANALYSIS_KEYS[head]] = _join(sec.body)
            continue

        # END OF LOG and anything else: ignore for structure.

    # Renumber the parent's own events sequentially across its sections.
    parent_events = [replace(ev, id=f"E-{k + 1:04d}") for k, ev in enumerate(parent_events)]

    return IncidentFile(
        metadata=metadata,
        parent_severity=normalize_severity(metadata.get("Severity")),
        parent_events=parent_events,
        parent_details=parent_details,
        children=children,
        analysis=analysis,
        format="block-hier" if children else "block",
    )


def _parse_flat(lines: list[str]) -> ParseResult:
    """Fallback: no block headers found — one Event per non-empty line, ts=None."""
    events: list[Event] = []
    details_list: list[dict] = []
    n = 0
    for idx, ln in enumerate(lines):
        s = ln.strip()
        if not s or _SEPARATOR_RE.match(s):
            continue
        n += 1
        events.append(
            Event(
                id=f"E-{n:04d}",
                ts=None,
                severity="INFO",
                host_token="",
                service="",
                message_masked=s,
                raw_line_no=idx + 1,
            )
        )
        details_list.append({})
    return ParseResult(events=events, details=details_list, metadata={}, unparsed=[], format="flat")
