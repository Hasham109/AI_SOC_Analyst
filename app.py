import html
import json
import math
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SENTINEL AI · SOC Analyst",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BACKEND_URL = st.secrets.get("BACKEND_API_URL", "http://127.0.0.1:8000").rstrip("/")
BACKEND_TOKEN = st.secrets.get("BACKEND_API_TOKEN", "super-secure-token-hackathon-2026-xyz987")

if not BACKEND_URL or not BACKEND_TOKEN:
    st.error("Backend configuration missing. Add BACKEND_API_URL and BACKEND_API_TOKEN to Streamlit secrets.")
    st.stop()

HEADERS = {"Authorization": f"Bearer {BACKEND_TOKEN}"}


# ── API Helpers ───────────────────────────────────────────────────────────────
def api_get(path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 15) -> Dict[str, Any]:
    url = f"{BACKEND_URL}{path}"
    resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def api_post(path: str, body: Optional[Dict[str, Any]] = None, timeout: int = 60) -> Dict[str, Any]:
    url = f"{BACKEND_URL}{path}"
    resp = requests.post(url, headers=HEADERS, json=body or {}, timeout=timeout)
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise RuntimeError(detail)
    return resp.json()


@st.cache_data(ttl=60)
def cached_api_get(path: str, params_tuple: Optional[tuple] = None) -> Dict[str, Any]:
    params = dict(params_tuple) if params_tuple else None
    return api_get(path, params=params)


# ── Global Styling ────────────────────────────────────────────────────────────
def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        /* Hide Streamlit Chrome */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display: none;}
        div[data-testid="stDecoration"] {display: none;}

        /* Core Canvas */
        .stApp {
            background: radial-gradient(circle at 90% 10%, #13254a 0%, transparent 45%),
                        radial-gradient(circle at 10% 90%, #1a0f33 0%, transparent 45%),
                        #070b14;
            color: #e6ecf7;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Mono styling */
        .mono {
            font-family: 'JetBrains Mono', monospace;
        }

        /* Glassmorphism Cards */
        .soc-card {
            background: linear-gradient(180deg, rgba(17,26,44,0.92) 0%, rgba(13,20,34,0.92) 100%);
            border: 1px solid #1c2740;
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
            margin-bottom: 16px;
            position: relative;
        }

        .soc-card-border-glow {
            border: 1px solid transparent;
            background: linear-gradient(180deg, rgba(17,26,44,0.92) 0%, rgba(13,20,34,0.92) 100%) padding-box,
                        linear-gradient(135deg, rgba(34,211,238,0.5) 0%, rgba(139,92,246,0.5) 100%) border-box;
        }

        /* KPI Strips */
        .kpi-strip {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            border-radius: 16px 16px 0 0;
        }
        .strip-cyan { background: #22d3ee; }
        .strip-orange { background: #f97316; }
        .strip-red { background: #f43f5e; }
        .strip-violet { background: #8b5cf6; }

        /* Severity Pills */
        .pill {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            line-height: 1.4;
        }
        .pill-critical {
            background: rgba(244, 63, 94, 0.15);
            color: #f43f5e;
            border: 1px solid rgba(244, 63, 94, 0.4);
        }
        .pill-high {
            background: rgba(249, 115, 22, 0.15);
            color: #f97316;
            border: 1px solid rgba(249, 115, 22, 0.4);
        }
        .pill-medium {
            background: rgba(234, 179, 8, 0.15);
            color: #eab308;
            border: 1px solid rgba(234, 179, 8, 0.4);
        }
        .pill-low {
            background: rgba(34, 197, 94, 0.15);
            color: #22c55e;
            border: 1px solid rgba(34, 197, 94, 0.4);
        }
        .pill-unknown {
            background: rgba(107, 114, 128, 0.15);
            color: #9ca3af;
            border: 1px solid rgba(107, 114, 128, 0.4);
        }

        /* MITRE Chips */
        .mitre-chip {
            display: inline-block;
            background: rgba(139, 92, 246, 0.15);
            color: #c4b5fd;
            border: 1px solid rgba(139, 92, 246, 0.35);
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 4px;
            margin: 2px;
        }

        /* Connection status dots */
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
        }
        .dot-green { background: #22c55e; box-shadow: 0 0 8px rgba(34, 197, 94, 0.6); }
        .dot-amber { background: #eab308; box-shadow: 0 0 8px rgba(234, 179, 8, 0.6); }
        .dot-red { background: #f43f5e; box-shadow: 0 0 8px rgba(244, 63, 94, 0.6); }
        .dot-grey { background: #6b7280; box-shadow: 0 0 6px rgba(107, 114, 128, 0.4); }

        /* Primary Button */
        div.stButton > button {
            background: linear-gradient(135deg, #22d3ee 0%, #3b82f6 100%);
            color: #070b14 !important;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            box-shadow: 0 4px 18px rgba(34, 211, 238, 0.3);
            transition: all 0.2s ease;
        }
        div.stButton > button:hover {
            box-shadow: 0 6px 24px rgba(34, 211, 238, 0.5);
            transform: translateY(-1px);
            color: #000 !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0a0f1d !important;
            border-right: 1px solid #1c2740;
        }
        section[data-testid="stSidebar"] .stRadio > div {
            gap: 4px;
        }
        section[data-testid="stSidebar"] .stRadio label {
            background: transparent;
            padding: 8px 12px;
            border-radius: 8px;
            border-left: 3px solid transparent;
            color: #94a3b8;
            font-weight: 500;
            transition: all 0.15s ease;
        }
        section[data-testid="stSidebar"] .stRadio label:hover {
            background: rgba(255, 255, 255, 0.03);
            color: #e6ecf7;
        }

        /* Input Controls */
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"] {
            background-color: #0d1422 !important;
            border: 1px solid #1c2740 !important;
            color: #e6ecf7 !important;
            border-radius: 8px !important;
        }

        /* Custom Table Styling */
        .soc-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        .soc-table th {
            text-align: left;
            padding: 10px 12px;
            color: #7d8aa5;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.05em;
            border-bottom: 1px solid #1c2740;
        }
        .soc-table td {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(28, 39, 64, 0.6);
            color: #e6ecf7;
            vertical-align: middle;
        }
        .soc-table tr:hover td {
            background-color: rgba(255, 255, 255, 0.02);
        }

        /* Timeline Items */
        .timeline-item {
            position: relative;
            padding-left: 28px;
            padding-bottom: 18px;
            border-left: 2px solid #1c2740;
        }
        .timeline-item:last-child {
            border-left: 2px solid transparent;
            padding-bottom: 0;
        }
        .timeline-node {
            position: absolute;
            left: -7px;
            top: 0;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            border: 2px solid #070b14;
        }

        /* Connection Strip Card */
        .conn-card {
            background: rgba(13, 20, 34, 0.85);
            border: 1px solid #1c2740;
            border-radius: 12px;
            padding: 12px 14px;
            height: 100%;
        }
        .conn-card-down {
            border-left: 3px solid #f43f5e !important;
        }
        .conn-card-ok {
            border-left: 3px solid #22c55e !important;
        }
        .conn-card-degraded {
            border-left: 3px solid #eab308 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Visual Helpers ────────────────────────────────────────────────────────────
def severity_pill(severity: Optional[str]) -> str:
    sev = (severity or "unknown").lower()
    if sev not in {"critical", "high", "medium", "low"}:
        sev = "unknown"
    return f'<span class="pill pill-{sev}">{html.escape(sev)}</span>'


def mitre_chips(techniques: Any) -> str:
    if not techniques:
        return '<span style="color:#6b7280">—</span>'
    if isinstance(techniques, str):
        try:
            techniques = json.loads(techniques)
        except Exception:
            techniques = [techniques]
    if not isinstance(techniques, list) or not techniques:
        return '<span style="color:#6b7280">—</span>'

    chips = [f'<span class="mitre-chip">{html.escape(str(t))}</span>' for t in techniques[:3]]
    if len(techniques) > 3:
        chips.append(f'<span class="mitre-chip">+{len(techniques) - 3}</span>')
    return "".join(chips)


def risk_gauge_svg(score: int) -> str:
    score = max(0, min(100, int(score)))
    if score >= 80:
        color = "#f43f5e"
        level = "CRITICAL"
    elif score >= 60:
        color = "#f97316"
        level = "HIGH"
    elif score >= 35:
        color = "#eab308"
        level = "MEDIUM"
    else:
        color = "#22c55e"
        level = "LOW"

    # SVG circular progress calculation
    radius = 42
    circ = 2 * math.pi * radius
    offset = circ - (score / 100.0) * circ

    return f"""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:10px 0;">
        <svg width="110" height="110" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="{radius}" fill="none" stroke="#1c2740" stroke-width="8"/>
            <circle cx="50" cy="50" r="{radius}" fill="none" stroke="{color}" stroke-width="8"
                    stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"
                    stroke-linecap="round" transform="rotate(-90 50 50)"/>
            <text x="50" y="47" text-anchor="middle" font-size="22" font-weight="700" fill="#e6ecf7" font-family="'JetBrains Mono', monospace">{score}</text>
            <text x="50" y="62" text-anchor="middle" font-size="9" font-weight="700" fill="{color}" letter-spacing="1">{level}</text>
        </svg>
        <span style="font-size:11px; color:#7d8aa5; margin-top:2px;">CORRELATED RISK SCORE</span>
    </div>
    """


def sparkline_svg(values: List[int], stroke_color: str = "#22d3ee", fill_color: str = "rgba(34,211,238,0.15)") -> str:
    if not values or len(values) < 2:
        values = [0, 0]
    width = 110
    height = 28
    max_val = max(max(values), 1)
    min_val = 0

    points = []
    step = width / (len(values) - 1)
    for i, val in enumerate(values):
        x = round(i * step, 1)
        y = round(height - ((val - min_val) / (max_val - min_val) * (height - 6)) - 3, 1)
        points.append(f"{x},{y}")

    poly_pts = " ".join(points)
    area_pts = f"0,{height} " + poly_pts + f" {width},{height}"

    return f"""
    <svg width="{width}" height="{height}" style="overflow:visible;">
        <polygon points="{area_pts}" fill="{fill_color}"/>
        <polyline points="{poly_pts}" fill="none" stroke="{stroke_color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """


# ── Top Bar & Header ──────────────────────────────────────────────────────────
def render_topbar() -> None:
    now_utc = datetime.now(timezone.utc).strftime("%H:%M:%S")
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:flex-end; padding-bottom:12px; border-bottom:1px solid #1c2740; margin-bottom:18px;">
            <div>
                <h2 style="margin:0; font-weight:700; color:#e6ecf7; letter-spacing:-0.02em; font-size:24px;">
                    🛡️ Security Operations Center
                </h2>
                <div style="color:#7d8aa5; font-size:13px; margin-top:3px;">
                    Evidence-first Wazuh monitoring · AI reasoning powered by Groq OpenAI gpt-oss models
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="background:rgba(34,197,94,0.12); color:#22c55e; border:1px solid rgba(34,197,94,0.3); padding:4px 10px; border-radius:9999px; font-size:11px; font-weight:700; letter-spacing:0.05em;">
                    ● LIVE
                </span>
                <span class="mono" style="color:#7d8aa5; font-size:12px;">
                    Last refreshed {now_utc} UTC
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── System Connections Strip (Part 2b) ────────────────────────────────────────
@st.fragment(run_every=60)
def render_system_connections_strip() -> None:
    # Trigger refresh if requested
    refresh_key = st.session_state.pop("_force_conn_refresh", False)
    recheck_clicked = False

    header_col, btn_col = st.columns([6, 1])
    with header_col:
        st.markdown(
            '<div style="font-size:12px; font-weight:600; color:#7d8aa5; letter-spacing:0.06em; text-transform:uppercase; margin-bottom:6px;">'
            'System Connections & Telemetry'
            '</div>',
            unsafe_allow_html=True,
        )
    with btn_col:
        if st.button("↻ Re-check", key="recheck_conn_btn", use_container_width=True):
            refresh_key = True
            recheck_clicked = True

    # Call /api/system/connections
    data: Optional[Dict[str, Any]] = None
    net_err: Optional[str] = None
    try:
        data = api_get(f"/api/system/connections?refresh={'true' if refresh_key else 'false'}")
        st.session_state["_last_system_conn"] = data
    except Exception as exc:
        net_err = str(exc)

    c1, c2, c3, c4 = st.columns(4)

    # 1. Backend API
    with c1:
        if net_err or not data:
            host_str = urlparse(BACKEND_URL).netloc or BACKEND_URL
            st.markdown(
                f"""
                <div class="conn-card conn-card-down">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; font-weight:600; color:#7d8aa5;">BACKEND API</span>
                        <span><span class="status-dot dot-red"></span><span style="font-size:12px; color:#f43f5e; font-weight:600;">Disconnected</span></span>
                    </div>
                    <div class="mono" style="font-size:13px; font-weight:600; color:#e6ecf7; margin-top:4px;">{html.escape(host_str)}</div>
                    <div style="font-size:11px; color:#f43f5e; margin-top:4px;">Backend unreachable at host</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            bk = data.get("backend", {})
            host_str = urlparse(BACKEND_URL).netloc or BACKEND_URL
            status_text = "Connected" if bk.get("status") == "ok" else "Error"
            dot_cls = "dot-green" if bk.get("status") == "ok" else "dot-red"
            border_cls = "conn-card-ok" if bk.get("status") == "ok" else "conn-card-down"
            st.markdown(
                f"""
                <div class="conn-card {border_cls}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; font-weight:600; color:#7d8aa5;">BACKEND API</span>
                        <span><span class="status-dot {dot_cls}"></span><span style="font-size:12px; font-weight:600; color:#e6ecf7;">{status_text}</span></span>
                    </div>
                    <div class="mono" style="font-size:13px; font-weight:600; color:#e6ecf7; margin-top:4px;">{html.escape(host_str)}</div>
                    <div style="font-size:11px; color:#7d8aa5; margin-top:4px;">FastAPI v{html.escape(str(bk.get('version', '1.0')))} · Auth active</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 2. Database
    with c2:
        if net_err or not data:
            st.markdown(
                """
                <div class="conn-card conn-card-down">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; font-weight:600; color:#7d8aa5;">DATABASE</span>
                        <span><span class="status-dot dot-red"></span><span style="font-size:12px; color:#f43f5e; font-weight:600;">Disconnected</span></span>
                    </div>
                    <div style="font-size:13px; font-weight:600; color:#e6ecf7; margin-top:4px;">Unknown</div>
                    <div style="font-size:11px; color:#f43f5e; margin-top:4px;">Backend unreachable</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            db_info = data.get("database", {})
            st_ok = db_info.get("status") == "ok"
            dot_cls = "dot-green" if st_ok else "dot-red"
            border_cls = "conn-card-ok" if st_ok else "conn-card-down"
            engine_str = (db_info.get("engine") or "sqlite").upper()
            lat_str = f"{db_info.get('latency_ms', 0)} ms" if db_info.get("latency_ms") is not None else "—"
            cnt_str = f"{db_info.get('alert_count', 0)} alerts stored"
            st.markdown(
                f"""
                <div class="conn-card {border_cls}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; font-weight:600; color:#7d8aa5;">DATABASE</span>
                        <span><span class="status-dot {dot_cls}"></span><span style="font-size:12px; font-weight:600; color:#e6ecf7;">{'Connected' if st_ok else 'Down'}</span></span>
                    </div>
                    <div class="mono" style="font-size:13px; font-weight:600; color:#e6ecf7; margin-top:4px;">{engine_str} · {lat_str}</div>
                    <div style="font-size:11px; color:#7d8aa5; margin-top:4px;">{cnt_str}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 3. Wazuh SIEM
    with c3:
        if net_err or not data:
            st.markdown(
                """
                <div class="conn-card conn-card-down">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; font-weight:600; color:#7d8aa5;">WAZUH SIEM</span>
                        <span><span class="status-dot dot-red"></span><span style="font-size:12px; color:#f43f5e; font-weight:600;">Disconnected</span></span>
                    </div>
                    <div style="font-size:13px; font-weight:600; color:#e6ecf7; margin-top:4px;">Down</div>
                    <div style="font-size:11px; color:#f43f5e; margin-top:4px;">Check Wazuh credentials</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            wz = data.get("wazuh", {})
            wz_st = wz.get("status", "down")
            if wz_st == "ok":
                dot_cls = "dot-green"
                border_cls = "conn-card-ok"
                st_label = "Connected"
            elif wz_st == "degraded":
                dot_cls = "dot-amber"
                border_cls = "conn-card-degraded"
                st_label = "Degraded"
            else:
                dot_cls = "dot-red"
                border_cls = "conn-card-down"
                st_label = "Disconnected"

            source_str = wz.get("source", "aws").upper()
            mgr_ver = wz.get("manager", {}).get("version", "v4.x")
            idx_st = wz.get("indexer", {}).get("status", "unknown")
            agents = wz.get("agents")
            if agents:
                ag_act = agents.get("active", 0)
                ag_tot = agents.get("total", 0)
                ag_disc = agents.get("disconnected", 0)
                ag_str = f"{ag_act}/{ag_tot} active"
            else:
                ag_str = "Agents summary unavailable"

            st.markdown(
                f"""
                <div class="conn-card {border_cls}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; font-weight:600; color:#7d8aa5;">WAZUH SIEM ({source_str})</span>
                        <span><span class="status-dot {dot_cls}"></span><span style="font-size:12px; font-weight:600; color:#e6ecf7;">{st_label}</span></span>
                    </div>
                    <div class="mono" style="font-size:13px; font-weight:600; color:#e6ecf7; margin-top:4px;">Mgr {html.escape(mgr_ver)} · Idx {html.escape(idx_st)}</div>
                    <div style="font-size:11px; color:#7d8aa5; margin-top:4px;">{html.escape(ag_str)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 4. Groq AI
    with c4:
        if net_err or not data:
            st.markdown(
                """
                <div class="conn-card conn-card-down">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; font-weight:600; color:#7d8aa5;">GROQ AI ENGINE</span>
                        <span><span class="status-dot dot-red"></span><span style="font-size:12px; color:#f43f5e; font-weight:600;">Disconnected</span></span>
                    </div>
                    <div style="font-size:13px; font-weight:600; color:#e6ecf7; margin-top:4px;">Unreachable</div>
                    <div style="font-size:11px; color:#f43f5e; margin-top:4px;">Check backend connection</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            gq = data.get("groq", {})
            gq_st = gq.get("status", "down")
            if gq_st == "ok":
                dot_cls = "dot-green"
                border_cls = "conn-card-ok"
                st_label = "Connected"
            elif gq_st == "not_configured":
                dot_cls = "dot-grey"
                border_cls = "conn-card-down"
                st_label = "Not Configured"
            else:
                dot_cls = "dot-red"
                border_cls = "conn-card-down"
                st_label = "Disconnected"

            lat_str = f"{gq.get('latency_ms', 0)} ms"
            models_list = gq.get("models", [])
            chips_html = "".join(
                [f'<span class="mono" style="font-size:10px; background:rgba(34,211,238,0.1); color:#22d3ee; padding:1px 5px; border-radius:4px; margin-right:3px;">{html.escape(m.split("/")[-1])}</span>' for m in models_list]
            ) or '<span style="color:#7d8aa5; font-size:11px;">No models</span>'

            err_hint = ""
            if gq_st == "down":
                err_hint = f'<div style="font-size:10px; color:#f43f5e; margin-top:3px;">{html.escape(str(gq.get("error", "Check model in .env"))[:60])}</div>'

            st.markdown(
                f"""
                <div class="conn-card {border_cls}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; font-weight:600; color:#7d8aa5;">GROQ AI ENGINE</span>
                        <span><span class="status-dot {dot_cls}"></span><span style="font-size:12px; font-weight:600; color:#e6ecf7;">{st_label}</span></span>
                    </div>
                    <div class="mono" style="font-size:12px; font-weight:600; color:#e6ecf7; margin-top:4px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                        {chips_html}
                    </div>
                    <div style="font-size:11px; color:#7d8aa5; margin-top:4px;">{lat_str} API ping latency</div>
                    {err_hint}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)


# ── KPI Row ───────────────────────────────────────────────────────────────────
def render_kpis(summary: Dict[str, Any], alerts_sample: List[Dict[str, Any]]) -> None:
    sev = summary.get("severity_counts", {})
    alert_count = summary.get("alert_count", 0)
    open_incidents = summary.get("open_incident_count", 0)
    high_count = sev.get("high", 0)
    crit_count = sev.get("critical", 0)
    high_crit = high_count + crit_count

    # Compute unique agents
    unique_agents = {a.get("agent_name") for a in alerts_sample if a.get("agent_name")}
    active_agents = len(unique_agents) if unique_agents else 1

    # Latest timestamp
    latest_ts = str(summary.get("latest_alert_timestamp", "-"))
    if "T" in latest_ts:
        time_part = latest_ts.split("T")[1][:8]
        date_part = latest_ts.split("T")[0]
    else:
        time_part = latest_ts[:8] if len(latest_ts) >= 8 else "-"
        date_part = ""

    # Synthetic hourly sparkline data from alerts_sample if available
    spark_vals = [0] * 12
    if alerts_sample:
        for a in alerts_sample:
            ts_str = a.get("timestamp") or ""
            if "T" in ts_str:
                try:
                    hour = int(ts_str.split("T")[1][:2])
                    spark_vals[hour % 12] += 1
                except Exception:
                    pass

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        sp_svg = sparkline_svg(spark_vals, "#22d3ee", "rgba(34,211,238,0.12)")
        st.markdown(
            f"""
            <div class="soc-card kpi-card">
                <div class="kpi-strip strip-cyan"></div>
                <div style="color:#7d8aa5; font-size:11px; font-weight:600; letter-spacing:0.06em; text-transform:uppercase;">Total Stored Alerts</div>
                <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:8px;">
                    <span class="mono" style="font-size:28px; font-weight:700; color:#22d3ee; line-height:1;">{alert_count:,}</span>
                    <div>{sp_svg}</div>
                </div>
                <div style="font-size:11px; color:#7d8aa5; margin-top:8px;">Continuous SIEM ingestion</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        sp_svg = sparkline_svg([max(1, open_incidents)] * 6, "#f97316", "rgba(249,115,22,0.12)")
        st.markdown(
            f"""
            <div class="soc-card kpi-card">
                <div class="kpi-strip strip-orange"></div>
                <div style="color:#7d8aa5; font-size:11px; font-weight:600; letter-spacing:0.06em; text-transform:uppercase;">Open Incidents</div>
                <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:8px;">
                    <span class="mono" style="font-size:28px; font-weight:700; color:#f97316; line-height:1;">{open_incidents}</span>
                    <div>{sp_svg}</div>
                </div>
                <div style="font-size:11px; color:#7d8aa5; margin-top:8px;">Active correlated clusters</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        sp_svg = sparkline_svg([crit_count, high_count, crit_count + 1, high_count], "#f43f5e", "rgba(244,63,94,0.12)")
        val_color = "#f43f5e" if high_crit > 0 else "#e6ecf7"
        st.markdown(
            f"""
            <div class="soc-card kpi-card">
                <div class="kpi-strip strip-red"></div>
                <div style="color:#7d8aa5; font-size:11px; font-weight:600; letter-spacing:0.06em; text-transform:uppercase;">High / Critical Alerts</div>
                <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:8px;">
                    <span class="mono" style="font-size:28px; font-weight:700; color:{val_color}; line-height:1;">{high_crit}</span>
                    <div>{sp_svg}</div>
                </div>
                <div style="font-size:11px; color:#f43f5e; margin-top:8px;">{crit_count} Critical · {high_count} High</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        sp_svg = sparkline_svg([active_agents] * 6, "#3b82f6", "rgba(59,130,246,0.12)")
        st.markdown(
            f"""
            <div class="soc-card kpi-card">
                <div class="kpi-strip strip-cyan"></div>
                <div style="color:#7d8aa5; font-size:11px; font-weight:600; letter-spacing:0.06em; text-transform:uppercase;">Active Monitored Hosts</div>
                <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:8px;">
                    <span class="mono" style="font-size:28px; font-weight:700; color:#3b82f6; line-height:1;">{active_agents}</span>
                    <div>{sp_svg}</div>
                </div>
                <div style="font-size:11px; color:#7d8aa5; margin-top:8px;">Connected endpoint agents</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c5:
        st.markdown(
            f"""
            <div class="soc-card kpi-card">
                <div class="kpi-strip strip-violet"></div>
                <div style="color:#7d8aa5; font-size:11px; font-weight:600; letter-spacing:0.06em; text-transform:uppercase;">Latest Activity</div>
                <div style="margin-top:8px;">
                    <span class="mono" style="font-size:24px; font-weight:700; color:#c4b5fd; line-height:1;">{time_part}</span>
                </div>
                <div class="mono" style="font-size:11px; color:#7d8aa5; margin-top:8px;">{date_part} UTC</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Render Error Card ─────────────────────────────────────────────────────────
def render_error_card(title: str, detail: str, hint: Optional[str] = None) -> None:
    st.markdown(
        f"""
        <div style="background:rgba(244,63,94,0.1); border:1px solid #f43f5e; border-radius:12px; padding:16px; margin:12px 0;">
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size:18px;">⚠️</span>
                <span style="font-weight:700; color:#f43f5e; font-size:14px;">{html.escape(title)}</span>
            </div>
            <div class="mono" style="font-size:12px; color:#fca5a5; margin-top:8px; white-space:pre-wrap; word-break:break-all;">{html.escape(detail)}</div>
            {f'<div style="font-size:11px; color:#7d8aa5; margin-top:8px; border-top:1px solid rgba(244,63,94,0.2); padding-top:6px;">💡 <b>Recommendation:</b> {html.escape(hint)}</div>' if hint else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Navigation / Sidebar ──────────────────────────────────────────────────────
def render_sidebar(summary: Dict[str, Any]) -> str:
    alert_count = summary.get("alert_count", 0)
    open_incidents = summary.get("open_incident_count", 0)

    with st.sidebar:
        # Brand Logo block
        st.markdown(
            """
            <div style="display:flex; align-items:center; gap:12px; padding:12px 6px 20px 6px; border-bottom:1px solid #1c2740; margin-bottom:16px;">
                <div style="width:40px; height:40px; border-radius:10px; background:linear-gradient(135deg, #22d3ee 0%, #8b5cf6 100%); display:flex; align-items:center; justify-content:center; box-shadow:0 0 16px rgba(34,211,238,0.4);">
                    <span style="font-size:22px;">🛡️</span>
                </div>
                <div>
                    <div style="font-weight:800; font-size:16px; letter-spacing:0.04em; color:#e6ecf7; line-height:1.1;">SENTINEL AI</div>
                    <div style="font-size:11px; font-weight:600; color:#22d3ee; letter-spacing:0.08em;">SOC PLATFORM</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_options = [
            "SOC Overview",
            f"Alerts ({alert_count})",
            f"Incidents ({open_incidents})",
            "Investigation",
            "── AI WORKSPACE ──",
            "AI Analyst",
            "Response Plan",
            "Reports",
            "── INTELLIGENCE ──",
            "Threat Context",
            "System Health",
        ]

        # Filter out separators for index tracking
        selectable = [opt for opt in nav_options if not opt.startswith("──")]

        # Default or restore
        current_nav = st.session_state.get("_active_page", "SOC Overview")
        if current_nav not in selectable:
            current_nav = "SOC Overview"

        choice = st.radio(
            "Navigation",
            options=selectable,
            index=selectable.index(current_nav) if current_nav in selectable else 0,
            label_visibility="collapsed",
        )
        st.session_state["_active_page"] = choice

        # Spacer
        st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

        # Footer Status Card
        conn_data = st.session_state.get("_last_system_conn", {})
        wz_st = conn_data.get("wazuh", {}).get("status", "ok") if conn_data else "ok"
        gq_st = conn_data.get("groq", {}).get("status", "ok") if conn_data else "ok"
        gq_models = conn_data.get("groq", {}).get("models", []) if conn_data else []
        active_model = gq_models[0].split("/")[-1] if gq_models else "gpt-oss-20b"

        wz_dot = "dot-green" if wz_st == "ok" else ("dot-amber" if wz_st == "degraded" else "dot-red")
        gq_dot = "dot-green" if gq_st == "ok" else "dot-red"

        st.markdown(
            f"""
            <div style="background:#0d1422; border:1px solid #1c2740; border-radius:12px; padding:12px; margin-top:20px;">
                <div style="font-size:10px; font-weight:700; color:#7d8aa5; letter-spacing:0.06em; text-transform:uppercase; margin-bottom:8px;">Live Telemetry</div>
                <div style="display:flex; align-items:center; margin-bottom:6px;">
                    <span class="status-dot {wz_dot}"></span>
                    <span style="font-size:12px; color:#e6ecf7;">Wazuh SIEM connected</span>
                </div>
                <div style="display:flex; align-items:center; margin-bottom:6px;">
                    <span class="status-dot {gq_dot}"></span>
                    <span class="mono" style="font-size:12px; color:#22d3ee;">Groq · {html.escape(active_model)}</span>
                </div>
                <div style="border-top:1px solid #1c2740; padding-top:6px; margin-top:6px; font-size:10px; color:#7d8aa5;">
                    🔄 Auto-refreshes every 2 min
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return choice


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1: SOC OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
@st.fragment(run_every=120)
def page_soc_overview(summary: Dict[str, Any]) -> None:
    # 1. Fetch latest alerts for feed & sparklines
    alerts_data: List[Dict[str, Any]] = []
    try:
        res = api_get("/api/alerts", params={"limit": 100, "offset": 0})
        alerts_data = res.get("items", [])
    except Exception as exc:
        st.warning(f"Could not load alerts: {exc}")

    # 2. System Connections Strip
    render_system_connections_strip()

    # 3. KPI Row
    render_kpis(summary, alerts_data)

    col_left, col_right = st.columns([1.55, 1])

    # ── Left Column: Live Feed & Charts ──
    with col_left:
        # Live Alert Feed Card
        sev_counts = summary.get("severity_counts", {})
        crit = sev_counts.get("critical", 0)
        high = sev_counts.get("high", 0)
        med = sev_counts.get("medium", 0)
        low = sev_counts.get("low", 0)

        pills_header = f"""
        <div style="display:flex; align-items:center; gap:8px;">
            <span class="pill pill-critical">{crit} CRITICAL</span>
            <span class="pill pill-high">{high} HIGH</span>
            <span class="pill pill-medium">{med} MEDIUM</span>
            <span class="pill pill-low">{low} LOW</span>
        </div>
        """

        feed_rows = []
        for a in alerts_data[:10]:
            ts_str = (a.get("timestamp") or "-")[:19].replace("T", " ")
            sev_pill = severity_pill(a.get("severity"))
            desc = html.escape(str(a.get("rule_description") or a.get("rule_id") or "Alert"))
            host = html.escape(str(a.get("agent_name") or a.get("agent_id") or "—"))
            src_ip = html.escape(str(a.get("src_ip") or "—"))
            lvl = html.escape(str(a.get("rule_level") or "—"))
            m_chips = mitre_chips(a.get("mitre_techniques"))

            feed_rows.append(
                f"""
                <tr>
                    <td class="mono" style="color:#7d8aa5; font-size:11px; white-space:nowrap;">{ts_str}</td>
                    <td>{sev_pill}</td>
                    <td style="max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="{desc}">{desc}</td>
                    <td class="mono" style="color:#c4b5fd;">{host}</td>
                    <td class="mono" style="color:#22d3ee;">{src_ip}</td>
                    <td>{m_chips}</td>
                    <td class="mono" style="text-align:center; font-weight:700;">{lvl}</td>
                </tr>
                """
            )

        table_content = "".join(feed_rows) or "<tr><td colspan='7' style='text-align:center; color:#7d8aa5;'>No alerts ingested yet</td></tr>"

        st.markdown(
            f"""
            <div class="soc-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                    <div>
                        <div style="font-size:14px; font-weight:700; color:#e6ecf7;">LIVE INGESTION ALERT FEED</div>
                        <div style="font-size:11px; color:#7d8aa5;">Real-time Wazuh normalized events stream</div>
                    </div>
                    {pills_header}
                </div>
                <div style="overflow-x:auto;">
                    <table class="soc-table">
                        <thead>
                            <tr>
                                <th>TIME (UTC)</th>
                                <th>SEVERITY</th>
                                <th>RULE DESCRIPTION</th>
                                <th>HOST</th>
                                <th>SOURCE IP</th>
                                <th>MITRE ATT&CK</th>
                                <th style="text-align:center;">LVL</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_content}
                        </tbody>
                    </table>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Bottom Two Cards: 24h Alert Volume & MITRE Coverage
        c_vol, c_mitre = st.columns(2)

        with c_vol:
            st.markdown(
                """
                <div class="soc-card" style="margin-bottom:0;">
                    <div style="font-size:13px; font-weight:700; color:#e6ecf7; margin-bottom:4px;">ALERT VOLUME · 24H</div>
                    <div style="font-size:11px; color:#7d8aa5; margin-bottom:10px;">Aggregated alerts per hour</div>
                """,
                unsafe_allow_html=True,
            )

            # Build Hourly Volume DataFrame
            hours_dict: Dict[str, int] = {f"{h:02d}:00": 0 for h in range(24)}
            for a in alerts_data:
                ts_str = a.get("timestamp") or ""
                if "T" in ts_str:
                    try:
                        h_key = f"{int(ts_str.split('T')[1][:2]):02d}:00"
                        hours_dict[h_key] = hours_dict.get(h_key, 0) + 1
                    except Exception:
                        pass

            vol_df = pd.DataFrame({"Hour": list(hours_dict.keys()), "Alerts": list(hours_dict.values())})
            busy_threshold = vol_df["Alerts"].max() * 0.75 if vol_df["Alerts"].max() > 0 else 100

            # Color bars: high load red, normal cyan
            bar_colors = ["#f43f5e" if val >= busy_threshold and val > 0 else "#22d3ee" for val in vol_df["Alerts"]]

            fig_vol = go.Figure(
                data=[
                    go.Bar(
                        x=vol_df["Hour"],
                        y=vol_df["Alerts"],
                        marker_color=bar_colors,
                        marker_line_width=0,
                        hoverinfo="x+y",
                    )
                ]
            )
            fig_vol.update_layout(
                height=190,
                margin=dict(l=0, r=0, t=10, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, color="#7d8aa5", tickfont=dict(size=9, family="JetBrains Mono")),
                yaxis=dict(showgrid=True, gridcolor="#1c2740", color="#7d8aa5", tickfont=dict(size=9, family="JetBrains Mono")),
            )
            st.plotly_chart(fig_vol, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with c_mitre:
            st.markdown(
                """
                <div class="soc-card" style="margin-bottom:0;">
                    <div style="font-size:13px; font-weight:700; color:#e6ecf7; margin-bottom:4px;">MITRE ATT&CK COVERAGE</div>
                    <div style="font-size:11px; color:#7d8aa5; margin-bottom:10px;">Detected adversary techniques</div>
                """,
                unsafe_allow_html=True,
            )

            # Count MITRE techniques
            mitre_counts: Dict[str, int] = {}
            for a in alerts_data:
                techs = a.get("mitre_techniques")
                if isinstance(techs, str):
                    try:
                        techs = json.loads(techs)
                    except Exception:
                        techs = [techs]
                if isinstance(techs, list):
                    for t in techs:
                        if t:
                            mitre_counts[t] = mitre_counts.get(t, 0) + 1

            if mitre_counts:
                m_df = pd.DataFrame(
                    [{"Technique": k, "Detections": v} for k, v in sorted(mitre_counts.items(), key=lambda x: x[1], reverse=True)[:8]]
                )
                fig_m = px.bar(
                    m_df,
                    x="Detections",
                    y="Technique",
                    orientation="h",
                    color="Detections",
                    color_continuous_scale=["#3b82f6", "#8b5cf6", "#f97316", "#f43f5e"],
                )
                fig_m.update_layout(
                    height=190,
                    margin=dict(l=0, r=0, t=10, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    coloraxis_showscale=False,
                    xaxis=dict(showgrid=True, gridcolor="#1c2740", color="#7d8aa5", tickfont=dict(size=9, family="JetBrains Mono")),
                    yaxis=dict(showgrid=False, color="#c4b5fd", tickfont=dict(size=10, family="JetBrains Mono"), autorange="reversed"),
                )
                st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})
            else:
                st.markdown(
                    '<div style="height:190px; display:flex; align-items:center; justify-content:center; color:#7d8aa5; font-size:12px;">'
                    'No MITRE ATT&CK techniques in current sample'
                    '</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    # ── Right Column: AI Verdict & Incident Timeline ──
    with col_right:
        # Fetch Incidents
        incidents: List[Dict[str, Any]] = []
        try:
            incidents = api_get("/api/incidents")
        except Exception as exc:
            st.warning(f"Could not load incidents: {exc}")

        # AI Analyst Verdict Card
        st.markdown(
            """
            <div class="soc-card soc-card-border-glow">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div>
                        <div style="font-size:14px; font-weight:700; color:#22d3ee; letter-spacing:0.02em;">⚡ AI ANALYST VERDICT</div>
                        <div style="font-size:11px; color:#7d8aa5;">Groq Automated Correlated Reasoning</div>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        selected_inc_id: Optional[int] = None
        if incidents:
            inc_options = {f"Incident #{inc['id']} · {inc['title'][:32]}...": inc["id"] for inc in incidents}
            inc_label = st.selectbox("Select Target Incident", options=list(inc_options.keys()), label_visibility="collapsed")
            selected_inc_id = inc_options[inc_label]
        else:
            st.info("No correlated incidents recorded yet.")

        # Load Full Details for Selected Incident
        inc_obj: Optional[Dict[str, Any]] = None
        if selected_inc_id is not None:
            try:
                inc_obj = api_get(f"/api/incidents/{selected_inc_id}")
            except Exception as exc:
                st.error(f"Failed to fetch incident #{selected_inc_id}: {exc}")

        if inc_obj:
            inc_sev = inc_obj.get("severity", "medium").lower()
            repeat_count = inc_obj.get("repeat_count", 1)
            linked_alerts = inc_obj.get("alerts", [])
            max_lvl = max([a.get("rule_level", 3) for a in linked_alerts] or [3])

            # Calculate risk gauge score
            base_score = {"critical": 90, "high": 70, "medium": 45, "low": 20}.get(inc_sev, 30)
            score = min(100, base_score + int(max_lvl * 0.8) + min(15, repeat_count * 2))

            # Display Risk Gauge
            st.markdown(risk_gauge_svg(score), unsafe_allow_html=True)

            # Fact Tiles
            conf_val = st.session_state.get(f"_conf_{selected_inc_id}", "HIGH (AI Ver)")
            unique_assets = len({a.get("agent_name") for a in linked_alerts if a.get("agent_name")}) or 1

            st.markdown(
                f"""
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:14px 0;">
                    <div style="background:#111a2c; border:1px solid #1c2740; border-radius:8px; padding:8px 10px;">
                        <div style="font-size:10px; color:#7d8aa5;">SEVERITY</div>
                        <div style="margin-top:2px;">{severity_pill(inc_sev)}</div>
                    </div>
                    <div style="background:#111a2c; border:1px solid #1c2740; border-radius:8px; padding:8px 10px;">
                        <div style="font-size:10px; color:#7d8aa5;">CONFIDENCE</div>
                        <div class="mono" style="font-size:12px; font-weight:700; color:#22d3ee; margin-top:2px;">{html.escape(conf_val)}</div>
                    </div>
                    <div style="background:#111a2c; border:1px solid #1c2740; border-radius:8px; padding:8px 10px;">
                        <div style="font-size:10px; color:#7d8aa5;">AFFECTED ASSETS</div>
                        <div class="mono" style="font-size:13px; font-weight:700; color:#e6ecf7; margin-top:2px;">{unique_assets} Endpoint(s)</div>
                    </div>
                    <div style="background:#111a2c; border:1px solid #1c2740; border-radius:8px; padding:8px 10px;">
                        <div style="font-size:10px; color:#7d8aa5;">LINKED EVENTS</div>
                        <div class="mono" style="font-size:13px; font-weight:700; color:#e6ecf7; margin-top:2px;">{len(linked_alerts)} Alerts</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Cached or generated finding text
            stored_finding = st.session_state.get(f"_triage_finding_{selected_inc_id}")
            if stored_finding:
                st.markdown(
                    f"""
                    <div style="background:rgba(34,211,238,0.06); border:1px solid rgba(34,211,238,0.25); border-radius:8px; padding:10px; font-size:12px; color:#e6ecf7; margin-bottom:12px;">
                        <div style="color:#22d3ee; font-weight:700; font-size:11px; margin-bottom:4px;">LATEST AI FINDING:</div>
                        {html.escape(stored_finding)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div style="font-size:12px; color:#7d8aa5; margin-bottom:12px; font-style:italic;">'
                    'No AI analysis recorded yet for this incident. Click "Run AI Triage" below.'
                    '</div>',
                    unsafe_allow_html=True,
                )

            # Action Buttons Row
            b_col1, b_col2, b_col3 = st.columns(3)
            with b_col1:
                if st.button("⚡ Run AI Triage", key=f"btn_triage_{selected_inc_id}", use_container_width=True):
                    with st.spinner("AI evaluating evidence..."):
                        try:
                            t_res = api_post(f"/api/incidents/{selected_inc_id}/analyze", {"task": "triage", "force": True})
                            if t_res.get("status") == "AI analysis unavailable":
                                render_error_card("AI Analysis Unavailable", t_res.get("detail", "Error"), "Check LLM models in backend")
                            else:
                                finding = t_res.get("result", {}).get("finding", "Triage completed successfully.")
                                conf = t_res.get("result", {}).get("confidence_label", "HIGH")
                                st.session_state[f"_triage_finding_{selected_inc_id}"] = finding
                                st.session_state[f"_conf_{selected_inc_id}"] = conf.upper()
                                st.session_state[f"_triage_res_{selected_inc_id}"] = t_res
                                st.rerun()
                        except Exception as e:
                            render_error_card("Triage Request Failed", str(e))
            with b_col2:
                if st.button("🛡️ Response Plan", key=f"btn_resp_{selected_inc_id}", use_container_width=True):
                    st.session_state["_active_incident_id"] = selected_inc_id
                    st.session_state["_active_page"] = "Response Plan"
                    st.rerun()
            with b_col3:
                if st.button("📄 Executive Report", key=f"btn_rep_{selected_inc_id}", use_container_width=True):
                    st.session_state["_active_incident_id"] = selected_inc_id
                    st.session_state["_active_page"] = "Reports"
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # Incident Timeline Card
        if inc_obj and inc_obj.get("alerts"):
            st.markdown(
                """
                <div class="soc-card">
                    <div style="font-size:13px; font-weight:700; color:#e6ecf7; margin-bottom:12px;">INCIDENT ATTACK TIMELINE</div>
                """,
                unsafe_allow_html=True,
            )

            # Sort alerts chronologically
            sorted_alerts = sorted(inc_obj.get("alerts", []), key=lambda x: str(x.get("timestamp") or ""))
            timeline_items = []
            for a in sorted_alerts[:8]:
                a_sev = (a.get("severity") or "unknown").lower()
                sev_color = {"critical": "#f43f5e", "high": "#f97316", "medium": "#eab308", "low": "#22c55e"}.get(a_sev, "#6b7280")
                a_ts = (a.get("timestamp") or "-")[:19].replace("T", " ")
                a_desc = html.escape(str(a.get("rule_description") or a.get("rule_id") or "Alert"))
                a_host = html.escape(str(a.get("agent_name") or a.get("src_ip") or "Endpoint"))

                timeline_items.append(
                    f"""
                    <div class="timeline-item">
                        <div class="timeline-node" style="background:{sev_color}; box-shadow:0 0 8px {sev_color};"></div>
                        <div class="mono" style="font-size:11px; color:#7d8aa5;">{a_ts}</div>
                        <div style="font-size:12px; font-weight:600; color:#e6ecf7; margin-top:2px;">{a_desc}</div>
                        <div class="mono" style="font-size:11px; color:#c4b5fd;">Host/IP: {a_host}</div>
                    </div>
                    """
                )

            st.markdown("".join(timeline_items) + "</div>", unsafe_allow_html=True)

    # ── Bottom Section: Trigger Manual Ingestion ──
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    ingest_col1, ingest_col2 = st.columns([1, 3])
    with ingest_col1:
        if st.button("⚡ Trigger Manual Ingestion", use_container_width=True):
            with st.spinner("Executing Wazuh SIEM ingestion & correlation..."):
                try:
                    res = api_post("/api/ingestion/run")
                    st.toast(
                        f"✅ Ingestion complete: fetched={res.get('fetched', 0)} stored={res.get('stored', 0)} "
                        f"simulated={res.get('simulated', 0)} dupes={res.get('duplicates', 0)}",
                        icon="🛡️",
                    )
                    time.sleep(1)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Manual ingestion failed: {exc}")
    with ingest_col2:
        st.caption("Manual ingestion immediately scans Wazuh indexer/API for fresh security events and auto-simulates attacks if SIEM is quiet.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2: ALERTS EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
def page_alerts() -> None:
    st.markdown("### 📋 Security Alerts Explorer")
    st.caption("Search, filter, and inspect normalized Wazuh SIEM security events.")

    # Filter controls
    f_col1, f_col2, f_col3 = st.columns([1.5, 2.5, 1])
    with f_col1:
        sev_filter = st.selectbox("Severity Filter", options=["All", "critical", "high", "medium", "low", "unknown"])
    with f_col2:
        search_query = st.text_input("Search (Rule / Host / Source IP / User)", placeholder="e.g. pam, root, 10.144...")
    with f_col3:
        page_limit = st.selectbox("Page Size", options=[15, 30, 50, 100], index=0)

    # Pagination state
    page_num = st.session_state.get("_alerts_page_num", 1)
    offset = (page_num - 1) * page_limit

    # Query Backend
    params: Dict[str, Any] = {"limit": page_limit, "offset": offset}
    if sev_filter != "All":
        params["severity"] = sev_filter

    try:
        data = api_get("/api/alerts", params=params)
        items = data.get("items", [])
        total = data.get("total", len(items))
    except Exception as exc:
        render_error_card("Failed to load alerts", str(exc))
        return

    # Client-side search filtering if entered
    if search_query.strip():
        q = search_query.strip().lower()
        items = [
            a for a in items
            if q in str(a.get("rule_description", "")).lower()
            or q in str(a.get("agent_name", "")).lower()
            or q in str(a.get("src_ip", "")).lower()
            or q in str(a.get("src_user", "")).lower()
        ]

    # Render Alerts Table
    st.markdown(
        f'<div style="font-size:12px; color:#7d8aa5; margin-bottom:8px;">Showing {len(items)} of {total} alerts</div>',
        unsafe_allow_html=True,
    )

    feed_rows = []
    for a in items:
        a_id = a.get("id")
        ts_str = (a.get("timestamp") or "-")[:19].replace("T", " ")
        sev_pill = severity_pill(a.get("severity"))
        desc = html.escape(str(a.get("rule_description") or a.get("rule_id") or "Alert"))
        host = html.escape(str(a.get("agent_name") or a.get("agent_id") or "—"))
        src_ip = html.escape(str(a.get("src_ip") or "—"))
        lvl = html.escape(str(a.get("rule_level") or "—"))
        m_chips = mitre_chips(a.get("mitre_techniques"))

        feed_rows.append(
            f"""
            <tr>
                <td class="mono" style="color:#7d8aa5;">#{a_id}</td>
                <td class="mono" style="color:#7d8aa5; font-size:11px; white-space:nowrap;">{ts_str}</td>
                <td>{sev_pill}</td>
                <td style="max-width:320px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="{desc}">{desc}</td>
                <td class="mono" style="color:#c4b5fd;">{host}</td>
                <td class="mono" style="color:#22d3ee;">{src_ip}</td>
                <td>{m_chips}</td>
                <td class="mono" style="text-align:center; font-weight:700;">{lvl}</td>
            </tr>
            """
        )

    table_content = "".join(feed_rows) or "<tr><td colspan='8' style='text-align:center; color:#7d8aa5;'>No matching alerts</td></tr>"
    st.markdown(
        f"""
        <div class="soc-card">
            <div style="overflow-x:auto;">
                <table class="soc-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>TIMESTAMP (UTC)</th>
                            <th>SEVERITY</th>
                            <th>RULE DESCRIPTION</th>
                            <th>HOST</th>
                            <th>SRC IP</th>
                            <th>MITRE ATT&CK</th>
                            <th style="text-align:center;">LVL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_content}
                    </tbody>
                </table>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Pagination Buttons
    max_pages = max(1, math.ceil(total / page_limit))
    p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
    with p_col1:
        if st.button("◀ Previous Page", disabled=(page_num <= 1), use_container_width=True):
            st.session_state["_alerts_page_num"] = page_num - 1
            st.rerun()
    with p_col2:
        st.markdown(f"<div style='text-align:center; color:#7d8aa5; font-size:13px; padding-top:8px;'>Page <b>{page_num}</b> of <b>{max_pages}</b></div>", unsafe_allow_html=True)
    with p_col3:
        if st.button("Next Page ▶", disabled=(page_num >= max_pages), use_container_width=True):
            st.session_state["_alerts_page_num"] = page_num + 1
            st.rerun()

    # Alert Inspector
    st.markdown("---")
    st.subheader("🔍 Deep Alert Inspector")
    alert_inspect_id = st.number_input("Enter Alert ID to inspect raw JSON payload", min_value=1, step=1, value=items[0].get("id", 1) if items else 1)
    if st.button("Inspect Raw Alert"):
        try:
            inspect_data = api_get(f"/api/alerts/{alert_inspect_id}")
            st.json(inspect_data)
        except Exception as exc:
            st.error(f"Alert #{alert_inspect_id} not found: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3: INCIDENTS
# ══════════════════════════════════════════════════════════════════════════════
def page_incidents() -> None:
    st.markdown("### 🚨 Correlated Security Incidents")
    st.caption("Automated attack clustering by host, IP fingerprint, and correlation windows.")

    try:
        incidents = api_get("/api/incidents")
    except Exception as exc:
        render_error_card("Failed to load incidents", str(exc))
        return

    if not incidents:
        st.info("No correlated incidents recorded. Ingestion poller continuously evaluates alerts.")
        return

    st.markdown(f'<div style="color:#7d8aa5; font-size:13px; margin-bottom:14px;">Total Correlated Incidents: <b>{len(incidents)}</b></div>', unsafe_allow_html=True)

    # Grid layout: 2 cards per row
    for i in range(0, len(incidents), 2):
        row_incs = incidents[i : i + 2]
        cols = st.columns(2)
        for idx, inc in enumerate(row_incs):
            inc_id = inc.get("id")
            title = html.escape(str(inc.get("title", "Security Incident")))
            sev = inc.get("severity", "medium").lower()
            status = html.escape(str(inc.get("status", "open")).upper())
            first_seen = (inc.get("first_seen") or "-")[:19].replace("T", " ")
            last_seen = (inc.get("last_seen") or "-")[:19].replace("T", " ")
            repeat_cnt = inc.get("repeat_count", 1)

            with cols[idx]:
                st.markdown(
                    f"""
                    <div class="soc-card">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <div>
                                <span class="mono" style="font-size:12px; color:#22d3ee; font-weight:700;">INCIDENT #{inc_id}</span>
                                <h4 style="margin:4px 0 8px 0; color:#e6ecf7; font-size:15px;">{title}</h4>
                            </div>
                            <div style="text-align:right;">
                                {severity_pill(sev)}
                                <div class="mono" style="font-size:10px; color:#7d8aa5; margin-top:4px;">STATUS: {status}</div>
                            </div>
                        </div>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin:12px 0; font-size:11px;">
                            <div><span style="color:#7d8aa5;">FIRST SEEN:</span> <span class="mono" style="color:#e6ecf7;">{first_seen}</span></div>
                            <div><span style="color:#7d8aa5;">LAST SEEN:</span> <span class="mono" style="color:#e6ecf7;">{last_seen}</span></div>
                            <div><span style="color:#7d8aa5;">REPEATS:</span> <span class="mono" style="color:#22d3ee; font-weight:700;">{repeat_cnt}x</span></div>
                        </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(f"🔍 Investigate Incident #{inc_id}", key=f"inv_btn_{inc_id}", use_container_width=True):
                    st.session_state["_active_incident_id"] = inc_id
                    st.session_state["_active_page"] = "Investigation"
                    st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4: INVESTIGATION
# ══════════════════════════════════════════════════════════════════════════════
def page_investigation() -> None:
    st.markdown("### 🔬 Incident Deep-Dive & Root-Cause Analysis")

    try:
        incidents = api_get("/api/incidents")
    except Exception as exc:
        render_error_card("Failed to load incidents", str(exc))
        return

    if not incidents:
        st.info("No incidents available for investigation.")
        return

    default_id = st.session_state.get("_active_incident_id", incidents[0]["id"])
    inc_options = {f"Incident #{inc['id']} · {inc['title'][:40]}": inc["id"] for inc in incidents}
    default_index = 0
    for idx, (lbl, iid) in enumerate(inc_options.items()):
        if iid == default_id:
            default_index = idx
            break

    sel_label = st.selectbox("Select Incident to Investigate", options=list(inc_options.keys()), index=default_index)
    incident_id = inc_options[sel_label]
    st.session_state["_active_incident_id"] = incident_id

    # Fetch incident details
    try:
        inc_data = api_get(f"/api/incidents/{incident_id}")
    except Exception as exc:
        render_error_card(f"Failed to fetch incident #{incident_id}", str(exc))
        return

    # Header Card
    sev = inc_data.get("severity", "medium").lower()
    title = html.escape(inc_data.get("title", ""))
    first_seen = (inc_data.get("first_seen") or "-")[:19].replace("T", " ")
    last_seen = (inc_data.get("last_seen") or "-")[:19].replace("T", " ")
    linked_alerts = inc_data.get("alerts", [])

    st.markdown(
        f"""
        <div class="soc-card soc-card-border-glow">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span class="mono" style="font-size:12px; color:#22d3ee; font-weight:700;">INVESTIGATING INCIDENT #{incident_id}</span>
                    <h3 style="margin:4px 0; color:#e6ecf7;">{title}</h3>
                    <div style="font-size:12px; color:#7d8aa5;">
                        Span: <span class="mono" style="color:#c4b5fd;">{first_seen}</span> to <span class="mono" style="color:#c4b5fd;">{last_seen}</span> UTC
                    </div>
                </div>
                <div>{severity_pill(sev)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Action: Run AI Investigation
    if st.button("⚡ Run AI Deep-Dive Investigation", use_container_width=True):
        with st.spinner("AI analyzing attack trajectory and next steps..."):
            try:
                res = api_post(f"/api/incidents/{incident_id}/analyze", {"task": "investigation", "force": True})
                if res.get("status") == "AI analysis unavailable":
                    render_error_card("AI Investigation Unavailable", res.get("detail", "Error"), "Check model in .env")
                else:
                    st.session_state[f"_inv_res_{incident_id}"] = res.get("result", {})
                    st.rerun()
            except Exception as exc:
                render_error_card("Investigation Failed", str(exc))

    # Display AI Investigation Results if cached
    inv_result = st.session_state.get(f"_inv_res_{incident_id}")
    if inv_result:
        st.markdown(
            f"""
            <div class="soc-card">
                <div style="font-size:14px; font-weight:700; color:#22d3ee; margin-bottom:8px;">AI INVESTIGATION SUMMARY</div>
                <div style="font-size:13px; color:#e6ecf7; line-height:1.5; margin-bottom:14px;">
                    {html.escape(inv_result.get('timeline_summary') or inv_result.get('finding') or '')}
                </div>
                <div style="font-size:13px; font-weight:700; color:#c4b5fd; margin-bottom:8px;">RECOMMENDED NEXT INVESTIGATION STEPS:</div>
            """,
            unsafe_allow_html=True,
        )
        steps = inv_result.get("next_investigation_steps") or inv_result.get("recommended_actions") or []
        for step_idx, step in enumerate(steps, start=1):
            st.markdown(
                f"""
                <div style="display:flex; align-items:flex-start; gap:10px; margin-bottom:8px;">
                    <div class="mono" style="background:#1c2740; color:#22d3ee; border-radius:50%; width:22px; height:22px; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:700; flex-shrink:0;">{step_idx}</div>
                    <div style="font-size:12px; color:#e6ecf7; line-height:1.4;">{html.escape(str(step))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # Linked Alerts Table
    st.subheader(f"Linked SIEM Alerts ({len(linked_alerts)})")
    feed_rows = []
    for a in linked_alerts:
        ts_str = (a.get("timestamp") or "-")[:19].replace("T", " ")
        sev_pill = severity_pill(a.get("severity"))
        desc = html.escape(str(a.get("rule_description") or a.get("rule_id") or "Alert"))
        host = html.escape(str(a.get("agent_name") or a.get("agent_id") or "—"))
        src_ip = html.escape(str(a.get("src_ip") or "—"))
        lvl = html.escape(str(a.get("rule_level") or "—"))

        feed_rows.append(
            f"""
            <tr>
                <td class="mono" style="color:#7d8aa5; font-size:11px;">{ts_str}</td>
                <td>{sev_pill}</td>
                <td>{desc}</td>
                <td class="mono" style="color:#c4b5fd;">{host}</td>
                <td class="mono" style="color:#22d3ee;">{src_ip}</td>
                <td class="mono" style="text-align:center; font-weight:700;">{lvl}</td>
            </tr>
            """
        )

    table_content = "".join(feed_rows) or "<tr><td colspan='6' style='text-align:center; color:#7d8aa5;'>No linked alerts</td></tr>"
    st.markdown(
        f"""
        <div class="soc-card">
            <table class="soc-table">
                <thead>
                    <tr>
                        <th>TIME</th>
                        <th>SEVERITY</th>
                        <th>DESCRIPTION</th>
                        <th>HOST</th>
                        <th>SRC IP</th>
                        <th style="text-align:center;">LVL</th>
                    </tr>
                </thead>
                <tbody>
                    {table_content}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5: AI ANALYST WORKSPACE
# ══════════════════════════════════════════════════════════════════════════════
def page_ai_analyst() -> None:
    st.markdown("### 🤖 Multi-Perspective AI Analyst")
    st.caption("Direct interaction with Groq reasoning engines across Triage, Investigation, and Manager Explanations.")

    try:
        incidents = api_get("/api/incidents")
    except Exception as exc:
        render_error_card("Failed to load incidents", str(exc))
        return

    if not incidents:
        st.info("No incidents available.")
        return

    c1, c2, c3 = st.columns([2, 1.5, 1])
    with c1:
        inc_options = {f"Incident #{inc['id']} · {inc['title'][:40]}": inc["id"] for inc in incidents}
        sel_label = st.selectbox("Select Target Incident", options=list(inc_options.keys()))
        incident_id = inc_options[sel_label]
    with c2:
        task_choice = st.selectbox("AI Reasoning Task", options=["triage", "investigation", "manager"])
    with c3:
        force_run = st.checkbox("Force Fresh Evaluation", value=True)

    if st.button("⚡ Execute AI Analysis", use_container_width=True):
        with st.spinner(f"Groq generating {task_choice} analysis..."):
            try:
                res = api_post(f"/api/incidents/{incident_id}/analyze", {"task": task_choice, "force": force_run})
                if res.get("status") == "AI analysis unavailable":
                    render_error_card(
                        f"AI {task_choice.title()} Unavailable",
                        res.get("detail", "Error"),
                        "Check configured LLM models in .env and restart backend",
                    )
                else:
                    st.session_state[f"_ai_analyst_res_{incident_id}_{task_choice}"] = res
                    st.rerun()
            except Exception as exc:
                render_error_card("Analysis Failed", str(exc))

    # Display results
    cached_res = st.session_state.get(f"_ai_analyst_res_{incident_id}_{task_choice}")
    if cached_res:
        res_data = cached_res.get("result", {})
        conf_pill = f'<span class="pill pill-high">{html.escape(str(res_data.get("confidence_label", "high")).upper())}</span>'
        finding_text = html.escape(str(res_data.get("finding", "Analysis complete.")))

        st.markdown(
            f"""
            <div class="soc-card soc-card-border-glow" style="margin-top:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div style="font-size:14px; font-weight:700; color:#22d3ee; text-transform:uppercase;">
                        {html.escape(task_choice)} Verdict
                    </div>
                    <div>Confidence: {conf_pill}</div>
                </div>
                <div style="font-size:14px; color:#e6ecf7; line-height:1.5; margin-bottom:14px;">
                    {finding_text}
                </div>
            """,
            unsafe_allow_html=True,
        )

        # Manager specific fields
        if task_choice == "manager":
            wh = html.escape(str(res_data.get("what_happened", "N/A")))
            why = html.escape(str(res_data.get("why_it_might_matter", "N/A")))
            aff = res_data.get("affected_systems", [])
            st.markdown(
                f"""
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px;">
                    <div style="background:#111a2c; border:1px solid #1c2740; border-radius:8px; padding:12px;">
                        <div style="font-size:11px; font-weight:700; color:#22d3ee; margin-bottom:4px;">WHAT HAPPENED</div>
                        <div style="font-size:12px; color:#e6ecf7;">{wh}</div>
                    </div>
                    <div style="background:#111a2c; border:1px solid #1c2740; border-radius:8px; padding:12px;">
                        <div style="font-size:11px; font-weight:700; color:#f97316; margin-bottom:4px;">WHY IT MATTERS</div>
                        <div style="font-size:12px; color:#e6ecf7;">{why}</div>
                    </div>
                </div>
                <div style="margin-bottom:14px;">
                    <span style="font-size:11px; color:#7d8aa5;">AFFECTED SYSTEMS:</span>
                    {"".join([f'<span class="mono" style="background:#1c2740; color:#c4b5fd; padding:2px 6px; border-radius:4px; margin-left:4px; font-size:11px;">{html.escape(str(s))}</span>' for s in aff]) or ' None specified'}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Recommended Actions
        actions = res_data.get("recommended_actions", [])
        if actions:
            st.markdown('<div style="font-size:12px; font-weight:700; color:#22d3ee; margin-bottom:8px;">RECOMMENDED ACTIONS:</div>', unsafe_allow_html=True)
            for act in actions:
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                        <span style="color:#22c55e;">✔</span>
                        <span style="font-size:12px; color:#e6ecf7;">{html.escape(str(act))}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Evidence references and Unknowns
        refs = res_data.get("evidence_refs", [])
        unknowns = res_data.get("unknowns", [])
        if refs:
            chips = "".join([f'<span class="mono" style="background:rgba(34,211,238,0.1); color:#22d3ee; padding:2px 6px; border-radius:4px; margin-right:4px; font-size:10px;">{html.escape(str(r))}</span>' for r in refs])
            st.markdown(f'<div style="margin-top:12px; font-size:11px; color:#7d8aa5;">EVIDENCE REFERENCES: {chips}</div>', unsafe_allow_html=True)

        if unknowns:
            u_text = ", ".join([html.escape(str(u)) for u in unknowns])
            st.markdown(f'<div style="margin-top:6px; font-size:11px; color:#9ca3af;">UNKNOWNS / BLIND SPOTS: <i>{u_text}</i></div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Inspect Raw JSON Result"):
            st.json(cached_res)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6: RESPONSE PLAN
# ══════════════════════════════════════════════════════════════════════════════
def page_response_plan() -> None:
    st.markdown("### 🛡️ Defensive Response Planning")
    st.caption("Tailored remediation steps, operational impact assessments, and rollback procedures.")

    # Human in the Loop Warning
    st.markdown(
        """
        <div style="background:rgba(234,179,8,0.1); border:1px solid #eab308; border-radius:10px; padding:12px 16px; margin-bottom:16px;">
            <div style="display:flex; align-items:center; gap:8px; color:#eab308; font-weight:700; font-size:13px;">
                <span>⚠️</span> HUMAN-IN-THE-LOOP SAFETY MANDATE
            </div>
            <div style="font-size:12px; color:#fef08a; margin-top:4px;">
                Recommendations are advisory only. No firewall rules, script executions, or endpoint isolation actions are applied automatically.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        incidents = api_get("/api/incidents")
    except Exception as exc:
        render_error_card("Failed to load incidents", str(exc))
        return

    if not incidents:
        st.info("No incidents available.")
        return

    inc_options = {f"Incident #{inc['id']} · {inc['title'][:40]}": inc["id"] for inc in incidents}
    default_id = st.session_state.get("_active_incident_id", incidents[0]["id"])
    default_index = 0
    for idx, (lbl, iid) in enumerate(inc_options.items()):
        if iid == default_id:
            default_index = idx
            break

    sel_label = st.selectbox("Select Target Incident", options=list(inc_options.keys()), index=default_index)
    incident_id = inc_options[sel_label]
    st.session_state["_active_incident_id"] = incident_id

    if st.button("⚡ Generate Guided Response Plan", use_container_width=True):
        with st.spinner("Synthesizing containment & remediation strategy..."):
            try:
                res = api_post(f"/api/incidents/{incident_id}/analyze", {"task": "response", "force": True})
                if res.get("status") == "AI analysis unavailable":
                    render_error_card("Response Planning Unavailable", res.get("detail", "Error"), "Check LLM models in .env")
                else:
                    st.session_state[f"_resp_res_{incident_id}"] = res.get("result", {})
                    st.rerun()
            except Exception as exc:
                render_error_card("Response Planning Failed", str(exc))

    resp_data = st.session_state.get(f"_resp_res_{incident_id}")
    if resp_data:
        st.markdown(
            f"""
            <div class="soc-card soc-card-border-glow" style="margin-top:16px;">
                <div style="font-size:14px; font-weight:700; color:#22d3ee; margin-bottom:8px;">PROPOSED MITIGATION STRATEGY</div>
                <div style="font-size:13px; color:#e6ecf7; line-height:1.5; margin-bottom:14px;">
                    {html.escape(str(resp_data.get('finding') or 'Defensive plan ready.'))}
                </div>
                <div style="background:rgba(249,115,22,0.1); border:1px solid #f97316; border-radius:8px; padding:10px 12px; margin-bottom:16px;">
                    <div style="font-size:11px; font-weight:700; color:#f97316;">OPERATIONAL IMPACT ASSESSMENT</div>
                    <div style="font-size:12px; color:#fdba74; margin-top:2px;">{html.escape(str(resp_data.get('impact') or 'Low operational disruption expected.'))}</div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        c_roll, c_ver = st.columns(2)
        with c_roll:
            st.markdown('<div style="font-size:12px; font-weight:700; color:#c4b5fd; margin-bottom:8px;">ROLLBACK PLAN</div>', unsafe_allow_html=True)
            rollback_steps = resp_data.get("rollback", [])
            for r_idx, step in enumerate(rollback_steps, start=1):
                st.markdown(f'<div style="font-size:12px; color:#e6ecf7; margin-bottom:6px;"><b>{r_idx}.</b> {html.escape(str(step))}</div>', unsafe_allow_html=True)

        with c_ver:
            st.markdown('<div style="font-size:12px; font-weight:700; color:#22d3ee; margin-bottom:8px;">VERIFICATION CRITERIA</div>', unsafe_allow_html=True)
            verify_steps = resp_data.get("verification", [])
            for v_idx, step in enumerate(verify_steps, start=1):
                st.markdown(f'<div style="font-size:12px; color:#e6ecf7; margin-bottom:6px;"><b>{v_idx}.</b> {html.escape(str(step))}</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 7: REPORTS
# ══════════════════════════════════════════════════════════════════════════════
def page_reports() -> None:
    st.markdown("### 📄 Executive & Technical Incident Reporting")
    st.caption("Generate formal post-incident documentation for leadership and compliance auditing.")

    try:
        incidents = api_get("/api/incidents")
    except Exception as exc:
        render_error_card("Failed to load incidents", str(exc))
        return

    if not incidents:
        st.info("No incidents recorded.")
        return

    inc_options = {f"Incident #{inc['id']} · {inc['title'][:40]}": inc["id"] for inc in incidents}
    default_id = st.session_state.get("_active_incident_id", incidents[0]["id"])
    default_index = 0
    for idx, (lbl, iid) in enumerate(inc_options.items()):
        if iid == default_id:
            default_index = idx
            break

    sel_label = st.selectbox("Select Target Incident", options=list(inc_options.keys()), index=default_index)
    incident_id = inc_options[sel_label]
    st.session_state["_active_incident_id"] = incident_id

    if st.button("📄 Generate Executive & Technical Report", use_container_width=True):
        with st.spinner("Synthesizing formal report across telemetry..."):
            try:
                res = api_post(f"/api/incidents/{incident_id}/analyze", {"task": "report", "force": True})
                if res.get("status") == "AI analysis unavailable":
                    render_error_card(
                        "AI Analysis Unavailable — " + str(res.get("error_type", "Error")),
                        str(res.get("detail", "Error")),
                        "Check LLM_*_MODEL_ID in .env and restart the backend.",
                    )
                else:
                    st.session_state[f"_rep_res_{incident_id}"] = res.get("result", {})
                    st.rerun()
            except Exception as exc:
                render_error_card("Report Generation Failed", str(exc), "Check LLM_*_MODEL_ID in .env and restart backend")

    rep_data = st.session_state.get(f"_rep_res_{incident_id}")
    if rep_data:
        exec_sum = rep_data.get("executive_summary") or rep_data.get("finding") or "Report compiled."
        tech_sum = rep_data.get("technical_summary") or "Technical summary compiled."
        timeline_items = rep_data.get("timeline") or []

        # Executive Card
        st.markdown(
            f"""
            <div class="soc-card" style="margin-top:16px;">
                <div style="font-size:14px; font-weight:700; color:#22d3ee; margin-bottom:8px;">EXECUTIVE SUMMARY</div>
                <div style="font-size:13px; color:#e6ecf7; line-height:1.5;">{html.escape(str(exec_sum))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Technical Card
        st.markdown(
            f"""
            <div class="soc-card">
                <div style="font-size:14px; font-weight:700; color:#c4b5fd; margin-bottom:8px;">TECHNICAL INVESTIGATION SUMMARY</div>
                <div style="font-size:13px; color:#e6ecf7; line-height:1.5;">{html.escape(str(tech_sum))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Timeline
        if timeline_items:
            st.markdown(
                """
                <div class="soc-card">
                    <div style="font-size:13px; font-weight:700; color:#e6ecf7; margin-bottom:12px;">INCIDENT EVENT TIMELINE</div>
                """,
                unsafe_allow_html=True,
            )
            for item in timeline_items:
                item_text = json.dumps(item) if isinstance(item, dict) else str(item)
                st.markdown(
                    f"""
                    <div class="timeline-item">
                        <div class="timeline-node" style="background:#22d3ee; box-shadow:0 0 6px #22d3ee;"></div>
                        <div style="font-size:12px; color:#e6ecf7;">{html.escape(item_text)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # Downloads Row
        md_content = f"# Incident Report #{incident_id}\n\n## Executive Summary\n{exec_sum}\n\n## Technical Summary\n{tech_sum}\n"
        json_content = json.dumps(rep_data, indent=2, default=str)

        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "📥 Download Incident Report (JSON)",
                data=json_content,
                file_name=f"incident-{incident_id}-report.json",
                mime="application/json",
                use_container_width=True,
            )
        with d2:
            st.download_button(
                "📥 Download Incident Report (Markdown)",
                data=md_content,
                file_name=f"incident-{incident_id}-report.md",
                mime="text/markdown",
                use_container_width=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 8: THREAT CONTEXT
# ══════════════════════════════════════════════════════════════════════════════
def page_threat_context() -> None:
    st.markdown("### 🌐 Threat Intelligence Context & Enrichment")
    st.caption("RFC-1918 Private classification and public threat reputation lookups.")

    ip_input = st.text_input("Enter Target IP Address", value="10.144.85.20", placeholder="e.g. 192.168.1.1 or 8.8.8.8")
    if st.button("Analyze IP Reputation", use_container_width=True):
        ip_clean = ip_input.strip()
        is_private = (
            ip_clean.startswith("10.")
            or ip_clean.startswith("192.168.")
            or (ip_clean.startswith("172.") and len(ip_clean.split(".")) > 1 and 16 <= int(ip_clean.split(".")[1]) <= 31)
            or ip_clean.startswith("127.")
        )

        if is_private:
            st.markdown(
                f"""
                <div class="soc-card" style="border-left:4px solid #22c55e;">
                    <div style="font-size:14px; font-weight:700; color:#22c55e; margin-bottom:4px;">🟢 RFC-1918 PRIVATE INTERNAL IP</div>
                    <div class="mono" style="font-size:16px; color:#e6ecf7; margin-bottom:8px;">{html.escape(ip_clean)}</div>
                    <div style="font-size:12px; color:#7d8aa5;">
                        This address belongs to a local private subnet and is not routable on the public internet.
                        Threats on this IP signify lateral movement, internal compromise, or authorized administrative actions.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="soc-card" style="border-left:4px solid #f97316;">
                    <div style="font-size:14px; font-weight:700; color:#f97316; margin-bottom:4px;">🌐 PUBLIC ROUTABLE INTERNET IP</div>
                    <div class="mono" style="font-size:16px; color:#e6ecf7; margin-bottom:8px;">{html.escape(ip_clean)}</div>
                    <div style="font-size:12px; color:#fdba74;">
                        External public address detected. Live threat intelligence lookup requires an external API key (VirusTotal / AbuseIPDB).
                        Configure keys in <code>.env</code> to stream autonomous reputation scoring.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 9: SYSTEM HEALTH
# ══════════════════════════════════════════════════════════════════════════════
def page_system_health() -> None:
    st.markdown("### 🩺 SIEM & Pipeline System Health")
    st.caption("Detailed diagnostics for Backend API, Database, Wazuh Manager/Indexer, and Groq LLM engines.")

    col_btn, col_blank = st.columns([1.5, 3])
    with col_btn:
        if st.button("↻ Re-check All Connections Now", use_container_width=True):
            st.session_state["_force_conn_refresh"] = True
            st.rerun()

    # Fetch Connections
    conn_data = {}
    try:
        conn_data = api_get("/api/system/connections?refresh=true")
    except Exception as exc:
        render_error_card("Failed to query /api/system/connections", str(exc))

    if conn_data:
        c1, c2 = st.columns(2)
        with c1:
            # Backend & DB
            bk = conn_data.get("backend", {})
            db = conn_data.get("database", {})
            st.markdown(
                f"""
                <div class="soc-card">
                    <div style="font-size:14px; font-weight:700; color:#22d3ee; margin-bottom:10px;">CORE BACKEND & DATABASE</div>
                    <div style="margin-bottom:8px;">
                        <span style="color:#7d8aa5; font-size:12px;">FastAPI Service:</span>
                        <span class="mono" style="color:#e6ecf7; font-weight:600; margin-left:6px;">v{html.escape(str(bk.get('version', '1.0')))} ({bk.get('status', 'ok').upper()})</span>
                    </div>
                    <div style="margin-bottom:8px;">
                        <span style="color:#7d8aa5; font-size:12px;">Database Engine:</span>
                        <span class="mono" style="color:#e6ecf7; font-weight:600; margin-left:6px;">{html.escape(str(db.get('engine', 'sqlite')).upper())}</span>
                    </div>
                    <div style="margin-bottom:8px;">
                        <span style="color:#7d8aa5; font-size:12px;">Query Latency:</span>
                        <span class="mono" style="color:#22c55e; font-weight:600; margin-left:6px;">{db.get('latency_ms', 0)} ms</span>
                    </div>
                    <div>
                        <span style="color:#7d8aa5; font-size:12px;">Total Stored Alerts:</span>
                        <span class="mono" style="color:#22d3ee; font-weight:700; margin-left:6px;">{db.get('alert_count', 0):,}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            # Wazuh SIEM
            wz = conn_data.get("wazuh", {})
            gq = conn_data.get("groq", {})
            st.markdown(
                f"""
                <div class="soc-card">
                    <div style="font-size:14px; font-weight:700; color:#c4b5fd; margin-bottom:10px;">SIEM & LLM TELEMETRY</div>
                    <div style="margin-bottom:8px;">
                        <span style="color:#7d8aa5; font-size:12px;">Wazuh Source:</span>
                        <span class="mono" style="color:#e6ecf7; font-weight:600; margin-left:6px;">{html.escape(str(wz.get('source', 'aws')).upper())}</span>
                    </div>
                    <div style="margin-bottom:8px;">
                        <span style="color:#7d8aa5; font-size:12px;">Manager / Indexer:</span>
                        <span class="mono" style="color:#e6ecf7; font-weight:600; margin-left:6px;">{html.escape(str(wz.get('manager', {}).get('version', 'v4.x')))} · {html.escape(str(wz.get('indexer', {}).get('status', 'green')).upper())}</span>
                    </div>
                    <div style="margin-bottom:8px;">
                        <span style="color:#7d8aa5; font-size:12px;">Groq Engine Status:</span>
                        <span class="mono" style="color:#22d3ee; font-weight:600; margin-left:6px;">{gq.get('status', 'ok').upper()} ({gq.get('latency_ms', 0)} ms)</span>
                    </div>
                    <div>
                        <span style="color:#7d8aa5; font-size:12px;">Configured Models:</span>
                        <span class="mono" style="color:#e6ecf7; font-size:11px; margin-left:6px;">{", ".join([m.split("/")[-1] for m in gq.get("models", [])])}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("Raw System Connections JSON Response"):
            st.json(conn_data)

    st.markdown("---")
    st.subheader("Raw Wazuh SIEM Status (/api/source/status)")
    if st.button("Ping Wazuh Server Directly"):
        try:
            status = api_get("/api/source/status")
            st.json(status)
        except Exception as exc:
            st.error(str(exc))


# ── Main Entrypoint ───────────────────────────────────────────────────────────
def main() -> None:
    inject_css()

    # Load initial dashboard summary
    summary: Dict[str, Any] = {}
    try:
        summary = api_get("/api/dashboard/summary")
    except Exception as exc:
        render_topbar()
        render_error_card(
            "Backend Service Unavailable",
            str(exc),
            "Ensure FastAPI is running: python -m uvicorn backend.main:app --port 8000",
        )
        st.stop()

    active_page = render_sidebar(summary)
    render_topbar()

    # Page Dispatcher
    if active_page == "SOC Overview":
        page_soc_overview(summary)
    elif active_page.startswith("Alerts"):
        page_alerts()
    elif active_page.startswith("Incidents"):
        page_incidents()
    elif active_page == "Investigation":
        page_investigation()
    elif active_page == "AI Analyst":
        page_ai_analyst()
    elif active_page == "Response Plan":
        page_response_plan()
    elif active_page == "Reports":
        page_reports()
    elif active_page == "Threat Context":
        page_threat_context()
    elif active_page == "System Health":
        page_system_health()


if __name__ == "__main__":
    main()
