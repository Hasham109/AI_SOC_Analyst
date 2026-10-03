from __future__ import annotations
from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.api.health import get_db
from backend.config import get_settings
from backend.db.models import Alert
from backend.wazuh.factory import get_wazuh_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["system"])

# In-memory cache for 30 seconds
_cache: Dict[str, Any] = {"data": None, "timestamp": 0.0}


@router.get("/connections")
def get_system_connections(
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    now_ts = time.time()
    if not refresh and _cache["data"] is not None and (now_ts - _cache["timestamp"]) < 30.0:
        return _cache["data"]

    settings = get_settings()
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Backend status
    backend_info = {
        "status": "ok",
        "version": settings.app_version,
    }

    # 2. Database status
    db_info: Dict[str, Any] = {}
    try:
        t0 = time.perf_counter()
        db.execute(text("SELECT 1"))
        alert_count = db.query(Alert).count()
        db_lat = round((time.perf_counter() - t0) * 1000, 1)
        engine_name = db.bind.dialect.name if db.bind else "sqlite"
        db_info = {
            "status": "ok",
            "engine": engine_name,
            "latency_ms": db_lat,
            "alert_count": alert_count,
        }
    except Exception as exc:
        logger.warning("Database connection check failed: %s", exc)
        db_info = {
            "status": "down",
            "engine": "unknown",
            "latency_ms": None,
            "alert_count": 0,
            "error": str(exc),
        }

    # 3. Wazuh status
    wazuh_info: Dict[str, Any] = {
        "status": "down",
        "source": settings.wazuh_source,
        "manager": {"status": "down", "version": "unknown"},
        "indexer": {"status": "red"},
        "agents": None,
    }
    try:
        w_client = get_wazuh_client(settings)
        h_check = w_client.health_check()
        w_source = h_check.get("source", settings.wazuh_source)
        wazuh_info["source"] = w_source

        # Parse Manager info
        mgr_data = h_check.get("manager", {})
        mgr_version = "unknown"
        if isinstance(mgr_data, dict):
            affected = mgr_data.get("affected_items", [])
            if affected and isinstance(affected, list) and isinstance(affected[0], dict):
                mgr_version = affected[0].get("version", "unknown")
            elif "version" in mgr_data:
                mgr_version = str(mgr_data.get("version", "unknown"))

        mgr_status = "ok" if h_check.get("status") == "ok" and mgr_version != "unknown" else "down"
        if "error" in h_check and mgr_version == "unknown":
            mgr_status = "down"

        wazuh_info["manager"] = {
            "status": mgr_status,
            "version": mgr_version,
        }

        # Parse Indexer info
        idx_data = h_check.get("indexer", [])
        idx_status = "unknown"
        if isinstance(idx_data, list) and len(idx_data) > 0 and isinstance(idx_data[0], dict):
            idx_status = idx_data[0].get("status", "unknown")
        elif isinstance(idx_data, dict):
            idx_status = idx_data.get("status", "unknown")
        wazuh_info["indexer"] = {"status": idx_status}

        # Check Agents via _manager_get("/agents/summary/status")
        try:
            raw_agents = w_client._manager_get("/agents/summary/status")
            ag_data = raw_agents.get("data", raw_agents)
            conn = ag_data.get("connection", ag_data)
            wazuh_info["agents"] = {
                "active": conn.get("active", 0),
                "disconnected": conn.get("disconnected", 0),
                "never_connected": conn.get("never_connected", 0),
                "pending": conn.get("pending", 0),
                "total": conn.get("total", 0),
            }
        except Exception as ag_exc:
            logger.warning("Wazuh agents status check failed: %s", ag_exc)
            wazuh_info["agents"] = None
            wazuh_info["agents_error"] = str(ag_exc)

        # Compute composite status
        if mgr_status == "ok" and idx_status in ("green", "yellow"):
            if idx_status == "yellow" or wazuh_info.get("agents") is None:
                wazuh_info["status"] = "degraded"
            else:
                wazuh_info["status"] = "ok"
        elif mgr_status == "ok" or idx_status in ("green", "yellow"):
            wazuh_info["status"] = "degraded"
        else:
            wazuh_info["status"] = "down"
            if "error" in h_check:
                wazuh_info["error"] = h_check["error"]
    except Exception as exc:
        logger.warning("Wazuh connection check failed: %s", exc)
        wazuh_info["status"] = "down"
        wazuh_info["error"] = str(exc)

    # 4. Groq status
    groq_info: Dict[str, Any] = {
        "status": "down",
        "models": [],
        "latency_ms": 0,
    }
    if not settings.groq_api_key or not settings.groq_api_key.get_secret_value().strip():
        groq_info["status"] = "not_configured"
    else:
        try:
            from groq import Groq

            distinct_models: List[str] = list(
                dict.fromkeys(
                    [
                        settings.llm_triage_model_id,
                        settings.llm_investigation_model_id,
                        settings.llm_response_model_id,
                        settings.llm_report_model_id,
                        settings.llm_manager_model_id,
                    ]
                )
            )

            client = Groq(
                api_key=settings.groq_api_key.get_secret_value(),
                timeout=10,
            )

            t0 = time.perf_counter()
            # Fetch model list to reliably match model IDs (avoids URL-encoding 404s on models with slashes)
            models_res = client.models.list()
            available_ids = {m.id for m in models_res.data}
            groq_lat = round((time.perf_counter() - t0) * 1000, 1)

            missing = [m for m in distinct_models if m not in available_ids]

            groq_info["latency_ms"] = groq_lat
            groq_info["models"] = distinct_models

            if missing:
                groq_info["status"] = "down"
                groq_info["error"] = f"Configured model(s) missing on Groq: {', '.join(missing)}"
                groq_info["missing_models"] = missing
            else:
                groq_info["status"] = "ok"
        except Exception as exc:
            logger.warning("Groq connection check failed: %s", exc)
            groq_info["status"] = "down"
            groq_info["error"] = str(exc)

    result = {
        "checked_at": checked_at,
        "backend": backend_info,
        "database": db_info,
        "wazuh": wazuh_info,
        "groq": groq_info,
    }

    _cache["data"] = result
    _cache["timestamp"] = now_ts
    return result
