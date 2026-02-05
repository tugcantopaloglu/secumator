from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, HttpUrl


class ScanCreate(BaseModel):
    target: str = Field(..., min_length=1, max_length=500, description="Target URL or IP address")
    scan_type: Literal["webapp", "network", "api", "full"] = Field(default="webapp")
    profile: str | None = Field(default=None, max_length=100, description="Scan profile name")
    options: dict[str, Any] | None = Field(default=None, description="Additional scan options")


class FindingResponse(BaseModel):
    id: int
    title: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    description: str | None
    evidence: str | None
    recommendation: str | None
    cve_id: str | None
    cvss_score: float | None
    affected_component: str | None
    source_tool: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ScanResponse(BaseModel):
    id: int
    target: str
    scan_type: Literal["webapp", "network", "api", "full"]
    status: Literal["pending", "running", "completed", "failed", "cancelled"]
    profile: str | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    findings_count: int = 0
    findings: list[FindingResponse] = []

    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    total: int
    items: list[ScanResponse]


class ReportRequest(BaseModel):
    scan_id: int
    format: Literal["pdf", "html", "json"] = "pdf"
    template: str = "professional"
    include_executive_summary: bool = True
    include_ai_analysis: bool = True


class ReportResponse(BaseModel):
    scan_id: int
    format: str
    filename: str
    download_url: str
    generated_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    redis: str
