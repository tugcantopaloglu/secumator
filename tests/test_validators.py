import pytest
from secumator.core.validators import TargetValidator, validate_target


@pytest.fixture
def validator():
    return TargetValidator(allow_private=False, allow_localhost=False)


@pytest.fixture
def permissive_validator():
    return TargetValidator(allow_private=True, allow_localhost=True)


def test_valid_url(validator):
    result = validator.validate("https://example.com")
    assert result.valid is True
    assert result.target_type == "url"


def test_valid_url_with_path(validator):
    result = validator.validate("https://example.com/path/to/resource")
    assert result.valid is True
    assert result.target_type == "url"


def test_valid_ip(validator):
    result = validator.validate("93.184.216.34")
    assert result.valid is True
    assert result.target_type == "ip"


def test_valid_cidr(validator):
    result = validator.validate("93.184.216.0/24")
    assert result.valid is True
    assert result.target_type == "cidr"


def test_valid_hostname(validator):
    result = validator.validate("example.com")
    assert result.valid is True
    assert result.target_type == "hostname"


def test_localhost_blocked(validator):
    result = validator.validate("http://localhost")
    assert result.valid is False
    assert "localhost" in result.error.lower()


def test_localhost_allowed(permissive_validator):
    result = permissive_validator.validate("http://localhost")
    assert result.valid is True


def test_private_ip_blocked(validator):
    result = validator.validate("192.168.1.1")
    assert result.valid is False
    assert "private" in result.error.lower()


def test_private_ip_allowed(permissive_validator):
    result = permissive_validator.validate("192.168.1.1")
    assert result.valid is True


def test_empty_target(validator):
    result = validator.validate("")
    assert result.valid is False
    assert "empty" in result.error.lower()


def test_too_long_target(validator):
    result = validator.validate("a" * 3000)
    assert result.valid is False
    assert "long" in result.error.lower()


def test_cidr_too_large(validator):
    result = validator.validate("93.184.0.0/8")
    assert result.valid is False
    assert "large" in result.error.lower()


def test_dangerous_port_warning(validator):
    result = validator.validate("https://example.com:22")
    assert result.valid is True
    assert len(result.warnings) > 0
    assert any("dangerous" in w.lower() for w in result.warnings)


def test_validate_target_function():
    result = validate_target("https://google.com")
    assert result.valid is True


def test_normalized_url(validator):
    result = validator.validate("https://example.com/")
    assert result.normalized == "https://example.com/"
