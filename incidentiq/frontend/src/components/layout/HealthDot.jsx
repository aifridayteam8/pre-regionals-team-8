const STATUS_LABELS = {
  checking: "Checking",
  healthy: "Operational",
  down: "Unreachable",
};

export default function HealthDot({ status = "checking" }) {
  return (
    <span className="health" title={`Backend status: ${STATUS_LABELS[status] ?? status}`}>
      <span className={`health-dot health-dot-${status}`} aria-hidden="true" />
      <span className="health-label">Backend {STATUS_LABELS[status] ?? status}</span>
    </span>
  );
}
