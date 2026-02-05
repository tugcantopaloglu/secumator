from dataclasses import dataclass, field
from typing import Any, Literal
import yaml
from pathlib import Path
from secumator.core import get_logger
from secumator.models.scan import ScanType

logger = get_logger("templates")


@dataclass
class ScanTemplate:
    name: str
    description: str
    scan_type: ScanType
    options: dict[str, Any] = field(default_factory=dict)
    nuclei_templates: list[str] = field(default_factory=list)
    nuclei_tags: list[str] = field(default_factory=list)
    nuclei_severity: list[str] = field(default_factory=list)
    nmap_args: list[str] = field(default_factory=list)
    nikto_args: list[str] = field(default_factory=list)
    rate_limit: int = 150
    timeout: int = 3600
    enabled_scanners: list[str] = field(default_factory=lambda: ["nuclei", "nmap", "nikto"])
    tags: list[str] = field(default_factory=list)


BUILTIN_TEMPLATES: dict[str, ScanTemplate] = {
    "quick-web": ScanTemplate(
        name="quick-web",
        description="Quick web application scan with critical/high severity focus",
        scan_type=ScanType.WEBAPP,
        nuclei_severity=["critical", "high"],
        nuclei_tags=["cve", "sqli", "xss", "rce"],
        rate_limit=200,
        timeout=1800,
        enabled_scanners=["nuclei"],
        tags=["quick", "web", "critical"],
    ),
    "full-web": ScanTemplate(
        name="full-web",
        description="Comprehensive web application security assessment",
        scan_type=ScanType.WEBAPP,
        nuclei_severity=["critical", "high", "medium", "low"],
        nuclei_tags=["cve", "sqli", "xss", "rce", "lfi", "ssrf", "xxe", "ssti"],
        rate_limit=100,
        timeout=7200,
        enabled_scanners=["nuclei", "nikto"],
        tags=["comprehensive", "web"],
    ),
    "owasp-top10": ScanTemplate(
        name="owasp-top10",
        description="OWASP Top 10 vulnerability assessment",
        scan_type=ScanType.WEBAPP,
        nuclei_tags=["owasp", "owasp-top-10"],
        rate_limit=150,
        timeout=3600,
        enabled_scanners=["nuclei"],
        tags=["owasp", "compliance", "web"],
    ),
    "cve-scan": ScanTemplate(
        name="cve-scan",
        description="Known CVE vulnerability scan",
        scan_type=ScanType.WEBAPP,
        nuclei_tags=["cve"],
        nuclei_severity=["critical", "high"],
        rate_limit=200,
        timeout=3600,
        enabled_scanners=["nuclei"],
        tags=["cve", "vulnerability"],
    ),
    "network-discovery": ScanTemplate(
        name="network-discovery",
        description="Network host discovery and service enumeration",
        scan_type=ScanType.NETWORK,
        nmap_args=["-sV", "-sC", "--top-ports", "1000"],
        timeout=3600,
        enabled_scanners=["nmap"],
        tags=["network", "discovery"],
    ),
    "network-full": ScanTemplate(
        name="network-full",
        description="Full network security scan with all ports",
        scan_type=ScanType.NETWORK,
        nmap_args=["-sV", "-sC", "-p-", "-A"],
        timeout=14400,
        enabled_scanners=["nmap"],
        tags=["network", "comprehensive"],
    ),
    "stealth-scan": ScanTemplate(
        name="stealth-scan",
        description="Low-profile stealth scan with reduced rate",
        scan_type=ScanType.WEBAPP,
        nuclei_severity=["critical", "high"],
        rate_limit=10,
        timeout=7200,
        enabled_scanners=["nuclei"],
        options={"stealth": True},
        tags=["stealth", "evasion"],
    ),
    "api-security": ScanTemplate(
        name="api-security",
        description="API security assessment",
        scan_type=ScanType.API,
        nuclei_tags=["api", "graphql", "rest"],
        nuclei_severity=["critical", "high", "medium"],
        rate_limit=100,
        timeout=3600,
        enabled_scanners=["nuclei"],
        tags=["api", "rest", "graphql"],
    ),
    "cms-scan": ScanTemplate(
        name="cms-scan",
        description="CMS vulnerability scan (WordPress, Drupal, Joomla)",
        scan_type=ScanType.WEBAPP,
        nuclei_tags=["wordpress", "drupal", "joomla", "cms"],
        rate_limit=150,
        timeout=3600,
        enabled_scanners=["nuclei", "nikto"],
        tags=["cms", "wordpress", "drupal"],
    ),
    "cloud-misconfig": ScanTemplate(
        name="cloud-misconfig",
        description="Cloud misconfiguration detection (AWS, Azure, GCP)",
        scan_type=ScanType.WEBAPP,
        nuclei_tags=["aws", "azure", "gcp", "cloud", "misconfig"],
        rate_limit=100,
        timeout=3600,
        enabled_scanners=["nuclei"],
        tags=["cloud", "aws", "azure", "gcp"],
    ),
    "exposed-panels": ScanTemplate(
        name="exposed-panels",
        description="Detect exposed admin panels and dashboards",
        scan_type=ScanType.WEBAPP,
        nuclei_tags=["panel", "login", "admin"],
        nuclei_severity=["info", "low", "medium"],
        rate_limit=200,
        timeout=1800,
        enabled_scanners=["nuclei"],
        tags=["exposure", "panels", "recon"],
    ),
    "ssl-tls": ScanTemplate(
        name="ssl-tls",
        description="SSL/TLS configuration and vulnerability assessment",
        scan_type=ScanType.WEBAPP,
        nuclei_tags=["ssl", "tls"],
        nmap_args=["--script", "ssl-enum-ciphers,ssl-cert,ssl-known-key"],
        timeout=1800,
        enabled_scanners=["nuclei", "nmap"],
        tags=["ssl", "tls", "crypto"],
    ),
    "pentest-full": ScanTemplate(
        name="pentest-full",
        description="Full penetration test simulation",
        scan_type=ScanType.FULL,
        nuclei_severity=["critical", "high", "medium", "low", "info"],
        nmap_args=["-sV", "-sC", "-A", "--top-ports", "10000"],
        rate_limit=50,
        timeout=28800,
        enabled_scanners=["nuclei", "nmap", "nikto"],
        tags=["pentest", "comprehensive"],
    ),
}


class TemplateManager:
    def __init__(self, custom_dir: Path | None = None):
        self._templates: dict[str, ScanTemplate] = dict(BUILTIN_TEMPLATES)
        self._custom_dir = custom_dir or Path.home() / ".secumator" / "templates"
        self._load_custom_templates()

    def _load_custom_templates(self):
        if not self._custom_dir.exists():
            self._custom_dir.mkdir(parents=True, exist_ok=True)
            return

        for file in self._custom_dir.glob("*.yaml"):
            try:
                with open(file) as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        template = ScanTemplate(
                            name=data.get("name", file.stem),
                            description=data.get("description", ""),
                            scan_type=ScanType(data.get("scan_type", "webapp")),
                            options=data.get("options", {}),
                            nuclei_templates=data.get("nuclei_templates", []),
                            nuclei_tags=data.get("nuclei_tags", []),
                            nuclei_severity=data.get("nuclei_severity", []),
                            nmap_args=data.get("nmap_args", []),
                            nikto_args=data.get("nikto_args", []),
                            rate_limit=data.get("rate_limit", 150),
                            timeout=data.get("timeout", 3600),
                            enabled_scanners=data.get("enabled_scanners", ["nuclei", "nmap", "nikto"]),
                            tags=data.get("tags", []),
                        )
                        self._templates[template.name] = template
                        logger.info("custom_template_loaded", name=template.name)
            except Exception as e:
                logger.error("template_load_error", file=str(file), error=str(e))

    def get(self, name: str) -> ScanTemplate | None:
        return self._templates.get(name)

    def list_all(self) -> list[ScanTemplate]:
        return list(self._templates.values())

    def list_by_tag(self, tag: str) -> list[ScanTemplate]:
        return [t for t in self._templates.values() if tag in t.tags]

    def list_by_type(self, scan_type: ScanType) -> list[ScanTemplate]:
        return [t for t in self._templates.values() if t.scan_type == scan_type]

    def save_custom(self, template: ScanTemplate):
        file_path = self._custom_dir / f"{template.name}.yaml"
        data = {
            "name": template.name,
            "description": template.description,
            "scan_type": template.scan_type.value,
            "options": template.options,
            "nuclei_templates": template.nuclei_templates,
            "nuclei_tags": template.nuclei_tags,
            "nuclei_severity": template.nuclei_severity,
            "nmap_args": template.nmap_args,
            "nikto_args": template.nikto_args,
            "rate_limit": template.rate_limit,
            "timeout": template.timeout,
            "enabled_scanners": template.enabled_scanners,
            "tags": template.tags,
        }
        with open(file_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        self._templates[template.name] = template
        logger.info("template_saved", name=template.name, path=str(file_path))

    def delete_custom(self, name: str) -> bool:
        if name in BUILTIN_TEMPLATES:
            logger.warning("cannot_delete_builtin", name=name)
            return False

        file_path = self._custom_dir / f"{name}.yaml"
        if file_path.exists():
            file_path.unlink()
            del self._templates[name]
            logger.info("template_deleted", name=name)
            return True
        return False

    def to_scan_options(self, template: ScanTemplate) -> dict[str, Any]:
        options = dict(template.options)
        options["rate_limit"] = template.rate_limit
        options["timeout"] = template.timeout

        if template.nuclei_templates:
            options["templates"] = ",".join(template.nuclei_templates)
        if template.nuclei_tags:
            options["tags"] = ",".join(template.nuclei_tags)
        if template.nuclei_severity:
            options["severity"] = ",".join(template.nuclei_severity)

        options["nmap_args"] = template.nmap_args
        options["nikto_args"] = template.nikto_args
        options["enabled_scanners"] = template.enabled_scanners

        return options


template_manager = TemplateManager()
