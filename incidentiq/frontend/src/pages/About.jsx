import Header from "../components/layout/Header";
import Card from "../components/common/Card";

const AI_FLOW = [
  "Parse the uploaded log into structured events",
  "Mask secrets, tokens, emails and IP addresses",
  "Build a compact event digest and prompt",
  "Generate summary, impact assessment and root cause analysis",
  "Validate the model response against a JSON schema, retry on failure",
];

const STACK = [
  "React 19",
  "Vite",
  "React Router",
  "Recharts",
  "Express mock server",
  "Server-Sent Events",
];

function ArchitectureDiagram() {
  const boxes = [
    { x: 8, label: "Browser UI" },
    { x: 183, label: "API / SSE" },
    { x: 358, label: "Log Pipeline" },
    { x: 533, label: "LLM + Validator" },
  ];

  return (
    <svg
      className="architecture-diagram"
      viewBox="0 0 700 120"
      role="img"
      aria-label="Architecture diagram"
    >
      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill="#3b82f6" />
        </marker>
      </defs>

      {boxes.map((box, index) => (
        <g key={box.label}>
          <rect
            x={box.x}
            y={30}
            width={150}
            height={58}
            rx={10}
            fill="#16202e"
            stroke="#2c3d59"
          />
          <text x={box.x + 75} y={64} textAnchor="middle" fill="#e8edf5" fontSize="13">
            {box.label}
          </text>

          {index < boxes.length - 1 && (
            <line
              x1={box.x + 150}
              y1={59}
              x2={box.x + 178}
              y2={59}
              stroke="#3b82f6"
              strokeWidth="2"
              markerEnd="url(#arrow)"
            />
          )}
        </g>
      ))}
    </svg>
  );
}

export default function About() {
  return (
    <>
      <Header
        eyebrow="Product"
        title="About IncidentIQ"
        subtitle="How incident logs become reviewable, evidence-backed reports."
      />

      <Card title="Architecture">
        <ArchitectureDiagram />
      </Card>

      <div className="report-grid">
        <Card title="AI flow">
          <ol className="about-list">
            {AI_FLOW.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </Card>

        <Card title="Privacy">
          <p>
            Logs are masked before they leave the pipeline: secrets, tokens, email
            addresses and IP addresses are redacted, and raw uploads are never
            persisted. Only the masked event digest is sent to the model, and every
            report records the prompt digest and validation result so any output can
            be audited.
          </p>
        </Card>
      </div>

      <Card title="Technology stack">
        <ul className="about-tags">
          {STACK.map((item) => (
            <li key={item} className="about-tag">
              {item}
            </li>
          ))}
        </ul>
      </Card>
    </>
  );
}
