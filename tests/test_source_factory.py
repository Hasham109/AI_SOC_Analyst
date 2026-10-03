from backend.config import Settings
from backend.wazuh.factory import get_wazuh_client


def make_settings():
    return Settings(
        local_wazuh_api_url="https://local:55000",
        aws_wazuh_api_url="https://aws:55000",
        local_wazuh_indexer_url="https://local:9200",
        aws_wazuh_indexer_url="https://aws:9200",
        wazuh_api_username="u",
        wazuh_api_password="p",
        wazuh_indexer_username="iu",
        wazuh_indexer_password="ip",
        soc_api_token="token",
    )


def test_local_factory():
    settings = make_settings()
    settings.wazuh_source = "local"
    assert get_wazuh_client(settings).source_name == "wazuh_local"


def test_aws_factory():
    settings = make_settings()
    settings.wazuh_source = "aws"
    assert get_wazuh_client(settings).source_name == "wazuh_aws"
