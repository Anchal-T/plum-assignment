import { use, useMemo, Suspense } from "react";
import { getClaim } from "../services/api";
import { DecisionBadge } from "../components/DecisionBadge";
import type { ClaimResponse } from "../types";

function ClaimDetailContent({ claimPromise }: { claimPromise: Promise<ClaimResponse> }) {
  const claim: ClaimResponse = use(claimPromise);
  const d = claim.decision!;

  return (
    <div style={pageWrap}>
      <h2 style={claimHeading}>Claim #{claim.claim_id.slice(0, 8)}</h2>
      <div style={decisionRow}>
        <DecisionBadge decision={d.decision} />
        <span style={mutedSmall}>Confidence: {(d.confidence_score * 100).toFixed(0)}%</span>
      </div>

      {d.approved_amount > 0 && (
        <p style={approvedAmount}>Approved: ₹{d.approved_amount.toLocaleString()}</p>
      )}
      <p style={mutedSmall}>Claim Amount: ₹{claim.claim_amount.toLocaleString()}</p>

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

      {d.notes && (
        <p style={notesBox}>{d.notes}</p>
      )}

      <p style={nextStepsText}>{d.next_steps}</p>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div style={pageWrap}>
      <div style={{ height: 24, width: 200, background: "#e5e7eb", borderRadius: 4, marginBottom: 16 }} />
      <div style={{ height: 16, width: 160, background: "#e5e7eb", borderRadius: 4, marginBottom: 8 }} />
      <div style={{ height: 16, width: 120, background: "#e5e7eb", borderRadius: 4 }} />
    </div>
  );
}

export function ClaimDetail({ claimId }: { claimId: string }) {
  // Create the promise once per claimId — never recreated on re-renders.
  const claimPromise = useMemo(() => getClaim(claimId), [claimId]);
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <ClaimDetailContent claimPromise={claimPromise} />
    </Suspense>
  );
}

// ---------------------------------------------------------------------------
// Module-level style constants
// ---------------------------------------------------------------------------

const pageWrap: React.CSSProperties = { maxWidth: 640, margin: "0 auto", padding: 24 };
const claimHeading: React.CSSProperties = { margin: "0 0 8px" };
const decisionRow: React.CSSProperties = { display: "flex", gap: 16, alignItems: "center", marginBottom: 16 };
const approvedAmount: React.CSSProperties = { fontSize: 18, fontWeight: 600, margin: "4px 0" };
const mutedSmall: React.CSSProperties = { fontSize: 14, color: "#666", margin: "4px 0" };
const mutedText: React.CSSProperties = { color: "#666" };
const sectionHeading: React.CSSProperties = { fontSize: 15, margin: "0 0 8px" };
const stepRow: React.CSSProperties = { display: "flex", gap: 8, padding: "6px 0", borderBottom: "1px solid #f0f0f0", fontSize: 14 };
const stepName: React.CSSProperties = { minWidth: 160 };
const notesBox: React.CSSProperties = { marginTop: 16, padding: 12, background: "#f0fdf4", borderRadius: 6, fontSize: 14 };
const nextStepsText: React.CSSProperties = { marginTop: 12, fontStyle: "italic", color: "#666", fontSize: 14 };
