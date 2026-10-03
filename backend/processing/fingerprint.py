import hashlib
import json
from typing import Any, Dict


def build_fingerprint(source_name: str, source_alert_id: str, fallback: Dict[str, Any] | None = None) -> str:
    if source_alert_id:
        raw = f"{source_name}|{source_alert_id}"
    else:
        fallback = fallback or {}
        raw = json.dumps(fallback, sort_keys=True, separators=(",", ":"), default=str)
        raw = f"{source_name}|{raw}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
