import { useState } from "react";
import { useNavigate } from "react-router-dom";

import Header from "../components/layout/Header";
import UploadDropzone from "../components/upload/UploadDropzone";
import UploadProgress from "../components/upload/UploadProgress";
import ErrorBanner from "../components/common/ErrorBanner";
import Button from "../components/common/Button";

import { uploadIncident, fetchFullReport } from "../api/client";
import { runStagedFlow } from "../api/sse";

const STAGES = ["Uploading", "Parsing & storing", "Building report"];

export default function NewIncident() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [stageIndex, setStageIndex] = useState(null);
  const [error, setError] = useState(null);

  const isGenerating = stageIndex !== null;

  function reset(selected = null) {
    setFile(selected);
    setStageIndex(null);
    setError(null);
  }

  async function handleGenerate() {
    if (!file) return;

    setError(null);

    try {
      const fullReport = await runStagedFlow(
        [
          {
            label: "Uploading",
            run: async () => (await uploadIncident(file)).parent_id,
          },
          // Parsing/storing already happened server-side inside the upload
          // call above; this stage just gives the progression a visible beat.
          { label: "Parsing & storing" },
          {
            label: "Building report",
            run: (parentId) => fetchFullReport(parentId),
          },
        ],
        setStageIndex
      );

      // Hand the freshly-built report to the report page via nav state so it
      // renders instantly instead of re-fetching what we just fetched.
      navigate(`/report/${fullReport.incidentId}`, { state: { report: fullReport } });
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

      {!isGenerating && error && (
        <ErrorBanner message={error} onRetry={handleGenerate} onDismiss={() => setError(null)} />
      )}
    </>
  );
}
