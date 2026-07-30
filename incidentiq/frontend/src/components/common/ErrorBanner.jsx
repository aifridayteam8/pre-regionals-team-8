import Button from "./Button";

export default function ErrorBanner({ message, onRetry, onDismiss }) {
  if (!message) return null;

  return (
    <div className="error-banner" role="alert">
      <span className="error-banner-message">{message}</span>
      <div className="error-banner-actions">
        {onRetry && (
          <Button variant="ghost" onClick={onRetry}>
            Retry
          </Button>
        )}
        {onDismiss && (
          <Button variant="ghost" onClick={onDismiss}>
            Dismiss
          </Button>
        )}
      </div>
    </div>
  );
}
