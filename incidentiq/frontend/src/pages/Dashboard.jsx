import { useEffect, useState } from "react";

import Header from "../components/layout/Header";
import ErrorBanner from "../components/common/ErrorBanner";
import Loader from "../components/common/Loader";
import KPICard from "../components/dashboard/KPICard";
import SeverityChart from "../components/dashboard/SeverityChart";
import CategoryChart from "../components/dashboard/CategoryChart";
import TrendChart from "../components/dashboard/TrendChart";
import RecurringChart from "../components/dashboard/RecurringChart";

import { listIncidents, buildDashboard } from "../api/client";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  function load() {
    setError(null);
    setData(null);
    listIncidents()
      .then((response) => setData(buildDashboard(response.incidents)))
      .catch((err) => setError(err.message));
  }

  useEffect(load, []);

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
    </>
  );
}
