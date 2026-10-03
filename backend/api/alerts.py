import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.api.health import get_db
from backend.db.repository import get_alert, list_alerts
from backend.schemas.alert import AlertListOut, AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _to_out(row) -> AlertOut:
    data = {
        "id": row.id,
        "source_name": row.source_name,
        "source_alert_id": row.source_alert_id,
        "timestamp": row.timestamp,
        "agent_id": row.agent_id,
        "agent_name": row.agent_name,
        "agent_ip": row.agent_ip,
        "rule_id": row.rule_id,
        "rule_level": row.rule_level,
        "severity": row.severity,
        "rule_description": row.rule_description,
        "src_ip": row.src_ip,
        "dst_ip": row.dst_ip,
        "src_user": row.src_user,
        "dst_user": row.dst_user,
        "groups": json.loads(row.groups_json or "[]"),
        "mitre_techniques": json.loads(row.mitre_techniques_json or "[]"),
        "location": row.location,
        "decoder": row.decoder,
        "full_log": row.full_log,
        "raw_json": json.loads(row.raw_json),
        "fingerprint": row.fingerprint,
        "created_at": row.created_at,
    }
    return AlertOut.model_validate(data)


@router.get("", response_model=AlertListOut)
def alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    severity: str | None = Query(None),
    db: Session = Depends(get_db),
):
    rows, total = list_alerts(db, limit, offset, severity)
    return {"items": [_to_out(row) for row in rows], "limit": limit, "offset": offset, "total": total}


@router.get("/{alert_id}", response_model=AlertOut)
def alert_detail(alert_id: int, db: Session = Depends(get_db)):
    row = get_alert(db, alert_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _to_out(row)
