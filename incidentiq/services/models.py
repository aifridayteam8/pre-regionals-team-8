from dataclasses import dataclass
from datetime import datetime

SEVERITIES = ("SEV1", "SEV2", "SEV3", "SEV4")
CATEGORIES = ("Network", "Compute", "Storage", "Database", "Application", "Security", "Unknown")


@dataclass(frozen=True)
class Event:
    id: str  # "E-0001"
    ts: datetime | None
    severity: str
    host_token: str
    service: str
    message_masked: str
    raw_line_no: int


@dataclass(frozen=True)
class IncidentGroup:
    events: list[Event]
    started_at: datetime | None
    ended_at: datetime | None
    hosts: set[str]
    services: set[str]


@dataclass(frozen=True)
class SectionResult:
    kind: str
    content: str
    confidence: str | None
    evidence_ids: list[str]
    model: str
    validated: bool
    error: str | None


@dataclass(frozen=True)
class Report:
    incident_id: str  # "INC-YYYYMMDD-NN"
    created_at: datetime
    title: str
    severity: str
    category: str
    status: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_s: int | None
    sections: dict[str, SectionResult]
    source_filename: str
