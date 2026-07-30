import Card from "../common/Card";
import EvidenceChip from "./EvidenceChip";
import ConfidenceMeter from "./ConfidenceMeter";

export default function RcaCard({ rca = {}, onEvidenceClick }) {
  const { rootCause, reasoning, confidence, evidence = [] } = rca;

  return (
    <Card title="Root Cause Analysis" className="rca-card">
      <p className="rca-root-cause">{rootCause ?? "Root cause not determined."}</p>

      {reasoning && <p className="rca-reasoning">{reasoning}</p>}

      {confidence != null && <ConfidenceMeter value={confidence} />}

      {evidence.length > 0 && (
        <div className="rca-evidence">
          {evidence.map((item, index) => (
            <EvidenceChip
              key={item.id ?? index}
              label={item.label ?? item.text}
              line={item.line}
              onClick={() => onEvidenceClick?.(item)}
            />
          ))}
        </div>
      )}
    </Card>
  );
}
