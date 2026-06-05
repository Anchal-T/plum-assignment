import { useRef } from "react";

interface FileUploaderProps {
  files: File[];
  onAdd: (f: File[]) => void;
  onRemove: (i: number) => void;
  disabled?: boolean;
}

export function FileUploader({ files, onAdd, onRemove, disabled }: FileUploaderProps) {
  const dropRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    if (disabled) return;
    const dropped = Array.from(e.dataTransfer.files);
    onAdd(dropped);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files) onAdd(Array.from(e.target.files));
  }

  function handleClick() {
    if (!disabled) inputRef.current?.click();
  }

  return (
    <div>
      <div
        ref={dropRef}
        onClick={handleClick}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        style={{
          border: "2px dashed #ccc",
          borderRadius: 8,
          padding: 32,
          textAlign: "center",
          cursor: disabled ? "not-allowed" : "pointer",
          opacity: disabled ? 0.6 : 1,
          background: "#f9f9f9",
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.webp"
          multiple
          onChange={handleChange}
          style={{ display: "none" }}
        />
        <p style={{ margin: 0, color: "#666" }}>
          📄 Drop documents here or click to browse
        </p>
        <p style={{ margin: "4px 0 0", fontSize: 12, color: "#999" }}>
          PDF, JPG, PNG (max 10MB each)
        </p>
      </div>

      {files.length > 0 && (
        <ul style={{ marginTop: 8, padding: 0, listStyle: "none" }}>
          {files.map((f, i) => (
            <li
              key={`${f.name}-${f.size}-${f.lastModified}`}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "4px 0",
              }}
            >
              <span>{f.name}</span>
              <button
                onClick={() => onRemove(i)}
                disabled={disabled}
                style={{ background: "none", border: "none", color: "red", cursor: "pointer" }}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
