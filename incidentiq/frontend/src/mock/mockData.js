const TIMELINE_MESSAGES = [
  ["ERROR", "api-gateway", "payments-api", "Upstream connect error: connection timed out"],
  ["WARN", "api-gateway", "payments-api", "Retry budget exhausted for upstream payments-db"],
  ["ERROR", "db-primary", "payments-db", "FATAL: sorry, too many clients already"],
  ["INFO", "db-primary", "payments-db", "Connection pool size 100/100"],
  ["ERROR", "worker-3", "settlement-worker", "Task failed: OperationalError (timeout)"],
  ["WARN", "worker-3", "settlement-worker", "Queue depth 12480 exceeds threshold 5000"],
  ["ERROR", "api-gateway", "checkout-api", "502 Bad Gateway returned to client"],
  ["INFO", "deploy-bot", "ci-cd", "Release v2.31.0 rolled out to 100% of fleet"],
  ["WARN", "db-primary", "payments-db", "Slow query 8.4s: SELECT * FROM settlements"],
  ["ERROR", "worker-1", "settlement-worker", "OOMKilled, restarting container"],
  ["INFO", "k8s", "settlement-worker", "Pod settlement-worker-1 restarted (1)"],
  ["ERROR", "api-gateway", "checkout-api", "Circuit breaker opened for payments-api"],
  ["WARN", "cache-1", "redis", "Evicted 24k keys due to maxmemory policy"],
  ["INFO", "oncall", "pagerduty", "Incident acknowledged by on-call engineer"],
  ["INFO", "deploy-bot", "ci-cd", "Rollback to v2.30.4 started"],
  ["INFO", "db-primary", "payments-db", "Connection pool size 42/100"],
  ["INFO", "api-gateway", "checkout-api", "Circuit breaker half-open"],
  ["INFO", "api-gateway", "checkout-api", "Error rate back under 0.5%"],
  ["INFO", "oncall", "pagerduty", "Incident mitigated"],
  ["INFO", "oncall", "pagerduty", "Incident resolved, monitoring for 30 min"],
];

export const mockTimeline = TIMELINE_MESSAGES.map(
  ([severity, host, service, message], index) => ({
    id: index + 1,
    timestamp: `2026-07-29T14:${String(12 + index).padStart(2, "0")}:03Z`,
    severity,
    host,
    service,
    message,
  })
);

export const mockReport = {
  incidentId: "INC-2451",
  title: "Checkout failures caused by exhausted database connection pool",
  detectedAt: "2026-07-29 14:12 UTC",
  durationMinutes: 47,
  severity: 1,
  category: "Database",
  summary:
    "Release v2.31.0 introduced an un-pooled database client in the settlement worker. " +
    "Within eight minutes the payments-db connection pool saturated at 100/100, causing " +
    "upstream timeouts in payments-api and 502s at checkout. Rolling back to v2.30.4 " +
    "restored the pool and error rates returned to baseline.",
  impact: {
    usersAffected: "~18,400",
    services: ["checkout-api", "payments-api", "settlement-worker"],
    durationMinutes: 47,
    description:
      "Checkout success rate dropped from 99.4% to 61.2% for 47 minutes. " +
      "Approximately 2,100 settlement jobs were delayed and retried after recovery.",
  },
  rca: {
    rootCause:
      "The settlement worker in v2.31.0 opened a new database connection per task " +
      "instead of reusing the shared pool, exhausting payments-db max_connections.",
    reasoning:
      "Connection pool saturation begins 6 minutes after the v2.31.0 rollout and clears " +
      "immediately after rollback, and the only errors preceding the API timeouts are " +
      "'too many clients already' from payments-db.",
    confidence: 0.87,
    evidence: [
      { id: "e1", label: "FATAL: too many clients already", line: 3 },
      { id: "e2", label: "Release v2.31.0 rolled out", line: 8 },
      { id: "e3", label: "Connection pool 100/100", line: 4 },
      { id: "e4", label: "Circuit breaker opened", line: 12 },
    ],
  },
  recommendations: [
    { id: "r1", text: "Restore pooled database client in settlement-worker", owner: "payments-team" },
    { id: "r2", text: "Add alert on payments-db connections > 80% of max_connections", owner: "sre" },
    { id: "r3", text: "Gate releases behind a 10% canary for 15 minutes", owner: "release-eng" },
    { id: "r4", text: "Add a load test that saturates the settlement queue", owner: "payments-team" },
  ],
  timeline: mockTimeline,
  transparency: {
    promptDigest: "sha256:9f2c…a41d",
    model: "gpt-4.1-mini",
    validation: "Schema valid (incident_report.v2)",
    latencyMs: 4820,
    retryCount: 1,
  },
};

export const mockHistory = [
  { id: "INC-2451", date: "2026-07-29", title: "Checkout failures from DB pool exhaustion", severity: 1, category: "Database", durationMinutes: 47, status: "Resolved" },
  { id: "INC-2447", date: "2026-07-26", title: "Elevated latency in search service", severity: 3, category: "Performance", durationMinutes: 26, status: "Resolved" },
  { id: "INC-2440", date: "2026-07-21", title: "Auth token refresh loop after config change", severity: 2, category: "Configuration", durationMinutes: 63, status: "Resolved" },
  { id: "INC-2436", date: "2026-07-18", title: "Image CDN cache miss storm", severity: 3, category: "Network", durationMinutes: 18, status: "Monitoring" },
  { id: "INC-2431", date: "2026-07-14", title: "Settlement worker OOM restarts", severity: 2, category: "Capacity", durationMinutes: 91, status: "Resolved" },
  { id: "INC-2428", date: "2026-07-09", title: "Partial outage in EU region", severity: 1, category: "Infrastructure", durationMinutes: 122, status: "Resolved" },
];

export const mockDashboard = {
  kpis: {
    totalIncidents: 42,
    openHighSeverity: 3,
    meanTimeToDetect: "6m 12s",
    recurringCauses: 5,
  },
  severity: [
    { severity: "SEV1", count: 4 },
    { severity: "SEV2", count: 9 },
    { severity: "SEV3", count: 17 },
    { severity: "SEV4", count: 12 },
  ],
  categories: [
    { category: "Database", count: 11 },
    { category: "Configuration", count: 8 },
    { category: "Capacity", count: 7 },
    { category: "Network", count: 6 },
    { category: "Deployment", count: 6 },
    { category: "Other", count: 4 },
  ],
  trend: [
    { date: "Feb", count: 5 },
    { date: "Mar", count: 8 },
    { date: "Apr", count: 6 },
    { date: "May", count: 9 },
    { date: "Jun", count: 7 },
    { date: "Jul", count: 7 },
  ],
  recurring: [
    { cause: "DB connection pool exhausted", count: 6 },
    { cause: "Missing config rollout gate", count: 5 },
    { cause: "Worker OOM under queue spike", count: 4 },
    { cause: "Expired TLS certificate", count: 3 },
    { cause: "Cache stampede on deploy", count: 2 },
  ],
};

export const mockSampleFiles = [
  { id: "apache", name: "Apache Log", fileName: "apache-access.log" },
  { id: "syslog", name: "Syslog", fileName: "syslog-payments.log" },
  { id: "json", name: "JSON", fileName: "structured-events.json" },
];

export const GENERATION_STAGES = [
  "Parsing",
  "Masking",
  "Generating Summary",
  "Generating RCA",
  "Generating Recommendations",
];
