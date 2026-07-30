import Card from "../common/Card";
import EmptyState from "../common/EmptyState";

export default function TimelineTable({ events = [] }) {
  return (
    <Card
      title="Timeline"
      flush={events.length > 0}
      actions={<span className="is-muted">{events.length} events</span>}
    >
      {events.length === 0 ? (
        <EmptyState title="No timeline events" message="Nothing was extracted from the log." />
      ) : (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Severity</th>
                <th>Host</th>
                <th>Service</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event, index) => (
                <tr key={event.id ?? index}>
                  <td className="cell-mono">{event.timestamp}</td>
                  <td>
                    <span className={`log-level log-${(event.severity ?? "info").toLowerCase()}`}>
                      {event.severity ?? "INFO"}
                    </span>
                  </td>
                  <td className="cell-mono">{event.host ?? "-"}</td>
                  <td className="cell-mono">{event.service ?? "-"}</td>
                  <td>{event.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
