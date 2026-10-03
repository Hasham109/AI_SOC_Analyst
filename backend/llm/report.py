import json
from typing import Dict
from backend.llm.router import get_router
from backend.schemas.analysis import ReportResult

PROMPT_VERSION = "report-v1"
SYSTEM = (
    "You write a SOC incident report from saved evidence. Keep observed evidence, AI interpretation, and "
    "recommended next steps distinct. Do not fabricate compromise, remediation, or threat-intelligence claims. "
    "Return JSON only with fields: finding, evidence_refs, confidence_label, unknowns, recommended_actions, "
    "executive_summary, technical_summary, timeline."
)


def write_report(evidence: Dict) -> ReportResult:
    prompt = "Write a structured incident report from this saved data:\n\n" + json.dumps(evidence, default=str)
    result, provider, model = get_router().run(
        task="report", system_prompt=SYSTEM, user_prompt=prompt, schema=ReportResult
    )
    result.provider = provider
    result.model = model
    result.prompt_version = PROMPT_VERSION
    return result
