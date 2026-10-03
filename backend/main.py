from __future__ import annotations
from collections import defaultdict, deque
import contextlib
import logging
import threading
from threading import Lock
import time

from fastapi import Depends, FastAPI, HTTPException, Request

from backend.api.alerts import router as alerts_router
from backend.api.health import router as health_router
from backend.api.incidents import router as incidents_router
from backend.api.investigations import router as dashboard_router
from backend.api.system import router as system_router
from backend.config import get_settings
from backend.db.models import Base
from backend.db.session import engine
from backend.ingest import run_ingestion

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

settings = get_settings()
Base.metadata.create_all(bind=engine)


# ── Rate limiter ──────────────────────────────────────────────────────────────
class RateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.events = defaultdict(deque)
        self.lock = Lock()

    def check(self, key: str) -> bool:
        now = time.time()
        cutoff = now - 60
        with self.lock:
            q = self.events[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


rate_limiter = RateLimiter(settings.rate_limit_per_minute)


# ── Auth middleware ───────────────────────────────────────────────────────────
def require_token(request: Request) -> None:
    if request.url.path == "/health":
        return
    expected = settings.soc_api_token.get_secret_value()
    presented = request.headers.get("Authorization", "")
    if presented != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


# ── Background poller ─────────────────────────────────────────────────────────
def _background_poll_worker() -> None:
    interval = max(30, getattr(settings, "poll_interval_seconds", 120))
    log.info("Background ingestion poller started — interval=%ds", interval)
    time.sleep(5)  # brief startup delay
    cycle = 0
    while True:
        cycle += 1
        try:
            result = run_ingestion()
            log.info(
                "Poller cycle #%d — fetched=%s stored=%s simulated=%s incidents=%s cursor=%s",
                cycle,
                result.get("fetched", "?"),
                result.get("stored", "?"),
                result.get("simulated", 0),
                result.get("incident_links_created", "?"),
                (result.get("cursor") or "")[:19],
            )
        except Exception as exc:
            log.error("Poller cycle #%d ERROR: %s", cycle, exc)
        time.sleep(interval)


# ── Lifespan (replaces deprecated on_event) ───────────────────────────────────
@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    t = threading.Thread(target=_background_poll_worker, daemon=True, name="ingestion-poller")
    t.start()
    log.info("Ingestion poller thread started (daemon=True)")
    yield
    log.info("Shutdown — poller will stop with process")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.include_router(health_router, dependencies=[Depends(require_token)])
app.include_router(alerts_router, dependencies=[Depends(require_token)])
app.include_router(incidents_router, dependencies=[Depends(require_token)])
app.include_router(dashboard_router, dependencies=[Depends(require_token)])
app.include_router(system_router, dependencies=[Depends(require_token)])


@app.post("/api/ingestion/run", dependencies=[Depends(require_token)])
def ingestion_run():
    return run_ingestion()


@app.get("/")
def root():
    return {"service": settings.app_name, "version": settings.app_version}
