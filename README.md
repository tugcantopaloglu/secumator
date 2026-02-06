# 🔒 Secumator

**Enterprise-Grade Security Scanning Platform** with AI-powered analysis, real-time dashboard, and comprehensive CI/CD integration.

[![CI](https://github.com/tugcantopaloglu/secumator/actions/workflows/ci.yml/badge.svg)](https://github.com/tugcantopaloglu/secumator/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

<p align="center">
  <img src="docs/images/dashboard.png" alt="Secumator Dashboard" width="800"/>
</p>

## ✨ Features

### 🎯 Core Capabilities
- **Multi-tool Scanning**: Integrates Nuclei, Nmap, and Nikto for comprehensive security assessments
- **AI-Powered Analysis**: GPT-4/Claude integration for vulnerability explanations and remediation suggestions
- **Real-time Dashboard**: Next.js 14 frontend with live scan progress via WebSocket
- **Professional Reports**: Beautiful PDF, HTML, and SARIF reports

### 🚀 Enterprise Features
- **Scan Queue System**: Priority-based scheduling with rate limiting and retry logic
- **Vulnerability Correlation**: Intelligent deduplication across scan types
- **CVSS Integration**: Real-time scoring and CVE lookup via NVD API
- **Webhook Notifications**: Slack, Discord, and Teams integration
- **GitHub Integration**: Scan repos directly, PR comments, and GitHub Actions support
- **Rate Limiting**: Per-user and global rate limits with graceful degradation

### 📊 Dashboard Features
- Real-time scan progress with WebSocket updates
- Severity distribution charts
- Activity trends over time
- Top vulnerabilities ranking
- Dark/Light mode support

## 🚀 Quick Start

### Docker Compose (Recommended)

```bash
git clone https://github.com/tugcantopaloglu/secumator.git
cd secumator
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose up -d

# Access the dashboard
open http://localhost:3000

# API documentation
open http://localhost:8000/docs
```

### Local Development

```bash
# Backend
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest  # Run tests
secumator serve  # Start API

# Frontend
cd frontend
npm install
npm run dev
```

## 📖 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Load Balancer (Nginx)                    │
└─────────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│      Next.js Frontend       │   │      FastAPI Backend        │
│   (Dashboard, Real-time)    │   │   (REST API, WebSocket)     │
└─────────────────────────────┘   └─────────────────────────────┘
                                               │
        ┌──────────────────────────────────────┼──────────────────┐
        │                                      │                  │
        ▼                                      ▼                  ▼
┌───────────────┐                    ┌───────────────┐  ┌───────────────┐
│  PostgreSQL   │                    │     Redis     │  │  AI Services  │
│  (Data Store) │                    │ (Queue/Cache) │  │ (GPT-4/Claude)│
└───────────────┘                    └───────────────┘  └───────────────┘
                                               │
                                               ▼
                              ┌─────────────────────────────┐
                              │      Scanning Engines       │
                              │  (Nuclei, Nmap, Nikto)      │
                              └─────────────────────────────┘
```

## 🛠️ API Reference

### Scans

```bash
# Create a scan
curl -X POST http://localhost:8000/api/v1/scans \
  -H "Content-Type: application/json" \
  -d '{"target": "https://example.com", "scan_type": "webapp"}'

# Get scan with findings
curl http://localhost:8000/api/v1/scans/1

# List all scans
curl http://localhost:8000/api/v1/scans
```

### AI Analysis

```bash
# Get AI explanation for a vulnerability
curl -X POST http://localhost:8000/api/v1/ai/explain \
  -H "Content-Type: application/json" \
  -d '{"title": "SQL Injection", "severity": "critical"}'

# Get remediation suggestions
curl -X POST http://localhost:8000/api/v1/ai/remediate \
  -H "Content-Type: application/json" \
  -d '{"title": "SQL Injection", "severity": "critical", "technology_stack": ["Python", "PostgreSQL"]}'

# Calculate risk score
curl -X POST http://localhost:8000/api/v1/ai/risk-score \
  -H "Content-Type: application/json" \
  -d '{"findings": [{"title": "SQLi", "severity": "critical"}]}'
```

### GitHub Integration

```bash
# Scan a GitHub repository
curl -X POST http://localhost:8000/api/v1/github/scan \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/owner/repo", "branch": "main"}'

# Post findings as PR comment
curl -X POST http://localhost:8000/api/v1/github/scan/1/comment \
  -H "X-GitHub-Token: YOUR_TOKEN" \
  -d '{"pr_number": 123, "repo": "owner/repo"}'
```

### Dashboard Stats

```bash
# Get dashboard overview
curl http://localhost:8000/api/v1/stats/dashboard

# Get trends over time
curl http://localhost:8000/api/v1/stats/trends?days=30

# Get top vulnerabilities
curl http://localhost:8000/api/v1/stats/top-vulnerabilities
```

## 🔧 Configuration

### Environment Variables

```env
# Core
APP_NAME=Secumator
DEBUG=false
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/secumator

# AI (at least one required for AI features)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AI_PROVIDER=openai  # or anthropic
AI_MODEL=gpt-4o

# GitHub Integration
GITHUB_TOKEN=ghp_...
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Rate Limiting
API_RATE_LIMIT_PER_MINUTE=60
API_RATE_LIMIT_BURST=20
SCAN_RATE_LIMIT_PER_MINUTE=30

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx
```

## 🎯 Scan Templates

| Template | Description | Tools |
|----------|-------------|-------|
| `quick-web` | Quick web scan (critical/high only) | Nuclei |
| `owasp-top10` | OWASP Top 10 vulnerabilities | Nuclei |
| `cve-scan` | Known CVE detection | Nuclei |
| `network-full` | Full port scan with scripts | Nmap |
| `api-security` | REST/GraphQL API testing | Nuclei |
| `pentest-full` | Full penetration test | All tools |

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: Security Scan
on:
  pull_request:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Secumator Scan
        run: |
          curl -X POST "${{ secrets.SECUMATOR_URL }}/api/v1/github/scan" \
            -H "Content-Type: application/json" \
            -d '{"repo_url": "${{ github.repository }}"}'
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: results.sarif
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/scans` | POST | Create new scan |
| `/api/v1/scans` | GET | List scans |
| `/api/v1/scans/{id}` | GET | Get scan details |
| `/api/v1/scans/{id}/correlate` | GET | Get correlated findings |
| `/api/v1/reports/{id}/sarif` | GET | Export SARIF |
| `/api/v1/ai/explain` | POST | AI vulnerability explanation |
| `/api/v1/ai/remediate` | POST | AI remediation suggestions |
| `/api/v1/ai/risk-score` | POST | AI risk scoring |
| `/api/v1/github/scan` | POST | Scan GitHub repo |
| `/api/v1/github/webhook` | POST | GitHub webhook handler |
| `/api/v1/stats/dashboard` | GET | Dashboard statistics |
| `/api/v1/stats/trends` | GET | Activity trends |
| `/ws` | WebSocket | Real-time updates |
| `/ws/scan/{id}` | WebSocket | Scan-specific updates |

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=secumator --cov-report=html

# Run specific test file
pytest tests/test_ai.py -v

# Run integration tests
pytest tests/test_integration.py -v
```

## 🐳 Docker

### Build Images

```bash
# Build backend
docker build -t secumator-api .

# Build frontend
docker build -t secumator-frontend ./frontend
```

### Production Deployment

```bash
# Start all services with production settings
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 👤 Author

**Tuğcan Topaloğlu** - [GitHub](https://github.com/tugcantopaloglu)
