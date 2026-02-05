import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Secumator"


@pytest.mark.asyncio
async def test_create_scan(client: AsyncClient):
    response = await client.post(
        "/api/v1/scans",
        json={
            "target": "https://example.com",
            "scan_type": "webapp",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["target"] == "https://example.com"
    assert data["scan_type"] == "webapp"
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_scans(client: AsyncClient):
    await client.post("/api/v1/scans", json={"target": "https://test1.com", "scan_type": "webapp"})
    await client.post("/api/v1/scans", json={"target": "https://test2.com", "scan_type": "network"})

    response = await client.get("/api/v1/scans")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_get_scan(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/scans",
        json={"target": "https://example.com", "scan_type": "webapp"},
    )
    scan_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/scans/{scan_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == scan_id
    assert data["target"] == "https://example.com"


@pytest.mark.asyncio
async def test_get_scan_not_found(client: AsyncClient):
    response = await client.get("/api/v1/scans/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_scan(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/scans",
        json={"target": "https://example.com", "scan_type": "webapp"},
    )
    scan_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/scans/{scan_id}")
    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/scans/{scan_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_scan(client: AsyncClient):
    create_response = await client.post(
        "/api/v1/scans",
        json={"target": "https://example.com", "scan_type": "webapp"},
    )
    scan_id = create_response.json()["id"]

    response = await client.post(f"/api/v1/scans/{scan_id}/cancel")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
