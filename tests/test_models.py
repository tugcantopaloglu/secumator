from secumator.models.scan import ScanStatus, ScanType, Severity
from secumator.models.schemas import ScanCreate, ReportRequest


def test_scan_create_schema():
    data = ScanCreate(target="https://example.com", scan_type="webapp")
    assert data.target == "https://example.com"
    assert data.scan_type == "webapp"


def test_scan_create_with_options():
    data = ScanCreate(
        target="https://example.com",
        scan_type="full",
        profile="aggressive",
        options={"timeout": 300},
    )
    assert data.profile == "aggressive"
    assert data.options["timeout"] == 300


def test_report_request_defaults():
    data = ReportRequest(scan_id=1)
    assert data.format == "pdf"
    assert data.template == "professional"
    assert data.include_executive_summary is True
    assert data.include_ai_analysis is True


def test_scan_status_enum():
    assert ScanStatus.PENDING.value == "pending"
    assert ScanStatus.COMPLETED.value == "completed"


def test_scan_type_enum():
    assert ScanType.WEBAPP.value == "webapp"
    assert ScanType.NETWORK.value == "network"


def test_severity_enum():
    assert Severity.CRITICAL.value == "critical"
    assert Severity.HIGH.value == "high"
