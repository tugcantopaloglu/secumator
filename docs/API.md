# Secumator API Documentation

## Overview

Secumator provides a comprehensive REST API for security scanning, vulnerability analysis, and report generation. All endpoints are prefixed with `/api/v1`.

## Authentication

Currently, the API supports API key authentication via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/scans
```

## Rate Limiting

- Default: 60 requests per minute per client
- Burst: 20 requests
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Endpoints

### Health Check

#### GET /health

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "healthy",
  "redis": "healthy"
}
```

---

### Scans

#### POST /api/v1/scans

Create a new security scan.

**Request Body:**
```json
{
  "target": "https://example.com",
  "scan_type": "webapp",
  "profile": "owasp-top10",
  "options": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| target | string | Yes | URL, IP, or CIDR to scan |
| scan_type | string | No | `webapp`, `network`, `api`, `full` |
| profile | string | No | Scan template name |
| options | object | No | Additional scan options |

**Response:**
```json
{
  "id": 1,
  "target": "https://example.com",
  "scan_type": "webapp",
  "status": "pending",
  "profile": "owasp-top10",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### GET /api/v1/scans

List all scans with pagination.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 20)

#### GET /api/v1/scans/{id}

Get detailed scan information including findings.

#### GET /api/v1/scans/{id}/correlate

Get correlated findings with deduplication.

**Response:**
```json
{
  "total_raw_findings": 50,
  "total_correlated": 25,
  "dedup_ratio": 0.5,
  "severity_distribution": {
    "critical": 2,
    "high": 8,
    "medium": 10,
    "low": 5
  },
  "findings": [...]
}
```

---

### Reports

#### POST /api/v1/reports

Generate a report for a scan.

**Request Body:**
```json
{
  "scan_id": 1,
  "format": "pdf",
  "template": "professional",
  "include_executive_summary": true,
  "include_ai_analysis": true
}
```

#### GET /api/v1/reports/{scan_id}/sarif

Export scan results in SARIF format for CI/CD integration.

---

### AI Analysis

#### POST /api/v1/ai/explain

Get AI-powered explanation for a vulnerability.

**Request Body:**
```json
{
  "title": "SQL Injection",
  "severity": "critical",
  "description": "Unsanitized user input",
  "cve_id": "CVE-2024-1234",
  "affected_component": "/api/users"
}
```

**Response:**
```json
{
  "explanation": "SQL Injection allows attackers to...",
  "risk_score": 9.0,
  "risk_factors": ["Remote exploitable", "No auth required"],
  "business_impact": "Data breach, unauthorized access",
  "technical_details": "Input not sanitized before query",
  "exploitation_likelihood": "High"
}
```

#### POST /api/v1/ai/remediate

Get AI-suggested remediation steps.

**Request Body:**
```json
{
  "title": "SQL Injection",
  "severity": "critical",
  "technology_stack": ["Python", "PostgreSQL"]
}
```

**Response:**
```json
{
  "immediate_actions": ["Disable affected endpoint"],
  "short_term_fixes": ["Implement parameterized queries"],
  "long_term_solutions": ["Use ORM", "Add WAF"],
  "code_examples": {
    "python": "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
  },
  "resources": ["https://owasp.org/sql-injection"],
  "estimated_effort": "2-4 hours",
  "priority": "P0"
}
```

#### POST /api/v1/ai/risk-score

Calculate overall risk score for findings.

---

### GitHub Integration

#### POST /api/v1/github/scan

Scan a GitHub repository.

**Request Body:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "branch": "main",
  "scan_type": "webapp",
  "create_pr_comment": true,
  "pr_number": 123
}
```

#### POST /api/v1/github/webhook

Handle GitHub webhook events for automatic scanning.

---

### Statistics

#### GET /api/v1/stats/dashboard

Get dashboard overview statistics.

**Response:**
```json
{
  "overview": {
    "total_scans": 150,
    "scans_this_week": 25,
    "scans_this_month": 80,
    "total_findings": 1250
  },
  "severity_distribution": {
    "critical": 15,
    "high": 120,
    "medium": 450,
    "low": 400,
    "info": 265
  },
  "scan_status": {
    "pending": 2,
    "running": 1,
    "completed": 140,
    "failed": 7
  },
  "recent_scans": [...]
}
```

#### GET /api/v1/stats/trends

Get activity trends over time.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

---

### WebSocket

#### WS /ws

Global WebSocket connection for real-time updates.

**Messages:**
```json
// Subscribe to scan updates
{"type": "subscribe", "scan_id": "123"}

// Ping/Pong
{"type": "ping"}
{"type": "pong"}

// Scan progress update
{"type": "scan_progress", "scan_id": 1, "progress": 50, "status": "running"}

// New finding
{"type": "finding", "scan_id": 1, "finding": {...}}

// Scan complete
{"type": "scan_complete", "scan_id": 1, "summary": {...}}
```

#### WS /ws/scan/{id}

Scan-specific WebSocket connection.

---

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

## CVSS Calculation

#### POST /api/v1/cvss/calculate

Calculate CVSS score from vector string.

**Request Body:**
```json
{
  "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
}
```

**Response:**
```json
{
  "version": "3.1",
  "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
  "base_score": 9.8,
  "severity": "Critical",
  "impact_score": 5.9,
  "exploitability_score": 3.9
}
```

#### GET /api/v1/cve/{cve_id}

Look up CVE information from NVD.

**Response:**
```json
{
  "cve_id": "CVE-2024-1234",
  "description": "Remote code execution vulnerability...",
  "cvss_score": 9.8,
  "severity": "Critical",
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
  "published": "2024-01-15",
  "references": ["https://nvd.nist.gov/..."],
  "weaknesses": ["CWE-89"]
}
```
