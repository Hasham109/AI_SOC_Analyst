from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NormalizedAlert(BaseModel):
    source_name: str
    source_alert_id: str
    timestamp: datetime
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    agent_ip: Optional[str] = None
    rule_id: Optional[str] = None
    rule_level: Optional[int] = None
    severity: str = "unknown"
    rule_description: Optional[str] = None
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_user: Optional[str] = None
    dst_user: Optional[str] = None
    groups: List[str] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    decoder: Optional[str] = None
    full_log: Optional[str] = None
    raw_json: Dict[str, Any]
    fingerprint: str


class AlertOut(NormalizedAlert):
    id: int
    created_at: datetime


class AlertListOut(BaseModel):
    items: List[AlertOut]
    limit: int
    offset: int
    total: int
