"""models/schemas.py — Pydantic request/response contracts for the API layer."""
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    goal: str = Field(..., min_length=3, max_length=500)


class ResearchResponse(BaseModel):
    plan: list[str]
    final_report: str
    report_path: str


class ReportSummary(BaseModel):
    id: int
    goal: str
    path: str
    created_at: str


class ReportDetail(ReportSummary):
    content: str
