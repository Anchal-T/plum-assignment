export interface ClaimSubmitRequest {
  member_id: string;
  member_name: string;
  treatment_date: string;
  claim_amount: number;
  hospital_name?: string;
  is_cashless?: boolean;
  documents: DocumentField[];
}

export interface DocumentField {
  doc_type: string;
  fields: Record<string, unknown>;
  confidence: number;
}

export interface DecisionResponse {
  decision: "APPROVED" | "REJECTED" | "PARTIAL" | "MANUAL_REVIEW";
  approved_amount: number;
  copay_amount: number;
  network_discount: number;
  cashless_approved: boolean;
  rejection_reasons: string[];
  adjudication_steps: AdjudicationStep[];
  fraud_flags: string[];
  confidence_score: number;
  notes: string;
  next_steps: string;
}

export interface AdjudicationStep {
  step: string;
  status: "PASS" | "FAIL" | "WARN";
  detail: string;
}

export interface ClaimResponse {
  claim_id: string;
  member_id: string;
  member_name: string;
  treatment_date: string;
  claim_amount: number;
  status: string;
  decision: DecisionResponse | null;
  submitted_at: string;
}
