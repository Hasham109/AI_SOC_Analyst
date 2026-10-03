from datetime import datetime, timedelta, timezone
from typing import Optional


def initial_since(mode: str, lookback_minutes: int) -> Optional[datetime]:
    if mode == "latest_only":
        return datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)
    return None


def overlap_timestamp(timestamp: datetime, overlap_seconds: int) -> datetime:
    return timestamp - timedelta(seconds=overlap_seconds)
