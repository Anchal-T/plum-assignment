import { useFormStatus } from "react-dom";

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      style={{
        ...submitBase,
        background: pending ? "#94a3b8" : "#2563eb",
        cursor: pending ? "not-allowed" : "pointer",
      }}
    >
      {pending ? "⏳ Processing..." : "Submit Claim ▶"}
    </button>
  );
}

function FormFields() {
  const { pending } = useFormStatus();
  return (
    <div style={fieldGrid}>
      <div style={fieldRow}>
        <div style={fieldCell}>
          <label style={labelStyle}>Member ID</label>
          <input name="member_id" required disabled={pending} placeholder="EMP001" style={inputStyle} />
        </div>
        <div style={fieldCell}>
          <label style={labelStyle}>Member Name</label>
          <input name="member_name" required disabled={pending} placeholder="Rajesh Kumar" style={inputStyle} />
        </div>
      </div>
      <div style={fieldRow}>
        <div style={fieldCell}>
          <label style={labelStyle}>Treatment Date</label>
          <input name="treatment_date" type="date" required disabled={pending} style={inputStyle} />
        </div>
        <div style={fieldCell}>
          <label style={labelStyle}>Claim Amount (₹)</label>
          <input name="claim_amount" type="number" required min={1} disabled={pending} placeholder="1500" style={inputStyle} />
        </div>
      </div>
      <div style={fieldRow}>
        <div style={fieldCell}>
          <label style={labelStyle}>Hospital (optional)</label>
          <input name="hospital_name" disabled={pending} placeholder="Apollo Hospitals" style={inputStyle} />
        </div>
        <div style={{ ...fieldCell, display: "flex", alignItems: "flex-end", paddingBottom: 4 }}>
          <label style={checkboxLabel}>
            <input name="is_cashless" type="checkbox" disabled={pending} />
            Cashless Request
          </label>
        </div>
      </div>
    </div>
  );
}

export function ClaimForm() {
  return (
    <>
      <FormFields />
      <SubmitButton />
    </>
  );
}

const fieldGrid: React.CSSProperties = { display: "flex", flexDirection: "column", gap: 12 };
const fieldRow: React.CSSProperties = { display: "flex", gap: 12 };
const fieldCell: React.CSSProperties = { flex: 1 };
const labelStyle: React.CSSProperties = { fontSize: 13, color: "#374151" };
const checkboxLabel: React.CSSProperties = { display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "#374151" };
const inputStyle: React.CSSProperties = {
  display: "block",
  width: "100%",
  padding: "8px 10px",
  fontSize: 14,
  border: "1px solid #d1d5db",
  borderRadius: 4,
  boxSizing: "border-box",
  marginTop: 2,
};
const submitBase: React.CSSProperties = {
  padding: "10px 24px",
  fontSize: 16,
  fontWeight: 600,
  color: "#fff",
  border: "none",
  borderRadius: 6,
  width: "100%",
};
