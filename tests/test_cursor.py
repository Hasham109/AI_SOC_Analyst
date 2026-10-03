from datetime import datetime, timezone
from backend.processing.cursor import initial_since, overlap_timestamp


def test_latest_only_returns_recent_time():
    assert initial_since("latest_only", 5) is not None


def test_overlap_moves_back():
    dt = datetime(2026, 10, 1, tzinfo=timezone.utc)
    assert overlap_timestamp(dt, 30).second == 30
