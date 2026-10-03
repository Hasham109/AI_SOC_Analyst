from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.api.health import get_db
from backend.db.repository import dashboard_summary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return dashboard_summary(db)
