import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def load_policy(policy_path: str = "policy_terms.json") -> dict:
    path = Path(policy_path)
    if not path.exists():
        path = Path(__file__).parent.parent.parent / "policy_terms.json"
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {policy_path}")
    with open(path) as f:
        return json.load(f)
