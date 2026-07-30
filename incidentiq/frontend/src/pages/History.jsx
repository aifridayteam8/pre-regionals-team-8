import { Fragment, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import Header from "../components/layout/Header";
import Card from "../components/common/Card";
import EmptyState from "../components/common/EmptyState";
import ErrorBanner from "../components/common/ErrorBanner";
import Loader from "../components/common/Loader";
import SeverityBadge from "../components/report/SeverityBadge";
import Highlight from "../components/common/Highlight";
import FilterBar from "../components/common/FilterBar";

import { listIncidents, toHistoryRow } from "../api/client";

function rowMatchesSearch(incident, query) {
  if (!query) return true;
  const needle = query.toLowerCase();
  return (
    incident.title.toLowerCase().includes(needle) ||
    String(incident.id).toLowerCase().includes(needle)
  );
}

function rowMatchesFilters(incident, filters) {
  if (filters.severity && String(incident.severity) !== filters.severity) return false;
  if (filters.category && incident.category !== filters.category) return false;
  if (filters.status && incident.status !== filters.status) return false;
  if (filters.dateFrom && incident.date < filters.dateFrom) return false;
  if (filters.dateTo && incident.date > filters.dateTo) return false;
  return true;
}

function IncidentRow({ incident, isChild = false, query, onOpen }) {
  return (
    <tr className={isChild ? "is-child-row is-clickable-row" : "is-clickable-row"} onClick={() => onOpen(incident)}>
      <td className="cell-mono">{isChild ? "" : incident.date}</td>
      <td className="cell-title">
        {isChild && <span className="is-muted">{"└ "}</span>}
        <Highlight text={incident.title} query={query} />
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

const EMPTY_FILTERS = { severity: "", category: "", status: "", dateFrom: "", dateTo: "" };

export default function History() {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState(null);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState(EMPTY_FILTERS);

  function load() {
    setError(null);
    setIncidents(null);
    listIncidents()
      .then((data) => setIncidents(data.incidents.map(toHistoryRow)))
      .catch((err) => setError(err.message));
  }

  useEffect(load, []);

  const categories = useMemo(
    () => [...new Set((incidents ?? []).map((incident) => incident.category))].sort(),
    [incidents]
  );
  const statuses = useMemo(
    () => [...new Set((incidents ?? []).map((incident) => incident.status))].sort(),
    [incidents]
  );

  const filtered = useMemo(() => {
    if (!incidents) return [];
    return incidents.filter((incident) => {
      const childMatchesSearch = incident.children.some((child) => rowMatchesSearch(child, query));
      const selfMatchesSearch = rowMatchesSearch(incident, query);
      if (!selfMatchesSearch && !childMatchesSearch) return false;
      return rowMatchesFilters(incident, filters);
    });
  }, [incidents, query, filters]);

  const totalRecords = filtered.reduce((sum, incident) => sum + 1 + incident.children.length, 0);
  const hasActiveFilters = query || Object.values(filters).some(Boolean);

  function openReport(incident) {
    navigate(`/report/${incident.id}`);
  }

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
        <>
          <FilterBar
            query={query}
            onQueryChange={setQuery}
            searchPlaceholder="Search by title or incident ID..."
            filters={filters}
            onFiltersChange={setFilters}
            onClear={() => {
              setQuery("");
              setFilters(EMPTY_FILTERS);
            }}
            fields={[
              {
                key: "severity",
                label: "Severity",
                options: [1, 2, 3, 4].map((level) => ({ value: String(level), label: `SEV${level}` })),
              },
              {
                key: "category",
                label: "Category",
                options: categories.map((category) => ({ value: category, label: category })),
              },
              {
                key: "status",
                label: "Status",
                options: statuses.map((status) => ({ value: status, label: status })),
              },
              { key: "dateFrom", label: "From", type: "date" },
              { key: "dateTo", label: "To", type: "date" },
            ]}
          />

          <Card
            title="Incidents"
            flush={filtered.length > 0}
            actions={
              <span className="is-muted">
                {totalRecords} record{totalRecords === 1 ? "" : "s"}
                {hasActiveFilters ? ` (of ${incidents.reduce((sum, i) => sum + 1 + i.children.length, 0)})` : ""}
              </span>
            }
          >
            {incidents.length === 0 ? (
              <EmptyState title="No incidents yet" message="Analyzed incidents will show up here." />
            ) : filtered.length === 0 ? (
              <EmptyState
                title="No matches"
                message="Nothing matches your search and filters."
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
                    {filtered.map((incident) => (
                      <Fragment key={incident.id}>
                        <IncidentRow incident={incident} query={query} onOpen={openReport} />
                        {incident.children.map((child) => (
                          <IncidentRow key={child.id} incident={child} isChild query={query} onOpen={openReport} />
                        ))}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </>
  );
}
