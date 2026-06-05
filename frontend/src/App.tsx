import { useState } from "react";
import { ClaimSubmission } from "./pages/ClaimSubmission";
import { ClaimDetail } from "./pages/ClaimDetail";

type View =
  | { page: "submit" }
  | { page: "detail"; claimId: string };

export default function App() {
  const [view, setView] = useState<View>({ page: "submit" });

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc" }}>
      <nav
        style={{
          background: "#1e293b",
          color: "#fff",
          padding: "12px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <strong style={{ fontSize: 16 }}>Plum OPD Claims</strong>
        <div style={{ display: "flex", gap: 12 }}>
          <button
            onClick={() => setView({ page: "submit" })}
            style={{
              background: view.page === "submit" ? "#334155" : "transparent",
              color: "#fff",
              border: "none",
              padding: "6px 12px",
              borderRadius: 4,
              cursor: "pointer",
            }}
          >
            Submit Claim
          </button>
          <input
            placeholder="Claim ID..."
            onKeyDown={(e) => {
              if (e.key === "Enter" && e.currentTarget.value) {
                setView({ page: "detail", claimId: e.currentTarget.value });
                e.currentTarget.value = "";
              }
            }}
            style={{
              padding: "4px 8px",
              borderRadius: 4,
              border: "1px solid #475569",
              background: "#1e293b",
              color: "#fff",
              fontSize: 13,
            }}
          />
        </div>
      </nav>

      <main style={{ padding: "24px 16px" }}>
        {view.page === "submit" && <ClaimSubmission />}
        {view.page === "detail" && <ClaimDetail claimId={view.claimId} />}
      </main>
    </div>
  );
}
