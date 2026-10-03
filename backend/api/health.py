from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.wazuh.factory import get_wazuh_client
from backend.config import get_settings

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/api/source/status")
def source_status(db: Session = Depends(get_db)):
    settings = get_settings()
    client = get_wazuh_client(settings)
    return client.health_check()
