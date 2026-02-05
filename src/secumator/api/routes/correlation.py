from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from secumator.core import get_logger, vulnerability_correlator, cve_lookup, cvss_calculator
from secumator.core.database import get_db
from secumator.models.scan import Scan, Finding

router = APIRouter()
logger = get_logger("api.correlation")


class CorrelatedFindingResponse(BaseModel):
    id: str
    title: str
    severity: str
    description: str
    affected_components: list[str]
    source_tools: list[str]
    cve_ids: list[str]
    evidence: list[str]
    recommendations: list[str]
    confidence: float
    correlated_count: int


class CorrelationResultResponse(BaseModel):
    total_raw_findings: int
    total_correlated: int
    dedup_ratio: float
    severity_distribution: dict[str, int]
    affected_components: list[str]
    correlation_summary: dict[str, Any]
    findings: list[CorrelatedFindingResponse]


class CVELookupResponse(BaseModel):
    cve_id: str | None
    description: str | None
    cvss_score: float | None
    severity: str | None
    cvss_vector: str | None
    published: str | None
    references: list[str]
    weaknesses: list[str]


class CVSSCalculateRequest(BaseModel):
    vector: str


class CVSSCalculateResponse(BaseModel):
    version: str
    vector: str
    base_score: float
    severity: str
    impact_score: float | None
    exploitability_score: float | None


@router.get("/scans/{scan_id}/correlate", response_model=CorrelationResultResponse)
async def correlate_scan_findings(scan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan).options(selectinload(Scan.findings)).where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    correlation_result = vulnerability_correlator.correlate(scan.findings)

    return CorrelationResultResponse(
        total_raw_findings=correlation_result.total_raw_findings,
        total_correlated=correlation_result.total_correlated,
        dedup_ratio=correlation_result.dedup_ratio,
        severity_distribution=correlation_result.severity_distribution,
        affected_components=correlation_result.affected_components,
        correlation_summary=correlation_result.correlation_summary,
        findings=[
            CorrelatedFindingResponse(
                id=cf.id,
                title=cf.title,
                severity=cf.severity.value,
                description=cf.description,
                affected_components=cf.affected_components,
                source_tools=cf.source_tools,
                cve_ids=cf.cve_ids,
                evidence=cf.evidence,
                recommendations=cf.recommendations,
                confidence=cf.confidence,
                correlated_count=cf.correlated_count,
            )
            for cf in correlation_result.correlated_findings
        ],
    )


@router.get("/cve/{cve_id}", response_model=CVELookupResponse)
async def lookup_cve(cve_id: str):
    result = await cve_lookup.lookup(cve_id)

    if not result:
        raise HTTPException(status_code=404, detail="CVE not found")

    return CVELookupResponse(
        cve_id=result.get("cve_id"),
        description=result.get("description"),
        cvss_score=result.get("cvss_score"),
        severity=result.get("severity"),
        cvss_vector=result.get("cvss_vector"),
        published=result.get("published"),
        references=result.get("references", []),
        weaknesses=result.get("weaknesses", []),
    )


@router.post("/cvss/calculate", response_model=CVSSCalculateResponse)
async def calculate_cvss(request: CVSSCalculateRequest):
    try:
        score = cvss_calculator.calculate(request.vector)
        return CVSSCalculateResponse(
            version=score.version.value,
            vector=score.vector,
            base_score=score.base_score,
            severity=score.severity,
            impact_score=score.impact_score,
            exploitability_score=score.exploitability_score,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/scans/{scan_id}/enrich-cves")
async def enrich_scan_cves(scan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan).options(selectinload(Scan.findings)).where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    enriched = 0
    for finding in scan.findings:
        if finding.cve_id and not finding.cvss_score:
            cve_data = await cve_lookup.lookup(finding.cve_id.split(",")[0].strip())
            if cve_data and cve_data.get("cvss_score"):
                finding.cvss_score = cve_data["cvss_score"]
                if not finding.description:
                    finding.description = cve_data.get("description")
                enriched += 1

    await db.commit()
    logger.info("cves_enriched", scan_id=scan_id, count=enriched)

    return {"status": "enriched", "scan_id": scan_id, "enriched_count": enriched}
