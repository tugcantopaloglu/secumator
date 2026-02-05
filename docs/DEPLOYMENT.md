# Deployment Guide

## Overview

This guide covers deploying Secumator in production environments.

## Prerequisites

- Docker 20.10+ with Docker Compose
- 4GB+ RAM (8GB recommended)
- PostgreSQL 14+ (if not using Docker)
- Redis 7+ (if not using Docker)
- Domain name with SSL certificate (for production)

## Quick Start (Docker Compose)

```bash
# Clone repository
git clone https://github.com/tugcantopaloglu/secumator.git
cd secumator

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start services
docker compose up -d

# Check status
docker compose ps
docker compose logs -f
```

## Production Configuration

### 1. Environment Variables

Create a production `.env` file:

```env
# Core
APP_NAME=Secumator
DEBUG=false
SECRET_KEY=<generate-secure-key>
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql+asyncpg://secumator:STRONG_PASSWORD@db:5432/secumator

# Redis
REDIS_URL=redis://redis:6379/0

# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AI_PROVIDER=openai

# GitHub (optional)
GITHUB_TOKEN=ghp_...
GITHUB_WEBHOOK_SECRET=<webhook-secret>

# Rate Limiting
API_RATE_LIMIT_PER_MINUTE=60
SCAN_RATE_LIMIT_PER_MINUTE=30

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 2. SSL/TLS Configuration

For production, update `nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name secumator.yourdomain.com;
    
    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    
    # ... rest of config
}

server {
    listen 80;
    server_name secumator.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. Database Setup

```bash
# Run migrations
docker compose exec api alembic upgrade head

# Create backup
docker compose exec db pg_dump -U secumator secumator > backup.sql
```

### 4. Scaling

For high availability, scale the API service:

```bash
docker compose up -d --scale api=3
```

Update nginx for load balancing:

```nginx
upstream api {
    least_conn;
    server api_1:8000;
    server api_2:8000;
    server api_3:8000;
}
```

## Kubernetes Deployment

### Helm Chart (Coming Soon)

```bash
helm repo add secumator https://charts.secumator.io
helm install secumator secumator/secumator \
  --set api.replicas=3 \
  --set database.enabled=true \
  --set redis.enabled=true
```

### Manual Kubernetes

See `k8s/` directory for manifests.

## Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000
```

### Prometheus Metrics (Coming Soon)

Metrics endpoint: `/metrics`

### Logging

Logs are structured JSON. Configure log aggregation:

```yaml
# docker-compose.override.yml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Backup & Recovery

### Database Backup

```bash
# Backup
docker compose exec db pg_dump -U secumator secumator | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip -c backup.sql.gz | docker compose exec -T db psql -U secumator secumator
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v secumator_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data.tar.gz /data
```

## Security Hardening

1. **Network Security**
   - Use internal Docker networks
   - Expose only necessary ports
   - Use firewall rules

2. **Secrets Management**
   - Use Docker secrets or external vault
   - Rotate API keys regularly

3. **Updates**
   - Keep base images updated
   - Monitor for vulnerabilities with Trivy

## Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check database status
docker compose exec db pg_isready -U secumator
```

**Redis Connection Failed**
```bash
# Check Redis status
docker compose exec redis redis-cli ping
```

**API Not Starting**
```bash
# Check logs
docker compose logs api --tail=100
```

### Support

- GitHub Issues: https://github.com/tugcantopaloglu/secumator/issues
- Documentation: https://docs.secumator.io
