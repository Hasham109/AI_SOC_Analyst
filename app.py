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


@st.fragment(run_every=120)
def _live_header():
    """Auto-refreshes every 2 minutes — fetches latest summary from backend."""
    try:
        summary = api_get("/api/dashboard/summary")
    except Exception as exc:
        st.error(f"⚠️ Backend unavailable: {exc}")
        st.info("Check if your FastAPI server is running with: `python -m uvicorn backend.main:app --port 8000`")
        return

    sev = summary.get("severity_counts", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Stored Alerts", summary.get("alert_count", 0))
    c2.metric("Open Incidents", summary.get("open_incident_count", 0))
    c3.metric("High/Critical Alerts", sev.get("high", 0) + sev.get("critical", 0))
    c4.metric("Latest Activity", str(summary.get("latest_alert_timestamp", "-"))[:19])
    st.caption(f"🔄 Last refreshed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC  •  Auto-refreshes every 2 min")
    st.session_state["_last_summary"] = summary


_live_header()

# Expose summary for tabs that need it (may be stale on first render)
try:
    summary = api_get("/api/dashboard/summary")
except Exception as exc:
    st.error(f"⚠️ Backend unavailable: {exc}")
    st.info("Check if your FastAPI server is running with: `python -m uvicorn backend.main:app --port 8000`")
    st.stop()
sev = summary.get("severity_counts", {})

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

    @st.fragment(run_every=120)
    def _live_overview():
        """Live overview panel — auto-refreshes every 2 minutes."""
        try:
            live_summary = api_get("/api/dashboard/summary")
        except Exception as exc:
            st.error(f"Failed to load overview: {exc}")
            return

        live_sev = live_summary.get("severity_counts", {})
        chart_df = pd.DataFrame({"severity": list(live_sev.keys()), "count": list(live_sev.values())})
        if not chart_df.empty:
            fig = px.bar(
                chart_df, x="severity", y="count", color="severity",
                color_discrete_map={"low": "#22c55e", "medium": "#f59e0b",
                                    "high": "#f97316", "critical": "#ef4444",
                                    "unknown": "#6b7280"},
                text_auto=True, title="Alert Distribution by Severity",
            )
            fig.update_layout(showlegend=False, margin=dict(t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No alerts stored yet in the database.")

        st.caption(
            f"📡 Live data — {live_summary.get('alert_count', 0)} total alerts  "
            f"• {live_summary.get('open_incident_count', 0)} open incidents  "
            f"• Auto-refreshes every 2 min"
        )

    _live_overview()

    st.divider()
    if st.button("⚡ Trigger Manual Ingestion Now", key="manual_ingest"):
        with st.spinner("Fetching newest alerts from Wazuh..."):
            try:
                ingest_res = api_post("/api/ingestion/run")
                sim = ingest_res.get('simulated', 0)
                sim_note = f" + {sim} simulated" if sim else ""
                st.success(
                    f"✅ Ingestion done — "
                    f"Fetched **{ingest_res.get('fetched')}**, "
                    f"Stored **{ingest_res.get('stored')}{sim_note}**, "
                    f"Duplicates skipped **{ingest_res.get('duplicates')}**"
                )
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
