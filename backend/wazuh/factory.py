from backend.config import Settings
from backend.wazuh.aws_client import AwsWazuhClient
from backend.wazuh.base import WazuhSourceClient
from backend.wazuh.local_client import LocalWazuhClient


def get_wazuh_client(settings: Settings) -> WazuhSourceClient:
    if settings.wazuh_source == "local":
        return LocalWazuhClient(settings)
    if settings.wazuh_source == "aws":
        return AwsWazuhClient(settings)
    raise ValueError(f"Unsupported WAZUH_SOURCE: {settings.wazuh_source}")
