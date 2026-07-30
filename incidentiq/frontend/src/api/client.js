// Real API client for the incidentiq Flask backend (see incidentiq/api/routes.py).
// Base URL comes from .env.development (VITE_API_BASE), default http://localhost:5000.

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:5000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  let body = null;
  try {
    body = await res.json();
  } catch {
    /* non-JSON response */
  }
  if (!res.ok) {
    throw new Error(body?.error ?? `Request failed (${res.status})`);
  }
  return body;
}

// --- raw endpoints -----------------------------------------------------------

export function getHealth() {
  return request("/api/health");
}

export function listIncidents() {
  return request("/api/incidents");
}

export function getIncident(id) {
  return request(`/api/incidents/${id}`);
}

export function uploadIncident(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/api/incidents", { method: "POST", body: form });
}

// --- shape mappers (Flask rows -> UI shapes) --------------------------------

export function severityNumber(sev) {
  const digits = String(sev ?? "").replace(/\D/g, "");
  return digits ? Number(digits) : 4;
}

function minutes(durationS) {
  return durationS != null ? Math.max(1, Math.round(durationS / 60)) : null;
}

function shortDate(row) {
  const iso = row.started_at ?? row.created_at;
  return iso ? iso.slice(0, 10) : "-";
}

function splitBullets(text) {
  if (!text) return [];
  return text
    .split("|")
    .map((part) => part.replace(/^[\s•\-–]+/, "").trim())
    .filter(Boolean);
}

/** Find a value in event details by key, first match wins. */
function findDetail(events, key) {
  for (const ev of events) {
    const value = ev.details?.[key];
    if (value) return value;
  }
  return null;
}

export function toHistoryRow(row) {
  return {
    id: row.incident_id,
    date: shortDate(row),
    title: row.title,
    severity: severityNumber(row.severity),
    category: row.category ?? "Unknown",
    durationMinutes: minutes(row.duration_s),
    status: row.status ?? "Unknown",
    children: (row.children ?? []).map(toHistoryRow),
  };
}

function toTimelineEvent(ev, index) {
  return {
    id: ev.db_id ?? index,
    timestamp: ev.ts ? ev.ts.slice(0, 19).replace("T", " ") : "-",
    severity: ev.severity ?? "INFO",
    host: ev.section ?? null, // cloud logs have no host; show log section instead
    service: ev.service || "-",
    message: ev.message,
    line: ev.line_no,
  };
}

function buildEvidence(events) {
  return events
    .filter((ev) => ["ERROR", "ALERT", "CRITICAL", "FATAL"].includes(ev.severity))
    .slice(0, 4)
    .map((ev, index) => ({
      id: `e${index + 1}`,
      label: `${ev.service || "event"}: ${
        ev.details?.Error ??
        ev.details?.["Failure Code"] ??
        ev.details?.["HTTP Status"] ??
        (ev.message ?? "").slice(0, 60)
      }`,
      line: ev.line_no,
    }));
}

/**
 * Build the ReportView shape from a parent incident detail response plus the
 * merged (parent + children) event list.
 */
export function toReport(incident, events, meta = {}) {
  const rootCause =
    incident.root_cause ?? findDetail(events, "Root Cause (System Generated)");
  const impactText =
    incident.business_impact ?? findDetail(events, "Impact");
  const recommendationsText =
    incident.recommendations ?? findDetail(events, "Recommendation");

  const services = [...new Set(events.map((ev) => ev.service).filter(Boolean))];

  return {
    incidentId: incident.incident_id,
    title: incident.title,
    detectedAt: incident.started_at
      ? incident.started_at.slice(0, 16).replace("T", " ") + " UTC"
      : null,
    durationMinutes: minutes(incident.duration_s),
    severity: severityNumber(incident.severity),
    category: incident.category ?? "Unknown",
    status: incident.status,
    summary:
      incident.final_summary ??
      rootCause ??
      `Parsed ${incident.event_count} events (${incident.error_count} errors, ${incident.warn_count} warnings) from ${incident.source_filename}.`,
    impact: {
      usersAffected: findDetail(events, "Affected User") ?? findDetail(events, "User") ?? "Unknown",
      services,
      durationMinutes: minutes(incident.duration_s),
      description: typeof impactText === "string" ? impactText.replace(/\s*\|\s*/g, " ") : null,
    },
    rca: {
      rootCause: typeof rootCause === "string" ? rootCause.replace(/\s*\|\s*/g, " ") : null,
      reasoning: null,
      confidence: null,
      evidence: buildEvidence(events),
    },
    recommendations: splitBullets(recommendationsText).map((text, index) => ({
      id: `r${index + 1}`,
      text,
    })),
    timeline: events.map(toTimelineEvent),
    transparency: {
      promptDigest: "n/a — deterministic parser (AI pipeline not wired yet)",
      model: "incidentiq rule-based parser",
      validation: `format=${incident.format} · ${incident.event_count} events stored`,
      latencyMs: meta.latencyMs ?? null,
      retryCount: 0,
    },
    children: meta.children ?? [],
  };
}

/** Fetch a parent report with the events of the parent and all its children merged. */
export async function fetchFullReport(parentId, meta = {}) {
  const detail = await getIncident(parentId);
  const children = detail.children ?? [];

  const childEvents = await Promise.all(
    children.map((child) => getIncident(child.incident_id).then((d) => d.events ?? []))
  );

  const events = [...(detail.events ?? []), ...childEvents.flat()].sort((a, b) =>
    (a.ts ?? "").localeCompare(b.ts ?? "")
  );

  return toReport(detail.incident, events, { ...meta, children });
}

// --- dashboard aggregation (client-side, from the incidents list) -----------

function countBy(rows, keyFn) {
  const counts = new Map();
  for (const row of rows) {
    const key = keyFn(row) ?? "Unknown";
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
}

function formatDuration(seconds) {
  if (!seconds) return "-";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${String(s).padStart(2, "0")}s`;
}

export function buildDashboard(parents) {
  const open = parents.filter((p) => (p.status ?? "").toLowerCase() === "open");
  const highSev = open.filter((p) => severityNumber(p.severity) <= 2);

  const durations = parents.map((p) => p.duration_s).filter((d) => d != null);
  const avgDuration = durations.length
    ? durations.reduce((a, b) => a + b, 0) / durations.length
    : null;

  const severity = ["SEV1", "SEV2", "SEV3", "SEV4"]
    .map((sev) => ({
      severity: sev,
      count: parents.filter((p) => p.severity === sev).length,
    }))
    .filter((entry) => entry.count > 0);

  const categories = [...countBy(parents, (p) => p.category)].map(([category, count]) => ({
    category,
    count,
  }));

  const trend = [...countBy(parents, (p) => shortDate(p))]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({ date, count }));

  const causeCounts = countBy(
    parents.filter((p) => p.root_cause),
    (p) => p.root_cause.replace(/\s*\|\s*/g, " ").slice(0, 60)
  );
  const recurring = [...causeCounts]
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .map(([cause, count]) => ({ cause, count }));

  return {
    kpis: {
      totalIncidents: parents.length,
      childIncidents: parents.reduce((sum, p) => sum + (p.children?.length ?? 0), 0),
      openHighSeverity: highSev.length,
      avgDuration: formatDuration(avgDuration),
      recurringCauses: [...causeCounts.values()].filter((count) => count > 1).length,
    },
    severity,
    categories,
    trend,
    recurring,
  };
}
