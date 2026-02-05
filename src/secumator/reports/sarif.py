import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from secumator.core import get_logger
from secumator.models.scan import Finding, Scan, Severity

logger = get_logger("sarif")

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"


class SARIFExporter:
    SEVERITY_TO_LEVEL = {
        Severity.CRITICAL: "error",
        Severity.HIGH: "error",
        Severity.MEDIUM: "warning",
        Severity.LOW: "note",
        Severity.INFO: "none",
    }

    SEVERITY_TO_RANK = {
        Severity.CRITICAL: 1.0,
        Severity.HIGH: 0.8,
        Severity.MEDIUM: 0.5,
        Severity.LOW: 0.3,
        Severity.INFO: 0.1,
    }

    def __init__(self, organization: str = "Secumator", tool_name: str = "Secumator Security Scanner"):
        self.organization = organization
        self.tool_name = tool_name

    def export(self, scan: Scan, findings: list[Finding], output_path: Path | None = None) -> dict[str, Any]:
        sarif_output = {
            "$schema": SARIF_SCHEMA,
            "version": SARIF_VERSION,
            "runs": [self._create_run(scan, findings)],
        }

        if output_path:
            output_path.write_text(json.dumps(sarif_output, indent=2, default=str))
            logger.info("sarif_exported", path=str(output_path), findings=len(findings))

        return sarif_output

    def _create_run(self, scan: Scan, findings: list[Finding]) -> dict[str, Any]:
        rules = self._create_rules(findings)
        results = self._create_results(findings, rules)

        invocations = [{
            "executionSuccessful": scan.status.value == "completed",
            "startTimeUtc": scan.started_at.isoformat() if scan.started_at else None,
            "endTimeUtc": scan.completed_at.isoformat() if scan.completed_at else None,
        }]

        return {
            "tool": {
                "driver": {
                    "name": self.tool_name,
                    "organization": self.organization,
                    "version": "1.0.0",
                    "informationUri": "https://github.com/tugcantopaloglu/secumator",
                    "rules": list(rules.values()),
                    "supportedTaxonomies": [{
                        "name": "CWE",
                        "guid": "25F72D7E-8A92-459D-AD67-64853F788765",
                        "organizationUri": "https://cwe.mitre.org/",
                    }],
                },
            },
            "invocations": invocations,
            "results": results,
            "artifacts": [{
                "location": {"uri": scan.target},
                "sourceLanguage": "html",
            }],
            "automationDetails": {
                "id": f"secumator/{scan.id}",
                "guid": f"scan-{scan.id}",
                "correlationGuid": f"target-{hash(scan.target) % 10**8:08d}",
            },
        }

    def _create_rules(self, findings: list[Finding]) -> dict[str, dict[str, Any]]:
        rules = {}
        seen_rules = set()

        for finding in findings:
            rule_id = self._generate_rule_id(finding)
            if rule_id in seen_rules:
                continue
            seen_rules.add(rule_id)

            rule = {
                "id": rule_id,
                "name": self._sanitize_name(finding.title),
                "shortDescription": {"text": finding.title[:100]},
                "fullDescription": {"text": finding.description or finding.title},
                "defaultConfiguration": {
                    "level": self.SEVERITY_TO_LEVEL.get(finding.severity, "warning"),
                    "enabled": True,
                    "rank": self.SEVERITY_TO_RANK.get(finding.severity, 0.5),
                },
                "properties": {
                    "security-severity": str(finding.cvss_score or self._default_cvss(finding.severity)),
                    "precision": "high" if finding.cve_id else "medium",
                    "problem.severity": finding.severity.value,
                    "tags": self._generate_tags(finding),
                },
            }

            if finding.recommendation:
                rule["help"] = {
                    "text": finding.recommendation,
                    "markdown": f"## Remediation\n\n{finding.recommendation}",
                }

            if finding.cve_id:
                rule["relationships"] = self._create_relationships(finding)

            rules[rule_id] = rule

        return rules

    def _create_results(self, findings: list[Finding], rules: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        results = []

        for finding in findings:
            rule_id = self._generate_rule_id(finding)

            result = {
                "ruleId": rule_id,
                "ruleIndex": list(rules.keys()).index(rule_id),
                "level": self.SEVERITY_TO_LEVEL.get(finding.severity, "warning"),
                "message": {
                    "text": finding.description or finding.title,
                },
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": finding.affected_component or "unknown",
                            "uriBaseId": "SRCROOT",
                        },
                    },
                    "logicalLocations": [{
                        "name": finding.affected_component or "unknown",
                        "kind": "resource",
                    }],
                }],
                "partialFingerprints": {
                    "primaryLocationLineHash": self._hash_finding(finding),
                },
                "properties": {
                    "security-severity": str(finding.cvss_score or self._default_cvss(finding.severity)),
                    "source-tool": finding.source_tool,
                },
            }

            if finding.evidence:
                result["codeFlows"] = [{
                    "threadFlows": [{
                        "locations": [{
                            "location": {
                                "message": {"text": finding.evidence[:500]},
                            },
                        }],
                    }],
                }]

            if finding.cve_id:
                result["taxa"] = [{
                    "toolComponent": {"name": "CWE"},
                    "id": finding.cve_id,
                }]

            if finding.recommendation:
                result["fixes"] = [{
                    "description": {"text": finding.recommendation},
                }]

            results.append(result)

        return results

    def _generate_rule_id(self, finding: Finding) -> str:
        if finding.cve_id:
            cves = finding.cve_id.split(",")
            return cves[0].strip().replace("-", "_")

        title = self._sanitize_name(finding.title)
        source = finding.source_tool or "secumator"
        return f"{source}/{title[:40]}"

    def _sanitize_name(self, name: str) -> str:
        import re
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        sanitized = re.sub(r"_+", "_", sanitized)
        return sanitized.strip("_")[:50]

    def _generate_tags(self, finding: Finding) -> list[str]:
        tags = ["security"]

        severity_tags = {
            Severity.CRITICAL: ["critical", "external/cwe/cwe-94"],
            Severity.HIGH: ["high-severity"],
            Severity.MEDIUM: ["medium-severity"],
            Severity.LOW: ["low-severity"],
            Severity.INFO: ["informational"],
        }
        tags.extend(severity_tags.get(finding.severity, []))

        title_lower = finding.title.lower()
        vuln_tags = {
            "sql": ["sql-injection", "external/cwe/cwe-89"],
            "xss": ["xss", "cross-site-scripting", "external/cwe/cwe-79"],
            "rce": ["rce", "remote-code-execution", "external/cwe/cwe-94"],
            "ssrf": ["ssrf", "external/cwe/cwe-918"],
            "lfi": ["lfi", "path-traversal", "external/cwe/cwe-22"],
            "xxe": ["xxe", "external/cwe/cwe-611"],
        }
        for keyword, related_tags in vuln_tags.items():
            if keyword in title_lower:
                tags.extend(related_tags)

        if finding.source_tool:
            tags.append(f"tool/{finding.source_tool}")

        return list(set(tags))

    def _create_relationships(self, finding: Finding) -> list[dict[str, Any]]:
        relationships = []
        if finding.cve_id:
            for cve in finding.cve_id.split(","):
                cve = cve.strip()
                if cve:
                    relationships.append({
                        "target": {
                            "toolComponent": {"name": "CVE"},
                            "id": cve,
                        },
                        "kinds": ["superset"],
                    })
        return relationships

    def _default_cvss(self, severity: Severity) -> float:
        defaults = {
            Severity.CRITICAL: 9.8,
            Severity.HIGH: 7.5,
            Severity.MEDIUM: 5.0,
            Severity.LOW: 2.5,
            Severity.INFO: 0.0,
        }
        return defaults.get(severity, 5.0)

    def _hash_finding(self, finding: Finding) -> str:
        import hashlib
        content = f"{finding.title}:{finding.affected_component}:{finding.severity.value}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


def export_sarif(scan: Scan, findings: list[Finding], output_path: Path | None = None) -> dict[str, Any]:
    exporter = SARIFExporter()
    return exporter.export(scan, findings, output_path)
