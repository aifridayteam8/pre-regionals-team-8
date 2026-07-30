import Card from "../common/Card";

export default function RecommendationCard({ recommendations = [] }) {
  return (
    <Card title="Recommendations" className="recommendation-card">
      {recommendations.length === 0 ? (
        <p className="is-muted">No recommendations available.</p>
      ) : (
        <ol className="recommendation-list">
          {recommendations.map((item, index) => {
            const text = typeof item === "string" ? item : item.text;
            const owner = typeof item === "string" ? null : item.owner;

            return (
              <li key={item.id ?? index} className="recommendation-item">
                <span className="recommendation-text">{text}</span>
                {owner && <span className="recommendation-owner">{owner}</span>}
              </li>
            );
          })}
        </ol>
      )}
    </Card>
  );
}
