import Header from "../components/layout/Header";
import KPICard from "../components/dashboard/KPICard";
import SeverityChart from "../components/dashboard/SeverityChart";
import CategoryChart from "../components/dashboard/CategoryChart";
import TrendChart from "../components/dashboard/TrendChart";
import RecurringChart from "../components/dashboard/RecurringChart";

import { mockDashboard } from "../mock/mockData";

export default function Dashboard() {
  const { kpis, severity, categories, trend, recurring } = mockDashboard;

  return (
    <>
      <Header
        eyebrow="Reliability overview"
        title="Dashboard"
        subtitle="Incident volume, severity mix and recurring root causes across your services."
      />

      <div className="kpi-row">
        <KPICard label="Total incidents" value={kpis.totalIncidents} hint="Last 6 months" />
        <KPICard label="Open SEV1/SEV2" value={kpis.openHighSeverity} delta={-12} />
        <KPICard label="Mean time to detect" value={kpis.meanTimeToDetect} delta={-8} />
        <KPICard label="Recurring causes" value={kpis.recurringCauses} delta={4} />
      </div>

      <div className="chart-grid">
        <SeverityChart data={severity} />
        <CategoryChart data={categories} />
        <TrendChart data={trend} />
        <RecurringChart data={recurring} />
      </div>
    </>
  );
}
