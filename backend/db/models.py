from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from backend.schemas.alert import NormalizedAlert


class Base(DeclarativeBase):
    pass


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (UniqueConstraint("source_name", "fingerprint", name="uq_alert_source_fingerprint"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(64), index=True)
    source_alert_id: Mapped[str] = mapped_column(String(255), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    agent_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    agent_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agent_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rule_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    rule_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    severity: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    rule_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    src_ip: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    dst_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    src_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dst_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    groups_json: Mapped[str] = mapped_column(Text, default="[]")
    mitre_techniques_json: Mapped[str] = mapped_column(Text, default="[]")
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decoder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    incident_links: Mapped[List["IncidentAlert"]] = relationship(back_populates="alert")

    @staticmethod
    def from_normalized(alert: NormalizedAlert) -> "Alert":
        return Alert(
            source_name=alert.source_name,
            source_alert_id=alert.source_alert_id,
            timestamp=alert.timestamp,
            agent_id=alert.agent_id,
            agent_name=alert.agent_name,
            agent_ip=alert.agent_ip,
            rule_id=alert.rule_id,
            rule_level=alert.rule_level,
            severity=alert.severity,
            rule_description=alert.rule_description,
            src_ip=alert.src_ip,
            dst_ip=alert.dst_ip,
            src_user=alert.src_user,
            dst_user=alert.dst_user,
            groups_json=json.dumps(alert.groups),
            mitre_techniques_json=json.dumps(alert.mitre_techniques),
            location=alert.location,
            decoder=alert.decoder,
            full_log=alert.full_log,
            raw_json=json.dumps(alert.raw_json),
            fingerprint=alert.fingerprint,
        )


class AlertFingerprint(Base):
    __tablename__ = "alert_fingerprints"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(64), index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    repeat_count: Mapped[int] = mapped_column(Integer, default=1)


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(500))
    severity: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    correlation_key: Mapped[str] = mapped_column(String(500), index=True)
    repeat_count: Mapped[int] = mapped_column(Integer, default=1)
    plain_summary: Mapped[str] = mapped_column(Text, default="")
    alerts: Mapped[List["IncidentAlert"]] = relationship(back_populates="incident", cascade="all, delete-orphan")


class IncidentAlert(Base):
    __tablename__ = "incident_alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), index=True)
    incident: Mapped[Incident] = relationship(back_populates="alerts")
    alert: Mapped[Alert] = relationship(back_populates="incident_links")
    __table_args__ = (UniqueConstraint("incident_id", "alert_id", name="uq_incident_alert"),)


class AiAnalysis(Base):
    __tablename__ = "ai_analyses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int | None] = mapped_column(ForeignKey("incidents.id"), nullable=True, index=True)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id"), nullable=True, index=True)
    task: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(255))
    prompt_version: Mapped[str] = mapped_column(String(64))
    result_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="success", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ProcessingState(Base):
    __tablename__ = "processing_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    cursor_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(255), index=True)
    target: Mapped[str] = mapped_column(String(255), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    details: Mapped[str] = mapped_column(Text, default="")
