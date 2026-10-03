import json
from typing import Any, Dict
from backend.config import Settings
from backend.llm.base import LLMProvider


class GroqProvider(LLMProvider):
    provider_name = "groq"

    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when a Groq task is enabled")
        self.settings = settings
        try:
            from groq import Groq
        except ImportError as exc:
            raise RuntimeError("The groq package is not installed. Run: pip install groq") from exc

        self.client = Groq(
            api_key=settings.groq_api_key.get_secret_value(),
            timeout=settings.groq_timeout_seconds,
        )

    def generate_json(self, *, model: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 4096,
        }
        if self.settings.groq_use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
