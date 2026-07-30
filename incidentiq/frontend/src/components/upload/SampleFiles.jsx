import Card from "../common/Card";

import { mockSampleFiles } from "../../mock/mockData";

export default function SampleFiles({ samples = mockSampleFiles, onSelect, disabled = false }) {
  return (
    <Card title="Sample Files">
      <ul className="sample-files-list">
        {samples.map((sample) => (
          <li key={sample.id}>
            <button
              type="button"
              className="sample-file"
              disabled={disabled}
              onClick={() => onSelect?.(sample)}
            >
              <span>
                <span className="sample-file-name">{sample.name}</span>
                <span className="sample-file-meta">{sample.fileName}</span>
              </span>
              <span aria-hidden="true">&rarr;</span>
            </button>
          </li>
        ))}
      </ul>
    </Card>
  );
}
