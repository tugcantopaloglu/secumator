# 🔒 Secumator

**Professional Security Audit Report Generator** with AI-powered analysis.

Secumator automates security scanning using industry-standard tools (Nuclei, Nmap, Nikto) and generates beautiful, professional PDF/HTML reports with AI-powered executive summaries and remediation plans.

## ✨ Features

- **Multi-tool Scanning**: Integrates Nuclei, Nmap, and Nikto for comprehensive security assessments
- **AI-Powered Reports**: Generate executive summaries and remediation plans using OpenAI or Anthropic
- **Professional Templates**: Beautiful PDF and HTML report templates
- **Multiple Scan Profiles**: Web application, network, API, and full security scans
- **REST API**: Full-featured FastAPI backend for integration
- **CLI Interface**: Easy command-line tool for quick scans
- **Docker Ready**: Production-ready Docker and docker-compose setup
- **Async Architecture**: Built with asyncio for efficient concurrent scanning

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/tugcantopaloglu/secumator.git
cd secumator

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d

# Access API docs
open http://localhost:8000/docs
```

### Local Installation

```bash
# Clone and install
git clone https://github.com/tugcantopaloglu/secumator.git
cd secumator
pip install -e ".[dev]"

# Run a scan
secumator scan https://example.com --type webapp --format pdf

# Or start the API server
secumator serve
```

## 📖 Usage

### CLI Commands

```bash
# Run a web application scan
secumator scan https://target.com --type webapp

# Run a network scan
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

### REST API

```bash
# Create a new scan
curl -X POST http://localhost:8000/api/v1/scans \
  -H "Content-Type: application/json" \
  -d '{"target": "https://example.com", "scan_type": "webapp"}'

# Get scan results
curl http://localhost:8000/api/v1/scans/1

# Generate report
curl -X POST http://localhost:8000/api/v1/reports \
  -H "Content-Type: application/json" \
  -d '{"scan_id": 1, "format": "pdf", "include_ai_analysis": true}'

# Download report
curl -O http://localhost:8000/api/v1/reports/download/secumator_report_1_20240101_120000.pdf
```

## 🔧 Configuration

Set environment variables in `.env`:

```env
# AI Configuration (at least one required for AI features)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AI_PROVIDER=openai  # or anthropic
AI_MODEL=gpt-4o

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/secumator

# Scanning
SCAN_TIMEOUT=3600
MAX_CONCURRENT_SCANS=5
```

## 📊 Scan Types

| Type | Tools Used | Description |
|------|------------|-------------|
| `webapp` | Nuclei, Nikto | Web application vulnerabilities |
| `network` | Nmap | Network discovery and port scanning |
| `api` | Nuclei | API-specific security testing |
| `full` | All tools | Comprehensive security assessment |

## 📄 Report Features

- **Executive Summary**: AI-generated overview of security posture
- **Risk Score**: Calculated based on finding severity
- **Severity Distribution**: Visual breakdown of findings
- **Detailed Findings**: Full vulnerability details with evidence
- **Remediation Plan**: Prioritized AI-generated fix recommendations
- **Professional Styling**: Print-ready PDF with modern design

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=secumator

# Lint code
ruff check src/

# Type checking
mypy src/
```

## 🏗️ Architecture

```
secumator/
├── src/secumator/
│   ├── api/           # FastAPI routes and middleware
│   ├── core/          # Configuration, database, logging
│   ├── models/        # SQLAlchemy models and Pydantic schemas
│   ├── scanners/      # Scanner integrations (nuclei, nmap, nikto)
│   ├── reports/       # Report generation and templates
│   └── cli.py         # Typer CLI application
├── tests/             # Pytest test suite
├── Dockerfile
└── docker-compose.yml
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 👤 Author

**Tuğcan Topaloğlu** - [GitHub](https://github.com/tugcantopaloglu)
