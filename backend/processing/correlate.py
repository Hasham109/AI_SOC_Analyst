from __future__ import annotations
from datetime import timedelta
from typing import Optional
from backend.db.models import Alert, Incident


def correlation_key(alert: Alert) -> str:
    parts = [
        alert.agent_id or "",
        alert.src_ip or "",
        alert.src_user or "",
    ]
    if not any(parts):
        parts.append(alert.rule_id or "")
    return "|".join(parts)


def add_to_or_create_incident(session, alert: Alert, window_minutes: int) -> Incident:
    window = timedelta(minutes=window_minutes)
    key = correlation_key(alert)
    candidates = (
        session.query(Incident)
        .filter(Incident.source_name == alert.source_name)
        .order_by(Incident.last_seen.desc())
        .limit(100)
        .all()
    )
    incident: Optional[Incident] = None
    for candidate in candidates:
        if candidate.correlation_key != key:
            continue
        if alert.timestamp - candidate.last_seen <= window:
            incident = candidate
            break

    if incident is None:
        incident = Incident(
            source_name=alert.source_name,
            title=alert.rule_description or "Wazuh activity",
            severity=alert.severity,
            status="open",
            first_seen=alert.timestamp,
            last_seen=alert.timestamp,
            correlation_key=key,
            repeat_count=1,
            plain_summary="",
        )
        session.add(incident)
        session.flush()
    else:
        incident.last_seen = max(incident.last_seen, alert.timestamp)
        incident.repeat_count += 1
        if _severity_rank(alert.severity) > _severity_rank(incident.severity):
            incident.severity = alert.severity
        if not incident.title and alert.rule_description:
            incident.title = alert.rule_description

    exists = any(link.alert_id == alert.id for link in incident.alerts)
    if not exists:
        from backend.db.models import IncidentAlert
        session.add(IncidentAlert(incident_id=incident.id, alert_id=alert.id))

    session.commit()
    session.refresh(incident)
    return incident


def _severity_rank(value: str) -> int:
    return {"unknown": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}.get(value, 0)
