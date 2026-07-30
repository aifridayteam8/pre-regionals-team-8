import Card from "../common/Card";

export default function ImpactCard({ impact = {} }) {
  const { services = [], durationMinutes, description } = impact;

  return (
    <Card title="Impact" className="impact-card">
      <dl className="impact-grid">
        <div className="impact-item">
          <dt>Duration</dt>
          <dd>{durationMinutes != null ? `${durationMinutes} min` : "Unknown"}</dd>
        </div>

        <div className="impact-item impact-item-wide">
          <dt>Services affected</dt>
          <dd>
            {services.length === 0 ? (
              <span className="is-muted">Unknown</span>
            ) : (
              <ul className="service-chips">
                {services.map((service) => (
                  <li key={service} className="service-chip">
                    {service}
                  </li>
                ))}
              </ul>
            )}
          </dd>
        </div>
      </dl>

      {description && <p className="impact-description">{description}</p>}
    </Card>
  );
}
