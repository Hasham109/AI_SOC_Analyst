import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.api.health import get_db
from backend.db.repository import get_incident, list_incidents, recent_analysis_exists, save_analysis
from backend.llm.investigation import investigate_incident
from backend.llm.manager_explanation import explain_for_manager
from backend.llm.report import write_report
from backend.llm.response import recommend_response
from backend.llm.triage import triage_alert
from backend.schemas.analysis import AnalysisRequest

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


def _evidence(incident):
    alerts = []
    for link in incident.alerts:
        a = link.alert
        alerts.append(
            {
                "id": a.id,
                "source_alert_id": a.source_alert_id,
                "timestamp": a.timestamp,
                "agent_id": a.agent_id,
                "agent_name": a.agent_name,
                "agent_ip": a.agent_ip,
                "rule_id": a.rule_id,
                "rule_level": a.rule_level,
                "severity": a.severity,
                "rule_description": a.rule_description,
                "src_ip": a.src_ip,
                "dst_ip": a.dst_ip,
                "src_user": a.src_user,
                "dst_user": a.dst_user,
            }
        )
    return {
        "incident_id": incident.id,
        "title": incident.title,
        "severity": incident.severity,
        "status": incident.status,
        "first_seen": incident.first_seen,
        "last_seen": incident.last_seen,
        "repeat_count": incident.repeat_count,
        "alerts": alerts,
    }


@router.get("")
def incidents(limit: int = Query(100, ge=1, le=200), db: Session = Depends(get_db)):
    rows = list_incidents(db, limit)
    return [
        {
            "id": i.id,
            "title": i.title,
            "severity": i.severity,
            "status": i.status,
            "first_seen": i.first_seen,
            "last_seen": i.last_seen,
            "repeat_count": i.repeat_count,
        }
        for i in rows
    ]


@router.get("/{incident_id}")
def incident_detail(incident_id: int, db: Session = Depends(get_db)):
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _evidence(incident)


@router.post("/{incident_id}/analyze")
def analyze_incident(incident_id: int, request: AnalysisRequest, db: Session = Depends(get_db)):
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    if request.task not in {"triage", "investigation", "response", "manager", "report"}:
        raise HTTPException(status_code=400, detail="Unsupported analysis task")

    if not request.force and recent_analysis_exists(db, incident_id, request.task):
        raise HTTPException(status_code=409, detail="Analysis already exists; set force=true to request another run")

    evidence = _evidence(incident)
    try:
        if request.task == "triage":
            result = triage_alert(evidence)
        elif request.task == "investigation":
            result = investigate_incident(evidence)
        elif request.task == "response":
            result = recommend_response(evidence)
        elif request.task == "manager":
            result = explain_for_manager(evidence)
        else:
            result = write_report(evidence)
    except Exception as exc:
        return {"status": "AI analysis unavailable", "error_type": exc.__class__.__name__, "detail": str(exc)}

    row = save_analysis(
        db,
        incident_id=incident_id,
        task=request.task,
        provider=result.provider,
        model=result.model,
        prompt_version=result.prompt_version,
        result_json=json.dumps(result.model_dump(), default=str),
        status="success",
    )
    return {"status": "success", "analysis_id": row.id, "result": result.model_dump()}
