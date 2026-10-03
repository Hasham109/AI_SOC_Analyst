from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMProvider(ABC):
    provider_name: str

    @abstractmethod
    def generate_json(self, *, model: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        raise NotImplementedError
