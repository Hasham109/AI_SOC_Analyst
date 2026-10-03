from __future__ import annotations
from datetime import datetime, timezone
import random
import uuid
from backend.schemas.alert import NormalizedAlert
from backend.processing.fingerprint import build_fingerprint

SIMULATION_TEMPLATES = [
    {
        "rule_id": "5710",
        "rule_level": 10,
        "severity": "high",
        "rule_description": "sshd: Multiple failed SSH login attempts (Brute Force detected)",
        "agent_name": "web-prod-01",
        "agent_ip": "10.144.85.20",
        "src_ip_pool": ["185.220.101.5", "45.142.214.18", "194.26.29.112", "193.32.162.88"],
        "src_user_pool": ["root", "admin", "ubuntu", "postgres"],
        "groups": ["syslog", "sshd", "authentication_failures"],
        "mitre_techniques": ["T1110.001", "T1078"],
        "location": "/var/log/auth.log",
        "decoder": "sshd",
    },
    {
        "rule_id": "31101",
        "rule_level": 12,
        "severity": "critical",
        "rule_description": "Web attack: SQL Injection attempt detected in HTTP GET parameters",
        "agent_name": "web-prod-01",
        "agent_ip": "10.144.85.20",
        "src_ip_pool": ["103.145.13.9", "185.191.171.8", "91.240.118.172"],
        "src_user_pool": ["www-data", "anonymous"],
        "groups": ["web", "accesslog", "attack"],
        "mitre_techniques": ["T1190"],
        "location": "/var/log/nginx/access.log",
        "decoder": "web-accesslog",
    },
    {
        "rule_id": "5402",
        "rule_level": 7,
        "severity": "medium",
        "rule_description": "Suspicious cron job scheduled by non-privileged user",
        "agent_name": "app-backend-02",
        "agent_ip": "10.144.85.21",
        "src_ip_pool": ["10.144.85.21"],
        "src_user_pool": ["appuser", "developer", "guest"],
        "groups": ["ossec", "syslog"],
        "mitre_techniques": ["T1053.003"],
        "location": "/var/log/syslog",
        "decoder": "crontab",
    },
    {
        "rule_id": "5501",
        "rule_level": 8,
        "severity": "medium",
        "rule_description": "PAM: User login failed outside normal working hours",
        "agent_name": "fileserver-01",
        "agent_ip": "10.144.85.35",
        "src_ip_pool": ["10.144.85.50", "10.144.85.99"],
        "src_user_pool": ["deployer", "finance_user", "sarah"],
        "groups": ["pam", "syslog"],
        "mitre_techniques": ["T1078"],
        "location": "/var/log/auth.log",
        "decoder": "pam",
    },
    {
        "rule_id": "60115",
        "rule_level": 13,
        "severity": "critical",
        "rule_description": "Suspicious PowerShell / Bash reverse shell invocation detected",
        "agent_name": "db-cluster-01",
        "agent_ip": "10.144.85.10",
        "src_ip_pool": ["198.51.100.44", "203.0.113.88"],
        "src_user_pool": ["daemon", "nobody"],
        "groups": ["process_monitor", "execution"],
        "mitre_techniques": ["T1059.004", "T1071"],
        "location": "auditd",
        "decoder": "auditd",
    },
    {
        "rule_id": "40111",
        "rule_level": 6,
        "severity": "low",
        "rule_description": "Network anomaly: High rate of SYN packets indicating port scan",
        "agent_name": "firewall-gw",
        "agent_ip": "10.144.85.1",
        "src_ip_pool": ["185.180.222.14", "94.102.61.22"],
        "src_user_pool": [None],
        "groups": ["firewall", "ids"],
        "mitre_techniques": ["T1046"],
        "location": "/var/log/suricata/eve.json",
        "decoder": "json",
    },
]


def generate_simulated_alert(source_name: str = "simulation") -> NormalizedAlert:
    """Generates a realistic live security telemetry alert."""
    template = random.choice(SIMULATION_TEMPLATES)
    sim_id = f"sim-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    src_ip = random.choice(template["src_ip_pool"])
    src_user = random.choice(template["src_user_pool"])

    raw_payload = {
        "timestamp": now.isoformat(),
        "rule": {
            "id": template["rule_id"],
            "level": template["rule_level"],
            "description": template["rule_description"],
            "groups": template["groups"],
            "mitre": {"id": template["mitre_techniques"]},
        },
        "agent": {
            "id": f"sim-agent-{template['agent_name'][-2:]}",
            "name": template["agent_name"],
            "ip": template["agent_ip"],
        },
        "data": {
            "srcip": src_ip,
            "srcuser": src_user,
        },
        "location": template["location"],
        "decoder": {"name": template["decoder"]},
    }

    fingerprint = build_fingerprint(source_name, sim_id, raw_payload)

    return NormalizedAlert(
        source_name=source_name,
        source_alert_id=sim_id,
        timestamp=now,
        agent_id=f"sim-agent-{template['agent_name'][-2:]}",
        agent_name=template["agent_name"],
        agent_ip=template["agent_ip"],
        rule_id=template["rule_id"],
        rule_level=template["rule_level"],
        severity=template["severity"],
        rule_description=template["rule_description"],
        src_ip=src_ip,
        dst_ip=template["agent_ip"],
        src_user=src_user,
        dst_user=None,
        groups=template["groups"],
        mitre_techniques=template["mitre_techniques"],
        location=template["location"],
        decoder=template["decoder"],
        full_log=f"[{template['agent_name']}] {template['rule_description']} from {src_ip} user {src_user}",
        raw_json=raw_payload,
        fingerprint=fingerprint,
    )
