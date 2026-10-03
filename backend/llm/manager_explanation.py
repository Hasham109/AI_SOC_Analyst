import json
from typing import Dict
from backend.llm.router import get_router
from backend.schemas.analysis import ManagerExplanation

PROMPT_VERSION = "manager-v1"
SYSTEM = (
    "Explain the incident in simple English for a non-technical manager. Answer what happened, why it might matter, "
    "affected systems, what is known, what is not known, and what the analyst should check next. "
    "Do not state unverified compromise as fact. Return JSON only with fields: finding, evidence_refs, confidence_label, "
    "unknowns, recommended_actions, what_happened, why_it_might_matter, affected_systems, what_we_know, "
    "what_we_do_not_know, next_check."
)


def explain_for_manager(evidence: Dict) -> ManagerExplanation:
    prompt = "Explain this validated incident:\n\n" + json.dumps(evidence, default=str)
    result, provider, model = get_router().run(
        task="manager", system_prompt=SYSTEM, user_prompt=prompt, schema=ManagerExplanation
    )
    result.provider = provider
    result.model = model
    result.prompt_version = PROMPT_VERSION
    return result
