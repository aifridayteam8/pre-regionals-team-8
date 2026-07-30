import { useState } from "react";

import Card from "../common/Card";
import Button from "../common/Button";

export default function DebugPanel({ transparency = {}, payload }) {
  const [isOpen, setIsOpen] = useState(false);

  const { promptDigest, model, validation, latencyMs, retryCount } = transparency;

  return (
    <Card title="AI Transparency" className="debug-panel">
      <dl className="debug-grid">
        <div className="debug-item">
          <dt>Prompt digest</dt>
          <dd>{promptDigest ?? "-"}</dd>
        </div>

        <div className="debug-item">
          <dt>Model</dt>
          <dd>{model ?? "-"}</dd>
        </div>

        <div className="debug-item">
          <dt>Validation</dt>
          <dd>{validation ?? "-"}</dd>
        </div>

        <div className="debug-item">
          <dt>Latency</dt>
          <dd>{latencyMs != null ? `${latencyMs} ms` : "-"}</dd>
        </div>

        <div className="debug-item">
          <dt>Retry count</dt>
          <dd>{retryCount ?? 0}</dd>
        </div>
      </dl>

      <Button variant="secondary" size="sm" onClick={() => setIsOpen((open) => !open)}>
        {isOpen ? "Hide" : "Show"} raw response
      </Button>

      {isOpen && (
        <pre className="debug-panel-body">{JSON.stringify(payload, null, 2)}</pre>
      )}
    </Card>
  );
}
