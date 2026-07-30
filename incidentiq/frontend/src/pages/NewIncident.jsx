import { useState } from "react";

import Header from "../components/layout/Header";
import UploadDropzone from "../components/upload/UploadDropzone";
import UploadProgress from "../components/upload/UploadProgress";
import ReportView from "../components/report/ReportView";
import Button from "../components/common/Button";

import { uploadIncident, fetchFullReport } from "../api/client";

const STAGES = ["Uploading", "Parsing & storing", "Building report"];

export default function NewIncident() {
  const [file, setFile] = useState(null);
  const [stageIndex, setStageIndex] = useState(null);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const isGenerating = stageIndex !== null;

  function reset(selected = null) {
    setFile(selected);
    setStageIndex(null);
    setReport(null);
    setError(null);
  }

  async function handleGenerate() {
    if (!file) return;

    setReport(null);
    setError(null);
    const startedAt = performance.now();

    try {
      setStageIndex(0);
      const uploaded = await uploadIncident(file);

      setStageIndex(1);
      // Parsing/storing happen server-side inside the upload call; give the
      // stage list a beat so the progression is visible.
      await new Promise((resolve) => setTimeout(resolve, 250));

      setStageIndex(2);
      const fullReport = await fetchFullReport(uploaded.parent_id, {
        latencyMs: Math.round(performance.now() - startedAt),
      });

      setReport(fullReport);
    } catch (err) {
      setError(err.message);
    } finally {
      setStageIndex(null);
    }
  }

  return (
    <>
      <Header
        eyebrow="Incident intake"
        title="Upload Incident Logs"
        subtitle="Upload a log file and IncidentIQ generates a severity assessment, root cause analysis and remediation plan."
        actions={
          <Button variant="primary" disabled={!file || isGenerating} onClick={handleGenerate}>
            {isGenerating ? "Generating..." : "Generate Report"}
          </Button>
        }
      />

      <div className="upload-grid">
        <UploadDropzone
          file={file}
          disabled={isGenerating}
          onFileSelected={(selected) => reset(selected)}
          onClear={() => reset(null)}
        />
      </div>

      {isGenerating && (
        <UploadProgress fileName={file?.name} stages={STAGES} activeIndex={stageIndex} />
      )}

      {!isGenerating && (
        <ReportView report={report} error={error} onRetry={handleGenerate} />
      )}
    </>
  );
}
