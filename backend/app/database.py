"""In-memory claim store for Phase 2. Replaced by Supabase in Phase 3."""

_store: dict = {"claims": {}, "members": {}}


def reset_store():
    _store["claims"] = {}
    _store["members"] = {}


def save_claim(claim_id: str, claim_data: dict):
    _store["claims"][claim_id] = claim_data


def get_claim(claim_id: str) -> dict | None:
    return _store["claims"].get(claim_id)


def save_member(member_id: str, member_data: dict):
    _store["members"][member_id] = member_data


def get_member(member_id: str) -> dict | None:
    return _store["members"].get(member_id)


def get_all_claims() -> list[dict]:
    return list(_store["claims"].values())
