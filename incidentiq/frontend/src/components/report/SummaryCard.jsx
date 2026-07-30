import Card from "../common/Card";

export default function SummaryCard({ summary }) {
  return (
    <Card title="Summary" className="summary-card">
      {summary ? (
        <p className="summary-text">{summary}</p>
      ) : (
        <p className="summary-text is-muted">No summary available.</p>
      )}
    </Card>
  );
}
