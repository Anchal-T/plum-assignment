from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class DocumentField(BaseModel):
    doc_type: str = "unknown"
    fields: dict = {}
    confidence: float = 0.95


class ClaimSubmitRequest(BaseModel):
    member_id: str
    member_name: str
    treatment_date: date
    claim_amount: Decimal = Field(gt=0)
    hospital_name: str | None = None
    is_cashless: bool = False
    documents: list[DocumentField] = []


class DecisionResponse(BaseModel):
    decision: str
    approved_amount: float
    copay_amount: float = 0.0
    network_discount: float = 0.0
    cashless_approved: bool = False
    rejection_reasons: list[str] = []
    adjudication_steps: list[dict] = []
    fraud_flags: list[str] = []
    confidence_score: float = 0.0
    notes: str = ""
    next_steps: str = ""


class ClaimResponse(BaseModel):
    claim_id: str
    member_id: str
    member_name: str
    treatment_date: str
    claim_amount: float
    status: str = "PENDING"
    decision: DecisionResponse | None = None
    submitted_at: str = ""

