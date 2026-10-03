from backend.config import Settings
from backend.wazuh.base import WazuhHttpSourceClient


class AwsWazuhClient(WazuhHttpSourceClient):
    def __init__(self, settings: Settings) -> None:
        super().__init__(
            source_name="wazuh_aws",
            manager_url=settings.aws_wazuh_api_url,
            indexer_url=settings.aws_wazuh_indexer_url,
            manager_username=settings.wazuh_api_username,
            manager_password=settings.wazuh_api_password.get_secret_value(),
            indexer_username=settings.wazuh_indexer_username,
            indexer_password=settings.wazuh_indexer_password.get_secret_value(),
            verify_tls=settings.wazuh_verify_tls,
        )
