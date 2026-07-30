import SeverityBadge from "./SeverityBadge";
import ConfidenceMeter from "./ConfidenceMeter";

export default function ReportHeader({ report = {}, actions }) {
  const { title, incidentId, detectedAt, durationMinutes, category, severity, rca } = report;

  return (
    <div className="report-header">
      <div className="report-header-main">
        <h2 className="report-title">{title ?? "Incident Report"}</h2>

        <p className="report-meta">
          {incidentId && <span className="report-id">#{incidentId}</span>}
          {detectedAt && <span>Detected {detectedAt}</span>}
          {durationMinutes != null && <span>Duration {durationMinutes} min</span>}
          {category && <span>Category {category}</span>}
        </p>
      </div>

      <div className="report-header-side">
        {severity != null && <SeverityBadge level={severity} />}
        {rca?.confidence != null && <ConfidenceMeter value={rca.confidence} />}
        {actions}
      </div>
    </div>
  );
}
