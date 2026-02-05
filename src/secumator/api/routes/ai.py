from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from secumator.core import get_logger, settings
from secumator.core.database import get_db
from secumator.models.scan import Scan

router = APIRouter()
logger = get_logger("api.ai")


class VulnerabilityExplanationRequest(BaseModel):
    title: str
    severity: str
    description: str | None = None
    cve_id: str | None = None
    affected_component: str | None = None


class VulnerabilityExplanationResponse(BaseModel):
    explanation: str
    risk_score: float
    risk_factors: list[str]
    business_impact: str
    technical_details: str
    exploitation_likelihood: str


class RemediationRequest(BaseModel):
    title: str
    severity: str
    description: str | None = None
    affected_component: str | None = None
    technology_stack: list[str] = Field(default_factory=list)


class RemediationResponse(BaseModel):
    immediate_actions: list[str]
    short_term_fixes: list[str]
    long_term_solutions: list[str]
    code_examples: dict[str, str]
    resources: list[str]
    estimated_effort: str
    priority: str


class RiskScoringRequest(BaseModel):
    findings: list[dict[str, Any]]
    context: dict[str, Any] = Field(default_factory=dict)


class RiskScoringResponse(BaseModel):
    overall_risk_score: float
    risk_level: str
    finding_scores: list[dict[str, Any]]
    risk_summary: str
    top_priorities: list[str]
    executive_summary: str


async def get_ai_client():
    if settings.ai_provider == "anthropic":
        import anthropic
        return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    else:
        import openai
        return openai.AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_completion(prompt: str, system_prompt: str = "") -> str:
    client = await get_ai_client()
    
    if settings.ai_provider == "anthropic":
        response = await client.messages.create(
            model=settings.ai_model or "claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    else:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await client.chat.completions.create(
            model=settings.ai_model or "gpt-4o",
            messages=messages,
            max_tokens=2000,
        )
        return response.choices[0].message.content


@router.post("/ai/explain", response_model=VulnerabilityExplanationResponse)
async def explain_vulnerability(request: VulnerabilityExplanationRequest):
    system_prompt = """You are a cybersecurity expert. Explain vulnerabilities in a clear, actionable way.
Provide practical risk assessment and business context. Be concise but thorough."""

    prompt = f"""Explain this vulnerability and assess its risk:

Title: {request.title}
Severity: {request.severity}
Description: {request.description or 'N/A'}
CVE ID: {request.cve_id or 'N/A'}
Affected Component: {request.affected_component or 'N/A'}

Provide:
1. Clear explanation of what this vulnerability is
2. Risk score (0-10) with factors
3. Business impact
4. Technical details
5. Likelihood of exploitation (Low/Medium/High/Critical)

Format your response as JSON:
{{
  "explanation": "...",
  "risk_score": 7.5,
  "risk_factors": ["factor1", "factor2"],
  "business_impact": "...",
  "technical_details": "...",
  "exploitation_likelihood": "High"
}}"""

    try:
        result = await generate_completion(prompt, system_prompt)
        import json
        data = json.loads(result.strip().replace("```json", "").replace("```", ""))
        return VulnerabilityExplanationResponse(**data)
    except Exception as e:
        logger.error("ai_explain_failed", error=str(e))
        return VulnerabilityExplanationResponse(
            explanation=f"Unable to generate AI explanation: {str(e)}",
            risk_score=5.0,
            risk_factors=["AI analysis unavailable"],
            business_impact="Manual assessment required",
            technical_details=request.description or "No details provided",
            exploitation_likelihood="Unknown",
        )


@router.post("/ai/remediate", response_model=RemediationResponse)
async def suggest_remediation(request: RemediationRequest):
    system_prompt = """You are a senior security engineer. Provide practical, implementable remediation advice.
Include code examples where relevant. Be specific to the technology stack when provided."""

    tech_stack_info = ", ".join(request.technology_stack) if request.technology_stack else "Unknown"
    
    prompt = f"""Suggest remediation for this vulnerability:

Title: {request.title}
Severity: {request.severity}
Description: {request.description or 'N/A'}
Affected Component: {request.affected_component or 'N/A'}
Technology Stack: {tech_stack_info}

Provide:
1. Immediate actions (stop the bleeding)
2. Short-term fixes (days)
3. Long-term solutions (weeks/months)
4. Code examples for fixes
5. Helpful resources/links
6. Estimated effort (hours/days/weeks)
7. Priority (P0-P3)

Format as JSON:
{{
  "immediate_actions": ["action1", "action2"],
  "short_term_fixes": ["fix1", "fix2"],
  "long_term_solutions": ["solution1", "solution2"],
  "code_examples": {{"language": "code snippet"}},
  "resources": ["url1", "url2"],
  "estimated_effort": "2-4 hours",
  "priority": "P1"
}}"""

    try:
        result = await generate_completion(prompt, system_prompt)
        import json
        data = json.loads(result.strip().replace("```json", "").replace("```", ""))
        return RemediationResponse(**data)
    except Exception as e:
        logger.error("ai_remediate_failed", error=str(e))
        return RemediationResponse(
            immediate_actions=["Review affected component immediately"],
            short_term_fixes=["Apply vendor patches if available"],
            long_term_solutions=["Implement security monitoring"],
            code_examples={},
            resources=["https://owasp.org/"],
            estimated_effort="Varies",
            priority="P2",
        )


@router.post("/ai/risk-score", response_model=RiskScoringResponse)
async def calculate_risk_score(request: RiskScoringRequest):
    system_prompt = """You are a security risk analyst. Analyze findings and provide comprehensive risk scoring.
Consider business context, exploitability, and impact. Prioritize findings effectively."""

    findings_summary = "\n".join([
        f"- {f.get('title', 'Unknown')}: {f.get('severity', 'unknown')} severity"
        for f in request.findings[:20]
    ])
    
    prompt = f"""Analyze these security findings and calculate risk:

Findings ({len(request.findings)} total):
{findings_summary}

Context: {request.context}

Provide:
1. Overall risk score (0-100)
2. Risk level (Low/Medium/High/Critical)
3. Individual finding scores
4. Risk summary paragraph
5. Top 5 priorities
6. Executive summary (2-3 sentences)

Format as JSON:
{{
  "overall_risk_score": 75.0,
  "risk_level": "High",
  "finding_scores": [{{"title": "...", "score": 8.5, "priority": 1}}],
  "risk_summary": "...",
  "top_priorities": ["priority1", "priority2"],
  "executive_summary": "..."
}}"""

    try:
        result = await generate_completion(prompt, system_prompt)
        import json
        data = json.loads(result.strip().replace("```json", "").replace("```", ""))
        return RiskScoringResponse(**data)
    except Exception as e:
        logger.error("ai_risk_score_failed", error=str(e))
        
        severity_weights = {"critical": 10, "high": 7, "medium": 4, "low": 2, "info": 0}
        total = sum(severity_weights.get(f.get("severity", "info"), 0) for f in request.findings)
        max_possible = len(request.findings) * 10
        score = (total / max_possible * 100) if max_possible > 0 else 0
        
        level = "Low"
        if score >= 75:
            level = "Critical"
        elif score >= 50:
            level = "High"
        elif score >= 25:
            level = "Medium"
        
        return RiskScoringResponse(
            overall_risk_score=round(score, 1),
            risk_level=level,
            finding_scores=[{"title": f.get("title", "Unknown"), "score": severity_weights.get(f.get("severity", "info"), 0)} for f in request.findings[:10]],
            risk_summary=f"Analysis of {len(request.findings)} findings resulted in {level} risk level.",
            top_priorities=[f.get("title", "Unknown") for f in request.findings if f.get("severity") in ["critical", "high"]][:5],
            executive_summary=f"Security scan identified {len(request.findings)} findings with an overall risk score of {round(score, 1)}/100.",
        )


@router.get("/ai/scan/{scan_id}/summary")
async def get_ai_scan_summary(scan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan).options(selectinload(Scan.findings)).where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    findings = [
        {"title": f.title, "severity": f.severity, "description": f.description}
        for f in scan.findings
    ]
    
    risk_response = await calculate_risk_score(
        RiskScoringRequest(findings=findings, context={"target": scan.target, "scan_type": scan.scan_type})
    )
    
    return {
        "scan_id": scan_id,
        "target": scan.target,
        "findings_count": len(findings),
        "risk_score": risk_response.overall_risk_score,
        "risk_level": risk_response.risk_level,
        "executive_summary": risk_response.executive_summary,
        "top_priorities": risk_response.top_priorities,
    }
