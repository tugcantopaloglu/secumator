import json
import tempfile
from pathlib import Path
from typing import Any
from secumator.core.config import settings
from .base import BaseScanner, ScanResult


class NiktoScanner(BaseScanner):
    name = "nikto"
    binary_path = settings.nikto_path

    async def scan(self, target: str, options: dict[str, Any] | None = None) -> ScanResult:
        if not self.is_available():
            return ScanResult(success=False, error="Nikto binary not found")

        options = options or {}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            cmd = [
                self.binary_path,
                "-h", target,
                "-Format", "json",
                "-output", output_file,
                "-nointeractive",
            ]

            if tuning := options.get("tuning"):
                cmd.extend(["-Tuning", tuning])
            if options.get("ssl"):
                cmd.append("-ssl")
            if port := options.get("port"):
                cmd.extend(["-p", str(port)])
            if options.get("no_404"):
                cmd.append("-no404")

            timeout = options.get("timeout", settings.scan_timeout)
            returncode, stdout, stderr = await self.run_command(cmd, timeout)

            output_path = Path(output_file)
            raw_output = output_path.read_text() if output_path.exists() else ""

            findings = self.parse_output(raw_output)

            return ScanResult(
                success=True,
                findings=findings,
                raw_output={"stdout": stdout, "stderr": stderr, "json": raw_output},
                error=stderr if returncode != 0 and not findings else None,
            )
        except TimeoutError as e:
            return ScanResult(success=False, error=str(e))
        except Exception as e:
            self.logger.error("nikto_scan_failed", error=str(e))
            return ScanResult(success=False, error=str(e))
        finally:
            Path(output_file).unlink(missing_ok=True)

    def parse_output(self, raw_output: str) -> list[dict[str, Any]]:
        findings = []
        if not raw_output:
            return findings

        try:
            data = json.loads(raw_output)

            for host_data in data if isinstance(data, list) else [data]:
                host = host_data.get("host", "unknown")
                vulnerabilities = host_data.get("vulnerabilities", [])

                for vuln in vulnerabilities:
                    osvdb_id = vuln.get("OSVDB", "")
                    severity = self._determine_severity(vuln)

                    finding = {
                        "title": vuln.get("msg", "Unknown vulnerability")[:200],
                        "severity": severity,
                        "description": vuln.get("msg", ""),
                        "evidence": vuln.get("url", ""),
                        "recommendation": self._get_recommendation(vuln),
                        "affected_component": f"{host}{vuln.get('url', '')}",
                        "source_tool": "nikto",
                        "raw_data": vuln,
                    }

                    if osvdb_id and osvdb_id != "0":
                        finding["cve_id"] = f"OSVDB-{osvdb_id}"

                    findings.append(finding)

        except json.JSONDecodeError:
            lines = raw_output.split("\n")
            for line in lines:
                if "+ " in line and "OSVDB" in line:
                    finding = {
                        "title": line.strip()[:200],
                        "severity": "medium",
                        "description": line.strip(),
                        "source_tool": "nikto",
                        "raw_data": {"line": line},
                    }
                    findings.append(finding)

        return findings

    def _determine_severity(self, vuln: dict) -> str:
        msg = vuln.get("msg", "").lower()
        if any(kw in msg for kw in ["remote code", "rce", "injection", "sqli", "command"]):
            return "critical"
        if any(kw in msg for kw in ["xss", "csrf", "directory listing", "backup"]):
            return "high"
        if any(kw in msg for kw in ["disclosure", "header", "cookie"]):
            return "medium"
        if any(kw in msg for kw in ["version", "server", "powered"]):
            return "low"
        return "info"

    def _get_recommendation(self, vuln: dict) -> str:
        msg = vuln.get("msg", "").lower()
        if "directory listing" in msg:
            return "Disable directory listing in web server configuration"
        if "backup" in msg:
            return "Remove backup files from web-accessible directories"
        if "header" in msg:
            return "Configure appropriate security headers"
        if "version" in msg:
            return "Hide server version information"
        return "Review and remediate the identified issue"
