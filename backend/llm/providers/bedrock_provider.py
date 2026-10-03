import json
from typing import Any, Dict
from backend.config import Settings
from backend.llm.base import LLMProvider


class BedrockProvider(LLMProvider):
    provider_name = "bedrock"

    def __init__(self, settings: Settings) -> None:
        import boto3
        self.settings = settings
        self.client = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    def generate_json(self, *, model: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        response = self.client.converse(
            modelId=model,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={
                "maxTokens": self.settings.aws_bedrock_max_tokens,
                "temperature": self.settings.aws_bedrock_default_temperature,
            },
        )
        content = response["output"]["message"]["content"][0]["text"]
        return json.loads(content)
