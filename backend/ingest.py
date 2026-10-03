from __future__ import annotations
import logging
from datetime import datetime, timezone

from backend.config import get_settings
from backend.db.repository import get_state, set_cursor
from backend.db.session import SessionLocal
from backend.processing.correlate import add_to_or_create_incident
from backend.processing.cursor import initial_since, overlap_timestamp
from backend.processing.deduplicate import insert_alert_if_new
from backend.processing.normalize import normalize_wazuh_hit
from backend.wazuh.factory import get_wazuh_client

log = logging.getLogger(__name__)

# How many simulated alerts to inject per cycle when Wazuh is quiet
_SIM_BATCH_SIZE = 3


def run_ingestion() -> dict:
    settings = get_settings()
    client = get_wazuh_client(settings)
    db = SessionLocal()
    source = client.source_name
    run_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        state = get_state(db, source)
        if state and state.cursor_timestamp:
            since = overlap_timestamp(state.cursor_timestamp, settings.cursor_overlap_seconds)
        else:
            since = initial_since(settings.initial_sync_mode, settings.lookback_minutes)

        # ── Fetch from Wazuh ──────────────────────────────────────────────────
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

        simulated = 0
        # ── Auto-simulate when Wazuh is quiet ─────────────────────────────────
        if stored == 0 and getattr(settings, "auto_simulate_on_empty", True):
            from backend.processing.simulate import generate_simulated_alert
            log.info("[%s] Wazuh returned 0 new alerts — injecting %d simulated events", run_ts, _SIM_BATCH_SIZE)
            for _ in range(_SIM_BATCH_SIZE):
                try:
                    sim = generate_simulated_alert(source_name="simulation")
                    row, is_new = insert_alert_if_new(db, sim)
                    if is_new:
                        simulated += 1
                        add_to_or_create_incident(db, row, settings.correlation_window_minutes)
                        if newest is None or row.timestamp > newest:
                            newest = row.timestamp
                except Exception as sim_err:
                    log.warning("Simulation insert failed: %s", sim_err)

        log.info(
            "[%s] Ingestion complete — fetched=%d stored=%d dupes=%d simulated=%d incidents_linked=%d",
            run_ts, len(hits), stored, duplicates, simulated, incidents,
        )

        return {
            "status": "ok",
            "source": source,
            "run_at": run_ts,
            "fetched": len(hits),
            "stored": stored,
            "duplicates": duplicates,
            "simulated": simulated,
            "cursor": newest.isoformat() if newest else None,
            "incident_links_created": incidents,
        }
    finally:
        db.close()

