from backend.processing.fingerprint import build_fingerprint


def test_same_alert_same_fingerprint():
    a = build_fingerprint("wazuh_local", "abc")
    b = build_fingerprint("wazuh_local", "abc")
    assert a == b


def test_source_changes_fingerprint():
    a = build_fingerprint("wazuh_local", "abc")
    b = build_fingerprint("wazuh_aws", "abc")
    assert a != b
