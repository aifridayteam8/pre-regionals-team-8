export default function EmptyState({ title = "Nothing here yet", message, action }) {
  return (
    <div className="empty-state">
      <h3 className="empty-state-title">{title}</h3>
      {message && <p className="empty-state-message">{message}</p>}
      {action && <div className="empty-state-action">{action}</div>}
    </div>
  );
}
