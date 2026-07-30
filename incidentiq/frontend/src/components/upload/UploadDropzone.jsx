import { useRef, useState } from "react";

import Button from "../common/Button";
import Icon from "../common/Icon";
import { ACCEPTED_HINT, validateFile } from "../../utils/validateFile";

function formatSize(bytes) {
  if (bytes == null) return null;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadDropzone({ file, onFileSelected, onClear, disabled = false }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState(null);

  function selectFile(selected) {
    if (!selected) return;

    const error = validateFile(selected);
    if (error) {
      setValidationError(error);
      return;
    }

    setValidationError(null);
    if (onFileSelected) onFileSelected(selected);
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    selectFile(event.dataTransfer.files?.[0]);
  }

  function handleClear() {
    setValidationError(null);
    onClear?.();
  }

  const size = formatSize(file?.size);

  return (
    <div>
      <div
        className={`dropzone ${isDragging ? "is-dragging" : ""} ${
          disabled ? "is-disabled" : ""
        }`.trim()}
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <div className="dropzone-icon">
          <Icon name="upload" size={28} />
        </div>

        <p className="dropzone-title">Drag &amp; drop your incident log</p>
        <p className="dropzone-hint">
          Accepted formats: {ACCEPTED_HINT} &middot; up to 5 MB
        </p>

        <Button variant="primary" disabled={disabled} onClick={() => inputRef.current?.click()}>
          <Icon name="file" size={15} />
          Choose File
        </Button>

        <input
          ref={inputRef}
          className="dropzone-input"
          type="file"
          accept=".log,.txt,.json,text/plain,application/json"
          disabled={disabled}
          onChange={(event) => {
            selectFile(event.target.files?.[0]);
            // Reset so re-selecting the same (now-invalid) file still fires onChange.
            event.target.value = "";
          }}
        />
      </div>

      {validationError && (
        <p className="dropzone-error" role="alert">
          {validationError}
        </p>
      )}

      <div className="upload-selection">
        {file ? (
          <>
            <span>
              Selected <span className="upload-selection-name">{file.name}</span>
              {size ? ` (${size})` : ""}
            </span>

            {onClear && (
              <Button variant="ghost" size="sm" disabled={disabled} onClick={handleClear}>
                Clear
              </Button>
            )}
          </>
        ) : (
          <span>No file selected</span>
        )}
      </div>
    </div>
  );
}
