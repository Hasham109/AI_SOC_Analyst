import json
from typing import Dict
from backend.llm.router import get_router
from backend.schemas.analysis import InvestigationResult

PROMPT_VERSION = "investigation-v1"
SYSTEM = (
    "You are a SOC investigation assistant. Use only the supplied incident timeline and evidence. "
    "Every factual statement must be linked to an evidence reference or marked as an inference. "
    "Do not invent missing facts. Return JSON only with fields: finding, evidence_refs, confidence_label, "
    "unknowns, recommended_actions, timeline_summary, next_investigation_steps."
)


def investigate_incident(evidence: Dict) -> InvestigationResult:
    prompt = "Analyze this incident and evidence:\n\n" + json.dumps(evidence, default=str)
    result, provider, model = get_router().run(
        task="investigation", system_prompt=SYSTEM, user_prompt=prompt, schema=InvestigationResult
    )
    result.provider = provider
    result.model = model
    result.prompt_version = PROMPT_VERSION
    return result
