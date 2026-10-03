def test_api_contract_exists():
    from backend.main import app
    paths = set(app.openapi().get("paths", {}).keys())
    assert "/health" in paths
    assert "/api/alerts" in paths
    assert "/api/incidents" in paths
    assert "/api/ingestion/run" in paths

