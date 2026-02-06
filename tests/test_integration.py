import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_scan_workflow(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/scans",
        json={"target": "https://example.com", "scan_type": "webapp"},
    )
    assert create_response.status_code == 201
    scan_id = create_response.json()["id"]
    
    get_response = await client.get(f"/api/v1/scans/{scan_id}")
    assert get_response.status_code == 200
    assert get_response.json()["target"].rstrip("/") == "https://example.com"
    
    correlate_response = await client.get(f"/api/v1/scans/{scan_id}/correlate")
    assert correlate_response.status_code == 200
    
    list_response = await client.get("/api/v1/scans")
    assert list_response.status_code == 200
    assert any(s["id"] == scan_id for s in list_response.json()["items"])


@pytest.mark.asyncio
async def test_template_workflow(client: AsyncClient):
    templates_response = await client.get("/api/v1/templates")
    assert templates_response.status_code == 200
    templates = templates_response.json()
    
    if templates:
        template_name = templates[0]["name"]
        detail_response = await client.get(f"/api/v1/templates/{template_name}")
        assert detail_response.status_code == 200
        
        scan_response = await client.post(
            "/api/v1/scans",
            json={
                "target": "https://example.com",
                "scan_type": "webapp",
                "profile": template_name,
            },
        )
        assert scan_response.status_code == 201


@pytest.mark.asyncio
async def test_queue_workflow(client: AsyncClient):
    status_response = await client.get("/api/v1/queue/status")
    assert status_response.status_code == 200
    status = status_response.json()
    assert "is_processing" in status
    
    items_response = await client.get("/api/v1/queue/items")
    assert items_response.status_code == 200


@pytest.mark.asyncio
async def test_cvss_and_cve_workflow(client: AsyncClient):
    cvss_response = await client.post(
        "/api/v1/cvss/calculate",
        json={"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"},
    )
    assert cvss_response.status_code == 200
    result = cvss_response.json()
    assert result["base_score"] == 9.8
    assert result["severity"] == "Critical"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data
    assert "database" in data
    assert "redis" in data


@pytest.mark.asyncio
async def test_api_rate_limiting_headers(client: AsyncClient):
    for _ in range(5):
        response = await client.get("/health")
        assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_scan_with_invalid_target(client: AsyncClient):
    response = await client.post(
        "/api/v1/scans",
        json={"target": "", "scan_type": "webapp"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_stats_dashboard_after_scans(client: AsyncClient):
    await client.post(
        "/api/v1/scans",
        json={"target": "https://test1.com", "scan_type": "webapp"},
    )
    await client.post(
        "/api/v1/scans",
        json={"target": "https://test2.com", "scan_type": "network"},
    )
    
    stats_response = await client.get("/api/v1/stats/dashboard")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["overview"]["total_scans"] >= 2
