"""Supabase client wrapper. In-memory fallback when Supabase is not configured."""

from app.config import settings
from app.database import (
    reset_store, save_claim as mem_save_claim, get_claim as mem_get_claim,
    save_member as mem_save_member, get_member as mem_get_member,
)

_use_supabase = False
_supabase = None


def _init():
    global _use_supabase, _supabase
    if settings.supabase_url and settings.supabase_key:
        try:
            from supabase import create_client
            _supabase = create_client(settings.supabase_url, settings.supabase_key)
            _use_supabase = True
        except Exception:
            _use_supabase = False


def save_claim(claim_id: str, claim_data: dict):
    if _use_supabase and _supabase:
        row = {
            "id": claim_id,
            "member_id": claim_data["member_id"],
            "treatment_date": claim_data["treatment_date"],
            "claim_amount": claim_data["claim_amount"],
            "hospital_name": claim_data.get("hospital_name"),
            "is_cashless": claim_data.get("is_cashless", False),
            "status": claim_data.get("status", "PENDING"),
        }
        _supabase.table("claims").upsert(row).execute()
        if claim_data.get("decision"):
            dec = claim_data["decision"]
            _supabase.table("decisions").upsert({
                "claim_id": claim_id,
                "decision": dec["decision"],
                "approved_amount": dec["approved_amount"],
                "rejection_reasons": dec.get("rejection_reasons", []),
                "confidence_score": dec.get("confidence_score", 0),
                "notes": dec.get("notes", ""),
                "next_steps": dec.get("next_steps", ""),
            }).execute()
    mem_save_claim(claim_id, claim_data)


def get_claim(claim_id: str) -> dict | None:
    if _use_supabase and _supabase:
        try:
            rows = _supabase.table("claims").select("*").eq("id", claim_id).execute()
            if rows.data:
                row = rows.data[0]
                dec_rows = _supabase.table("decisions").select("*").eq("claim_id", claim_id).execute()
                if dec_rows.data:
                    row["decision"] = dec_rows.data[0]
                mem_save_claim(claim_id, row)
                return row
        except Exception:
            pass
    return mem_get_claim(claim_id)


def save_member(member_id: str, member_data: dict):
    if _use_supabase and _supabase:
        _supabase.table("members").upsert({
            "member_id": member_id,
            "name": member_data["name"],
            "join_date": member_data.get("join_date"),
            "status": "active",
        }).execute()
    mem_save_member(member_id, member_data)


def get_member(member_id: str) -> dict | None:
    return mem_get_member(member_id)


def reset():
    reset_store()
    _init()


_init()
