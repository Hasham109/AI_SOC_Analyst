from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.models import Base
from backend.processing.deduplicate import insert_alert_if_new
from backend.schemas.alert import NormalizedAlert


def test_exact_duplicate_is_stored_once():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    alert = NormalizedAlert(
        source_name="wazuh_local",
        source_alert_id="abc",
        timestamp=datetime.now(timezone.utc),
        severity="medium",
        raw_json={"id": "abc"},
        fingerprint="a" * 64,
    )
    first, created1 = insert_alert_if_new(db, alert)
    second, created2 = insert_alert_if_new(db, alert)
    assert created1 is True
    assert created2 is False
    assert first.id == second.id
