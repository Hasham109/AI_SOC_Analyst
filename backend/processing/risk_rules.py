from collections import Counter
from typing import Dict, Iterable
from backend.db.models import Alert


def basic_risk_flags(alerts: Iterable[Alert]) -> Dict[str, object]:
    alerts_list = list(alerts)
    counts = Counter(a.severity for a in alerts_list)
    high_or_critical = sum(counts.get(level, 0) for level in ("high", "critical"))
    return {
        "alert_count": len(alerts_list),
        "severity_counts": dict(counts),
        "high_or_critical_count": high_or_critical,
    }
