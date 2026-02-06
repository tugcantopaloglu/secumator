import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_scan_github_repo(client: AsyncClient):
    response = await client.post(
        "/api/v1/github/scan",
        json={
            "repo_url": "https://github.com/test/repo",
            "branch": "main",
            "scan_type": "webapp",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["repo_url"] == "https://github.com/test/repo"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_scan_github_invalid_url(client: AsyncClient):
    response = await client.post(
        "/api/v1/github/scan",
        json={
            "repo_url": "invalid-url",
            "branch": "main",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_github_webhook_pull_request(client: AsyncClient):
    payload = {
        "action": "opened",
        "repository": {"html_url": "https://github.com/test/repo"},
        "pull_request": {
            "number": 1,
            "head": {"sha": "abc123"},
        },
    }
    response = await client.post(
        "/api/v1/github/webhook",
        json=payload,
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_github_webhook_ignored_event(client: AsyncClient):
    response = await client.post(
        "/api/v1/github/webhook",
        json={"action": "created"},
        headers={"X-GitHub-Event": "star"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "acknowledged"
