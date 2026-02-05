import pytest
from secumator.core.cvss import CVSSCalculator, CVSSVersion


@pytest.fixture
def calculator():
    return CVSSCalculator()


def test_parse_vector_v31(calculator):
    vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    metrics = calculator.parse_vector(vector)
    assert metrics["AV"] == "N"
    assert metrics["AC"] == "L"
    assert metrics["PR"] == "N"
    assert metrics["UI"] == "N"
    assert metrics["S"] == "U"
    assert metrics["C"] == "H"
    assert metrics["I"] == "H"
    assert metrics["A"] == "H"


def test_calculate_critical_severity(calculator):
    vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    score = calculator.calculate(vector)
    assert score.base_score == 9.8
    assert score.severity == "Critical"


def test_calculate_high_severity(calculator):
    vector = "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N"
    score = calculator.calculate(vector)
    assert 7.0 <= score.base_score < 9.0
    assert score.severity == "High"


def test_calculate_medium_severity(calculator):
    vector = "CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:U/C:L/I:L/A:L"
    score = calculator.calculate(vector)
    assert 4.0 <= score.base_score < 7.0
    assert score.severity == "Medium"


def test_calculate_low_severity(calculator):
    vector = "CVSS:3.1/AV:L/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N"
    score = calculator.calculate(vector)
    assert 0.1 <= score.base_score < 4.0
    assert score.severity == "Low"


def test_calculate_none_severity(calculator):
    vector = "CVSS:3.1/AV:L/AC:H/PR:H/UI:R/S:U/C:N/I:N/A:N"
    score = calculator.calculate(vector)
    assert score.base_score == 0.0
    assert score.severity == "None"


def test_invalid_vector(calculator):
    with pytest.raises(ValueError):
        calculator.parse_vector("invalid-vector")


def test_unsupported_version(calculator):
    with pytest.raises(ValueError):
        calculator.calculate("CVSS:4.0/AV:N/AC:L")


def test_scope_changed(calculator):
    vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"
    score = calculator.calculate(vector)
    assert score.base_score == 10.0


def test_severity_from_score():
    assert CVSSCalculator.severity_from_score(0.0) == "none"
    assert CVSSCalculator.severity_from_score(2.5) == "low"
    assert CVSSCalculator.severity_from_score(5.0) == "medium"
    assert CVSSCalculator.severity_from_score(7.5) == "high"
    assert CVSSCalculator.severity_from_score(9.5) == "critical"


def test_score_has_impact_and_exploitability(calculator):
    vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    score = calculator.calculate(vector)
    assert score.impact_score is not None
    assert score.exploitability_score is not None
    assert score.impact_score > 0
    assert score.exploitability_score > 0


def test_version_in_result(calculator):
    vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    score = calculator.calculate(vector)
    assert score.version == CVSSVersion.V31
