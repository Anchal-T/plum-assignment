from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from app.schemas.claim import ClaimSubmitRequest, ClaimResponse, DecisionResponse
from app.services.rule_engine import RuleEngine
from app.supabase_client import save_claim, get_claim, save_member, get_member

router = APIRouter(prefix="/claims")


@router.post("", status_code=201)
async def submit_claim(req: ClaimSubmitRequest, request: Request) -> ClaimResponse:
    engine: RuleEngine = request.app.state.engine

    claim_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    member = get_member(req.member_id)
    if not member:
        member = {"member_id": req.member_id, "name": req.member_name,
                  "join_date": None, "is_active": True}
        save_member(req.member_id, member)

    docs = [d.model_dump() for d in req.documents]
    result = engine.adjudicate(member, {
        "claim_amount": float(req.claim_amount),
        "treatment_date": str(req.treatment_date),
        "hospital_name": req.hospital_name,
        "is_cashless": req.is_cashless,
    }, docs)

    decision = DecisionResponse(
        decision=result["decision"],
        approved_amount=float(result["approved_amount"]),
        copay_amount=float(result["copay_amount"]),
        network_discount=float(result["network_discount"]),
        cashless_approved=result.get("cashless_approved", False),
        rejection_reasons=[str(r) for r in result.get("rejection_reasons", [])],
        adjudication_steps=result.get("steps", []),
        fraud_flags=result.get("fraud_flags", []),
        confidence_score=result["confidence_score"],
        notes=result.get("notes", ""),
        next_steps=result.get("next_steps", ""),
    )

    claim_data = {
        "claim_id": claim_id,
        "member_id": req.member_id,
        "member_name": req.member_name,
        "treatment_date": str(req.treatment_date),
        "claim_amount": float(req.claim_amount),
        "status": "DECIDED",
        "decision": decision.model_dump(mode="json"),
        "submitted_at": now,
    }
    save_claim(claim_id, claim_data)
    return ClaimResponse(**claim_data)


@router.get("/{claim_id}")
async def get_claim_by_id(claim_id: str) -> ClaimResponse:
    data = get_claim(claim_id)
    if not data:
        raise HTTPException(status_code=404, detail="Claim not found")
    return ClaimResponse(**data)
