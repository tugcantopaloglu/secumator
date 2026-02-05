import pytest
from datetime import datetime, timezone
from secumator.core.correlation import (
    VulnerabilityCorrelator,
    FindingDeduplicator,
    CorrelatedFinding,
)
from secumator.models.scan import Finding, Severity


@pytest.fixture
def correlator():
    return VulnerabilityCorrelator()


@pytest.fixture
def deduplicator():
    return FindingDeduplicator()


def make_finding(
    id: int,
    title: str,
    severity: str = "medium",
    cve_id: str | None = None,
    component: str | None = None,
    tool: str = "nuclei",
) -> Finding:
    f = Finding(
        id=id,
        scan_id=1,
        title=title,
        severity=Severity(severity),
        cve_id=cve_id,
        affected_component=component,
        source_tool=tool,
        created_at=datetime.now(timezone.utc),
    )
    return f


def test_correlate_by_cve(correlator):
    findings = [
        make_finding(1, "SQL Injection", cve_id="CVE-2023-1234", tool="nuclei"),
        make_finding(2, "SQLi Vulnerability", cve_id="CVE-2023-1234", tool="nikto"),
    ]

    result = correlator.correlate(findings)
    assert result.total_correlated == 1
    assert result.correlated_findings[0].cve_ids == ["CVE-2023-1234"]
    assert len(result.correlated_findings[0].source_tools) == 2


def test_correlate_by_title_similarity(correlator):
    findings = [
        make_finding(1, "SQL Injection Vulnerability in login form"),
        make_finding(2, "SQL Injection Vulnerability in login"),
    ]

    result = correlator.correlate(findings)
    assert result.total_correlated < result.total_raw_findings


def test_no_correlation_different_findings(correlator):
    findings = [
        make_finding(1, "SQL Injection", severity="high"),
        make_finding(2, "XSS Vulnerability", severity="medium"),
        make_finding(3, "SSRF Attack", severity="high"),
    ]

    result = correlator.correlate(findings)
    assert result.total_correlated == 3


def test_severity_ordering(correlator):
    findings = [
        make_finding(1, "Info Finding", severity="info"),
        make_finding(2, "Critical Finding", severity="critical"),
        make_finding(3, "Low Finding", severity="low"),
    ]

    result = correlator.correlate(findings)
    assert result.correlated_findings[0].severity == Severity.CRITICAL
    assert result.correlated_findings[-1].severity == Severity.INFO


def test_severity_distribution(correlator):
    findings = [
        make_finding(1, "F1", severity="critical"),
        make_finding(2, "F2", severity="high"),
        make_finding(3, "F3", severity="high"),
        make_finding(4, "F4", severity="medium"),
    ]

    result = correlator.correlate(findings)
    assert result.severity_distribution["critical"] == 1
    assert result.severity_distribution["high"] == 2
    assert result.severity_distribution["medium"] == 1


def test_dedup_ratio(correlator):
    findings = [
        make_finding(1, "Same", cve_id="CVE-2023-1234"),
        make_finding(2, "Same", cve_id="CVE-2023-1234"),
        make_finding(3, "Same", cve_id="CVE-2023-1234"),
    ]

    result = correlator.correlate(findings)
    assert result.total_raw_findings == 3
    assert result.total_correlated == 1
    assert result.dedup_ratio < 1.0


def test_affected_components(correlator):
    findings = [
        make_finding(1, "F1", component="https://example.com/login"),
        make_finding(2, "F2", component="https://example.com/admin"),
        make_finding(3, "F3", component="https://example.com/login"),
    ]

    result = correlator.correlate(findings)
    assert "https://example.com/login" in result.affected_components
    assert "https://example.com/admin" in result.affected_components


def test_deduplicator_basic(deduplicator):
    findings = [
        make_finding(1, "SQL Injection", severity="high", component="/login"),
        make_finding(2, "SQL Injection", severity="medium", component="/login"),
    ]

    result = deduplicator.deduplicate(findings)
    assert len(result) == 1
    assert result[0].severity == Severity.HIGH


def test_deduplicator_cve_priority(deduplicator):
    findings = [
        make_finding(1, "Different Title 1", cve_id="CVE-2023-1234"),
        make_finding(2, "Different Title 2", cve_id="CVE-2023-1234"),
    ]

    result = deduplicator.deduplicate(findings)
    assert len(result) == 1


def test_empty_findings(correlator):
    result = correlator.correlate([])
    assert result.total_raw_findings == 0
    assert result.total_correlated == 0
    assert result.dedup_ratio == 1.0


def test_correlation_summary(correlator):
    findings = [
        make_finding(1, "CVE Finding", cve_id="CVE-2023-1234", tool="nuclei"),
        make_finding(2, "CVE Finding", cve_id="CVE-2023-1234", tool="nikto"),
        make_finding(3, "Other Finding", tool="nuclei"),
    ]

    result = correlator.correlate(findings)
    assert result.correlation_summary["cve_correlations"] >= 1
    assert result.correlation_summary["multi_tool_correlations"] >= 1
