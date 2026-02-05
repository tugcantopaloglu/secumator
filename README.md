# 🔒 Secumator

**Production-Grade Security Audit Platform** with AI-powered analysis, vulnerability correlation, and CI/CD integration.

Secumator automates comprehensive security scanning using industry-standard tools (Nuclei, Nmap, Nikto) and generates professional reports with AI-powered insights, CVSS scoring, and SARIF export for seamless CI/CD integration.

## ✨ Features

### Core Scanning
- **Multi-tool Scanning**: Integrates Nuclei, Nmap, and Nikto for comprehensive security assessments
- **AI-Powered Reports**: Generate executive summaries and remediation plans using OpenAI or Anthropic
- **Professional Templates**: Beautiful PDF and HTML report templates
- **Multiple Scan Profiles**: Web application, network, API, and full security scans

### Advanced Features (v2.0)
- **🔄 Scan Queue System**: Priority-based scheduling with rate limiting and retry logic
- **🔗 Vulnerability Correlation**: Intelligent deduplication and correlation across scan types
- **📊 CVSS Integration**: Real-time CVSS scoring and CVE lookup via NVD API
- **📢 Webhook Notifications**: Slack, Discord, and Teams integration for scan alerts
- **🎯 Scan Templates**: 12+ built-in presets (OWASP Top 10, CMS, Cloud, etc.) plus custom templates
- **📄 SARIF Export**: Standard format for GitHub Security, GitLab SAST, and CI/CD pipelines
- **🛡️ Target Validation**: Comprehensive URL/IP/CIDR validation with private network protection
- **⚡ Rate Limiting**: Token bucket algorithm with per-target and global limits

### Infrastructure
- **REST API**: Full-featured FastAPI backend with OpenAPI documentation
- **CLI Interface**: Easy command-line tool for quick scans
- **Docker Ready**: Production-ready Docker and docker-compose setup
- **Async Architecture**: Built with asyncio for efficient concurrent scanning

## 🚀 Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/tugcantopaloglu/secumator.git
cd secumator
cp .env.example .env
# Edit .env with your configuration

# Start with docker compose (requires Docker with compose plugin)
docker compose up -d

# Verify the API is running
curl http://localhost:8000/health

# Access the API docs
open http://localhost:8000/docs
```

### Local Installation

```bash
git clone https://github.com/tugcantopaloglu/secumator.git
cd secumator

# Create virtual environment (Python 3.11+ required)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests to verify installation
pytest

# Run a scan
secumator scan https://example.com --type webapp --format pdf

# Start the API server
secumator serve
```

### Requirements

- **Python**: 3.11 or higher
- **Docker**: 20.10+ with compose plugin (for containerized deployment)
- **External Tools** (for full scanning capabilities):
  - Nmap
  - Nuclei
  - Nikto (optional)

## 📖 Usage

### CLI Commands

```bash
# Quick web scan with critical/high findings only
secumator scan https://target.com --type webapp

# Full network scan
secumator scan 192.168.1.0/24 --type network

# Generate PDF report with AI analysis
secumator scan https://target.com --format pdf --output report.pdf

# Disable AI analysis
secumator scan https://target.com --no-ai

# List recent scans
secumator list-scans

# Start API server
secumator serve --host 0.0.0.0 --port 8000
```

### REST API Examples

```bash
# Create scan with template
curl -X POST http://localhost:8000/api/v1/scans \
  -H "Content-Type: application/json" \
  -d '{"target": "https://example.com", "scan_type": "webapp", "profile": "owasp-top10"}'

# Get scan with correlated findings
curl http://localhost:8000/api/v1/scans/1/correlate

# Export SARIF for CI/CD
curl http://localhost:8000/api/v1/reports/1/sarif > results.sarif

# Calculate CVSS score
curl -X POST http://localhost:8000/api/v1/cvss/calculate \
  -H "Content-Type: application/json" \
  -d '{"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"}'

# CVE lookup
curl http://localhost:8000/api/v1/cve/CVE-2023-1234

# Queue management
curl http://localhost:8000/api/v1/queue/status
curl http://localhost:8000/api/v1/queue/items

# List templates
curl http://localhost:8000/api/v1/templates
curl http://localhost:8000/api/v1/templates/owasp-top10
```

## 🎯 Scan Templates

| Template | Description | Tools |
|----------|-------------|-------|
| `quick-web` | Quick web scan (critical/high only) | Nuclei |
| `full-web` | Comprehensive web assessment | Nuclei, Nikto |
| `owasp-top10` | OWASP Top 10 vulnerabilities | Nuclei |
| `cve-scan` | Known CVE detection | Nuclei |
| `network-discovery` | Host discovery & enumeration | Nmap |
| `network-full` | Full port scan with scripts | Nmap |
| `stealth-scan` | Low-profile evasive scan | Nuclei |
| `api-security` | REST/GraphQL API testing | Nuclei |
| `cms-scan` | WordPress/Drupal/Joomla | Nuclei, Nikto |
| `cloud-misconfig` | AWS/Azure/GCP misconfigurations | Nuclei |
| `exposed-panels` | Admin panel detection | Nuclei |
| `ssl-tls` | SSL/TLS configuration | Nuclei, Nmap |
| `pentest-full` | Full penetration test | All tools |

Create custom templates in `~/.secumator/templates/`:
```yaml
name: my-custom-scan
description: Custom scan profile
scan_type: webapp
nuclei_tags: [cve, sqli, xss]
nuclei_severity: [critical, high]
rate_limit: 100
timeout: 3600
enabled_scanners: [nuclei]
tags: [custom, web]
```

## 🔔 Webhook Notifications

Configure in `.env`:
```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/xxx
NOTIFY_ON_SCAN_COMPLETE=true
NOTIFY_ON_CRITICAL_FINDING=true
```

Notifications include:
- Scan started/completed/failed events
- Critical and high severity finding alerts
- Findings summary with severity breakdown
- Direct links to reports

## 📄 SARIF Export (CI/CD Integration)

Export scan results in SARIF format for integration with:
- GitHub Code Scanning
- GitLab SAST
- Azure DevOps
- SonarQube

```bash
# Export via API
curl http://localhost:8000/api/v1/reports/1/sarif?download=true -o results.sarif

# GitHub Actions example
- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: results.sarif
```

## 🔧 Configuration

Full `.env` configuration:

```env
# Core
APP_NAME=Secumator
DEBUG=false
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/secumator

# AI (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AI_PROVIDER=openai
AI_MODEL=gpt-4o

# Scanning
SCAN_TIMEOUT=3600
MAX_CONCURRENT_SCANS=5
SCAN_RATE_LIMIT_PER_MINUTE=30
ALLOW_PRIVATE_TARGETS=false
ALLOW_LOCALHOST_TARGETS=false

# Notifications
SLACK_WEBHOOK_URL=
DISCORD_WEBHOOK_URL=
TEAMS_WEBHOOK_URL=
NOTIFY_ON_SCAN_COMPLETE=true
NOTIFY_ON_CRITICAL_FINDING=true

# CVE Lookup
NVD_API_KEY=  # Optional, increases rate limits

# Output
REPORT_OUTPUT_DIR=/var/lib/secumator/reports
LOG_LEVEL=INFO
```

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/scans` | POST | Create new scan |
| `/api/v1/scans` | GET | List scans |
| `/api/v1/scans/{id}` | GET | Get scan details |
| `/api/v1/scans/{id}/correlate` | GET | Get correlated findings |
| `/api/v1/scans/{id}/enrich-cves` | POST | Enrich findings with CVE data |
| `/api/v1/reports` | POST | Generate report |
| `/api/v1/reports/{id}/sarif` | GET | Export SARIF |
| `/api/v1/queue/status` | GET | Queue status |
| `/api/v1/queue/items` | GET | List queued scans |
| `/api/v1/templates` | GET | List templates |
| `/api/v1/templates/{name}` | GET | Get template details |
| `/api/v1/cvss/calculate` | POST | Calculate CVSS score |
| `/api/v1/cve/{id}` | GET | CVE lookup |

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=secumator --cov-report=html

# Lint code
ruff check src/

# Type checking
mypy src/
```

## 🏗️ Architecture

```
secumator/
├── src/secumator/
│   ├── api/              # FastAPI routes and middleware
│   │   └── routes/       # Scans, Reports, Queue, Templates, Correlation
│   ├── core/             # Configuration, database, logging
│   │   ├── queue.py      # Scan scheduling system
│   │   ├── validators.py # Target validation
│   │   ├── rate_limiter.py
│   │   ├── notifications.py
│   │   ├── cvss.py       # CVSS calculator & CVE lookup
│   │   ├── templates.py  # Scan templates
│   │   └── correlation.py # Finding correlation
│   ├── models/           # SQLAlchemy models and Pydantic schemas
│   ├── scanners/         # Scanner integrations
│   ├── reports/          # Report generation
│   │   ├── generator.py  # PDF/HTML reports
│   │   ├── sarif.py      # SARIF export
│   │   └── ai_writer.py  # AI analysis
│   └── cli.py            # Typer CLI application
├── tests/                # Comprehensive test suite
├── Dockerfile
└── docker-compose.yml
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 👤 Author

**Tuğcan Topaloğlu** - [GitHub](https://github.com/tugcantopaloglu)
