import { Fragment, useEffect, useState } from "react";

import Header from "../components/layout/Header";
import Card from "../components/common/Card";
import EmptyState from "../components/common/EmptyState";
import ErrorBanner from "../components/common/ErrorBanner";
import Loader from "../components/common/Loader";
import SeverityBadge from "../components/report/SeverityBadge";

import { listIncidents, toHistoryRow } from "../api/client";

function IncidentRow({ incident, isChild = false }) {
  return (
    <tr className={isChild ? "is-child-row" : undefined}>
      <td className="cell-mono">{isChild ? "" : incident.date}</td>
      <td className="cell-title">
        {isChild && <span className="is-muted">{"└ "}</span>}
        {incident.title}
      </td>
      <td>
        <SeverityBadge level={incident.severity} />
      </td>
      <td>{incident.category}</td>
      <td className="cell-mono">
        {incident.durationMinutes != null ? `${incident.durationMinutes} min` : "-"}
      </td>
      <td>
        <span className={`status-pill status-${incident.status.toLowerCase()}`}>
          {incident.status}
        </span>
      </td>
    </tr>
  );
}

export default function History() {
  const [incidents, setIncidents] = useState(null);
  const [error, setError] = useState(null);

  function load() {
    setError(null);
    setIncidents(null);
    listIncidents()
      .then((data) => setIncidents(data.incidents.map(toHistoryRow)))
      .catch((err) => setError(err.message));
  }

  useEffect(load, []);

  const totalRecords =
    incidents?.reduce((sum, incident) => sum + 1 + incident.children.length, 0) ?? 0;

  return (
    <>
      <Header
        eyebrow="Archive"
        title="Incident History"
        subtitle="Every incident IncidentIQ has analyzed, newest first."
      />

      {error ? (
        <ErrorBanner message={`Could not load incidents: ${error}`} onRetry={load} />
      ) : incidents === null ? (
        <Loader label="Loading incidents..." />
      ) : (
        <Card
          title="Incidents"
          flush={incidents.length > 0}
          actions={<span className="is-muted">{totalRecords} records</span>}
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
                    <Fragment key={incident.id}>
                      <IncidentRow incident={incident} />
                      {incident.children.map((child) => (
                        <IncidentRow key={child.id} incident={child} isChild />
                      ))}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </>
  );
}
