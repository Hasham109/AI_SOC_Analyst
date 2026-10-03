from backend.config import Settings
from backend.wazuh.base import WazuhHttpSourceClient


class LocalWazuhClient(WazuhHttpSourceClient):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            source_name="wazuh_local",
            manager_url=settings.local_wazuh_api_url,
            indexer_url=settings.local_wazuh_indexer_url,
            manager_username=settings.wazuh_api_username,
            manager_password=settings.wazuh_api_password.get_secret_value(),
            indexer_username=settings.wazuh_indexer_username,
            indexer_password=settings.wazuh_indexer_password.get_secret_value(),
            verify_tls=settings.wazuh_verify_tls,
        )
