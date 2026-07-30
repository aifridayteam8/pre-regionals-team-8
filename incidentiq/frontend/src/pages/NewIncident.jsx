import { useEffect, useRef, useState } from "react";

import Header from "../components/layout/Header";
import UploadDropzone from "../components/upload/UploadDropzone";
import SampleFiles from "../components/upload/SampleFiles";
import UploadProgress from "../components/upload/UploadProgress";
import ReportView from "../components/report/ReportView";
import Button from "../components/common/Button";

import { GENERATION_STAGES, mockReport } from "../mock/mockData";

export default function NewIncident() {
  const [file, setFile] = useState(null);
  const [stageIndex, setStageIndex] = useState(null);
  const [report, setReport] = useState(null);
  const timers = useRef([]);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const isGenerating = stageIndex !== null;

  function reset(selected = null) {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setFile(selected);
    setStageIndex(null);
    setReport(null);
  }

  function handleGenerate() {
    if (!file) return;

    setReport(null);
    setStageIndex(0);

    timers.current = GENERATION_STAGES.map((_, index) =>
      setTimeout(() => {
        const next = index + 1;

        if (next === GENERATION_STAGES.length) {
          setStageIndex(null);
          setReport(mockReport);
        } else {
          setStageIndex(next);
        }
      }, 700 * (index + 1))
    );
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

        <SampleFiles
          disabled={isGenerating}
          onSelect={(sample) => reset({ name: sample.fileName })}
        />
      </div>

      {isGenerating && (
        <UploadProgress
          fileName={file?.name}
          stages={GENERATION_STAGES}
          activeIndex={stageIndex}
        />
      )}

      {!isGenerating && <ReportView report={report} />}
    </>
  );
}
