import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_explain_vulnerability(client: AsyncClient):
    with patch("secumator.api.routes.ai.generate_completion", new_callable=AsyncMock) as mock:
        mock.return_value = """{
            "explanation": "SQL Injection allows attackers to manipulate database queries.",
            "risk_score": 9.0,
            "risk_factors": ["Remote exploitable", "No authentication required"],
            "business_impact": "Data breach, unauthorized access",
            "technical_details": "Input not sanitized before SQL query",
            "exploitation_likelihood": "High"
        }"""
        
        response = await client.post(
            "/api/v1/ai/explain",
            json={
                "title": "SQL Injection",
                "severity": "critical",
                "description": "Unsanitized user input in SQL query",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert data["risk_score"] >= 0


@pytest.mark.asyncio
async def test_suggest_remediation(client: AsyncClient):
    with patch("secumator.api.routes.ai.generate_completion", new_callable=AsyncMock) as mock:
        mock.return_value = """{
            "immediate_actions": ["Disable affected endpoint"],
            "short_term_fixes": ["Implement parameterized queries"],
            "long_term_solutions": ["Use ORM", "Add WAF"],
            "code_examples": {"python": "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"},
            "resources": ["https://owasp.org/sql-injection"],
            "estimated_effort": "2-4 hours",
            "priority": "P0"
        }"""
        
        response = await client.post(
            "/api/v1/ai/remediate",
            json={
                "title": "SQL Injection",
                "severity": "critical",
                "technology_stack": ["Python", "PostgreSQL"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "immediate_actions" in data
        assert len(data["immediate_actions"]) > 0


@pytest.mark.asyncio
async def test_calculate_risk_score(client: AsyncClient):
    with patch("secumator.api.routes.ai.generate_completion", new_callable=AsyncMock) as mock:
        mock.return_value = """{
            "overall_risk_score": 75.0,
            "risk_level": "High",
            "finding_scores": [{"title": "SQLi", "score": 9.0, "priority": 1}],
            "risk_summary": "Critical vulnerabilities detected",
            "top_priorities": ["Fix SQL Injection"],
            "executive_summary": "High risk environment requiring immediate attention."
        }"""
        
        response = await client.post(
            "/api/v1/ai/risk-score",
            json={
                "findings": [
                    {"title": "SQL Injection", "severity": "critical"},
                    {"title": "XSS", "severity": "high"},
                ],
                "context": {"target": "https://example.com"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["overall_risk_score"] <= 100
        assert data["risk_level"] in ["Low", "Medium", "High", "Critical"]


@pytest.mark.asyncio
async def test_ai_fallback_on_error(client: AsyncClient):
    with patch("secumator.api.routes.ai.generate_completion", new_callable=AsyncMock) as mock:
        mock.side_effect = Exception("API error")
        
        response = await client.post(
            "/api/v1/ai/explain",
            json={
                "title": "Test Vulnerability",
                "severity": "medium",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unable to generate" in data["explanation"] or data["exploitation_likelihood"] == "Unknown"
