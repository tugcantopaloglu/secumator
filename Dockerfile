FROM python:3.12-slim

LABEL maintainer="Tuğcan Topaloğlu <tugcan@tugcan.dev>"
LABEL description="Secumator - Professional Security Audit Report Generator"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    curl \
    wget \
    unzip \
    git \
    perl \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/sullo/nikto.git /opt/nikto && \
    ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto

RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        NUCLEI_ARCH="linux_amd64"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        NUCLEI_ARCH="linux_arm64"; \
    else \
        NUCLEI_ARCH="linux_amd64"; \
    fi && \
    wget -q https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_*_${NUCLEI_ARCH}.zip -O nuclei.zip || \
    wget -q https://github.com/projectdiscovery/nuclei/releases/download/v3.2.0/nuclei_3.2.0_${NUCLEI_ARCH}.zip -O nuclei.zip && \
    unzip -o nuclei.zip -d /usr/local/bin/ && \
    rm nuclei.zip && \
    chmod +x /usr/local/bin/nuclei

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir -e .

RUN mkdir -p /var/lib/secumator/reports && \
    useradd -m -s /bin/bash secumator && \
    chown -R secumator:secumator /var/lib/secumator

USER secumator

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "secumator.api:app", "--host", "0.0.0.0", "--port", "8000"]
