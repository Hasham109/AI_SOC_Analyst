from __future__ import annotations
from functools import lru_cache
from typing import Dict, Type
from pydantic import BaseModel, ValidationError
from backend.config import Settings


class LLMRouter:
    TASKS = {
        "triage": ("llm_triage_provider", "llm_triage_model_id"),
        "investigation": ("llm_investigation_provider", "llm_investigation_model_id"),
        "response": ("llm_response_provider", "llm_response_model_id"),
        "manager": ("llm_manager_provider", "llm_manager_model_id"),
        "report": ("llm_report_provider", "llm_report_model_id"),
    }

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._providers = {}

    def _get_provider(self, name: str):
        if name not in self._providers:
            if name == "groq":
                from backend.llm.providers.groq_provider import GroqProvider
                self._providers["groq"] = GroqProvider(self.settings)
            elif name == "bedrock":
                from backend.llm.providers.bedrock_provider import BedrockProvider
                self._providers["bedrock"] = BedrockProvider(self.settings)
            else:
                raise ValueError(f"Unsupported LLM provider: {name}")
        return self._providers[name]

    def _provider_and_model(self, task: str):
        if task not in self.TASKS:
            raise ValueError(f"Unsupported LLM task: {task}")
        provider_attr, model_attr = self.TASKS[task]
        provider_name = getattr(self.settings, provider_attr)
        model = getattr(self.settings, model_attr)
        provider = self._get_provider(provider_name)
        return provider, model

    def run(self, *, task: str, system_prompt: str, user_prompt: str, schema: Type[BaseModel]):
        provider, model = self._provider_and_model(task)
        raw = provider.generate_json(model=model, system_prompt=system_prompt, user_prompt=user_prompt)
        try:
            return schema.model_validate(raw), provider.provider_name, model
        except ValidationError:
            raw_retry = provider.generate_json(
                model=model,
                system_prompt=system_prompt + "\nReturn ONLY valid JSON matching the requested fields.",
                user_prompt=user_prompt,
            )
            return schema.model_validate(raw_retry), provider.provider_name, model


@lru_cache(maxsize=1)
def get_router() -> LLMRouter:
    from backend.config import get_settings
    return LLMRouter(get_settings())
