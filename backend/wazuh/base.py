from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests


class WazuhSourceClient(ABC):
    source_name: str

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def fetch_alerts(self, since: Optional[datetime], limit: int) -> List[Dict[str, Any]]:
        raise NotImplementedError


class WazuhHttpSourceClient(WazuhSourceClient):
    def __init__(
        self,
        source_name: str,
        manager_url: str,
        indexer_url: str,
        manager_username: str,
        manager_password: str,
        indexer_username: str,
        indexer_password: str,
        timeout_seconds: int = 15,
        verify_tls: bool = False,
    ) -> None:
        self.source_name = source_name
        self.manager_url = manager_url.rstrip("/")
        self.indexer_url = indexer_url.rstrip("/")
        self.manager_username = manager_username
        self.manager_password = manager_password
        self.indexer_username = indexer_username
        self.indexer_password = indexer_password
        self.timeout_seconds = timeout_seconds
        self.verify_tls = verify_tls
        self.session = requests.Session()

    def _manager_token(self) -> str:
        response = self.session.post(
            f"{self.manager_url}/security/user/authenticate?raw=true",
            auth=(self.manager_username, self.manager_password),
            timeout=self.timeout_seconds,
            verify=self.verify_tls,
        )
        response.raise_for_status()
        token = response.text.strip().strip('"')
        if not token:
            raise RuntimeError("Wazuh API authentication returned an empty token")
        return token

    def _manager_get(self, path: str) -> Dict[str, Any]:
        token = self._manager_token()
        response = self.session.get(
            f"{self.manager_url}{path}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout_seconds,
            verify=self.verify_tls,
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        try:
            manager_info = self._manager_get("/manager/info")
            indexer_response = self.session.get(
                f"{self.indexer_url}/_cat/health?format=json",
                auth=(self.indexer_username, self.indexer_password),
                timeout=self.timeout_seconds,
                verify=self.verify_tls,
            )
            indexer_response.raise_for_status()
            indexer_health = indexer_response.json()
            return {
                "status": "ok",
                "source": self.source_name,
                "manager": manager_info.get("data", manager_info),
                "indexer": indexer_health,
            }
        except Exception as e:
            return {"status": "degraded", "source": self.source_name, "error": str(e)}

    @staticmethod
    def _build_alert_query(since: Optional[datetime], limit: int) -> Dict[str, Any]:
        filters: List[Dict[str, Any]] = []
        if since is not None:
            iso = since.isoformat().replace("+00:00", "Z")
            filters.append(
                {
                    "bool": {
                        "should": [
                            {"range": {"timestamp": {"gte": iso}}},
                            {"range": {"@timestamp": {"gte": iso}}},
                        ],
                        "minimum_should_match": 1,
                    }
                }
            )
        return {
            "size": limit,
            "track_total_hits": False,
            "sort": [
                {"timestamp": {"order": "asc", "unmapped_type": "date"}},
                {"@timestamp": {"order": "asc", "unmapped_type": "date"}},
                {"_id": {"order": "asc"}},
            ],
            "query": {"bool": {"filter": filters}} if filters else {"match_all": {}},
        }

    def fetch_alerts(self, since: Optional[datetime], limit: int) -> List[Dict[str, Any]]:
        query = self._build_alert_query(since, limit)
        response = self.session.post(
            f"{self.indexer_url}/wazuh-alerts-4.x-*/_search",
            auth=(self.indexer_username, self.indexer_password),
            json=query,
            timeout=self.timeout_seconds,
            verify=self.verify_tls,
        )
        response.raise_for_status()
        payload = response.json()
        hits = payload.get("hits", {}).get("hits", [])
        return [
            {
                "_index": hit.get("_index"),
                "_id": hit.get("_id"),
                "_source": hit.get("_source", {}),
            }
            for hit in hits
            if isinstance(hit, dict)
        ]
