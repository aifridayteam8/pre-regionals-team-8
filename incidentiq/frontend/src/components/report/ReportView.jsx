import { useState } from "react";

import ReportHeader from "./ReportHeader";
import SummaryCard from "./SummaryCard";
import ImpactCard from "./ImpactCard";
import RcaCard from "./RcaCard";
import RecommendationCard from "./RecommendationCard";
import TimelineTable from "./TimelineTable";
import DebugPanel from "./DebugPanel";
import Loader from "../common/Loader";
import EmptyState from "../common/EmptyState";
import ErrorBanner from "../common/ErrorBanner";
import Button from "../common/Button";
import Icon from "../common/Icon";

const TABS = ["Report", "Timeline", "AI Transparency"];

export default function ReportView({ report, isLoading = false, error, onRetry }) {
  const [activeTab, setActiveTab] = useState(TABS[0]);

  if (isLoading) return <Loader label="Analyzing incident..." />;

  if (error) return <ErrorBanner message={error} onRetry={onRetry} />;

  if (!report) {
    return (
      <EmptyState
        title="No report yet"
        message="Upload an incident log or pick a sample file to generate an AI incident report."
      />
    );
  }

  return (
    <div className="report-view">
      <ReportHeader
        report={report}
        actions={
          <Button variant="secondary" size="sm">
            <Icon name="download" size={14} />
            Export
          </Button>
        }
      />

      <div className="tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={activeTab === tab}
            className={`tab ${activeTab === tab ? "is-active" : ""}`.trim()}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "Report" && (
        <>
          <SummaryCard summary={report.summary} />

          <div className="report-grid">
            <ImpactCard impact={report.impact} />
            <RcaCard rca={report.rca} />
          </div>

          <RecommendationCard recommendations={report.recommendations} />
        </>
      )}

      {activeTab === "Timeline" && <TimelineTable events={report.timeline} />}

      {activeTab === "AI Transparency" && (
        <DebugPanel transparency={report.transparency} payload={report} />
      )}
    </div>
  );
}
