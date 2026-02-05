import json
import tempfile
from pathlib import Path
from typing import Any
from secumator.core.config import settings
from .base import BaseScanner, ScanResult


class NucleiScanner(BaseScanner):
    name = "nuclei"
    binary_path = settings.nuclei_path

    async def scan(self, target: str, options: dict[str, Any] | None = None) -> ScanResult:
        if not self.is_available():
            return ScanResult(success=False, error="Nuclei binary not found")

        options = options or {}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            cmd = [
                self.binary_path,
                "-target", target,
                "-jsonl",
                "-output", output_file,
                "-silent",
            ]

            if templates := options.get("templates"):
                cmd.extend(["-t", templates])
            if severity := options.get("severity"):
                cmd.extend(["-severity", severity])
            if rate_limit := options.get("rate_limit"):
                cmd.extend(["-rate-limit", str(rate_limit)])
            if options.get("new_templates"):
                cmd.append("-nt")

            timeout = options.get("timeout", settings.scan_timeout)
            returncode, stdout, stderr = await self.run_command(cmd, timeout)

            output_path = Path(output_file)
            raw_output = output_path.read_text() if output_path.exists() else ""

            findings = self.parse_output(raw_output)

            return ScanResult(
                success=returncode == 0,
                findings=findings,
                raw_output={"stdout": stdout, "stderr": stderr, "results": raw_output},
                error=stderr if returncode != 0 else None,
            )
        except TimeoutError as e:
            return ScanResult(success=False, error=str(e))
        except Exception as e:
            self.logger.error("nuclei_scan_failed", error=str(e))
            return ScanResult(success=False, error=str(e))
        finally:
            Path(output_file).unlink(missing_ok=True)

    def parse_output(self, raw_output: str) -> list[dict[str, Any]]:
        findings = []
        for line in raw_output.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                finding = {
                    "title": data.get("info", {}).get("name", "Unknown"),
                    "severity": self.normalize_severity(data.get("info", {}).get("severity", "info")).value,
                    "description": data.get("info", {}).get("description", ""),
                    "evidence": data.get("matched-at", ""),
                    "recommendation": "\n".join(data.get("info", {}).get("remediation", [])) if isinstance(data.get("info", {}).get("remediation"), list) else data.get("info", {}).get("remediation", ""),
                    "cve_id": ",".join(data.get("info", {}).get("classification", {}).get("cve-id", [])) or None,
                    "cvss_score": data.get("info", {}).get("classification", {}).get("cvss-score"),
                    "affected_component": data.get("host", ""),
                    "source_tool": "nuclei",
                    "raw_data": data,
                }
                findings.append(finding)
            except json.JSONDecodeError:
                continue
        return findings
