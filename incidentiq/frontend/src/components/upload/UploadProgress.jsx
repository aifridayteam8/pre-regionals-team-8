import Card from "../common/Card";

const ICONS = {
  done: "\u2713",
  active: "\u27F3",
  pending: "\u25CB",
};

function stageState(index, activeIndex) {
  if (index < activeIndex) return "done";
  if (index === activeIndex) return "active";
  return "pending";
}

export default function UploadProgress({ fileName, stages = [], activeIndex = 0 }) {
  const total = stages.length || 1;
  const percent = Math.min(100, Math.round((activeIndex / total) * 100));

  return (
    <Card title="Generating Report">
      <div className="upload-progress-head">
        <span className="upload-progress-name">{fileName}</span>
        <span className="upload-progress-percent">{percent}%</span>
      </div>

      <div
        className="upload-progress-track"
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className="upload-progress-bar" style={{ width: `${percent}%` }} />
      </div>

      <ul className="stage-list">
        {stages.map((stage, index) => {
          const state = stageState(index, activeIndex);

          return (
            <li key={stage} className={`stage-item stage-${state}`}>
              <span className={`stage-icon ${state === "active" ? "is-spinning" : ""}`.trim()}>
                {ICONS[state]}
              </span>
              <span className="stage-label">{stage}</span>
              {state === "pending" && <span className="stage-note">Waiting...</span>}
              {state === "active" && <span className="stage-note">In progress</span>}
              {state === "done" && <span className="stage-note">Done</span>}
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
