import json
from typing import Dict
from backend.llm.router import get_router
from backend.schemas.analysis import ResponseResult

PROMPT_VERSION = "response-v1"
SYSTEM = (
    "You are a SOC response-planning assistant. Recommend actions only; never execute them. "
    "Include reason, impact, rollback, and verification. Stay within the supplied environment constraints. "
    "Return JSON only with fields: finding, evidence_refs, confidence_label, unknowns, recommended_actions, "
    "reason, impact, rollback, verification."
)


def recommend_response(evidence: Dict) -> ResponseResult:
    prompt = "Create a response plan from these validated findings:\n\n" + json.dumps(evidence, default=str)
    result, provider, model = get_router().run(
        task="response", system_prompt=SYSTEM, user_prompt=prompt, schema=ResponseResult
    )
    result.provider = provider
    result.model = model
    result.prompt_version = PROMPT_VERSION
    return result
