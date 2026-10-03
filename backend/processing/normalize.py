from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from backend.processing.fingerprint import build_fingerprint
from backend.schemas.alert import NormalizedAlert


def _get(data: Dict[str, Any], *keys: str) -> Optional[Any]:
    for key in keys:
        value: Any = data
        ok = True
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                ok = False
                break
            value = value[part]
        if ok and value not in (None, ""):
            return value
    return None


def _to_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_wazuh_hit(source_name: str, hit: Dict[str, Any]) -> NormalizedAlert:
    source = hit.get("_source") or {}
    alert_id = str(hit.get("_id") or _get(source, "id") or "")
    timestamp = _get(source, "timestamp", "@timestamp")
    if timestamp is None:
        raise ValueError("Wazuh alert has no timestamp")

    rule_level_raw = _get(source, "rule.level")
    try:
        rule_level = int(rule_level_raw) if rule_level_raw is not None else None
    except (TypeError, ValueError):
        rule_level = None

    if rule_level is None:
        severity = "unknown"
    elif rule_level >= 12:
        severity = "critical"
    elif rule_level >= 8:
        severity = "high"
    elif rule_level >= 4:
        severity = "medium"
    else:
        severity = "low"

    groups = _get(source, "rule.groups") or []
    if isinstance(groups, str):
        groups = [groups]

    mitre_ids = _get(source, "rule.mitre.id") or []
    if isinstance(mitre_ids, str):
        mitre_ids = [mitre_ids]

    fallback = {
        "agent_id": _get(source, "agent.id"),
        "rule_id": _get(source, "rule.id"),
        "timestamp": str(timestamp),
        "event": _get(source, "event"),
        "src_ip": _get(source, "data.srcip", "data.src_ip", "srcip"),
    }
    fingerprint = build_fingerprint(source_name, alert_id, fallback)

    return NormalizedAlert(
        source_name=source_name,
        source_alert_id=alert_id or fingerprint[:16],
        timestamp=_to_datetime(timestamp),
        agent_id=_get(source, "agent.id"),
        agent_name=_get(source, "agent.name"),
        agent_ip=_get(source, "agent.ip"),
        rule_id=str(_get(source, "rule.id")) if _get(source, "rule.id") is not None else None,
        rule_level=rule_level,
        severity=severity,
        rule_description=_get(source, "rule.description"),
        src_ip=_get(source, "data.srcip", "data.src_ip", "srcip"),
        dst_ip=_get(source, "data.dstip", "data.dst_ip", "dstip"),
        src_user=_get(source, "data.srcuser", "data.src_user", "srcuser"),
        dst_user=_get(source, "data.dstuser", "data.dst_user", "dstuser"),
        groups=list(groups),
        mitre_techniques=list(mitre_ids),
        location=_get(source, "location"),
        decoder=_get(source, "decoder.name"),
        full_log=_get(source, "full_log"),
        raw_json=source,
        fingerprint=fingerprint,
    )
