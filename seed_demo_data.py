"""
Demo Data Seeder — SOC Analyst Platform
Populates the database with realistic Wazuh-style alerts for hackathon demo.
Run: python seed_demo_data.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timezone, timedelta
from backend.db.session import SessionLocal
from backend.db.models import Alert
import hashlib, json

DEMO_ALERTS = [
    {
        "wazuh_id": "demo-001",
        "rule_id": "5763",
        "rule_level": 12,
        "rule_description": "SSH Brute Force Attack — Multiple failed authentications",
        "agent_id": "001",
        "agent_name": "web-server-01",
        "agent_ip": "10.10.1.5",
        "src_ip": "185.234.219.41",
        "src_user": "root",
        "mitre_ids": ["T1110", "T1078"],
        "mitre_tactics": ["Credential Access", "Initial Access"],
        "log_location": "/var/log/auth.log",
        "raw_log": "sshd[1234]: Failed password for root from 185.234.219.41 port 52413 ssh2",
        "risk_score": 85,
        "triage_label": "true_positive",
        "minutes_ago": 5,
    },
    {
        "wazuh_id": "demo-002",
        "rule_id": "31103",
        "rule_level": 10,
        "rule_description": "Web Shell Detected — PHP webshell uploaded via file upload",
        "agent_id": "002",
        "agent_name": "web-server-01",
        "agent_ip": "10.10.1.5",
        "src_ip": "91.108.56.12",
        "src_user": "www-data",
        "mitre_ids": ["T1505.003"],
        "mitre_tactics": ["Persistence"],
        "log_location": "/var/log/apache2/access.log",
        "raw_log": "POST /uploads/shell.php HTTP/1.1 200 - 91.108.56.12",
        "risk_score": 92,
        "triage_label": "true_positive",
        "minutes_ago": 12,
    },
    {
        "wazuh_id": "demo-003",
        "rule_id": "18107",
        "rule_level": 14,
        "rule_description": "Ransomware Indicators — Mass file encryption detected",
        "agent_id": "003",
        "agent_name": "fileserver-01",
        "agent_ip": "10.10.2.10",
        "src_ip": "10.10.2.10",
        "src_user": "john.doe",
        "mitre_ids": ["T1486"],
        "mitre_tactics": ["Impact"],
        "log_location": "/var/log/syslog",
        "raw_log": "kernel: mass rename events: 2400 files modified in 60s",
        "risk_score": 98,
        "triage_label": "true_positive",
        "minutes_ago": 20,
    },
    {
        "wazuh_id": "demo-004",
        "rule_id": "5501",
        "rule_level": 5,
        "rule_description": "User Account Created — New privileged user added",
        "agent_id": "001",
        "agent_name": "web-server-01",
        "agent_ip": "10.10.1.5",
        "src_ip": "10.10.1.5",
        "src_user": "admin",
        "mitre_ids": ["T1136.001"],
        "mitre_tactics": ["Persistence"],
        "log_location": "/var/log/auth.log",
        "raw_log": "useradd[5521]: new user: name=backdoor, UID=0, GID=0, home=/root",
        "risk_score": 75,
        "triage_label": "true_positive",
        "minutes_ago": 35,
    },
    {
        "wazuh_id": "demo-005",
        "rule_id": "87105",
        "rule_level": 11,
        "rule_description": "SQL Injection Attempt — Malicious query in web logs",
        "agent_id": "002",
        "agent_name": "web-server-01",
        "agent_ip": "10.10.1.5",
        "src_ip": "203.0.113.42",
        "src_user": None,
        "mitre_ids": ["T1190"],
        "mitre_tactics": ["Initial Access"],
        "log_location": "/var/log/nginx/access.log",
        "raw_log": "GET /login?id=1' OR '1'='1'-- HTTP/1.1 200 203.0.113.42",
        "risk_score": 80,
        "triage_label": "true_positive",
        "minutes_ago": 50,
    },
    {
        "wazuh_id": "demo-006",
        "rule_id": "5104",
        "rule_level": 8,
        "rule_description": "Privilege Escalation — sudo su by standard user",
        "agent_id": "005",
        "agent_name": "hr-workstation",
        "agent_ip": "10.10.4.15",
        "src_ip": "10.10.4.15",
        "src_user": "emily.smith",
        "mitre_ids": ["T1548.003"],
        "mitre_tactics": ["Privilege Escalation"],
        "log_location": "/var/log/auth.log",
        "raw_log": "sudo: emily.smith : command not allowed: /bin/su",
        "risk_score": 60,
        "triage_label": "needs_review",
        "minutes_ago": 70,
    },
    {
        "wazuh_id": "demo-007",
        "rule_id": "60122",
        "rule_level": 13,
        "rule_description": "Data Exfiltration — Large outbound DNS transfer to unknown C2",
        "agent_id": "003",
        "agent_name": "fileserver-01",
        "agent_ip": "10.10.2.10",
        "src_ip": "10.10.2.10",
        "src_user": "SYSTEM",
        "mitre_ids": ["T1048.001"],
        "mitre_tactics": ["Exfiltration"],
        "log_location": "/var/log/named.log",
        "raw_log": "named: 2.5MB TXT query to evil-c2.xyz — threshold exceeded",
        "risk_score": 95,
        "triage_label": "true_positive",
        "minutes_ago": 90,
    },
    {
        "wazuh_id": "demo-008",
        "rule_id": "40111",
        "rule_level": 6,
        "rule_description": "Port Scan Detected — Nmap scan from internal host",
        "agent_id": "006",
        "agent_name": "dev-laptop",
        "agent_ip": "10.10.5.88",
        "src_ip": "10.10.5.88",
        "src_user": "developer",
        "mitre_ids": ["T1046"],
        "mitre_tactics": ["Discovery"],
        "log_location": "/var/log/syslog",
        "raw_log": "nf_conntrack: table full, dropping packet from 10.10.5.88",
        "risk_score": 40,
        "triage_label": "false_positive",
        "minutes_ago": 110,
    },
    {
        "wazuh_id": "demo-009",
        "rule_id": "5302",
        "rule_level": 4,
        "rule_description": "Login Outside Business Hours — User authenticated at 2:47 AM",
        "agent_id": "007",
        "agent_name": "vpn-gateway",
        "agent_ip": "10.10.0.1",
        "src_ip": "77.91.124.55",
        "src_user": "michael.jones",
        "mitre_ids": ["T1078"],
        "mitre_tactics": ["Initial Access"],
        "log_location": "/var/log/openvpn.log",
        "raw_log": "openvpn: michael.jones authenticated from 77.91.124.55 at 02:47:13",
        "risk_score": 55,
        "triage_label": "needs_review",
        "minutes_ago": 150,
    },
    {
        "wazuh_id": "demo-010",
        "rule_id": "5402",
        "rule_level": 3,
        "rule_description": "Scheduled Task Created — Cron job by non-root user",
        "agent_id": "004",
        "agent_name": "db-server-01",
        "agent_ip": "10.10.3.20",
        "src_ip": "10.10.3.20",
        "src_user": "postgres",
        "mitre_ids": ["T1053.003"],
        "mitre_tactics": ["Persistence"],
        "log_location": "/var/log/syslog",
        "raw_log": "crontab: postgres installed new crontab",
        "risk_score": 45,
        "triage_label": "needs_review",
        "minutes_ago": 200,
    },
]


def seed():
    db = SessionLocal()
    try:
        deleted = db.query(Alert).filter(Alert.wazuh_alert_id.like("demo-%")).delete()
        db.commit()
        print(f"Cleared {deleted} old demo alerts")

        now = datetime.now(timezone.utc)
        created = 0

        for a in DEMO_ALERTS:
            ts = now - timedelta(minutes=a["minutes_ago"])
            fingerprint = hashlib.sha256(
                f"{a['rule_id']}{a['agent_ip']}{a['src_ip']}".encode()
            ).hexdigest()

            alert = Alert(
                wazuh_alert_id=a["wazuh_id"],
                fingerprint=fingerprint,
                timestamp=ts,
                rule_id=a["rule_id"],
                rule_level=a["rule_level"],
                rule_description=a["rule_description"],
                agent_id=a["agent_id"],
                agent_name=a["agent_name"],
                agent_ip=a["agent_ip"],
                src_ip=a.get("src_ip"),
                src_user=a.get("src_user"),
                mitre_ids=json.dumps(a.get("mitre_ids", [])),
                mitre_tactics=json.dumps(a.get("mitre_tactics", [])),
                log_location=a.get("log_location"),
                raw_log=a.get("raw_log"),
                risk_score=a["risk_score"],
                triage_label=a["triage_label"],
                is_duplicate=False,
            )
            db.add(alert)
            created += 1
            print(f"  OK [{a['rule_level']:>2}] {a['rule_description'][:55]}")

        db.commit()
        print(f"\nSeeded {created} demo alerts!")
        print("Refresh your dashboard at http://localhost:8501")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
