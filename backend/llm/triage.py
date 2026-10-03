import json
from typing import Dict
from backend.llm.router import get_router
from backend.schemas.analysis import TriageResult

PROMPT_VERSION = "triage-v1"
SYSTEM = (
    "You are a SOC triage assistant. Use only the evidence supplied. "
    "Do not invent IPs, users, devices, timestamps, logins, or remediation results. "
    "Separate observations from inference and allow unknowns. Return JSON only with fields: "
    "finding, evidence_refs, confidence_label, unknowns, recommended_actions."
)


def triage_alert(evidence: Dict) -> TriageResult:
    user = json.dumps(evidence, default=str)
    prompt = (
        "Review this normalized Wazuh evidence. State what happened in plain English, "
        "list evidence references, identify unknowns, and provide non-destructive analyst checks. "
        "Do not say a host is compromised unless the evidence supports it.\n\n" + user
    )
    result, provider, model = get_router().run(
        task="triage", system_prompt=SYSTEM, user_prompt=prompt, schema=TriageResult
    )
    result.provider = provider
    result.model = model
    result.prompt_version = PROMPT_VERSION
    return result
