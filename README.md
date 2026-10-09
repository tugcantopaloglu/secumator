# Secumator

Secumator combines a FastAPI backend, a Next.js dashboard, scan scheduling, and security reports. The backend integrates Nuclei, Nmap, and Nikto. Optional AI providers can explain findings and produce summaries.

## Local development

Use Python 3.11 or newer, PostgreSQL, and Redis:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
secumator serve
```

Configure `DATABASE_URL` and `REDIS_URL` using `.env.example`. `secumator serve` listens on `127.0.0.1` by default. The API does not implement account authentication or tenant isolation. Keep it on a trusted local network or place it behind an authenticated gateway before sharing access. Its endpoints can start scans and expose findings.

```bash
cd frontend
npm ci
npm run dev
```

The dashboard uses Next.js 15 and React 18. Set `NEXT_PUBLIC_API_URL` to the browser-reachable backend URL and `NEXT_PUBLIC_WS_URL` to its WebSocket URL. API calls use `/api/v1` and live events use `/ws`.

## Containers

```bash
cp .env.example .env
docker compose up --build -d
```

Review published ports, default database credentials, AI keys, and the Nginx configuration before starting services. The repository includes one main Compose file and no separate production Compose override. There is no production deployment in CI. Container builds and unit tests do not establish real scanner execution or an authenticated public installation.

## Scan and report behavior

The backend provides scan creation/listing, queue status, templates, correlation, GitHub integration, AI analysis, and statistics. See the running API's `/docs` for the current request and response contracts. Install scanner binaries separately for non-container development. Scan only targets that you are authorized to assess.

PDF output requires the native libraries used by WeasyPrint. HTML and SARIF exports are also available. XML from Nmap is parsed with entity expansion disabled. Stable MD5-based correlation identifiers are explicitly marked as non-security hashes; they are not used for authentication or integrity checks.

## Verification

```bash
python -m pytest tests -q
python -m ruff check src --select E9,F63,F7,F82
python -m bandit -r src -lll
```

```bash
cd frontend
npm run build
npm test -- --runInBand
```

CI blocks on backend tests, frontend lint/build/tests, Python syntax checks, and high severity Python security findings. The configured Python lint gate is blocking. Remaining type-checking findings are visible advisory steps. Dependency audit reports also remain advisory. The frontend and ML/reporting dependencies still require compatibility review for remaining advisories.

The tests mock external scanners and AI where appropriate and use SQLite for API tests. Real PostgreSQL migrations, Redis queue behavior, scanner binaries, AI output, PDF rendering, and deployed WebSockets need separate acceptance. Notification and API-key controls in the settings screen currently have no persistence endpoint and should not be treated as completed configuration features.

## License

MIT. See [LICENSE](LICENSE).
