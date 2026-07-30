const SEVERITY_LABELS = {
  1: "SEV1 \u00B7 Critical",
  2: "SEV2 \u00B7 High",
  3: "SEV3 \u00B7 Medium",
  4: "SEV4 \u00B7 Low",
};

export default function SeverityBadge({ level = 4 }) {
  return (
    <span className={`severity-badge severity-${level}`}>
      {SEVERITY_LABELS[level] ?? `SEV${level}`}
    </span>
  );
}
