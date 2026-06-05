import { useActionState, useState } from "react";
import { FileUploader } from "../components/FileUploader";
import { ClaimForm } from "../components/ClaimForm";
import { DecisionBadge } from "../components/DecisionBadge";
import { submitClaim, processDocument } from "../services/api";
import type { ClaimResponse, DocumentField } from "../types";

type FormState = {
  status: "idle" | "success" | "error";
  claim: ClaimResponse | null;
  error: string | null;
};

const INITIAL_STATE: FormState = { status: "idle", claim: null, error: null };

function buildRequest(formData: FormData, documents: DocumentField[]) {
  return {
    member_id: formData.get("member_id") as string,
    member_name: formData.get("member_name") as string,
    treatment_date: formData.get("treatment_date") as string,
    claim_amount: Number(formData.get("claim_amount")),
    hospital_name: (formData.get("hospital_name") as string) || undefined,
    is_cashless: formData.get("is_cashless") === "on",
    documents,
  };
}

function ClaimSubmissionInner({ onReset }: { onReset: () => void }) {
  const [files, setFiles] = useState<File[]>([]);

  async function submitAction(_prev: FormState, formData: FormData): Promise<FormState> {
    try {
      const documents = await Promise.all(files.map(processDocument));
      const claim = await submitClaim(buildRequest(formData, documents));
      return { status: "success", claim, error: null };
    } catch (e) {
      return { status: "error", claim: null, error: (e as Error).message };
    }
  }

  const [state, formAction, isPending] = useActionState<FormState, FormData>(
    submitAction,
    INITIAL_STATE,
  );

  if (state.status === "success" && state.claim?.decision) {
    const d = state.claim.decision;
    return (
      <div style={pageWrap}>
        <h2 style={claimHeading}>Claim #{state.claim.claim_id.slice(0, 8)}</h2>
        <div style={decisionRow}>
          <DecisionBadge decision={d.decision} />
          <span style={mutedSmall}>Confidence: {(d.confidence_score * 100).toFixed(0)}%</span>
        </div>

        {d.approved_amount > 0 && (
          <p style={approvedAmount}>Approved: ₹{d.approved_amount.toLocaleString()}</p>
        )}
        {d.copay_amount > 0 && <p style={mutedSmall}>Copay: ₹{d.copay_amount}</p>}
        {d.network_discount > 0 && <p style={mutedSmall}>Network Discount: ₹{d.network_discount}</p>}

        {d.adjudication_steps.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <h3 style={sectionHeading}>Adjudication Steps</h3>
            {d.adjudication_steps.map((s) => (
              <div key={s.step} style={stepRow}>
                <span>{s.status === "PASS" ? "✅" : s.status === "WARN" ? "⚠️" : "❌"}</span>
                <strong style={stepName}>{s.step}</strong>
                <span style={mutedText}>{s.detail}</span>
              </div>
            ))}
          </div>
        )}

        {d.rejection_reasons.length > 0 && (
          <div style={rejectionBox}>
            <strong>Rejection Reasons:</strong>
            <ul style={listStyle}>
              {d.rejection_reasons.map((r) => <li key={r}>{r}</li>)}
            </ul>
          </div>
        )}

        {d.fraud_flags.length > 0 && (
          <div style={fraudBox}>
            <strong>Fraud Flags:</strong>
            <ul style={listStyle}>
              {d.fraud_flags.map((f) => <li key={f}>{f}</li>)}
            </ul>
          </div>
        )}

        {d.notes && <p style={notesBox}>{d.notes}</p>}
        <p style={nextStepsText}>{d.next_steps}</p>

        <button onClick={onReset} style={resetButton}>
          Submit Another Claim
        </button>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div style={pageWrap}>
        <div style={errorBox}>
          <strong>Error:</strong> {state.error}
        </div>
        <button onClick={onReset} style={{ marginTop: 12, padding: "8px 16px" }}>
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div style={pageWrap}>
      <h1 style={pageTitle}>Plum OPD Claim Adjudication</h1>
      <form action={formAction}>
        <div style={formSection}>
          <h3 style={sectionHeading}>Member Details</h3>
          <ClaimForm />
        </div>

        <div style={formSection}>
          <h3 style={sectionHeading}>Upload Documents</h3>
          {isPending && files.length > 0 && (
            <p style={mutedSmall}>⏳ Processing {files.length} document(s)…</p>
          )}
          <FileUploader
            files={files}
            onAdd={(newFiles) => setFiles((prev) => [...prev, ...newFiles])}
            onRemove={(i) => setFiles((prev) => prev.filter((_, j) => j !== i))}
            disabled={isPending}
          />
        </div>
      </form>
    </div>
  );
}

export function ClaimSubmission() {
  const [key, setKey] = useState(0);
  return <ClaimSubmissionInner key={key} onReset={() => setKey((k) => k + 1)} />;
}

// ---------------------------------------------------------------------------
// Module-level style constants (avoids new object refs on every render)
// ---------------------------------------------------------------------------

const pageWrap: React.CSSProperties = { maxWidth: 640, margin: "0 auto", padding: 24 };
const pageTitle: React.CSSProperties = { fontSize: 22, margin: "0 0 16px" };
const claimHeading: React.CSSProperties = { margin: "0 0 8px" };
const decisionRow: React.CSSProperties = { display: "flex", gap: 16, alignItems: "center", marginBottom: 16 };
const approvedAmount: React.CSSProperties = { fontSize: 18, fontWeight: 600 };
const mutedSmall: React.CSSProperties = { fontSize: 14, color: "#666" };
const mutedText: React.CSSProperties = { color: "#666" };
const sectionHeading: React.CSSProperties = { fontSize: 15, margin: "0 0 8px", color: "#374151" };
const stepRow: React.CSSProperties = { display: "flex", gap: 8, padding: "6px 0", borderBottom: "1px solid #f0f0f0", fontSize: 14 };
const stepName: React.CSSProperties = { minWidth: 160 };
const listStyle: React.CSSProperties = { margin: "4px 0 0", fontSize: 14 };
const rejectionBox: React.CSSProperties = { marginTop: 16, padding: 12, background: "#fef2f2", borderRadius: 6 };
const fraudBox: React.CSSProperties = { marginTop: 16, padding: 12, background: "#fffbeb", borderRadius: 6 };
const notesBox: React.CSSProperties = { marginTop: 16, padding: 12, background: "#f0fdf4", borderRadius: 6, fontSize: 14 };
const nextStepsText: React.CSSProperties = { marginTop: 12, fontStyle: "italic", color: "#666", fontSize: 14 };
const resetButton: React.CSSProperties = { marginTop: 16, padding: "8px 16px", background: "#f3f4f6", border: "1px solid #d1d5db", borderRadius: 4, cursor: "pointer" };
const formSection: React.CSSProperties = { marginBottom: 20 };
