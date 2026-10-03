from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from backend.db.models import AiAnalysis, Alert, Incident, IncidentAlert, ProcessingState


def get_state(session: Session, source_name: str) -> Optional[ProcessingState]:
    return session.scalar(select(ProcessingState).where(ProcessingState.source_name == source_name))


def set_cursor(session: Session, source_name: str, cursor_timestamp: datetime) -> None:
    state = get_state(session, source_name)
    if state is None:
        state = ProcessingState(source_name=source_name, cursor_timestamp=cursor_timestamp)
        session.add(state)
    else:
        state.cursor_timestamp = cursor_timestamp
        state.updated_at = datetime.now(timezone.utc)
    session.commit()


def list_alerts(session: Session, limit: int, offset: int, severity: Optional[str] = None) -> tuple[List[Alert], int]:
    query = select(Alert).order_by(Alert.timestamp.desc()).limit(limit).offset(offset)
    count_query = select(func.count()).select_from(Alert)
    if severity:
        query = query.where(Alert.severity == severity)
        count_query = count_query.where(Alert.severity == severity)
    return list(session.scalars(query).all()), int(session.scalar(count_query) or 0)


def get_alert(session: Session, alert_id: int) -> Optional[Alert]:
    return session.get(Alert, alert_id)


def list_incidents(session: Session, limit: int = 100) -> List[Incident]:
    return list(session.scalars(select(Incident).order_by(Incident.last_seen.desc()).limit(limit)).all())


def get_incident(session: Session, incident_id: int) -> Optional[Incident]:
    return session.scalar(
        select(Incident)
        .options(joinedload(Incident.alerts).joinedload(IncidentAlert.alert))
        .where(Incident.id == incident_id)
    )


def recent_analysis_exists(session: Session, incident_id: int, task: str) -> bool:
    return bool(session.scalar(
        select(AiAnalysis.id).where(AiAnalysis.incident_id == incident_id, AiAnalysis.task == task).limit(1)
    ))


def save_analysis(
    session: Session,
    incident_id: int,
    task: str,
    provider: str,
    model: str,
    prompt_version: str,
    result_json: str,
    status: str = "success",
) -> AiAnalysis:
    row = AiAnalysis(
        incident_id=incident_id,
        task=task,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        result_json=result_json,
        status=status,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def dashboard_summary(session: Session) -> dict:
    severity_counts = dict(session.execute(select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)).all())
    open_incidents = session.scalar(select(func.count()).select_from(Incident).where(Incident.status == "open")) or 0
    return {
        "alert_count": session.scalar(select(func.count()).select_from(Alert)) or 0,
        "open_incident_count": open_incidents,
        "severity_counts": severity_counts,
        "latest_alert_timestamp": session.scalar(select(func.max(Alert.timestamp))),
    }
