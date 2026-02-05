import pytest
import json
from datetime import datetime, timezone
from secumator.reports.sarif import SARIFExporter, export_sarif, SARIF_VERSION
from secumator.models.scan import Scan, Finding, ScanStatus, ScanType, Severity


@pytest.fixture
def exporter():
    return SARIFExporter()


@pytest.fixture
def sample_scan():
    scan = Scan(
        id=1,
        target="https://example.com",
        scan_type=ScanType.WEBAPP,
        status=ScanStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    return scan


@pytest.fixture
def sample_findings():
    return [
        Finding(
            id=1,
            scan_id=1,
            title="SQL Injection",
            severity=Severity.CRITICAL,
            description="SQL injection vulnerability found",
            evidence="GET /search?q=' OR '1'='1",
            recommendation="Use parameterized queries",
            cve_id="CVE-2023-1234",
            cvss_score=9.8,
            affected_component="https://example.com/search",
            source_tool="nuclei",
            created_at=datetime.now(timezone.utc),
        ),
        Finding(
            id=2,
            scan_id=1,
            title="XSS Vulnerability",
            severity=Severity.HIGH,
            description="Cross-site scripting found",
            evidence="<script>alert(1)</script>",
            recommendation="Sanitize user input",
            affected_component="https://example.com/comment",
            source_tool="nikto",
            created_at=datetime.now(timezone.utc),
        ),
        Finding(
            id=3,
            scan_id=1,
            title="Information Disclosure",
            severity=Severity.INFO,
            description="Server version disclosed",
            affected_component="https://example.com",
            source_tool="nmap",
            created_at=datetime.now(timezone.utc),
        ),
    ]


def test_sarif_version(exporter, sample_scan, sample_findings):
    sarif = exporter.export(sample_scan, sample_findings)
    assert sarif["version"] == SARIF_VERSION


def test_sarif_structure(exporter, sample_scan, sample_findings):
    sarif = exporter.export(sample_scan, sample_findings)
    assert "$schema" in sarif
    assert "runs" in sarif
    assert len(sarif["runs"]) == 1


def test_tool_driver(exporter, sample_scan, sample_findings):
    sarif = exporter.export(sample_scan, sample_findings)
    driver = sarif["runs"][0]["tool"]["driver"]
    assert driver["name"] == "Secumator Security Scanner"
    assert "rules" in driver


def test_results_count(exporter, sample_scan, sample_findings):
    sarif = exporter.export(sample_scan, sample_findings)
    results = sarif["runs"][0]["results"]
    assert len(results) == 3


def test_severity_mapping(exporter, sample_scan, sample_findings):
    sarif = exporter.export(sample_scan, sample_findings)
    results = sarif["runs"][0]["results"]

    critical_result = next(r for r in results if "SQL" in r["message"]["text"])
    assert critical_result["level"] == "error"

    info_result = next(r for r in results if "Server version" in r["message"]["text"])
    assert info_result["level"] == "none"


def test_rules_have_security_severity(exporter, sample_scan, sample_findings):
    sarif = exporter.export(sample_scan, sample_findings)
    rules = sarif["runs"][0]["tool"]["driver"]["rules"]

    for rule in rules:
        assert "security-severity" in rule["properties"]


def test_results_have_locations(exporter, sample_scan, sample_findings):
    sarif = exporter.export(sample_scan, sample_findings)
    results = sarif["runs"][0]["results"]

    for result in results:
        assert "locations" in result
        assert len(result["locations"]) > 0


def test_invocations(exporter, sample_scan, sample_findings):
    sarif = exporter.export(sample_scan, sample_findings)
    invocations = sarif["runs"][0]["invocations"]

    assert len(invocations) == 1
    assert invocations[0]["executionSuccessful"] is True


def test_automation_details(exporter, sample_scan, sample_findings):
    sarif = exporter.export(sample_scan, sample_findings)
    automation = sarif["runs"][0]["automationDetails"]

    assert "secumator/1" in automation["id"]


def test_cve_in_rule_id(exporter, sample_scan, sample_findings):
    sarif = exporter.export(sample_scan, sample_findings)
    rules = sarif["runs"][0]["tool"]["driver"]["rules"]

    cve_rule = next((r for r in rules if "CVE_2023_1234" in r["id"]), None)
    assert cve_rule is not None


def test_export_sarif_function(sample_scan, sample_findings):
    sarif = export_sarif(sample_scan, sample_findings)
    assert sarif["version"] == SARIF_VERSION


def test_tags_generation(exporter, sample_scan, sample_findings):
    sarif = exporter.export(sample_scan, sample_findings)
    rules = sarif["runs"][0]["tool"]["driver"]["rules"]

    for rule in rules:
        assert "tags" in rule["properties"]
        assert "security" in rule["properties"]["tags"]


def test_empty_findings(exporter, sample_scan):
    sarif = exporter.export(sample_scan, [])
    assert len(sarif["runs"][0]["results"]) == 0
    assert len(sarif["runs"][0]["tool"]["driver"]["rules"]) == 0
