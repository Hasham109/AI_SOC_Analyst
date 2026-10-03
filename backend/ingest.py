from backend.config import get_settings
from backend.db.repository import get_state, set_cursor
from backend.db.session import SessionLocal
from backend.processing.correlate import add_to_or_create_incident
from backend.processing.cursor import initial_since, overlap_timestamp
from backend.processing.deduplicate import insert_alert_if_new
from backend.processing.normalize import normalize_wazuh_hit
from backend.wazuh.factory import get_wazuh_client


def run_ingestion() -> dict:
    settings = get_settings()
    client = get_wazuh_client(settings)
    db = SessionLocal()
    source = client.source_name
    try:
        state = get_state(db, source)
        if state and state.cursor_timestamp:
            since = overlap_timestamp(state.cursor_timestamp, settings.cursor_overlap_seconds)
        else:
            since = initial_since(settings.initial_sync_mode, settings.lookback_minutes)

        hits = client.fetch_alerts(since, settings.fetch_limit)
        stored = 0
        duplicates = 0
        newest = state.cursor_timestamp if state else None
        incidents = 0

        for hit in hits:
            normalized = normalize_wazuh_hit(source, hit)
            row, is_new = insert_alert_if_new(db, normalized)
            if is_new:
                stored += 1
                add_to_or_create_incident(db, row, settings.correlation_window_minutes)
                incidents += 1
            else:
                duplicates += 1

            if newest is None or row.timestamp > newest:
                newest = row.timestamp

        if newest is not None:
            set_cursor(db, source, newest)

        return {
            "status": "ok",
            "source": source,
            "fetched": len(hits),
            "stored": stored,
            "duplicates": duplicates,
            "cursor": newest.isoformat() if newest else None,
            "incident_links_created": incidents,
        }
    finally:
        db.close()
