from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.db.models import Alert
from backend.schemas.alert import NormalizedAlert


def insert_alert_if_new(session, normalized: NormalizedAlert) -> tuple[Alert, bool]:
    existing = session.scalar(
        select(Alert).where(
            Alert.source_name == normalized.source_name,
            Alert.fingerprint == normalized.fingerprint,
        )
    )
    if existing:
        return existing, False

    row = Alert.from_normalized(normalized)
    session.add(row)
    try:
        session.commit()
        session.refresh(row)
        return row, True
    except IntegrityError:
        session.rollback()
        existing = session.scalar(
            select(Alert).where(
                Alert.source_name == normalized.source_name,
                Alert.fingerprint == normalized.fingerprint,
            )
        )
        if existing is None:
            raise
        return existing, False
