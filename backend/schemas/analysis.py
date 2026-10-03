from typing import List, Optional
from pydantic import BaseModel, Field


class TriageResult(BaseModel):
    finding: str
    evidence_refs: List[str] = Field(default_factory=list)
    confidence_label: str = "unknown"
    unknowns: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    provider: str = "unknown"
    model: str = "unknown"
    prompt_version: str = "unknown"


class InvestigationResult(TriageResult):
    timeline_summary: str = ""
    next_investigation_steps: List[str] = Field(default_factory=list)


class ResponseResult(TriageResult):
    reason: str = ""
    impact: str = ""
    rollback: List[str] = Field(default_factory=list)
    verification: List[str] = Field(default_factory=list)


class ManagerExplanation(TriageResult):
    what_happened: str = ""
    why_it_might_matter: str = ""
    affected_systems: List[str] = Field(default_factory=list)
    what_we_know: List[str] = Field(default_factory=list)
    what_we_do_not_know: List[str] = Field(default_factory=list)
    next_check: List[str] = Field(default_factory=list)


class ReportResult(TriageResult):
    executive_summary: str = ""
    technical_summary: str = ""
    timeline: List[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    task: str
    force: bool = False
