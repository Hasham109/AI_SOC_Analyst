# 🛡️ SentinalIQ — AI Powered Security Operations Platform

<p align="center">
  <img src="https://img.shields.io/badge/Security-SOC%20Analyst-blue?style=for-the-badge&logo=shield" alt="SOC Analyst"/>
  <img src="https://img.shields.io/badge/SIEM-Wazuh-00a4e4?style=for-the-badge&logo=wazuh&logoColor=white" alt="Wazuh SIEM"/>
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
 <img src="https://img.shields.io/badge/LLM-Groq%20openai%2Fgpt--oss--20b-f55036?style=for-the-badge" alt="Groq openai/gpt-oss-20b"/>
  <img src="https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Database-SQLite%20%2F%20SQLAlchemy-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
  <img src="https://img.shields.io/badge/Framework-MITRE%20ATT%26CK-orange?style=for-the-badge" alt="MITRE ATT&CK"/>
</p>

---

## 📌 Executive Summary

**SENTINEL AI** is a production-grade, AI-augmented Security Operations Center (SOC) platform designed to tackle the primary bottleneck in cybersecurity monitoring: **alert fatigue and slow Mean Time to Respond (MTTR)**.

Modern SOC teams receive thousands of raw SIEM logs every day. Sifting through noisy events, correlating multi-stage attacks, and writing response plans manually causes burn-out and missed threats. 

SENTINEL AI bridges the gap between raw telemetry and actionable incident response:
1. **Ingests & Normalizes** security alerts in real-time from **Wazuh SIEM** (Local & AWS Cloud).
2. **Deduplicates & Correlates** isolated events into unified, context-rich security incidents using sliding time-windows and cryptographic fingerprinting.
3. **Deploys Groq Ultra-Low-Latency LLMs** to provide multi-perspective reasoning:
   - ⚡ **Triage Analyst**: Fast classification (True Positive vs. False Positive vs. Benign).
   - 🔬 **Deep Investigator**: Root-cause analysis and MITRE ATT&CK technique mapping.
   - 🛡️ **Response Strategist**: Containment, eradication, and recovery playbooks (NIST/SANS aligned).
   - 👔 **Executive Explainer**: Plain-English, business-risk briefings for non-technical leadership.
4. **Visualizes All Telemetry** via a high-performance **Streamlit 9-view Command Center**.

---

## 🏛️ System Architecture

```
                       ┌──────────────────────────────────────────────┐
                       │           Wazuh Manager / Indexer            │
                       │   (Local VM / Docker or AWS Cloud Host)      │
                       └──────────────────────┬───────────────────────┘
                                              │ 
                                              │ 1. Read-Only Poller / Ingestion API
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FASTAPI BACKEND ENGINE                                    │
│                                                                                             │
│  ┌─────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐  │
│  │   Source Adapter        ├────►│  Normalize & Clean     ├────►│ SHA-256 Deduplication  │  │
│  │ (Wazuh API / Fallback)  │     │  (Schema Standardization)│   │ (Fingerprint Cache)    │  │
│  └─────────────────────────┘     └────────────────────────┘     └───────────┬────────────┘  │
│                                                                             │               │
│                                                                             ▼               │
│  ┌─────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐  │
│  │ Database (SQLAlchemy)   │◄────┤ SQLAlchemy ORM Models  │◄────┤ Correlation Engine     │  │
│  │ (Alerts, Incidents, Ops)│     │ (SQLite / PostgreSQL)  │     │ (Sliding Time Windows) │  │
│  └───────────┬─────────────┘     └────────────────────────┘     └────────────────────────┘  │
│              │                                                                              │
│              │ (Strict Bounded Evidence Prompts — Anti-Hallucination)                       │
│              ▼                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                              Groq High-Speed LLM Router                               │  │
│  │   • Triage: Fast Decision-Tree Reasoning                                              │  │
│  │   • Investigation: MITRE ATT&CK Mapping & Evidence Synthesis                           │  │
│  │   • Playbooks: NIST SP 800-61 / SANS Guided Response Strategy                         │  │
│  │   • Executive Summary: Plain-English Risk Explanations for C-Suite                    │  │
│  └───────────────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               │ 2. Public RESTful API (Bearer Auth + Rate Limits)
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 SENTINEL AI STREAMLIT UI                                    │
│                                                                                             │
│  [1. SOC Overview]      [2. Alerts Explorer]      [3. Incidents]     [4. Investigation]     │
│  [5. AI Analyst Studio] [6. Response Plan]        [7. Reports]       [8. Threat Intel]      │
│  [9. System Health]                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Highlights & Core Capabilities

### 1. 🛡️ Wazuh SIEM Integration & Ingestion Poller
- Multi-source adapter supporting **Local Wazuh API (port 55000)**, **Indexer (port 9200)**, and **AWS Cloud Wazuh**.
- Resilient cursor-based tracking with automatic lookback windows to prevent data loss across restarts.
- Built-in **Auto-Simulation Fallback**: If the SIEM is idle during demonstrations, realistic Wazuh events (e.g., SSH Brute Force, Web Shells, Reverse Shells, Privilege Escalation) are simulated safely.

### 2. 🧬 Deterministic Deduplication & Incident Correlation
- **SHA-256 Event Fingerprinting**: Suppresses duplicate alerts within identical timestamp/rule boundaries, saving database storage and LLM token costs.
- **Sliding-Window Correlation**: Automatically correlates alerts sharing identical source IPs, targeted hostnames, or MITRE techniques into consolidated **Incidents** within configurable time windows (default: 10 minutes).

### 3. 🤖 Multi-Perspective AI Reasoning (Groq Ultra-Fast Inference)
- Powered by high-throughput models on **Groq Cloud** with deterministic, temperature-controlled JSON output.
- **Strict Anti-Hallucination Guardrails**: The LLM is injected *only* with validated, bounded alert evidence. Missing attributes (e.g., unset IP or unknown user) are explicitly flagged as unknown rather than invented.
- **Human-in-the-Loop Principle**: The AI recommends actions; it *never* unilaterally modifies firewall rules or disables accounts without explicit human authorization.

### 4. 📊 9-View Operations Dashboard (Streamlit)
| View | Description |
| :--- | :--- |
| **1. SOC Overview** | High-level situational awareness: KPI cards, real-time alert feed, chronological attack timeline, and MITRE tactic distributions. |
| **2. Alerts Explorer** | Paginated security event feed with severity filters, multi-column search, and raw JSON payload inspector. |
| **3. Incidents** | Attack clusters grouped by affected host and source IP with progression status and repeat counts. |
| **4. Investigation** | Deep-dive incident console with linked alert breakdown, evidence timelines, and MITRE mapping. |
| **5. AI Analyst** | Multi-engine reasoning studio for automated triage, root cause analysis, and managerial summaries. |
| **6. Response Plan** | Step-by-step NIST-aligned containment, eradication, and recovery playbooks with executable CLI commands. |
| **7. Reports** | Executive incident report generator exporting formatted executive briefings. |
| **8. Threat Context** | Threat intelligence dashboard tracking IOCs, attacker fingerprints, and MITRE ATT&CK heatmaps. |
| **9. System Health** | Live backend telemetry: database metrics, API response latency, poller cycles, and rate limit counters. |

---

## 📂 Project Directory Structure

```text
AI_SOC_Analyst/
├── app.py                     # Streamlit frontend dashboard (9 integrated views)
├── seed_demo_data.py          # Demo data generator with realistic attack patterns
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables configuration template
├── .gitignore                 # Git ignore rules
│
├── backend/                   # FastAPI backend service
│   ├── main.py                # Server entrypoint, middleware, lifespan poller
│   ├── config.py              # Pydantic Settings configuration & secrets loader
│   ├── ingest.py              # Ingestion orchestration & cursor management
│   │
│   ├── api/                   # RESTful API route controllers
│   │   ├── alerts.py          # Alert querying, filtering & details
│   │   ├── incidents.py       # Incident clustering & correlation endpoints
│   │   ├── investigations.py  # AI reasoning routes (Triage, Analysis, Playbooks)
│   │   ├── health.py          # Health checks & uptime telemetry
│   │   └── system.py          # System diagnostic & ingestion trigger APIs
│   │
│   ├── db/                    # Persistence layer
│   │   ├── session.py         # SQLAlchemy engine & session factory
│   │   └── models.py          # Alert, Incident, and Audit database models
│   │
│   ├── llm/                   # AI / LLM orchestration
│   │   ├── router.py          # Dynamic model router & prompt builders
│   │   ├── triage.py          # Fast triage decision engine
│   │   ├── investigation.py   # In-depth root-cause investigation
│   │   ├── response.py        # Remediation playbook synthesis
│   │   ├── manager_explanation.py # Non-technical executive summary engine
│   │   └── providers/         # LLM client drivers (Groq, AWS Bedrock)
│   │
│   ├── processing/            # Data engineering
│   │   ├── normalize.py       # Wazuh alert field normalization
│   │   ├── fingerprint.py     # Cryptographic alert fingerprinting
│   │   ├── deduplicate.py     # Deduplication logic
│   │   └── correlation.py     # Temporal incident correlation engine
│   │
│   ├── schemas/               # Pydantic request/response schemas
│   └── wazuh/                 # Wazuh SIEM client & mock generator
│
├── fixtures/                  # Mock alert fixtures for testing
└── tests/                     # Unit and integration test suite
    ├── test_api.py            # API endpoint validation
    ├── test_normalize.py      # Normalization tests
    ├── test_fingerprint.py    # Fingerprint determinism tests
    ├── test_deduplicate.py    # Deduplication edge-case tests
    ├── test_cursor.py         # Ingestion cursor recovery tests
    └── test_source_factory.py # Ingestion source adapter tests
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Streamlit, Plotly, Pandas, HTML5/CSS3 (Glassmorphism SOC Theme) |
| **Backend** | FastAPI, Uvicorn, Pydantic v2, Python 3.11+ |
| **LLM & Reasoning** | Groq Cloud SDK (`Openai/gpt-os-20b`, `Openai/gpt-os-120b`), AWS Bedrock (Optional) |
| **Database & ORM** | SQLite / PostgreSQL, SQLAlchemy 2.0 |
| **Security Telemetry** | Wazuh SIEM (REST API & OpenSearch Indexer), MITRE ATT&CK Framework |
| **Testing & CI** | Pytest, Pytest-Mock |

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Hasham109/AI_SOC_Analyst.git
cd AI_SOC_Analyst
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows:
.venv\Scripts\activate

# Activate on Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and provide your **Groq API Key**:
```ini
GROQ_API_KEY=gsk_your_groq_api_key_here
SOC_API_TOKEN=super-secure-token-hackathon-2026-xyz987
DATABASE_URL=sqlite:///./soc_app.db
AUTO_SIMULATE_ON_EMPTY=true
```

### 4. Seed Demo Data (Optional for Quick Evaluation)
Populate your database with realistic attack scenarios (SSH Brute Force, Web Shells, Cron Injections, Ransomware):
```bash
python seed_demo_data.py
```

### 5. Launch the Application

#### Option A: Run Backend & Frontend in Two Terminals

**Terminal 1 (FastAPI Backend):**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Streamlit UI):**
```bash
streamlit run app.py
```

Open your browser at: **`http://localhost:8501`**

---

## ☁️ Streamlit Cloud Deployment

When deploying the frontend to **Streamlit Community Cloud**:
1. Connect your GitHub repository: `Hasham109/AI_SOC_Analyst`.
2. Main file path: `app.py`.
3. In **App Settings ➔ Secrets**, configure the backend URL and security token:
   ```toml
   BACKEND_API_URL = "https://your-fastapi-backend.onrender.com"
   BACKEND_API_TOKEN = "super-secure-token-hackathon-2026-xyz987"
   ```

---

## 🔒 Security & AI Safety Guardrails

1. **Human-in-the-Loop (No Autonomous System Execution)**:
   SENTINEL AI does **not** execute containment scripts or API commands on infrastructure automatically. It generates verified, actionable CLI commands and playbooks for human SOC analysts to review, authorize, and run.
2. **Anti-Hallucination Evidence Boundary**:
   LLM prompt templates enforce strict grounding. If specific metadata (e.g., target user, hash, IP) is not present in the Wazuh alert payload, the AI is explicitly instructed to label it as `"Unknown"` rather than inferring or hallucinating data.
3. **API Protection**:
   - Bearer Token Authentication on all endpoints (except `/health`).
   - In-memory token bucket rate limiting (120 req/min per IP).

---

## 🧪 Testing

Execute the test suite to verify normalization, deduplication, cursor management, and API routes:
```bash
pytest tests/ -v
```

<p align="center">
  <b>Built for Modern Security Operations Centers</b><br/>
  <i>Streamlining Threat Detection, Correlation, and Incident Response with Generative AI.</i>
</p>
        
