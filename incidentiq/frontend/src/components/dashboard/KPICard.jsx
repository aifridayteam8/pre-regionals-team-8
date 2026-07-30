export default function KPICard({ label, value, delta, hint }) {
  const trend = delta == null ? null : delta >= 0 ? "up" : "down";

  return (
    <article className="kpi-card">
      <span className="kpi-label">{label}</span>
      <strong className="kpi-value">{value ?? "-"}</strong>

      <span className="kpi-foot">
        {trend && (
          <span className={`kpi-delta kpi-delta-${trend}`}>
            {delta > 0 ? "\u2191" : "\u2193"} {Math.abs(delta)}%
          </span>
        )}
        {hint && <span>{hint}</span>}
        {!hint && trend && <span>vs. previous period</span>}
      </span>
    </article>
  );
}
