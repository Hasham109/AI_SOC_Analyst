import logging
from functools import lru_cache
from typing import Literal, Optional
from pydantic import Field, SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Model IDs from the old Llama setup that now return 404 model_not_found.
RETIRED_MODEL_PREFIXES = ("llama", "meta-llama/")


class Settings(BaseSettings):
    """Application configuration loaded from environment variables/.env."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "SentinalIQ - AI Powered Security Operations"
    app_version: str = "1.0.0"

    wazuh_source: Literal["local", "aws"] = "local"
    local_wazuh_api_url: str = "https://127.0.0.1:55000"
    aws_wazuh_api_url: str = ""
    local_wazuh_indexer_url: str = "https://127.0.0.1:9200"
    aws_wazuh_indexer_url: str = ""

    wazuh_api_username: str = "admin"
    wazuh_api_password: SecretStr = SecretStr("admin")
    wazuh_indexer_username: str = "admin"
    wazuh_indexer_password: SecretStr = SecretStr("admin")

    database_url: str = "sqlite:///./soc_app.db"
    soc_api_token: SecretStr = SecretStr("soc-secret-token")

    initial_sync_mode: Literal["latest_only", "lookback"] = "latest_only"
    lookback_minutes: int = Field(default=5, ge=1, le=1440)
    poll_interval_seconds: int = Field(default=120, ge=10, le=3600)
    fetch_limit: int = Field(default=100, ge=1, le=500)
    cursor_overlap_seconds: int = Field(default=0, ge=0, le=300)
    auto_simulate_on_empty: bool = True
    correlation_window_minutes: int = Field(default=10, ge=1, le=120)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=600)

    # Groq Model Defaults (Updated with live active models)
    llm_triage_provider: str = "groq"
    llm_triage_model_id: str = "openai/gpt-oss-20b"
    llm_investigation_provider: str = "groq"
    llm_investigation_model_id: str = "openai/gpt-oss-120b"
    llm_response_provider: str = "groq"
    llm_response_model_id: str = "openai/gpt-oss-20b"
    llm_report_provider: str = "groq"
    llm_report_model_id: str = "openai/gpt-oss-20b"
    llm_manager_provider: str = "groq"
    llm_manager_model_id: str = "openai/gpt-oss-20b"

    groq_api_key: Optional[SecretStr] = None
    groq_use_json_mode: bool = True
    groq_timeout_seconds: int = Field(default=30, ge=5, le=120)

    aws_region: str = "us-east-1"
    aws_bedrock_default_temperature: float = Field(default=0.2, ge=0, le=1)
    aws_bedrock_max_tokens: int = Field(default=1200, ge=128, le=8192)
    wazuh_verify_tls: bool = False

    @field_validator(
        "llm_triage_model_id",
        "llm_investigation_model_id",
        "llm_response_model_id",
        "llm_report_model_id",
        "llm_manager_model_id",
        mode="before",
    )
    @classmethod
    def _replace_retired_models(cls, value: str, info: ValidationInfo) -> str:
        """Stale .env files may still point at Llama models that Groq no longer serves."""
        model = str(value).strip().strip('"').strip("'")
        if model.startswith("model="):
            model = model[len("model="):]
        if not model or model.lower().startswith(RETIRED_MODEL_PREFIXES):
            replacement = cls.model_fields[info.field_name].default
            logger.warning(
                "%s=%r is not available on Groq; using %r instead. Update your .env.",
                info.field_name.upper(), value, replacement,
            )
            return replacement
        return model

    def active_wazuh_api_url(self) -> str:
        return self.local_wazuh_api_url if self.wazuh_source == "local" else self.aws_wazuh_api_url

    def active_wazuh_indexer_url(self) -> str:
        return (
            self.local_wazuh_indexer_url
            if self.wazuh_source == "local"
            else self.aws_wazuh_indexer_url
        )

    def validate_runtime(self) -> None:
        if self.wazuh_source == "aws" and not self.aws_wazuh_api_url:
            raise ValueError("WAZUH_SOURCE=aws but AWS_WAZUH_API_URL is empty")
        if self.wazuh_source == "aws" and not self.aws_wazuh_indexer_url:
            raise ValueError("WAZUH_SOURCE=aws but AWS_WAZUH_INDEXER_URL is empty")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime()
    return settings
