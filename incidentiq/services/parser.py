"""Turn an unstructured incident log into structured Event records.

Built for block-structured logs like logs/Subscription Provisioning Failed: each event is a header line

    2026-07-30T09:19:12.108Z WARN Azure AD Graph API

followed by a free-form body of ``Key: value`` pairs and JSON payloads, with
events separated by dashed rules and a banner header/footer. Falls back to
treating each line as its own event when no block headers are found.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime

from services.models import Event

# --- regexes -----------------------------------------------------------------

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Event header: "<ISO8601 ts> <SEVERITY> <service (free text)>"
_HEADER_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)"
    r"\s+(?P<sev>FATAL|CRITICAL|ERROR|WARN|WARNING|INFO|DEBUG)"
    r"\s+(?P<svc>.+?)\s*$"
)

# A "Key: value" detail line. Key is letters/digits/spaces/()._- but NOT slashes,
# so URLs ("https://...") don't get mistaken for keys.
_KV_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9 _().\-]*?):\s*(?P<val>.*)$")

_SEPARATOR_RE = re.compile(r"^(?:-{3,}|={3,})\s*$")
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_REQUEST_RE = re.compile(r"^(GET|POST|PUT|DELETE|PATCH|HEAD)\s+\S", re.IGNORECASE)

_SEVERITY_NORMALIZE = {"WARNING": "WARN", "CRITICAL": "CRITICAL", "FATAL": "FATAL"}


@dataclass
class ParseResult:
    events: list[Event]
    details: list[dict]  # parallel to events: structured key/values per event
    metadata: dict  # banner fields (Environment, Region, Correlation ID, ...)
    unparsed: list[str]
    format: str


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
    """Pull key/value fields out of the header banner before the first event."""
    meta: dict = {}
    for line in lines:
        s = line.strip()
        if not s or _SEPARATOR_RE.match(s):
            continue
        m = _KV_RE.match(s)
        if m and m.group("val").strip():
            meta[m.group("key").strip()] = m.group("val").strip()
    return meta


def parse(raw: bytes, filename: str = "") -> ParseResult:
    text = raw.decode("utf-8", errors="replace")
    text = _ANSI_RE.sub("", text)
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    # Find the header lines that start each event block.
    header_idxs = [i for i, ln in enumerate(lines) if _HEADER_RE.match(ln)]

    if not header_idxs:
        return _parse_flat(lines, filename)

    metadata = _parse_banner(lines[: header_idxs[0]])

    events: list[Event] = []
    details_list: list[dict] = []
    unparsed: list[str] = []

    for n, start in enumerate(header_idxs):
        end = header_idxs[n + 1] if n + 1 < len(header_idxs) else len(lines)
        header = lines[start]
        m = _HEADER_RE.match(header)
        assert m is not None

        # Body = everything up to the next header, minus separator rules and banners.
        body_lines = [
            ln
            for ln in lines[start + 1 : end]
            if not _SEPARATOR_RE.match(ln.strip())
        ]
        body_nonempty = [ln.strip() for ln in body_lines if ln.strip()]

        severity = m.group("sev").upper()
        severity = _SEVERITY_NORMALIZE.get(severity, severity)

        details = _extract_details(body_lines)
        message = " | ".join(body_nonempty)

        events.append(
            Event(
                id=f"E-{n + 1:04d}",
                ts=_parse_ts(m.group("ts")),
                severity=severity,
                host_token="",  # cloud log — no per-event host; masking is Phase 3
                service=m.group("svc").strip(),
                message_masked=message,
                raw_line_no=start + 1,
            )
        )
        details_list.append(details)

    return ParseResult(
        events=events,
        details=details_list,
        metadata=metadata,
        unparsed=unparsed,
        format="block",
    )


def _parse_flat(lines: list[str], filename: str) -> ParseResult:
    """Fallback: no block headers found — one Event per non-empty line, ts=None."""
    events: list[Event] = []
    details_list: list[dict] = []
    unparsed: list[str] = []
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
    return ParseResult(
        events=events,
        details=details_list,
        metadata={},
        unparsed=unparsed,
        format="flat",
    )
