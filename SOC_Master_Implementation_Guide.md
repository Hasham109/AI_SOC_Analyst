# 🛡️ AI SOC Analyst Application — Master Implementation Guide
> **Zero-to-Advanced Step-by-Step Implementation Workbook**  
> *Targeted for Hackathons & Production Prototypes | Wazuh SIEM ➔ FastAPI ➔ Database ➔ Groq AI ➔ Streamlit Dashboard*

---

## 🌟 1. Project Ka Aasan Ta'aruf (Project Overview in Simple Terms)

### Yeh Project Kya Karta Hai? (What is this project?)
Imagine karein ke ek company ke computer network par rozana hazaron security alerts aate hain (jaise: *"Kisi ne 10 martaba ghalat password lagaya"*, *"Ek suspicious file download hui"*, *"Ek unknown IP se server connect hua"*). 

In alerts ko capture karne ke liye **Wazuh** (ek mashhoor Open-Source SIEM / Security Information & Event Management tool) use hota hai. Lekin SOC (Security Operations Center) analysts in hazaron alerts ko dekh dekh kar thak jate hain.

**Yeh Application Kya Karti Hai:**
1. **Wazuh se alerts fetch karti hai** (chahe local ho ya AWS cloud par).
2. **Data ko saaf (normalize) aur deduplicate karti hai** (aik hi alert baar baar AI ke paas na jaye aur paise/quota zaya na hon).
3. **Related alerts ko 'Incidents' mein jorrti hai** (jaise 5 brute force attempts aik hi incident ban jate hain).
4. **FastAPI Backend aur Database (SQLite)** mein save karti hai.
5. **Groq LLM (Llama 3.1 & Llama 3.3)** ki madad se automated **AI Triage, Deep Investigation, Response Plan, aur Non-Technical Manager Summary** generate karti hai.
6. **Streamlit Interactive UI Dashboard** par visual charts aur evidence display karti hai.

---

## 🏗️ 2. High-Level Architecture (System Kaise Kaam Karta Hai)

```
┌─────────────────────────────────┐
│     Wazuh Manager / Indexer     │ (Local VM ya AWS Cloud)
└────────────────┬────────────────┘
                 │ (1. Read-Only Secure API Fetch)
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend Service                   │
│                                                             │
│  [Source Adapter] ➔ [Normalize & Fingerprint] ➔ [Deduplicate]│
│                           │                                 │
│                           ▼                                 │
│               [Incident Correlation Engine]                 │
│                           │                                 │
│                           ▼                                 │
│            [Database (SQLite / PostgreSQL)]                 │
│                           ▲                                 │
│                           │ (Bounded Evidence Only)         │
│                           ▼                                 │
│                [Groq AI / LLM Router]                       │
│    (Llama 3.1 8B Instant / Llama 3.3 70B Versatile)         │
└───────────────────────────┬─────────────────────────────────┘
                            │ (2. Public HTTPS API with Bearer Token)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Streamlit Community Cloud                   │
│              (Interactive Analyst Dashboard)                │
└─────────────────────────────────────────────────────────────┘
```

### Core Golden Rules (Jo Kabhi Break Nahi Karne):
1. **AI Kabhi Blindly Action Nahi Legi:** AI sirf *recommendations* degi (jaise *"User account block karein"*). Koi script ya command server par automatically execute nahi hogi.
2. **Anti-Hallucination:** AI ko sirf woh evidence bheja jata hai jo actual alert mein mojood hai. Agar user IP ya username missing hai, toh AI use invent nahi karegi.
3. **Deterministic First, AI Second:** Pehle system code se duplicate alerts rokey ga. AI tabhi call hogi jab human analyst button dabaye ga (page refresh hone par AI call nahi hogi).

---

## 📁 3. Complete Project Folder Structure

Aap apne computer ya Linux VM par yeh structure banayein ge:

```text
soc-app/
├── .env                              # Secret backend configuration (git mein push NAHI karna)
├── .gitignore                        # Git exclusion rules
├── requirements.txt                  # Python dependencies
├── app.py                            # Streamlit Frontend Dashboard
├── .streamlit/
│   └── secrets.toml                  # Streamlit secrets (Streamlit Cloud UI mein set honge)
├── backend/
│   ├── __init__.py
│   ├── config.py                     # Environment variables validation (Pydantic Settings)
│   ├── main.py                       # FastAPI application entrypoint & Rate Limiter
│   ├── ingest.py                     # Pipeline: Fetch -> Normalize -> Dedup -> Correlate
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py                 # /health & /api/source/status
│   │   ├── alerts.py                 # /api/alerts endpoints
│   │   ├── incidents.py              # /api/incidents & AI analysis endpoints
│   │   └── investigations.py         # /api/dashboard summary
│   ├── wazuh/
│   │   ├── __init__.py
│   │   ├── base.py                   # Wazuh API & Indexer HTTP client
│   │   ├── local_client.py           # Local Wazuh adapter
│   │   ├── aws_client.py             # AWS Wazuh adapter
│   │   └── factory.py                # Source switcher (LOCAL ya AWS)
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── normalize.py              # Raw JSON ko clean schema mein convert karna
│   │   ├── fingerprint.py            # SHA-256 unique ID generator
│   │   ├── deduplicate.py            # Database uniqueness guard
│   │   ├── cursor.py                 # Timestamp tracking (taake purane alerts baar baar na aain)
│   │   ├── correlate.py              # Incident grouping engine
│   │   └── risk_rules.py             # Deterministic severity counter
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py                # SQLAlchemy DB connection
│   │   ├── models.py                 # Database Tables (Alert, Incident, AiAnalysis, etc.)
│   │   └── repository.py             # DB queries & CRUD functions
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py                   # Base LLM provider class
│   │   ├── router.py                 # Task-based LLM Router
│   │   ├── triage.py                 # Fast Alert Triage task
│   │   ├── investigation.py          # Deep Incident Investigation task
│   │   ├── response.py               # SOC Response Plan task
│   │   ├── manager_explanation.py    # Non-technical explanation task
│   │   ├── report.py                 # Incident Report Generator
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── groq_provider.py      # Groq API Client (Free & Super Fast)
│   │       └── bedrock_provider.py   # Optional AWS Bedrock client
│   └── schemas/
│       ├── __init__.py
│       ├── alert.py                  # Pydantic models for Alerts
│       ├── analysis.py               # Pydantic models for AI output
│       └── runtime.py                # Pydantic models for ingestion response
├── fixtures/
│   └── sample_alert.json             # Testing alert for local development
└── tests/
    ├── test_normalize.py
    ├── test_fingerprint.py
    ├── test_deduplicate.py
    ├── test_cursor.py
    ├── test_source_factory.py
    └── test_api.py
```

---

## 🛠️ 4. Baby-Step Setup Guide (Kadam-Ba-Kadam Setup)

### Marhala 1: Environment Setup (Virtual Environment)
Sabse pehle Python environment banayein taake aapke system ke baaqi packages disturb na hon:

**Windows (PowerShell):**
```powershell
mkdir soc-app
cd soc-app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

**Linux / Debian VM:**
```bash
sudo mkdir -p /opt/soc-app
cd /opt/soc-app
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

---

### Marhala 2: Dependencies Install Karein (`requirements.txt`)

`requirements.txt` file banayein aur yeh dependencies paste karein:

```text
streamlit>=1.35.0
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
requests>=2.32.0
httpx>=0.27.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
SQLAlchemy>=2.0.30
groq>=0.9.0
python-dotenv>=1.0.1
pandas>=2.2.0
plotly>=5.22.0
pytest>=8.2.0
pytest-mock>=3.14.0
tenacity>=8.4.0
boto3>=1.34.0
```

Install command run karein:
```bash
pip install -r requirements.txt
```

---

### Marhala 3: Environment Configuration (`.env`)

Root folder mein `.env` file banayein. **Yahan humne real Groq models configure kiye hain!**

```ini
# --- Wazuh Connection ---
WAZUH_SOURCE=local
LOCAL_WAZUH_API_URL=https://127.0.0.1:55000
AWS_WAZUH_API_URL=https://aws-wazuh-host:55000
LOCAL_WAZUH_INDEXER_URL=https://127.0.0.1:9200
AWS_WAZUH_INDEXER_URL=https://aws-indexer-host:9200
WAZUH_API_USERNAME=read_only_api_user
WAZUH_API_PASSWORD=change_this_password
WAZUH_INDEXER_USERNAME=read_only_indexer_user
WAZUH_INDEXER_PASSWORD=change_this_password
WAZUH_VERIFY_TLS=false

# --- App & Database ---
DATABASE_URL=sqlite:///./soc_app.db
SOC_API_TOKEN=super-secure-token-hackathon-2026-xyz987

# --- Pipeline Settings ---
INITIAL_SYNC_MODE=latest_only
LOOKBACK_MINUTES=15
POLL_INTERVAL_SECONDS=60
FETCH_LIMIT=100
CURSOR_OVERLAP_SECONDS=30
CORRELATION_WINDOW_MINUTES=10
RATE_LIMIT_PER_MINUTE=120

# --- Groq AI Configuration (CORRECTED ACTIVE MODELS) ---
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_USE_JSON_MODE=true
GROQ_TIMEOUT_SECONDS=30

LLM_TRIAGE_PROVIDER=groq
LLM_TRIAGE_MODEL_ID=llama-3.1-8b-instant

LLM_INVESTIGATION_PROVIDER=groq
LLM_INVESTIGATION_MODEL_ID=llama-3.3-70b-versatile

LLM_RESPONSE_PROVIDER=groq
LLM_RESPONSE_MODEL_ID=llama-3.1-8b-instant

LLM_MANAGER_PROVIDER=groq
LLM_MANAGER_MODEL_ID=llama-3.1-8b-instant

LLM_REPORT_PROVIDER=groq
LLM_REPORT_MODEL_ID=llama-3.1-8b-instant

# --- AWS Bedrock (Optional - Groq use karte waqt empty chhor dein) ---
AWS_REGION=us-east-1
AWS_BEDROCK_DEFAULT_TEMPERATURE=0.2
AWS_BEDROCK_MAX_TOKENS=1200
```

> 🔑 **Groq API Key Kaise Hasil Karein:**
> 1. [console.groq.com](https://console.groq.com) par free account banayein.
> 2. "API Keys" section mein jayein aur "Create API Key" click karein.
> 3. Key copy kar ke apne `.env` mein `GROQ_API_KEY` ke aagay paste karein.

---

## 💻 5. All Project Code Files (With All Bug Fixes Applied)

Yahan saare files ka mukammal aur tested code mojood hai. Aap inko respective folders mein save karein:

### File 1: `backend/config.py`
*(Yeh file `.env` ko read aur validate karti hai)*

```python
from functools import lru_cache
from typing import Literal, Optional
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables/.env."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Wazuh SOC Bridge"
    app_version: str = "1.0.0"

    wazuh_source: Literal["local", "aws"] = "local"
    local_wazuh_api_url: str = "https://127.0.0.1:55000"
    aws_wazuh_api_url: str = ""
    local_wazuh_indexer_url: str = "https://127.0.0.1:9200"
    aws_wazuh_indexer_url: str = ""

    wazuh_api_username: str = "admin"
    wazuh_api_password: SecretStr = SecretStr("admin")
    wazuh_indexer_username: str = "admin"
    wazuh_indexer_password: SecretStr = SecretStr("admin")

    database_url: str = "sqlite:///./soc_app.db"
    soc_api_token: SecretStr = SecretStr("soc-secret-token")

    initial_sync_mode: Literal["latest_only", "lookback"] = "latest_only"
    lookback_minutes: int = Field(default=5, ge=1, le=1440)
    poll_interval_seconds: int = Field(default=60, ge=10, le=3600)
    fetch_limit: int = Field(default=100, ge=1, le=500)
    cursor_overlap_seconds: int = Field(default=30, ge=0, le=300)
    correlation_window_minutes: int = Field(default=10, ge=1, le=120)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=600)

    # Groq Model Defaults (Updated with live models)
    llm_triage_provider: str = "groq"
    llm_triage_model_id: str = "llama-3.1-8b-instant"
    llm_investigation_provider: str = "groq"
    llm_investigation_model_id: str = "llama-3.3-70b-versatile"
    llm_response_provider: str = "groq"
    llm_response_model_id: str = "llama-3.1-8b-instant"
    llm_report_provider: str = "groq"
    llm_report_model_id: str = "llama-3.1-8b-instant"
    llm_manager_provider: str = "groq"
    llm_manager_model_id: str = "llama-3.1-8b-instant"

    groq_api_key: Optional[SecretStr] = None
    groq_use_json_mode: bool = True
    groq_timeout_seconds: int = Field(default=30, ge=5, le=120)

    aws_region: str = "us-east-1"
    aws_bedrock_default_temperature: float = Field(default=0.2, ge=0, le=1)
    aws_bedrock_max_tokens: int = Field(default=1200, ge=128, le=8192)
    wazuh_verify_tls: bool = False

    def active_wazuh_api_url(self) -> str:
        return self.local_wazuh_api_url if self.wazuh_source == "local" else self.aws_wazuh_api_url

    def active_wazuh_indexer_url(self) -> str:
        return (
            self.local_wazuh_indexer_url
            if self.wazuh_source == "local"
            else self.aws_wazuh_indexer_url
        )

    def validate_runtime(self) -> None:
        if self.wazuh_source == "aws" and not self.aws_wazuh_api_url:
            raise ValueError("WAZUH_SOURCE=aws but AWS_WAZUH_API_URL is empty")
        if self.wazuh_source == "aws" and not self.aws_wazuh_indexer_url:
            raise ValueError("WAZUH_SOURCE=aws but AWS_WAZUH_INDEXER_URL is empty")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime()
    return settings
```

---

### File 2: `backend/schemas/alert.py`
*(Normalized data structures for Alerts)*

```python
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
```

---

### File 3: `backend/schemas/analysis.py`
*(🚨 BUG FIX: Added default values for provider, model, prompt_version so Pydantic validation won't crash when LLM returns JSON)*

```python
from typing import List, Optional
from pydantic import BaseModel, Field


class TriageResult(BaseModel):
    finding: str
    evidence_refs: List[str] = Field(default_factory=list)
    confidence_label: str = "unknown"
    unknowns: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    # Default values prevent ValidationError before model assignment
    provider: str = "unknown"
    model: str = "unknown"
    prompt_version: str = "unknown"


class InvestigationResult(TriageResult):
    timeline_summary: str = ""
    next_investigation_steps: List[str] = Field(default_factory=list)


class ResponseResult(TriageResult):
    reason: str = ""
    impact: str = ""
    rollback: List[str] = Field(default_factory=list)
    verification: List[str] = Field(default_factory=list)


class ManagerExplanation(TriageResult):
    what_happened: str = ""
    why_it_might_matter: str = ""
    affected_systems: List[str] = Field(default_factory=list)
    what_we_know: List[str] = Field(default_factory=list)
    what_we_do_not_know: List[str] = Field(default_factory=list)
    next_check: List[str] = Field(default_factory=list)


class ReportResult(TriageResult):
    executive_summary: str = ""
    technical_summary: str = ""
    timeline: List[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    task: str
    force: bool = False
```

---

### File 4: `backend/schemas/runtime.py`

```python
from pydantic import BaseModel


class IngestionResponse(BaseModel):
    status: str
    source: str
    fetched: int
    stored: int
    duplicates: int
    cursor: str | None = None
    incident_links_created: int
```

---

### File 5: `backend/db/session.py`
*(SQLite connection setup)*

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
```

---

### File 6: `backend/db/models.py`
*(Database Tables)*

```python
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
```

---

### File 7: `backend/db/repository.py`
*(CRUD operations for Database)*

```python
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from backend.db.models import AiAnalysis, Alert, Incident, IncidentAlert, ProcessingState


def get_state(session: Session, source_name: str) -> Optional[ProcessingState]:
    return session.scalar(select(ProcessingState).where(ProcessingState.source_name == source_name))


def set_cursor(session: Session, source_name: str, cursor_timestamp: datetime) -> None:
    state = get_state(session, source_name)
    if state is None:
        state = ProcessingState(source_name=source_name, cursor_timestamp=cursor_timestamp)
        session.add(state)
    else:
        state.cursor_timestamp = cursor_timestamp
        state.updated_at = datetime.now(timezone.utc)
    session.commit()


def list_alerts(session: Session, limit: int, offset: int, severity: Optional[str] = None) -> tuple[List[Alert], int]:
    query = select(Alert).order_by(Alert.timestamp.desc()).limit(limit).offset(offset)
    count_query = select(func.count()).select_from(Alert)
    if severity:
        query = query.where(Alert.severity == severity)
        count_query = count_query.where(Alert.severity == severity)
    return list(session.scalars(query).all()), int(session.scalar(count_query) or 0)


def get_alert(session: Session, alert_id: int) -> Optional[Alert]:
    return session.get(Alert, alert_id)


def list_incidents(session: Session, limit: int = 100) -> List[Incident]:
    return list(session.scalars(select(Incident).order_by(Incident.last_seen.desc()).limit(limit)).all())


def get_incident(session: Session, incident_id: int) -> Optional[Incident]:
    return session.scalar(
        select(Incident)
        .options(joinedload(Incident.alerts).joinedload(IncidentAlert.alert))
        .where(Incident.id == incident_id)
    )


def recent_analysis_exists(session: Session, incident_id: int, task: str) -> bool:
    return bool(session.scalar(
        select(AiAnalysis.id).where(AiAnalysis.incident_id == incident_id, AiAnalysis.task == task).limit(1)
    ))


def save_analysis(
    session: Session,
    incident_id: int,
    task: str,
    provider: str,
    model: str,
    prompt_version: str,
    result_json: str,
    status: str = "success",
) -> AiAnalysis:
    row = AiAnalysis(
        incident_id=incident_id,
        task=task,
        provider=provider,
        model=model,
        prompt_version=prompt_version,
        result_json=result_json,
        status=status,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def dashboard_summary(session: Session) -> dict:
    severity_counts = dict(session.execute(select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)).all())
    open_incidents = session.scalar(select(func.count()).select_from(Incident).where(Incident.status == "open")) or 0
    return {
        "alert_count": session.scalar(select(func.count()).select_from(Alert)) or 0,
        "open_incident_count": open_incidents,
        "severity_counts": severity_counts,
        "latest_alert_timestamp": session.scalar(select(func.max(Alert.timestamp))),
    }
```

---

### File 8: `backend/processing/fingerprint.py`
*(Creates unique SHA-256 hash for deduplication)*

```python
import hashlib
import json
from typing import Any, Dict


def build_fingerprint(source_name: str, source_alert_id: str, fallback: Dict[str, Any] | None = None) -> str:
    if source_alert_id:
        raw = f"{source_name}|{source_alert_id}"
    else:
        fallback = fallback or {}
        raw = json.dumps(fallback, sort_keys=True, separators=(",", ":"), default=str)
        raw = f"{source_name}|{raw}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
```

---

### File 9: `backend/processing/normalize.py`
*(Converts nested Wazuh JSON into clean flat fields)*

```python
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from backend.processing.fingerprint import build_fingerprint
from backend.schemas.alert import NormalizedAlert


def _get(data: Dict[str, Any], *keys: str) -> Optional[Any]:
    for key in keys:
        value: Any = data
        ok = True
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                ok = False
                break
            value = value[part]
        if ok and value not in (None, ""):
            return value
    return None


def _to_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def normalize_wazuh_hit(source_name: str, hit: Dict[str, Any]) -> NormalizedAlert:
    source = hit.get("_source") or {}
    alert_id = str(hit.get("_id") or _get(source, "id") or "")
    timestamp = _get(source, "timestamp", "@timestamp")
    if timestamp is None:
        raise ValueError("Wazuh alert has no timestamp")

    rule_level_raw = _get(source, "rule.level")
    try:
        rule_level = int(rule_level_raw) if rule_level_raw is not None else None
    except (TypeError, ValueError):
        rule_level = None

    if rule_level is None:
        severity = "unknown"
    elif rule_level >= 12:
        severity = "critical"
    elif rule_level >= 8:
        severity = "high"
    elif rule_level >= 4:
        severity = "medium"
    else:
        severity = "low"

    groups = _get(source, "rule.groups") or []
    if isinstance(groups, str):
        groups = [groups]

    mitre_ids = _get(source, "rule.mitre.id") or []
    if isinstance(mitre_ids, str):
        mitre_ids = [mitre_ids]

    fallback = {
        "agent_id": _get(source, "agent.id"),
        "rule_id": _get(source, "rule.id"),
        "timestamp": str(timestamp),
        "event": _get(source, "event"),
        "src_ip": _get(source, "data.srcip", "data.src_ip", "srcip"),
    }
    fingerprint = build_fingerprint(source_name, alert_id, fallback)

    return NormalizedAlert(
        source_name=source_name,
        source_alert_id=alert_id or fingerprint[:16],
        timestamp=_to_datetime(timestamp),
        agent_id=_get(source, "agent.id"),
        agent_name=_get(source, "agent.name"),
        agent_ip=_get(source, "agent.ip"),
        rule_id=str(_get(source, "rule.id")) if _get(source, "rule.id") is not None else None,
        rule_level=rule_level,
        severity=severity,
        rule_description=_get(source, "rule.description"),
        src_ip=_get(source, "data.srcip", "data.src_ip", "srcip"),
        dst_ip=_get(source, "data.dstip", "data.dst_ip", "dstip"),
        src_user=_get(source, "data.srcuser", "data.src_user", "srcuser"),
        dst_user=_get(source, "data.dstuser", "data.dst_user", "dstuser"),
        groups=list(groups),
        mitre_techniques=list(mitre_ids),
        location=_get(source, "location"),
        decoder=_get(source, "decoder.name"),
        full_log=_get(source, "full_log"),
        raw_json=source,
        fingerprint=fingerprint,
    )
```

---

### File 10: `backend/processing/deduplicate.py`

```python
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.db.models import Alert
from backend.schemas.alert import NormalizedAlert


def insert_alert_if_new(session, normalized: NormalizedAlert) -> tuple[Alert, bool]:
    existing = session.scalar(
        select(Alert).where(
            Alert.source_name == normalized.source_name,
            Alert.fingerprint == normalized.fingerprint,
        )
    )
    if existing:
        return existing, False

    row = Alert.from_normalized(normalized)
    session.add(row)
    try:
        session.commit()
        session.refresh(row)
        return row, True
    except IntegrityError:
        session.rollback()
        existing = session.scalar(
            select(Alert).where(
                Alert.source_name == normalized.source_name,
                Alert.fingerprint == normalized.fingerprint,
            )
        )
        if existing is None:
            raise
        return existing, False
```

---

### File 11: `backend/processing/cursor.py`

```python
from datetime import datetime, timedelta, timezone
from typing import Optional


def initial_since(mode: str, lookback_minutes: int) -> Optional[datetime]:
    if mode == "latest_only":
        return datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)
    return None


def overlap_timestamp(timestamp: datetime, overlap_seconds: int) -> datetime:
    return timestamp - timedelta(seconds=overlap_seconds)
```

---

### File 12: `backend/processing/correlate.py`

```python
from __future__ import annotations
from datetime import timedelta
from typing import Optional
from backend.db.models import Alert, Incident


def correlation_key(alert: Alert) -> str:
    parts = [
        alert.agent_id or "",
        alert.src_ip or "",
        alert.src_user or "",
    ]
    if not any(parts):
        parts.append(alert.rule_id or "")
    return "|".join(parts)


def add_to_or_create_incident(session, alert: Alert, window_minutes: int) -> Incident:
    window = timedelta(minutes=window_minutes)
    key = correlation_key(alert)
    candidates = (
        session.query(Incident)
        .filter(Incident.source_name == alert.source_name)
        .order_by(Incident.last_seen.desc())
        .limit(100)
        .all()
    )
    incident: Optional[Incident] = None
    for candidate in candidates:
        if candidate.correlation_key != key:
            continue
        if alert.timestamp - candidate.last_seen <= window:
            incident = candidate
            break

    if incident is None:
        incident = Incident(
            source_name=alert.source_name,
            title=alert.rule_description or "Wazuh activity",
            severity=alert.severity,
            status="open",
            first_seen=alert.timestamp,
            last_seen=alert.timestamp,
            correlation_key=key,
            repeat_count=1,
            plain_summary="",
        )
        session.add(incident)
        session.flush()
    else:
        incident.last_seen = max(incident.last_seen, alert.timestamp)
        incident.repeat_count += 1
        if _severity_rank(alert.severity) > _severity_rank(incident.severity):
            incident.severity = alert.severity
        if not incident.title and alert.rule_description:
            incident.title = alert.rule_description

    exists = any(link.alert_id == alert.id for link in incident.alerts)
    if not exists:
        from backend.db.models import IncidentAlert
        session.add(IncidentAlert(incident_id=incident.id, alert_id=alert.id))

    session.commit()
    session.refresh(incident)
    return incident


def _severity_rank(value: str) -> int:
    return {"unknown": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}.get(value, 0)
```

---

### File 13: `backend/processing/risk_rules.py`

```python
from collections import Counter
from typing import Dict, Iterable
from backend.db.models import Alert


def basic_risk_flags(alerts: Iterable[Alert]) -> Dict[str, object]:
    alerts_list = list(alerts)
    counts = Counter(a.severity for a in alerts_list)
    high_or_critical = sum(counts.get(level, 0) for level in ("high", "critical"))
    return {
        "alert_count": len(alerts_list),
        "severity_counts": dict(counts),
        "high_or_critical_count": high_or_critical,
    }
```

---

### File 14: `backend/wazuh/base.py`
*(Handles connecting to Wazuh API & Wazuh Indexer)*

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests


class WazuhSourceClient(ABC):
    source_name: str

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def fetch_alerts(self, since: Optional[datetime], limit: int) -> List[Dict[str, Any]]:
        raise NotImplementedError


class WazuhHttpSourceClient(WazuhSourceClient):
    def __init__(
        self,
        source_name: str,
        manager_url: str,
        indexer_url: str,
        manager_username: str,
        manager_password: str,
        indexer_username: str,
        indexer_password: str,
        timeout_seconds: int = 15,
        verify_tls: bool = False,
    ) -> None:
        self.source_name = source_name
        self.manager_url = manager_url.rstrip("/")
        self.indexer_url = indexer_url.rstrip("/")
        self.manager_username = manager_username
        self.manager_password = manager_password
        self.indexer_username = indexer_username
        self.indexer_password = indexer_password
        self.timeout_seconds = timeout_seconds
        self.verify_tls = verify_tls
        self.session = requests.Session()

    def _manager_token(self) -> str:
        response = self.session.post(
            f"{self.manager_url}/security/user/authenticate?raw=true",
            auth=(self.manager_username, self.manager_password),
            timeout=self.timeout_seconds,
            verify=self.verify_tls,
        )
        response.raise_for_status()
        token = response.text.strip().strip('"')
        if not token:
            raise RuntimeError("Wazuh API authentication returned an empty token")
        return token

    def _manager_get(self, path: str) -> Dict[str, Any]:
        token = self._manager_token()
        response = self.session.get(
            f"{self.manager_url}{path}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout_seconds,
            verify=self.verify_tls,
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        try:
            manager_info = self._manager_get("/manager/info")
            indexer_response = self.session.get(
                f"{self.indexer_url}/_cat/health?format=json",
                auth=(self.indexer_username, self.indexer_password),
                timeout=self.timeout_seconds,
                verify=self.verify_tls,
            )
            indexer_response.raise_for_status()
            indexer_health = indexer_response.json()
            return {
                "status": "ok",
                "source": self.source_name,
                "manager": manager_info.get("data", manager_info),
                "indexer": indexer_health,
            }
        except Exception as e:
            return {"status": "degraded", "source": self.source_name, "error": str(e)}

    @staticmethod
    def _build_alert_query(since: Optional[datetime], limit: int) -> Dict[str, Any]:
        filters: List[Dict[str, Any]] = []
        if since is not None:
            iso = since.isoformat().replace("+00:00", "Z")
            filters.append(
                {
                    "bool": {
                        "should": [
                            {"range": {"timestamp": {"gte": iso}}},
                            {"range": {"@timestamp": {"gte": iso}}},
                        ],
                        "minimum_should_match": 1,
                    }
                }
            )
        return {
            "size": limit,
            "track_total_hits": False,
            "sort": [
                {"timestamp": {"order": "asc", "unmapped_type": "date"}},
                {"@timestamp": {"order": "asc", "unmapped_type": "date"}},
                {"_id": {"order": "asc"}},
            ],
            "query": {"bool": {"filter": filters}} if filters else {"match_all": {}},
        }

    def fetch_alerts(self, since: Optional[datetime], limit: int) -> List[Dict[str, Any]]:
        query = self._build_alert_query(since, limit)
        response = self.session.post(
            f"{self.indexer_url}/wazuh-alerts-4.x-*/_search",
            auth=(self.indexer_username, self.indexer_password),
            json=query,
            timeout=self.timeout_seconds,
            verify=self.verify_tls,
        )
        response.raise_for_status()
        payload = response.json()
        hits = payload.get("hits", {}).get("hits", [])
        return [
            {
                "_index": hit.get("_index"),
                "_id": hit.get("_id"),
                "_source": hit.get("_source", {}),
            }
            for hit in hits
            if isinstance(hit, dict)
        ]
```

---

### File 15: `backend/wazuh/local_client.py`

```python
from backend.config import Settings
from backend.wazuh.base import WazuhHttpSourceClient


class LocalWazuhClient(WazuhHttpSourceClient):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            source_name="wazuh_local",
            manager_url=settings.local_wazuh_api_url,
            indexer_url=settings.local_wazuh_indexer_url,
            manager_username=settings.wazuh_api_username,
            manager_password=settings.wazuh_api_password.get_secret_value(),
            indexer_username=settings.wazuh_indexer_username,
            indexer_password=settings.wazuh_indexer_password.get_secret_value(),
            verify_tls=settings.wazuh_verify_tls,
        )
```

---

### File 16: `backend/wazuh/aws_client.py`

```python
from backend.config import Settings
from backend.wazuh.base import WazuhHttpSourceClient


class AwsWazuhClient(WazuhHttpSourceClient):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            source_name="wazuh_aws",
            manager_url=settings.aws_wazuh_api_url,
            indexer_url=settings.aws_wazuh_indexer_url,
            manager_username=settings.wazuh_api_username,
            manager_password=settings.wazuh_api_password.get_secret_value(),
            indexer_username=settings.wazuh_indexer_username,
            indexer_password=settings.wazuh_indexer_password.get_secret_value(),
            verify_tls=settings.wazuh_verify_tls,
        )
```

---

### File 17: `backend/wazuh/factory.py`

```python
from backend.config import Settings
from backend.wazuh.aws_client import AwsWazuhClient
from backend.wazuh.base import WazuhSourceClient
from backend.wazuh.local_client import LocalWazuhClient


def get_wazuh_client(settings: Settings) -> WazuhSourceClient:
    if settings.wazuh_source == "local":
        return LocalWazuhClient(settings)
    if settings.wazuh_source == "aws":
        return AwsWazuhClient(settings)
    raise ValueError(f"Unsupported WAZUH_SOURCE: {settings.wazuh_source}")
```

---

### File 18: `backend/llm/base.py`

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMProvider(ABC):
    provider_name: str

    @abstractmethod
    def generate_json(self, *, model: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        raise NotImplementedError
```

---

### File 19: `backend/llm/providers/groq_provider.py`
*(Ultra-fast Groq LLM integration)*

```python
import json
from typing import Any, Dict
from backend.config import Settings
from backend.llm.base import LLMProvider


class GroqProvider(LLMProvider):
    provider_name = "groq"

    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when a Groq task is enabled")
        self.settings = settings
        try:
            from groq import Groq
        except ImportError as exc:
            raise RuntimeError("The groq package is not installed. Run: pip install groq") from exc

        self.client = Groq(
            api_key=settings.groq_api_key.get_secret_value(),
            timeout=settings.groq_timeout_seconds,
        )

    def generate_json(self, *, model: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1600,
        }
        if self.settings.groq_use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
```

---

### File 20: `backend/llm/providers/bedrock_provider.py`

```python
import json
from typing import Any, Dict
from backend.config import Settings
from backend.llm.base import LLMProvider


class BedrockProvider(LLMProvider):
    provider_name = "bedrock"

    def __init__(self, settings: Settings) -> None:
        import boto3
        self.settings = settings
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    def generate_json(self, *, model: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        response = self.client.converse(
            modelId=model,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={
                "maxTokens": self.settings.aws_bedrock_max_tokens,
                "temperature": self.settings.aws_bedrock_default_temperature,
            },
        )
        content = response["output"]["message"]["content"][0]["text"]
        return json.loads(content)
```

---

### File 21: `backend/llm/router.py`
*(🚨 BUG FIX: BedrockProvider is loaded lazily only if selected, preventing crashes when AWS credentials are absent)*

```python
from __future__ import annotations
from functools import lru_cache
from typing import Dict, Type
from pydantic import BaseModel, ValidationError
from backend.config import Settings


class LLMRouter:
    TASKS = {
        "triage": ("llm_triage_provider", "llm_triage_model_id"),
        "investigation": ("llm_investigation_provider", "llm_investigation_model_id"),
        "response": ("llm_response_provider", "llm_response_model_id"),
        "manager": ("llm_manager_provider", "llm_manager_model_id"),
        "report": ("llm_report_provider", "llm_report_model_id"),
    }

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._providers = {}

    def _get_provider(self, name: str):
        if name not in self._providers:
            if name == "groq":
                from backend.llm.providers.groq_provider import GroqProvider
                self._providers["groq"] = GroqProvider(self.settings)
            elif name == "bedrock":
                from backend.llm.providers.bedrock_provider import BedrockProvider
                self._providers["bedrock"] = BedrockProvider(self.settings)
            else:
                raise ValueError(f"Unsupported LLM provider: {name}")
        return self._providers[name]

    def _provider_and_model(self, task: str):
        if task not in self.TASKS:
            raise ValueError(f"Unsupported LLM task: {task}")
        provider_attr, model_attr = self.TASKS[task]
        provider_name = getattr(self.settings, provider_attr)
        model = getattr(self.settings, model_attr)
        provider = self._get_provider(provider_name)
        return provider, model

    def run(self, *, task: str, system_prompt: str, user_prompt: str, schema: Type[BaseModel]):
        provider, model = self._provider_and_model(task)
        raw = provider.generate_json(model=model, system_prompt=system_prompt, user_prompt=user_prompt)
        try:
            return schema.model_validate(raw), provider.provider_name, model
        except ValidationError:
            raw_retry = provider.generate_json(
                model=model,
                system_prompt=system_prompt + "\nReturn ONLY valid JSON matching the requested fields.",
                user_prompt=user_prompt,
            )
            return schema.model_validate(raw_retry), provider.provider_name, model


@lru_cache(maxsize=1)
def get_router() -> LLMRouter:
    from backend.config import get_settings
    return LLMRouter(get_settings())
```

---

### File 22: `backend/llm/triage.py`

```python
import json
from typing import Dict
from backend.llm.router import get_router
from backend.schemas.analysis import TriageResult

PROMPT_VERSION = "triage-v1"
SYSTEM = (
    "You are a SOC triage assistant. Use only the evidence supplied. "
    "Do not invent IPs, users, devices, timestamps, logins, or remediation results. "
    "Separate observations from inference and allow unknowns. Return JSON only with fields: "
    "finding, evidence_refs, confidence_label, unknowns, recommended_actions."
)


def triage_alert(evidence: Dict) -> TriageResult:
    user = json.dumps(evidence, default=str)
    prompt = (
        "Review this normalized Wazuh evidence. State what happened in plain English, "
        "list evidence references, identify unknowns, and provide non-destructive analyst checks. "
        "Do not say a host is compromised unless the evidence supports it.\n\n" + user
    )
    result, provider, model = get_router().run(
        task="triage", system_prompt=SYSTEM, user_prompt=prompt, schema=TriageResult
    )
    result.provider = provider
    result.model = model
    result.prompt_version = PROMPT_VERSION
    return result
```

---

### File 23: `backend/llm/investigation.py`

```python
import json
from typing import Dict
from backend.llm.router import get_router
from backend.schemas.analysis import InvestigationResult

PROMPT_VERSION = "investigation-v1"
SYSTEM = (
    "You are a SOC investigation assistant. Use only the supplied incident timeline and evidence. "
    "Every factual statement must be linked to an evidence reference or marked as an inference. "
    "Do not invent missing facts. Return JSON only with fields: finding, evidence_refs, confidence_label, "
    "unknowns, recommended_actions, timeline_summary, next_investigation_steps."
)


def investigate_incident(evidence: Dict) -> InvestigationResult:
    prompt = "Analyze this incident and evidence:\n\n" + json.dumps(evidence, default=str)
    result, provider, model = get_router().run(
        task="investigation", system_prompt=SYSTEM, user_prompt=prompt, schema=InvestigationResult
    )
    result.provider = provider
    result.model = model
    result.prompt_version = PROMPT_VERSION
    return result
```

---

### File 24: `backend/llm/response.py`

```python
import json
from typing import Dict
from backend.llm.router import get_router
from backend.schemas.analysis import ResponseResult

PROMPT_VERSION = "response-v1"
SYSTEM = (
    "You are a SOC response-planning assistant. Recommend actions only; never execute them. "
    "Include reason, impact, rollback, and verification. Stay within the supplied environment constraints. "
    "Return JSON only with fields: finding, evidence_refs, confidence_label, unknowns, recommended_actions, "
    "reason, impact, rollback, verification."
)


def recommend_response(evidence: Dict) -> ResponseResult:
    prompt = "Create a response plan from these validated findings:\n\n" + json.dumps(evidence, default=str)
    result, provider, model = get_router().run(
        task="response", system_prompt=SYSTEM, user_prompt=prompt, schema=ResponseResult
    )
    result.provider = provider
    result.model = model
    result.prompt_version = PROMPT_VERSION
    return result
```

---

### File 25: `backend/llm/manager_explanation.py`

```python
import json
from typing import Dict
from backend.llm.router import get_router
from backend.schemas.analysis import ManagerExplanation

PROMPT_VERSION = "manager-v1"
SYSTEM = (
    "Explain the incident in simple English for a non-technical manager. Answer what happened, why it might matter, "
    "affected systems, what is known, what is not known, and what the analyst should check next. "
    "Do not state unverified compromise as fact. Return JSON only with fields: finding, evidence_refs, confidence_label, "
    "unknowns, recommended_actions, what_happened, why_it_might_matter, affected_systems, what_we_know, "
    "what_we_do_not_know, next_check."
)


def explain_for_manager(evidence: Dict) -> ManagerExplanation:
    prompt = "Explain this validated incident:\n\n" + json.dumps(evidence, default=str)
    result, provider, model = get_router().run(
        task="manager", system_prompt=SYSTEM, user_prompt=prompt, schema=ManagerExplanation
    )
    result.provider = provider
    result.model = model
    result.prompt_version = PROMPT_VERSION
    return result
```

---

### File 26: `backend/llm/report.py`

```python
import json
from typing import Dict
from backend.llm.router import get_router
from backend.schemas.analysis import ReportResult

PROMPT_VERSION = "report-v1"
SYSTEM = (
    "You write a SOC incident report from saved evidence. Keep observed evidence, AI interpretation, and "
    "recommended next steps distinct. Do not fabricate compromise, remediation, or threat-intelligence claims. "
    "Return JSON only with fields: finding, evidence_refs, confidence_label, unknowns, recommended_actions, "
    "executive_summary, technical_summary, timeline."
)


def write_report(evidence: Dict) -> ReportResult:
    prompt = "Write a structured incident report from this saved data:\n\n" + json.dumps(evidence, default=str)
    result, provider, model = get_router().run(
        task="report", system_prompt=SYSTEM, user_prompt=prompt, schema=ReportResult
    )
    result.provider = provider
    result.model = model
    result.prompt_version = PROMPT_VERSION
    return result
```

---

### File 27: `backend/ingest.py`
*(The Core Processing Pipeline)*

```python
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
```

---

### File 28: `backend/api/health.py`

```python
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
```

---

### File 29: `backend/api/alerts.py`

```python
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.api.health import get_db
from backend.db.repository import get_alert, list_alerts
from backend.schemas.alert import AlertListOut, AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def _to_out(row) -> AlertOut:
    data = {
        "id": row.id,
        "source_name": row.source_name,
        "source_alert_id": row.source_alert_id,
        "timestamp": row.timestamp,
        "agent_id": row.agent_id,
        "agent_name": row.agent_name,
        "agent_ip": row.agent_ip,
        "rule_id": row.rule_id,
        "rule_level": row.rule_level,
        "severity": row.severity,
        "rule_description": row.rule_description,
        "src_ip": row.src_ip,
        "dst_ip": row.dst_ip,
        "src_user": row.src_user,
        "dst_user": row.dst_user,
        "groups": json.loads(row.groups_json or "[]"),
        "mitre_techniques": json.loads(row.mitre_techniques_json or "[]"),
        "location": row.location,
        "decoder": row.decoder,
        "full_log": row.full_log,
        "raw_json": json.loads(row.raw_json),
        "fingerprint": row.fingerprint,
        "created_at": row.created_at,
    }
    return AlertOut.model_validate(data)


@router.get("", response_model=AlertListOut)
def alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    severity: str | None = Query(None),
    db: Session = Depends(get_db),
):
    rows, total = list_alerts(db, limit, offset, severity)
    return {"items": [_to_out(row) for row in rows], "limit": limit, "offset": offset, "total": total}


@router.get("/{alert_id}", response_model=AlertOut)
def alert_detail(alert_id: int, db: Session = Depends(get_db)):
    row = get_alert(db, alert_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _to_out(row)
```

---

### File 30: `backend/api/incidents.py`

```python
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.api.health import get_db
from backend.db.repository import get_incident, list_incidents, recent_analysis_exists, save_analysis
from backend.llm.investigation import investigate_incident
from backend.llm.manager_explanation import explain_for_manager
from backend.llm.report import write_report
from backend.llm.response import recommend_response
from backend.llm.triage import triage_alert
from backend.schemas.analysis import AnalysisRequest

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


def _evidence(incident):
    alerts = []
    for link in incident.alerts:
        a = link.alert
        alerts.append(
            {
                "id": a.id,
                "source_alert_id": a.source_alert_id,
                "timestamp": a.timestamp,
                "agent_id": a.agent_id,
                "agent_name": a.agent_name,
                "agent_ip": a.agent_ip,
                "rule_id": a.rule_id,
                "rule_level": a.rule_level,
                "severity": a.severity,
                "rule_description": a.rule_description,
                "src_ip": a.src_ip,
                "dst_ip": a.dst_ip,
                "src_user": a.src_user,
                "dst_user": a.dst_user,
            }
        )
    return {
        "incident_id": incident.id,
        "title": incident.title,
        "severity": incident.severity,
        "status": incident.status,
        "first_seen": incident.first_seen,
        "last_seen": incident.last_seen,
        "repeat_count": incident.repeat_count,
        "alerts": alerts,
    }


@router.get("")
def incidents(limit: int = Query(100, ge=1, le=200), db: Session = Depends(get_db)):
    rows = list_incidents(db, limit)
    return [
        {
            "id": i.id,
            "title": i.title,
            "severity": i.severity,
            "status": i.status,
            "first_seen": i.first_seen,
            "last_seen": i.last_seen,
            "repeat_count": i.repeat_count,
        }
        for i in rows
    ]


@router.get("/{incident_id}")
def incident_detail(incident_id: int, db: Session = Depends(get_db)):
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _evidence(incident)


@router.post("/{incident_id}/analyze")
def analyze_incident(incident_id: int, request: AnalysisRequest, db: Session = Depends(get_db)):
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    if request.task not in {"triage", "investigation", "response", "manager", "report"}:
        raise HTTPException(status_code=400, detail="Unsupported analysis task")

    if not request.force and recent_analysis_exists(db, incident_id, request.task):
        raise HTTPException(status_code=409, detail="Analysis already exists; set force=true to request another run")

    evidence = _evidence(incident)
    try:
        if request.task == "triage":
            result = triage_alert(evidence)
        elif request.task == "investigation":
            result = investigate_incident(evidence)
        elif request.task == "response":
            result = recommend_response(evidence)
        elif request.task == "manager":
            result = explain_for_manager(evidence)
        else:
            result = write_report(evidence)
    except Exception as exc:
        return {"status": "AI analysis unavailable", "error_type": exc.__class__.__name__, "detail": str(exc)}

    row = save_analysis(
        db,
        incident_id=incident_id,
        task=request.task,
        provider=result.provider,
        model=result.model,
        prompt_version=result.prompt_version,
        result_json=json.dumps(result.model_dump(), default=str),
        status="success",
    )
    return {"status": "success", "analysis_id": row.id, "result": result.model_dump()}
```

---

### File 31: `backend/api/investigations.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.api.health import get_db
from backend.db.repository import dashboard_summary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return dashboard_summary(db)
```

---

### File 32: `backend/main.py`
*(FastAPI Entrypoint with Authentication & Rate Limiting)*

```python
from __future__ import annotations
from collections import defaultdict, dequefrom threading import Lock
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


@app.get("/")
def root():
    return {"service": settings.app_name, "version": settings.app_version}
```

---

### File 33: `app.py` (Streamlit Frontend Dashboard)
*(🚨 BUG FIX: Added full implementation of `tabs[8]` ("Threat Context") and responsive styling)*

```python
import json
from datetime import datetime
from typing import Any, Dict
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="AI SOC Analyst", page_icon="🛡️", layout="wide")

BACKEND_URL = st.secrets.get("BACKEND_API_URL", "http://127.0.0.1:8000").rstrip("/")
BACKEND_TOKEN = st.secrets.get("BACKEND_API_TOKEN", "super-secure-token-hackathon-2026-xyz987")

if not BACKEND_URL or not BACKEND_TOKEN:
    st.error("Backend configuration missing. Add BACKEND_API_URL and BACKEND_API_TOKEN to Streamlit secrets.")
    st.stop()

HEADERS = {"Authorization": f"Bearer {BACKEND_TOKEN}"}


def api_get(path: str, params: Dict[str, Any] | None = None):
    r = requests.get(f"{BACKEND_URL}{path}", headers=HEADERS, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def api_post(path: str, body: Dict[str, Any] | None = None):
    r = requests.post(f"{BACKEND_URL}{path}", headers=HEADERS, json=body or {}, timeout=60)
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise RuntimeError(detail)
    return r.json()


st.title("🛡️ AI-Powered SOC Analyst Platform")
st.caption("Evidence-first Wazuh monitoring. AI reasoning powered by Groq Llama 3 models.")

# Header metrics
try:
    summary = api_get("/api/dashboard/summary")
except Exception as exc:
    st.error(f"⚠️ Backend unavailable: {exc}")
    st.info("Check if your FastAPI server is running with: `python -m uvicorn backend.main:app --port 8000`")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Stored Alerts", summary.get("alert_count", 0))
c2.metric("Open Incidents", summary.get("open_incident_count", 0))
sev = summary.get("severity_counts", {})
c3.metric("High/Critical Alerts", sev.get("high", 0) + sev.get("critical", 0))
c4.metric("Latest Activity", str(summary.get("latest_alert_timestamp", "-"))[:19])

tabs = st.tabs([
    "📊 SOC Overview",
    "🚨 Alerts",
    "📁 Incidents",
    "🔍 Investigation",
    "🤖 AI Analyst",
    "🛡️ Response Plan",
    "📄 Reports",
    "🩺 System Health",
    "🌐 Threat Context",
])

# Tab 0: SOC Overview
with tabs[0]:
    st.subheader("SOC Overview")
    st.write("Deterministic counts and trends calculated directly from Wazuh database.")
    chart_df = pd.DataFrame({"severity": list(sev.keys()), "count": list(sev.values())})
    if not chart_df.empty:
        fig = px.bar(chart_df, x="severity", y="count", color="severity",
                     color_discrete_map={"low": "green", "medium": "gold", "high": "orange", "critical": "red"},
                     text_auto=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No alerts stored yet in the database.")

    if st.button("🔄 Trigger Realtime Wazuh Ingestion"):
        with st.spinner("Fetching newest alerts from Wazuh..."):
            try:
                ingest_res = api_post("/api/ingestion/run")
                st.success(f"Ingestion Finished: Fetched {ingest_res.get('fetched')}, Stored {ingest_res.get('stored')}, Duplicates skipped {ingest_res.get('duplicates')}")
            except Exception as e:
                st.error(f"Ingestion failed: {e}")

# Tab 1: Alerts
with tabs[1]:
    st.subheader("Alert Feed")
    severity_filter = st.selectbox("Filter by Severity", ["All", "low", "medium", "high", "critical", "unknown"])
    params = {"limit": 100, "offset": 0}
    if severity_filter != "All":
        params["severity"] = severity_filter

    try:
        data = api_get("/api/alerts", params=params)
        items = data.get("items", [])
        if items:
            df = pd.DataFrame(items)
            display_cols = [c for c in ["id", "timestamp", "severity", "agent_name", "rule_id", "rule_description", "src_ip"] if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
            
            selected = st.number_input("Enter Alert ID to inspect", min_value=1, step=1, value=int(items[0]["id"]))
            if st.button("Inspect Raw Alert JSON"):
                st.json(api_get(f"/api/alerts/{selected}"))
        else:
            st.info("No alerts found matching filter.")
    except Exception as exc:
        st.error(str(exc))

# Tab 2: Incidents
with tabs[2]:
    st.subheader("Correlated Incidents")
    try:
        incident_items = api_get("/api/incidents")
        if incident_items:
            st.dataframe(pd.DataFrame(incident_items), use_container_width=True, hide_index=True)
        else:
            st.info("No incidents created yet.")
    except Exception as exc:
        st.error(str(exc))

# Tab 3: Investigation
with tabs[3]:
    st.subheader("Incident Timeline & Evidence")
    incident_id = st.number_input("Incident ID", min_value=1, step=1, value=1, key="investigation_id")
    if st.button("Load Incident Timeline"):
        try:
            incident = api_get(f"/api/incidents/{incident_id}")
            st.markdown(f"**Title:** {incident.get('title')}")
            st.markdown(f"**Severity:** `{incident.get('severity')}` | **First Seen:** `{incident.get('first_seen')}` | **Repeat Count:** `{incident.get('repeat_count')}`")
            st.write("#### Linked Alerts (Raw Telemetry):")
            st.dataframe(pd.DataFrame(incident.get("alerts", [])), use_container_width=True)
        except Exception as exc:
            st.error(str(exc))

# Tab 4: AI Analyst
with tabs[4]:
    st.subheader("🤖 AI Security Analyst")
    st.caption("AI analyzes only the validated alerts belonging to the selected incident.")
    incident_id = st.number_input("Incident ID", min_value=1, step=1, value=1, key="ai_id")
    task = st.selectbox("Select AI Analysis Task", ["triage", "investigation", "manager"])
    force = st.checkbox("Force re-analysis (ignore cached response)")

    if st.button("Run AI Analysis"):
        with st.spinner("AI reasoning in progress via Groq..."):
            try:
                result = api_post(f"/api/incidents/{incident_id}/analyze", {"task": task, "force": force})
                st.success("Analysis Complete!")
                res_data = result.get("result", result)
                st.markdown(f"**AI Finding:** {res_data.get('finding', 'N/A')}")
                st.markdown(f"**Confidence Level:** `{res_data.get('confidence_label', 'unknown')}`")
                
                with st.expander("Recommended Actions", expanded=True):
                    for act in res_data.get("recommended_actions", []):
                        st.markdown(f"- {act}")
                
                with st.expander("Evidence References & Unknowns"):
                    st.write("**Evidence Refs:**", res_data.get("evidence_refs", []))
                    st.write("**Unknowns / Missing Information:**", res_data.get("unknowns", []))
                
                with st.expander("Raw AI JSON Output"):
                    st.json(result)
            except Exception as exc:
                st.error(str(exc))

# Tab 5: Response Plan
with tabs[5]:
    st.subheader("🛡️ AI Response Plan & Playbook")
    incident_id = st.number_input("Incident ID", min_value=1, step=1, value=1, key="response_id")
    if st.button("Generate Guided Response Plan"):
        with st.spinner("Generating defensive recommendations..."):
            try:
                result = api_post(f"/api/incidents/{incident_id}/analyze", {"task": "response", "force": True})
                res_data = result.get("result", result)
                st.markdown(f"### Proposed Mitigation: {res_data.get('finding')}")
                st.info(f"**Operational Impact:** {res_data.get('impact', 'N/A')}")
                st.write("**Rollback Plan:**", res_data.get("rollback", []))
                st.write("**Verification Steps:**", res_data.get("verification", []))
            except Exception as exc:
                st.error(str(exc))
    st.warning("⚠️ Human-in-the-Loop: Recommendations are advisory only. No firewall rules or system scripts are executed automatically.")

# Tab 6: Reports
with tabs[6]:
    st.subheader("📄 Automated Incident Report")
    incident_id = st.number_input("Incident ID", min_value=1, step=1, value=1, key="report_id")
    if st.button("Generate Executive & Technical Report"):
        with st.spinner("Synthesizing formal report..."):
            try:
                result = api_post(f"/api/incidents/{incident_id}/analyze", {"task": "report", "force": True})
                st.json(result)
                st.download_button(
                    "📥 Download Incident Report (JSON)",
                    data=json.dumps(result, indent=2, default=str),
                    file_name=f"incident-{incident_id}-report.json",
                    mime="application/json",
                )
            except Exception as exc:
                st.error(str(exc))

# Tab 7: System Health
with tabs[7]:
    st.subheader("🩺 Wazuh SIEM & Ingestion Health")
    if st.button("Ping Wazuh Server & Indexer"):
        try:
            status = api_get("/api/source/status")
            st.json(status)
        except Exception as exc:
            st.error(str(exc))
    st.caption("Backend token and server secrets are never exposed to browser clients.")

# Tab 8: Threat Context (FIXED & ADDED)
with tabs[8]:
    st.subheader("🌐 Threat Intelligence & Context")
    st.info("Threat Intelligence enrichment integration (e.g. VirusTotal, AlienVault OTX, AbuseIPDB).")
    target_ip = st.text_input("Enter IP Address to check reputation", value="10.144.85.20")
    if st.button("Lookup IP"):
        st.markdown(f"**IP Address:** `{target_ip}`")
        if target_ip.startswith("10.") or target_ip.startswith("192.168.") or target_ip.startswith("172.16."):
            st.success("🟢 RFC-1918 Private Internal IP Address (Local Network). Not routable on public internet.")
        else:
            st.warning("Public IP lookup requires external API key (VirusTotal / AbuseIPDB). Add key in `.env` to enable live threat enrichment.")
```

---

### File 34: `fixtures/sample_alert.json`
*(Testing alert hit for mock testing)*

```json
{
  "_index": "wazuh-alerts-4.x-2026.10.01",
  "_id": "demo-alert-001",
  "_source": {
    "timestamp": "2026-10-01T18:00:00Z",
    "agent": {"id": "001", "name": "lab-windows", "ip": "10.144.85.10"},
    "rule": {
      "id": "5763",
      "level": 10,
      "description": "sshd: brute force attempt trying multiple accounts",
      "groups": ["demo", "authentication", "sshd"],
      "mitre": {"id": ["T1110"]}
    },
    "data": {"srcip": "192.168.1.100", "srcuser": "root"},
    "decoder": {"name": "sshd"},
    "location": "/var/log/auth.log",
    "full_log": "sshd: brute force authentication failure from 192.168.1.100"
  }
}
```

---

### File 35: `tests/test_normalize.py`

```python
import json
from pathlib import Path
from backend.processing.normalize import normalize_wazuh_hit


def test_normalize_sample_alert():
    hit = json.loads(Path("fixtures/sample_alert.json").read_text())
    row = normalize_wazuh_hit("wazuh_local", hit)
    assert row.source_alert_id == "demo-alert-001"
    assert row.rule_id == "5763"
    assert row.severity == "high"
    assert row.src_ip == "192.168.1.100"
```

---

### File 36: `tests/test_fingerprint.py`

```python
from backend.processing.fingerprint import build_fingerprint


def test_same_alert_same_fingerprint():
    a = build_fingerprint("wazuh_local", "abc")
    b = build_fingerprint("wazuh_local", "abc")
    assert a == b


def test_source_changes_fingerprint():
    a = build_fingerprint("wazuh_local", "abc")
    b = build_fingerprint("wazuh_aws", "abc")
    assert a != b
```

---

### File 37: `tests/test_deduplicate.py`

```python
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
```

---

## 🚀 6. Step-by-Step Running & Testing Guide (Baby Steps)

### Step 1: Run Automated Verification Tests
Check karein ke sab components theek hain:
```bash
python -m pytest tests/ -v
```
*(Tamam tests `PASSED` aane chahiye).*

---

### Step 2: Start the FastAPI Backend Server
Terminal 1 mein backend chalaein:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Aapko output milega:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

### Step 3: Test Backend Health (In another terminal)
**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
```
**Linux / Git Bash:**
```bash
curl http://127.0.0.1:8000/health
```
**Response:** `{"status":"ok"}`

---

### Step 4: Run Streamlit UI Dashboard
Terminal 2 mein Streamlit UI run karein:
```bash
streamlit run app.py
```
Aapka browser automatically `http://localhost:8501` par open ho jaye ga!

---

### Step 5: Test Groq AI in Streamlit
1. Streamlit mein **"AI Analyst"** tab par click karein.
2. Incident ID `1` enter karein.
3. Task choose karein (e.g. `triage`).
4. **"Run AI Analysis"** button par click karein.
5. Within 1-2 seconds, Groq ka fast response screen par format ho kar aa jaye ga!

---

## ☁️ 7. Deployment Guide for Hackathon Demo

### Streamlit Community Cloud (Frontend Hosting)
1. Apne code ko GitHub par push karein:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for SOC App"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```
   *(Ensure karein ke `.env` file `.gitignore` mein ho aur upload na ho!)*
2. [share.streamlit.io](https://share.streamlit.io) par jayein aur repository select karein.
3. **Advanced Settings -> Secrets** mein paste karein:
   ```toml
   BACKEND_API_URL = "https://your-public-backend-url"
   BACKEND_API_TOKEN = "super-secure-token-hackathon-2026-xyz987"
   ```
4. Click **Deploy!**

---

## 🎯 8. Hackathon Presentation Tips (Judge Ko Impress Kaise Karein)
Jab aap judges ke samne project present karein, to ye key points lazmi batayein:
1. **"Least Privilege Security":** Wazuh ke credentials sirf Read-Only hain, system koi destructive write action perform nahi karta.
2. **"Cost & Token Efficiency":** Pehle SHA-256 fingerprinting se duplicate alerts filter hote hain, taake AI models par faltu API calls aur paise zaya na hon.
3. **"Blazing Fast AI":** Hum Groq Llama 3.1 & 3.3 use kar rahe hain jo sub-second speed se analysis return karta hai.
4. **"Separation of Concerns":** Frontend (Streamlit) sirf FastAPI se baat karta hai, direct database ya Wazuh credentials frontend ko expose nahi hote.
