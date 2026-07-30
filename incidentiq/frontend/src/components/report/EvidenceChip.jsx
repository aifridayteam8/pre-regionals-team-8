export default function EvidenceChip({ label, line, onClick }) {
  return (
    <button type="button" className="evidence-chip" onClick={onClick}>
      {line != null && <span className="evidence-chip-line">L{line}</span>}
      <span className="evidence-chip-label">{label}</span>
    </button>
  );
}
