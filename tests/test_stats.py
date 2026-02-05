import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_dashboard_stats(client: AsyncClient):
    response = await client.get("/api/v1/stats/dashboard")
    assert response.status_code == 200
    data = response.json()
    
    assert "overview" in data
    assert "severity_distribution" in data
    assert "scan_status" in data
    assert "recent_scans" in data
    
    assert "total_scans" in data["overview"]
    assert "total_findings" in data["overview"]


@pytest.mark.asyncio
async def test_get_trends(client: AsyncClient):
    response = await client.get("/api/v1/stats/trends?days=30")
    assert response.status_code == 200
    data = response.json()
    
    assert data["period_days"] == 30
    assert "scans_by_day" in data
    assert "findings_by_day" in data
    assert "severity_trend" in data


@pytest.mark.asyncio
async def test_get_trends_custom_period(client: AsyncClient):
    response = await client.get("/api/v1/stats/trends?days=7")
    assert response.status_code == 200
    data = response.json()
    assert data["period_days"] == 7
    assert len(data["scans_by_day"]) == 7


@pytest.mark.asyncio
async def test_get_top_vulnerabilities(client: AsyncClient):
    response = await client.get("/api/v1/stats/top-vulnerabilities")
    assert response.status_code == 200
    data = response.json()
    
    assert "top_vulnerabilities" in data
    assert "most_affected_components" in data
    assert isinstance(data["top_vulnerabilities"], list)


@pytest.mark.asyncio
async def test_top_vulnerabilities_with_limit(client: AsyncClient):
    response = await client.get("/api/v1/stats/top-vulnerabilities?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["top_vulnerabilities"]) <= 5
