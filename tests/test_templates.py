import pytest
import tempfile
from pathlib import Path
from secumator.core.templates import TemplateManager, ScanTemplate, BUILTIN_TEMPLATES
from secumator.models.scan import ScanType


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def manager(temp_dir):
    return TemplateManager(custom_dir=temp_dir)


def test_builtin_templates_exist(manager):
    templates = manager.list_all()
    assert len(templates) >= len(BUILTIN_TEMPLATES)


def test_get_builtin_template(manager):
    template = manager.get("quick-web")
    assert template is not None
    assert template.name == "quick-web"
    assert template.scan_type == ScanType.WEBAPP


def test_list_by_tag(manager):
    templates = manager.list_by_tag("web")
    assert len(templates) > 0
    assert all("web" in t.tags for t in templates)


def test_list_by_type(manager):
    templates = manager.list_by_type(ScanType.NETWORK)
    assert len(templates) > 0
    assert all(t.scan_type == ScanType.NETWORK for t in templates)


def test_save_custom_template(manager, temp_dir):
    template = ScanTemplate(
        name="my-custom",
        description="Custom template",
        scan_type=ScanType.WEBAPP,
        nuclei_tags=["custom"],
        rate_limit=50,
        tags=["custom", "test"],
    )
    manager.save_custom(template)

    loaded = manager.get("my-custom")
    assert loaded is not None
    assert loaded.name == "my-custom"
    assert loaded.rate_limit == 50
    assert (temp_dir / "my-custom.yaml").exists()


def test_delete_custom_template(manager, temp_dir):
    template = ScanTemplate(
        name="to-delete",
        description="Will be deleted",
        scan_type=ScanType.WEBAPP,
    )
    manager.save_custom(template)
    assert manager.get("to-delete") is not None

    success = manager.delete_custom("to-delete")
    assert success is True
    assert manager.get("to-delete") is None


def test_cannot_delete_builtin(manager):
    success = manager.delete_custom("quick-web")
    assert success is False
    assert manager.get("quick-web") is not None


def test_to_scan_options(manager):
    template = manager.get("owasp-top10")
    options = manager.to_scan_options(template)

    assert "rate_limit" in options
    assert "timeout" in options
    assert "tags" in options


def test_template_with_all_fields(manager, temp_dir):
    template = ScanTemplate(
        name="full-test",
        description="Full template",
        scan_type=ScanType.FULL,
        options={"extra": "value"},
        nuclei_templates=["/path/to/template.yaml"],
        nuclei_tags=["cve", "sqli"],
        nuclei_severity=["critical", "high"],
        nmap_args=["-sV", "-sC"],
        nikto_args=["-Tuning", "x"],
        rate_limit=100,
        timeout=7200,
        enabled_scanners=["nuclei", "nmap"],
        tags=["full", "custom"],
    )
    manager.save_custom(template)

    loaded = manager.get("full-test")
    assert loaded.nuclei_templates == ["/path/to/template.yaml"]
    assert loaded.nuclei_tags == ["cve", "sqli"]
    assert loaded.nmap_args == ["-sV", "-sC"]
    assert loaded.enabled_scanners == ["nuclei", "nmap"]
