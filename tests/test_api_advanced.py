import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_queue_status(client: AsyncClient):
    response = await client.get("/api/v1/queue/status")
    assert response.status_code == 200
    data = response.json()
    assert "queued" in data
    assert "running" in data
    assert "completed" in data


@pytest.mark.asyncio
async def test_queue_items_empty(client: AsyncClient):
    response = await client.get("/api/v1/queue/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_templates(client: AsyncClient):
    response = await client.get("/api/v1/templates")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(t["name"] == "quick-web" for t in data)


@pytest.mark.asyncio
async def test_get_template(client: AsyncClient):
    response = await client.get("/api/v1/templates/quick-web")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "quick-web"
    assert data["is_builtin"] is True


@pytest.mark.asyncio
async def test_get_template_not_found(client: AsyncClient):
    response = await client.get("/api/v1/templates/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_templates_by_tag(client: AsyncClient):
    response = await client.get("/api/v1/templates?tag=web")
    assert response.status_code == 200
    data = response.json()
    assert all("web" in t["tags"] for t in data)


@pytest.mark.asyncio
async def test_list_templates_by_type(client: AsyncClient):
    response = await client.get("/api/v1/templates?scan_type=network")
    assert response.status_code == 200
    data = response.json()
    assert all(t["scan_type"] == "network" for t in data)


@pytest.mark.asyncio
async def test_get_template_options(client: AsyncClient):
    response = await client.get("/api/v1/templates/quick-web/options")
    assert response.status_code == 200
    data = response.json()
    assert "rate_limit" in data
    assert "timeout" in data


@pytest.mark.asyncio
async def test_cannot_delete_builtin_template(client: AsyncClient):
    response = await client.delete("/api/v1/templates/quick-web")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cvss_calculate(client: AsyncClient):
    response = await client.post(
        "/api/v1/cvss/calculate",
        json={"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["base_score"] == 9.8
    assert data["severity"] == "Critical"


@pytest.mark.asyncio
async def test_cvss_calculate_invalid(client: AsyncClient):
    response = await client.post(
        "/api/v1/cvss/calculate",
        json={"vector": "invalid-vector"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_scan_with_template(client: AsyncClient):
    response = await client.post(
        "/api/v1/scans",
        json={
            "target": "https://example.com",
            "scan_type": "webapp",
            "profile": "quick-web",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["profile"] == "quick-web"


@pytest.mark.asyncio
async def test_correlate_scan_not_found(client: AsyncClient):
    response = await client.get("/api/v1/scans/99999/correlate")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cve_lookup_invalid_format(client: AsyncClient):
    response = await client.get("/api/v1/cve/invalid-cve")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_sarif_export_not_found(client: AsyncClient):
    response = await client.get("/api/v1/reports/99999/sarif")
    assert response.status_code == 404
