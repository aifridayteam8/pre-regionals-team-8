import Header from "../components/layout/Header";
import Card from "../components/common/Card";
import EmptyState from "../components/common/EmptyState";
import SeverityBadge from "../components/report/SeverityBadge";

import { mockHistory } from "../mock/mockData";

export default function History() {
  const incidents = mockHistory;

  return (
    <>
      <Header
        eyebrow="Archive"
        title="Incident History"
        subtitle="Every incident IncidentIQ has analyzed, newest first."
      />

      <Card
        title="Incidents"
        flush={incidents.length > 0}
        actions={<span className="is-muted">{incidents.length} records</span>}
      >
        {incidents.length === 0 ? (
          <EmptyState
            title="No incidents yet"
            message="Analyzed incidents will show up here."
          />
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Title</th>
                  <th>Severity</th>
                  <th>Category</th>
                  <th>Duration</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((incident) => (
                  <tr key={incident.id}>
                    <td className="cell-mono">{incident.date}</td>
                    <td className="cell-title">{incident.title}</td>
                    <td>
                      <SeverityBadge level={incident.severity} />
                    </td>
                    <td>{incident.category}</td>
                    <td className="cell-mono">{incident.durationMinutes} min</td>
                    <td>
                      <span className={`status-pill status-${incident.status.toLowerCase()}`}>
                        {incident.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
