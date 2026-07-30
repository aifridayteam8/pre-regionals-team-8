import { useEffect, useMemo, useState } from "react";

import Header from "../components/layout/Header";
import ErrorBanner from "../components/common/ErrorBanner";
import Loader from "../components/common/Loader";
import EmptyState from "../components/common/EmptyState";
import FilterBar from "../components/common/FilterBar";
import KPICard from "../components/dashboard/KPICard";
import SeverityChart from "../components/dashboard/SeverityChart";
import CategoryChart from "../components/dashboard/CategoryChart";
import TrendChart from "../components/dashboard/TrendChart";
import RecurringChart from "../components/dashboard/RecurringChart";

import { listIncidents, buildDashboard, shortDate } from "../api/client";

const EMPTY_FILTERS = { severity: "", category: "", status: "", dateFrom: "", dateTo: "" };
const SEVERITY_OPTIONS = ["SEV1", "SEV2", "SEV3", "SEV4"].map((sev) => ({ value: sev, label: sev }));

export default function Dashboard() {
  const [incidents, setIncidents] = useState(null);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState(EMPTY_FILTERS);

  function load() {
    setError(null);
    setIncidents(null);
    listIncidents()
      .then((response) => setIncidents(response.incidents))
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
    if (!incidents) return null;
    return incidents.filter((incident) => {
      if (filters.severity && incident.severity !== filters.severity) return false;
      if (filters.category && incident.category !== filters.category) return false;
      if (filters.status && incident.status !== filters.status) return false;
      const date = shortDate(incident);
      if (filters.dateFrom && date < filters.dateFrom) return false;
      if (filters.dateTo && date > filters.dateTo) return false;
      return true;
    });
  }, [incidents, filters]);

  const data = useMemo(() => (filtered ? buildDashboard(filtered) : null), [filtered]);
  const hasActiveFilters = Object.values(filters).some(Boolean);

  return (
    <>
      <Header
        eyebrow="Reliability overview"
        title="Dashboard"
        subtitle="Incident volume, severity mix and recurring root causes across your services."
      />

      {error ? (
        <ErrorBanner message={`Could not load dashboard: ${error}`} onRetry={load} />
      ) : data === null ? (
        <Loader label="Loading dashboard..." />
      ) : (
        <>
          <FilterBar
            filters={filters}
            onFiltersChange={setFilters}
            onClear={() => setFilters(EMPTY_FILTERS)}
            fields={[
              { key: "severity", label: "Severity", options: SEVERITY_OPTIONS },
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

          {filtered.length === 0 ? (
            <EmptyState title="No matching incidents" message="Try widening your filters." />
          ) : (
            <>
              <div className="kpi-row">
                <KPICard
                  label="Total incidents"
                  value={data.kpis.totalIncidents}
                  hint={`${data.kpis.childIncidents} child incidents`}
                />
                <KPICard label="Open SEV1/SEV2" value={data.kpis.openHighSeverity} />
                <KPICard label="Avg incident duration" value={data.kpis.avgDuration} />
                <KPICard label="Recurring causes" value={data.kpis.recurringCauses} />
              </div>

              <div className="chart-grid">
                <SeverityChart data={data.severity} />
                <CategoryChart data={data.categories} />
                <TrendChart data={data.trend} />
                <RecurringChart data={data.recurring} />
              </div>
            </>
          )}

          {hasActiveFilters && (
            <p className="is-muted dashboard-filter-note">
              Showing {filtered.length} of {incidents.length} incidents.
            </p>
          )}
        </>
      )}
    </>
  );
}
