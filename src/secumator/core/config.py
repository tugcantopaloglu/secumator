from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Secumator"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-production"
    allowed_origins: list[str] = ["*"]

    database_url: str = "postgresql+asyncpg://secumator:secumator@localhost:5432/secumator"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_provider: Literal["openai", "anthropic"] = "openai"
    ai_model: str = "gpt-4o"

    nuclei_path: str = "/usr/bin/nuclei"
    nmap_path: str = "/usr/bin/nmap"
    nikto_path: str = "/usr/bin/nikto"

    scan_timeout: int = 3600
    max_concurrent_scans: int = 5
    scan_rate_limit_per_minute: int = 30

    allow_private_targets: bool = False
    allow_localhost_targets: bool = False

    slack_webhook_url: str = ""
    discord_webhook_url: str = ""
    teams_webhook_url: str = ""
    notify_on_scan_complete: bool = True
    notify_on_critical_finding: bool = True

    nvd_api_key: str = ""

    report_output_dir: str = "/var/lib/secumator/reports"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
