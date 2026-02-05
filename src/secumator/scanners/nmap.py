import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from secumator.core.config import settings
from .base import BaseScanner, ScanResult


class NmapScanner(BaseScanner):
    name = "nmap"
    binary_path = settings.nmap_path

    async def scan(self, target: str, options: dict[str, Any] | None = None) -> ScanResult:
        if not self.is_available():
            return ScanResult(success=False, error="Nmap binary not found")

        options = options or {}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            output_file = f.name

        try:
            cmd = [self.binary_path, "-oX", output_file]

            scan_type = options.get("scan_type", "default")
            if scan_type == "quick":
                cmd.extend(["-T4", "-F"])
            elif scan_type == "intense":
                cmd.extend(["-T4", "-A", "-v"])
            elif scan_type == "vuln":
                cmd.extend(["--script", "vuln"])
            else:
                cmd.extend(["-sV", "-sC"])

            if ports := options.get("ports"):
                cmd.extend(["-p", ports])
            if options.get("udp"):
                cmd.append("-sU")

            cmd.append(target)

            timeout = options.get("timeout", settings.scan_timeout)
            returncode, stdout, stderr = await self.run_command(cmd, timeout)

            output_path = Path(output_file)
            raw_output = output_path.read_text() if output_path.exists() else ""

            findings = self.parse_output(raw_output)

            return ScanResult(
                success=returncode == 0,
                findings=findings,
                raw_output={"stdout": stdout, "stderr": stderr, "xml": raw_output},
                error=stderr if returncode != 0 else None,
            )
        except TimeoutError as e:
            return ScanResult(success=False, error=str(e))
        except Exception as e:
            self.logger.error("nmap_scan_failed", error=str(e))
            return ScanResult(success=False, error=str(e))
        finally:
            Path(output_file).unlink(missing_ok=True)

    def parse_output(self, raw_output: str) -> list[dict[str, Any]]:
        findings = []
        if not raw_output:
            return findings

        try:
            root = ET.fromstring(raw_output)

            for host in root.findall(".//host"):
                addr = host.find("address")
                ip = addr.get("addr", "unknown") if addr is not None else "unknown"

                for port in host.findall(".//port"):
                    port_id = port.get("portid", "")
                    protocol = port.get("protocol", "tcp")
                    state = port.find("state")
                    service = port.find("service")

                    if state is not None and state.get("state") == "open":
                        service_name = service.get("name", "unknown") if service is not None else "unknown"
                        version = service.get("version", "") if service is not None else ""
                        product = service.get("product", "") if service is not None else ""

                        finding = {
                            "title": f"Open Port: {port_id}/{protocol} ({service_name})",
                            "severity": "info",
                            "description": f"Port {port_id}/{protocol} is open on {ip}. Service: {product} {version}".strip(),
                            "evidence": f"{ip}:{port_id}",
                            "affected_component": f"{ip}:{port_id}",
                            "source_tool": "nmap",
                            "raw_data": {
                                "ip": ip,
                                "port": port_id,
                                "protocol": protocol,
                                "service": service_name,
                                "product": product,
                                "version": version,
                            },
                        }
                        findings.append(finding)

                for script in host.findall(".//script"):
                    script_id = script.get("id", "")
                    output = script.get("output", "")

                    if "vuln" in script_id.lower() or "VULNERABLE" in output:
                        cve_match = re.search(r"CVE-\d{4}-\d+", output)
                        severity = "high" if "VULNERABLE" in output else "medium"

                        finding = {
                            "title": f"Vulnerability: {script_id}",
                            "severity": severity,
                            "description": output[:1000],
                            "evidence": output,
                            "cve_id": cve_match.group() if cve_match else None,
                            "affected_component": ip,
                            "source_tool": "nmap",
                            "raw_data": {"script_id": script_id, "output": output},
                        }
                        findings.append(finding)

        except ET.ParseError as e:
            self.logger.error("nmap_parse_error", error=str(e))

        return findings
