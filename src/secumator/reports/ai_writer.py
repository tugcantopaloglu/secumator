from typing import Any
import httpx
from secumator.core import get_logger, settings
from secumator.models.scan import Finding, Scan, Severity


class AIReportWriter:
    def __init__(self):
        self.logger = get_logger("ai_writer")
        self.provider = settings.ai_provider
        self.model = settings.ai_model

    async def generate_executive_summary(self, scan: Scan, findings: list[Finding]) -> str:
        severity_counts = self._count_severities(findings)
        prompt = self._build_executive_summary_prompt(scan, findings, severity_counts)

        try:
            response = await self._call_ai(prompt)
            return response
        except Exception as e:
            self.logger.error("ai_summary_failed", error=str(e))
            return self._generate_fallback_summary(scan, findings, severity_counts)

    async def generate_finding_analysis(self, finding: Finding) -> dict[str, str]:
        prompt = self._build_finding_analysis_prompt(finding)

        try:
            response = await self._call_ai(prompt)
            return {"analysis": response, "ai_generated": True}
        except Exception as e:
            self.logger.error("ai_analysis_failed", finding_id=finding.id, error=str(e))
            return {"analysis": finding.description or "", "ai_generated": False}

    async def generate_remediation_plan(self, findings: list[Finding]) -> str:
        critical_high = [f for f in findings if f.severity in (Severity.CRITICAL, Severity.HIGH)]
        if not critical_high:
            critical_high = findings[:10]

        prompt = self._build_remediation_prompt(critical_high)

        try:
            response = await self._call_ai(prompt)
            return response
        except Exception as e:
            self.logger.error("ai_remediation_failed", error=str(e))
            return self._generate_fallback_remediation(critical_high)

    async def _call_ai(self, prompt: str) -> str:
        if self.provider == "anthropic":
            return await self._call_anthropic(prompt)
        return await self._call_openai(prompt)

    async def _call_openai(self, prompt: str) -> str:
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a professional cybersecurity analyst writing a security audit report. Be concise, technical, and actionable."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.3,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    async def _call_anthropic(self, prompt: str) -> str:
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": self.model if "claude" in self.model else "claude-3-sonnet-20240229",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                    "system": "You are a professional cybersecurity analyst writing a security audit report. Be concise, technical, and actionable.",
                },
            )
            response.raise_for_status()
            return response.json()["content"][0]["text"]

    def _count_severities(self, findings: list[Finding]) -> dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            counts[f.severity.value] = counts.get(f.severity.value, 0) + 1
        return counts

    def _build_executive_summary_prompt(self, scan: Scan, findings: list[Finding], severity_counts: dict[str, int]) -> str:
        finding_summaries = []
        for f in findings[:20]:
            finding_summaries.append(f"- [{f.severity.value.upper()}] {f.title}")

        return f"""Write a professional executive summary for a security audit report.

Target: {scan.target}
Scan Type: {scan.scan_type.value}
Total Findings: {len(findings)}
Critical: {severity_counts['critical']}, High: {severity_counts['high']}, Medium: {severity_counts['medium']}, Low: {severity_counts['low']}, Info: {severity_counts['info']}

Top Findings:
{chr(10).join(finding_summaries)}

Write 2-3 paragraphs covering:
1. Overall security posture assessment
2. Key risks identified
3. Recommended immediate actions"""

    def _build_finding_analysis_prompt(self, finding: Finding) -> str:
        return f"""Analyze this security finding and provide technical details:

Title: {finding.title}
Severity: {finding.severity.value}
Description: {finding.description or 'N/A'}
Evidence: {finding.evidence or 'N/A'}
CVE: {finding.cve_id or 'N/A'}

Provide:
1. Technical explanation of the vulnerability
2. Potential impact if exploited
3. Attack scenarios"""

    def _build_remediation_prompt(self, findings: list[Finding]) -> str:
        finding_list = []
        for f in findings:
            finding_list.append(f"- [{f.severity.value.upper()}] {f.title}: {f.description or 'N/A'}")

        return f"""Create a prioritized remediation plan for these security findings:

{chr(10).join(finding_list)}

Provide:
1. Immediate actions (within 24-48 hours)
2. Short-term fixes (within 1-2 weeks)
3. Long-term improvements
4. Quick wins that are easy to implement"""

    def _generate_fallback_summary(self, scan: Scan, findings: list[Finding], severity_counts: dict[str, int]) -> str:
        risk_level = "CRITICAL" if severity_counts["critical"] > 0 else "HIGH" if severity_counts["high"] > 0 else "MEDIUM" if severity_counts["medium"] > 0 else "LOW"

        return f"""## Executive Summary

A security assessment was conducted on **{scan.target}** using automated scanning tools. The assessment identified **{len(findings)} findings** across various severity levels.

### Risk Overview
- **Critical Issues:** {severity_counts['critical']}
- **High Issues:** {severity_counts['high']}
- **Medium Issues:** {severity_counts['medium']}
- **Low Issues:** {severity_counts['low']}
- **Informational:** {severity_counts['info']}

### Overall Risk Rating: {risk_level}

Immediate attention is recommended for all critical and high severity findings. A detailed remediation plan should be developed to address the identified vulnerabilities in order of severity."""

    def _generate_fallback_remediation(self, findings: list[Finding]) -> str:
        remediation_items = []
        for i, f in enumerate(findings[:10], 1):
            remediation_items.append(f"{i}. **{f.title}**: {f.recommendation or 'Review and remediate this issue.'}")

        return f"""## Remediation Plan

The following issues should be addressed in priority order:

{chr(10).join(remediation_items)}

### General Recommendations
1. Patch all systems to the latest security updates
2. Review and harden server configurations
3. Implement security headers and best practices
4. Conduct regular security assessments"""
