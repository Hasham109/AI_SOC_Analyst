from __future__ import annotations
from collections import defaultdict, deque
import threading
from threading import Lock
import time
from fastapi import Depends, FastAPI, HTTPException, Request
from backend.api.alerts import router as alerts_router
from backend.api.health import router as health_router
from backend.api.incidents import router as incidents_router
from backend.api.investigations import router as dashboard_router
from backend.config import get_settings
from backend.db.models import Base
from backend.db.session import engine
from backend.ingest import run_ingestion

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version=settings.app_version)


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


app.include_router(health_router, dependencies=[Depends(require_token)])
app.include_router(alerts_router, dependencies=[Depends(require_token)])
app.include_router(incidents_router, dependencies=[Depends(require_token)])
app.include_router(dashboard_router, dependencies=[Depends(require_token)])


@app.post("/api/ingestion/run", dependencies=[Depends(require_token)])
def ingestion_run():
    return run_ingestion()


def _background_poll_worker():
    interval = max(30, getattr(settings, "poll_interval_seconds", 60))
    time.sleep(5)  # initial delay
    while True:
        try:
            run_ingestion()
        except Exception as exc:
            print(f"[Background Ingestion Error]: {exc}")
        time.sleep(interval)


@app.on_event("startup")
def start_poller():
    t = threading.Thread(target=_background_poll_worker, daemon=True)
    t.start()


@app.get("/")
def root():
    return {"service": settings.app_name, "version": settings.app_version}

