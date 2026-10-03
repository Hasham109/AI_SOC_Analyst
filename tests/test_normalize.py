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
