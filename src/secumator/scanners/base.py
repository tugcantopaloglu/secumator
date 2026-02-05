import asyncio
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from secumator.core import get_logger
from secumator.models.scan import Severity


@dataclass
class ScanResult:
    success: bool
    findings: list[dict[str, Any]] = field(default_factory=list)
    raw_output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class BaseScanner(ABC):
    name: str = "base"
    binary_path: str = ""

    def __init__(self):
        self.logger = get_logger(f"scanner.{self.name}")

    def is_available(self) -> bool:
        return shutil.which(self.binary_path) is not None

    @abstractmethod
    async def scan(self, target: str, options: dict[str, Any] | None = None) -> ScanResult:
        pass

    @abstractmethod
    def parse_output(self, raw_output: str) -> list[dict[str, Any]]:
        pass

    async def run_command(self, cmd: list[str], timeout: int = 3600) -> tuple[int, str, str]:
        self.logger.info("running_command", cmd=" ".join(cmd))
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return proc.returncode or 0, stdout.decode(), stderr.decode()
        except asyncio.TimeoutError:
            proc.kill()
            raise TimeoutError(f"Command timed out after {timeout}s")
        except Exception as e:
            self.logger.error("command_failed", error=str(e))
            raise

    @staticmethod
    def normalize_severity(severity: str) -> Severity:
        mapping = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO,
            "informational": Severity.INFO,
            "unknown": Severity.INFO,
        }
        return mapping.get(severity.lower(), Severity.INFO)
