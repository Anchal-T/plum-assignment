interface DecisionBadgeProps {
  decision: string;
}

const COLORS: Record<string, string> = {
  APPROVED: "#16a34a",
  REJECTED: "#dc2626",
  PARTIAL: "#ea580c",
  MANUAL_REVIEW: "#ca8a04",
};

export function DecisionBadge({ decision }: DecisionBadgeProps) {
  const color = COLORS[decision] || "#6b7280";
  return (
    <span
      role="status"
      aria-label={`Claim decision: ${decision}`}
      style={{
        display: "inline-block",
        padding: "4px 12px",
        borderRadius: 999,
        fontSize: 14,
        fontWeight: 600,
        color: "#fff",
        background: color,
      }}
    >
      {decision}
    </span>
  );
}
