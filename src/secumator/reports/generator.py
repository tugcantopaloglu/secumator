import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from secumator.core import get_logger, settings
from secumator.models.scan import Finding, Scan, Severity
from .ai_writer import AIReportWriter


class ReportGenerator:
    def __init__(self):
        self.logger = get_logger("report_generator")
        self.ai_writer = AIReportWriter()
        self.output_dir = Path(settings.report_output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        self.env.filters["severity_color"] = self._severity_color
        self.env.filters["severity_badge"] = self._severity_badge

    async def generate(
        self,
        scan: Scan,
        findings: list[Finding],
        format: str = "pdf",
        template: str = "professional",
        include_executive_summary: bool = True,
        include_ai_analysis: bool = True,
    ) -> Path:
        self.logger.info("generating_report", scan_id=scan.id, format=format, template=template)

        report_data = await self._prepare_report_data(
            scan, findings, include_executive_summary, include_ai_analysis
        )

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        base_filename = f"secumator_report_{scan.id}_{timestamp}"

        if format == "json":
            return self._generate_json(report_data, base_filename)
        elif format == "html":
            return self._generate_html(report_data, template, base_filename)
        else:
            return await self._generate_pdf(report_data, template, base_filename)

    async def _prepare_report_data(
        self,
        scan: Scan,
        findings: list[Finding],
        include_executive_summary: bool,
        include_ai_analysis: bool,
    ) -> dict[str, Any]:
        severity_counts = {
            "critical": sum(1 for f in findings if f.severity == Severity.CRITICAL),
            "high": sum(1 for f in findings if f.severity == Severity.HIGH),
            "medium": sum(1 for f in findings if f.severity == Severity.MEDIUM),
            "low": sum(1 for f in findings if f.severity == Severity.LOW),
            "info": sum(1 for f in findings if f.severity == Severity.INFO),
        }

        sorted_findings = sorted(findings, key=lambda f: self._severity_order(f.severity))

        executive_summary = ""
        remediation_plan = ""

        if include_ai_analysis and (settings.openai_api_key or settings.anthropic_api_key):
            if include_executive_summary:
                executive_summary = await self.ai_writer.generate_executive_summary(scan, findings)
            if findings:
                remediation_plan = await self.ai_writer.generate_remediation_plan(findings)
        elif include_executive_summary:
            executive_summary = self.ai_writer._generate_fallback_summary(scan, findings, severity_counts)

        findings_data = []
        for f in sorted_findings:
            findings_data.append({
                "id": f.id,
                "title": f.title,
                "severity": f.severity.value,
                "description": f.description,
                "evidence": f.evidence,
                "recommendation": f.recommendation,
                "cve_id": f.cve_id,
                "cvss_score": f.cvss_score,
                "affected_component": f.affected_component,
                "source_tool": f.source_tool,
            })

        return {
            "report_title": f"Security Assessment Report",
            "target": scan.target,
            "scan_type": scan.scan_type.value,
            "scan_id": scan.id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scan_started": scan.started_at.isoformat() if scan.started_at else None,
            "scan_completed": scan.completed_at.isoformat() if scan.completed_at else None,
            "total_findings": len(findings),
            "severity_counts": severity_counts,
            "executive_summary": executive_summary,
            "remediation_plan": remediation_plan,
            "findings": findings_data,
            "risk_score": self._calculate_risk_score(severity_counts),
        }

    def _generate_json(self, report_data: dict[str, Any], base_filename: str) -> Path:
        output_path = self.output_dir / f"{base_filename}.json"
        output_path.write_text(json.dumps(report_data, indent=2, default=str))
        self.logger.info("report_generated", path=str(output_path), format="json")
        return output_path

    def _generate_html(self, report_data: dict[str, Any], template: str, base_filename: str) -> Path:
        template_file = f"{template}.html"
        try:
            tmpl = self.env.get_template(template_file)
        except Exception:
            tmpl = self.env.get_template("professional.html")

        html_content = tmpl.render(**report_data)
        output_path = self.output_dir / f"{base_filename}.html"
        output_path.write_text(html_content)
        self.logger.info("report_generated", path=str(output_path), format="html")
        return output_path

    async def _generate_pdf(self, report_data: dict[str, Any], template: str, base_filename: str) -> Path:
        html_path = self._generate_html(report_data, template, f"{base_filename}_temp")

        output_path = self.output_dir / f"{base_filename}.pdf"
        HTML(filename=str(html_path)).write_pdf(str(output_path))

        html_path.unlink()
        self.logger.info("report_generated", path=str(output_path), format="pdf")
        return output_path

    @staticmethod
    def _severity_order(severity: Severity) -> int:
        order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        return order.get(severity, 5)

    @staticmethod
    def _severity_color(severity: str) -> str:
        colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#17a2b8",
            "info": "#6c757d",
        }
        return colors.get(severity.lower(), "#6c757d")

    @staticmethod
    def _severity_badge(severity: str) -> str:
        return f'<span class="badge badge-{severity.lower()}">{severity.upper()}</span>'

    @staticmethod
    def _calculate_risk_score(severity_counts: dict[str, int]) -> float:
        weights = {"critical": 40, "high": 20, "medium": 10, "low": 5, "info": 1}
        total = sum(severity_counts[k] * weights[k] for k in severity_counts)
        max_score = 100
        return min(total, max_score)
