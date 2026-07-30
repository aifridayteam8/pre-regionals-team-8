export default function ConfidenceMeter({ value = 0 }) {
  const percent = Math.min(100, Math.max(0, Math.round(value * 100)));

  return (
    <div className="confidence-meter">
      <span className="confidence-label">Confidence</span>

      <div
        className="confidence-track"
        role="meter"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className="confidence-fill" style={{ width: `${percent}%` }} />
      </div>

      <span className="confidence-value">{percent}%</span>
    </div>
  );
}
