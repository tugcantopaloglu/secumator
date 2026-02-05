import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import httpx
from secumator.core import get_logger
from secumator.models.scan import Scan, Finding

logger = get_logger("notifications")


class NotificationEvent(str, Enum):
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    CRITICAL_FINDING = "critical_finding"
    HIGH_FINDING = "high_finding"
    REPORT_GENERATED = "report_generated"


@dataclass
class NotificationPayload:
    event: NotificationEvent
    scan_id: int | None = None
    target: str | None = None
    status: str | None = None
    findings_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    message: str = ""
    report_url: str | None = None
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class WebhookProvider(ABC):
    @abstractmethod
    async def send(self, payload: NotificationPayload) -> bool:
        pass


class SlackWebhook(WebhookProvider):
    def __init__(self, webhook_url: str, channel: str | None = None, username: str = "Secumator"):
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username

    def _format_message(self, payload: NotificationPayload) -> dict[str, Any]:
        colors = {
            NotificationEvent.SCAN_STARTED: "#3498db",
            NotificationEvent.SCAN_COMPLETED: "#2ecc71",
            NotificationEvent.SCAN_FAILED: "#e74c3c",
            NotificationEvent.CRITICAL_FINDING: "#e74c3c",
            NotificationEvent.HIGH_FINDING: "#e67e22",
            NotificationEvent.REPORT_GENERATED: "#9b59b6",
        }

        icons = {
            NotificationEvent.SCAN_STARTED: "🔍",
            NotificationEvent.SCAN_COMPLETED: "✅",
            NotificationEvent.SCAN_FAILED: "❌",
            NotificationEvent.CRITICAL_FINDING: "🚨",
            NotificationEvent.HIGH_FINDING: "⚠️",
            NotificationEvent.REPORT_GENERATED: "📄",
        }

        fields = []
        if payload.target:
            fields.append({"title": "Target", "value": payload.target, "short": True})
        if payload.scan_id:
            fields.append({"title": "Scan ID", "value": str(payload.scan_id), "short": True})
        if payload.findings_count:
            fields.append({
                "title": "Findings",
                "value": f"🔴 {payload.critical_count} Critical | 🟠 {payload.high_count} High | 🟡 {payload.medium_count} Medium",
                "short": False,
            })
        if payload.report_url:
            fields.append({"title": "Report", "value": f"<{payload.report_url}|Download Report>", "short": True})

        message = {
            "username": self.username,
            "icon_emoji": ":shield:",
            "attachments": [{
                "color": colors.get(payload.event, "#95a5a6"),
                "title": f"{icons.get(payload.event, '📢')} {payload.event.value.replace('_', ' ').title()}",
                "text": payload.message,
                "fields": fields,
                "footer": "Secumator Security Scanner",
                "ts": int(payload.timestamp.timestamp()) if payload.timestamp else None,
            }],
        }

        if self.channel:
            message["channel"] = self.channel

        return message

    async def send(self, payload: NotificationPayload) -> bool:
        try:
            message = self._format_message(payload)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    timeout=10.0,
                )
                success = response.status_code == 200
                if not success:
                    logger.error("slack_webhook_failed", status=response.status_code, body=response.text)
                return success
        except Exception as e:
            logger.error("slack_webhook_error", error=str(e))
            return False


class DiscordWebhook(WebhookProvider):
    def __init__(self, webhook_url: str, username: str = "Secumator"):
        self.webhook_url = webhook_url
        self.username = username

    def _format_message(self, payload: NotificationPayload) -> dict[str, Any]:
        colors = {
            NotificationEvent.SCAN_STARTED: 0x3498DB,
            NotificationEvent.SCAN_COMPLETED: 0x2ECC71,
            NotificationEvent.SCAN_FAILED: 0xE74C3C,
            NotificationEvent.CRITICAL_FINDING: 0xE74C3C,
            NotificationEvent.HIGH_FINDING: 0xE67E22,
            NotificationEvent.REPORT_GENERATED: 0x9B59B6,
        }

        icons = {
            NotificationEvent.SCAN_STARTED: "🔍",
            NotificationEvent.SCAN_COMPLETED: "✅",
            NotificationEvent.SCAN_FAILED: "❌",
            NotificationEvent.CRITICAL_FINDING: "🚨",
            NotificationEvent.HIGH_FINDING: "⚠️",
            NotificationEvent.REPORT_GENERATED: "📄",
        }

        fields = []
        if payload.target:
            fields.append({"name": "Target", "value": f"`{payload.target}`", "inline": True})
        if payload.scan_id:
            fields.append({"name": "Scan ID", "value": str(payload.scan_id), "inline": True})
        if payload.findings_count:
            fields.append({
                "name": "Findings Summary",
                "value": f"🔴 **{payload.critical_count}** Critical\n🟠 **{payload.high_count}** High\n🟡 **{payload.medium_count}** Medium",
                "inline": False,
            })
        if payload.report_url:
            fields.append({"name": "Report", "value": f"[Download Report]({payload.report_url})", "inline": True})

        embed = {
            "title": f"{icons.get(payload.event, '📢')} {payload.event.value.replace('_', ' ').title()}",
            "description": payload.message,
            "color": colors.get(payload.event, 0x95A5A6),
            "fields": fields,
            "footer": {"text": "Secumator Security Scanner"},
            "timestamp": payload.timestamp.isoformat() if payload.timestamp else None,
        }

        return {
            "username": self.username,
            "avatar_url": "https://raw.githubusercontent.com/tugcantopaloglu/secumator/main/assets/logo.png",
            "embeds": [embed],
        }

    async def send(self, payload: NotificationPayload) -> bool:
        try:
            message = self._format_message(payload)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    timeout=10.0,
                )
                success = response.status_code in (200, 204)
                if not success:
                    logger.error("discord_webhook_failed", status=response.status_code, body=response.text)
                return success
        except Exception as e:
            logger.error("discord_webhook_error", error=str(e))
            return False


class TeamsWebhook(WebhookProvider):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def _format_message(self, payload: NotificationPayload) -> dict[str, Any]:
        colors = {
            NotificationEvent.SCAN_STARTED: "0078D7",
            NotificationEvent.SCAN_COMPLETED: "00A651",
            NotificationEvent.SCAN_FAILED: "E74C3C",
            NotificationEvent.CRITICAL_FINDING: "E74C3C",
            NotificationEvent.HIGH_FINDING: "E67E22",
            NotificationEvent.REPORT_GENERATED: "9B59B6",
        }

        facts = []
        if payload.target:
            facts.append({"name": "Target", "value": payload.target})
        if payload.scan_id:
            facts.append({"name": "Scan ID", "value": str(payload.scan_id)})
        if payload.findings_count:
            facts.append({
                "name": "Findings",
                "value": f"Critical: {payload.critical_count} | High: {payload.high_count} | Medium: {payload.medium_count}",
            })

        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": colors.get(payload.event, "95A5A6"),
            "summary": payload.event.value.replace("_", " ").title(),
            "sections": [{
                "activityTitle": f"🔒 {payload.event.value.replace('_', ' ').title()}",
                "activitySubtitle": "Secumator Security Scanner",
                "facts": facts,
                "text": payload.message,
            }],
        }

    async def send(self, payload: NotificationPayload) -> bool:
        try:
            message = self._format_message(payload)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    timeout=10.0,
                )
                return response.status_code == 200
        except Exception as e:
            logger.error("teams_webhook_error", error=str(e))
            return False


class NotificationManager:
    def __init__(self):
        self._providers: list[WebhookProvider] = []
        self._event_filters: dict[str, list[NotificationEvent]] = {}

    def add_provider(self, name: str, provider: WebhookProvider, events: list[NotificationEvent] | None = None):
        self._providers.append(provider)
        if events:
            self._event_filters[name] = events

    async def notify(self, payload: NotificationPayload):
        tasks = [provider.send(payload) for provider in self._providers]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            logger.info(
                "notifications_sent",
                event=payload.event.value,
                total=len(tasks),
                success=success_count,
            )

    async def notify_scan_started(self, scan: Scan):
        await self.notify(NotificationPayload(
            event=NotificationEvent.SCAN_STARTED,
            scan_id=scan.id,
            target=scan.target,
            message=f"Security scan initiated for {scan.target}",
        ))

    async def notify_scan_completed(self, scan: Scan, findings: list[Finding]):
        critical = sum(1 for f in findings if f.severity.value == "critical")
        high = sum(1 for f in findings if f.severity.value == "high")
        medium = sum(1 for f in findings if f.severity.value == "medium")

        event = NotificationEvent.SCAN_COMPLETED
        if critical > 0:
            event = NotificationEvent.CRITICAL_FINDING
        elif high > 0:
            event = NotificationEvent.HIGH_FINDING

        await self.notify(NotificationPayload(
            event=event,
            scan_id=scan.id,
            target=scan.target,
            status=scan.status.value,
            findings_count=len(findings),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            message=f"Scan completed with {len(findings)} findings" + 
                    (f" including {critical} critical vulnerabilities!" if critical else ""),
        ))

    async def notify_scan_failed(self, scan: Scan, error: str):
        await self.notify(NotificationPayload(
            event=NotificationEvent.SCAN_FAILED,
            scan_id=scan.id,
            target=scan.target,
            message=f"Scan failed: {error}",
        ))


notification_manager = NotificationManager()
