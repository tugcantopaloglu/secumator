from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from secumator.core import get_logger
from secumator.models.scan import Finding, Scan, ScanStatus, ScanType, Severity
from .base import ScanResult
from .nuclei import NucleiScanner
from .nmap import NmapScanner
from .nikto import NiktoScanner


class ScanEngine:
    def __init__(self):
        self.logger = get_logger("scan_engine")
        self.nuclei = NucleiScanner()
        self.nmap = NmapScanner()
        self.nikto = NiktoScanner()

    def get_scanners_for_type(self, scan_type: ScanType) -> list[tuple[str, Any]]:
        scanners = {
            ScanType.WEBAPP: [("nuclei", self.nuclei), ("nikto", self.nikto)],
            ScanType.NETWORK: [("nmap", self.nmap)],
            ScanType.API: [("nuclei", self.nuclei)],
            ScanType.FULL: [("nuclei", self.nuclei), ("nmap", self.nmap), ("nikto", self.nikto)],
        }
        return scanners.get(scan_type, [])

    async def run_scan(self, scan: Scan, db: AsyncSession) -> Scan:
        self.logger.info("starting_scan", scan_id=scan.id, target=scan.target, type=scan.scan_type.value)

        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now(timezone.utc)
        await db.commit()

        scanners = self.get_scanners_for_type(scan.scan_type)
        all_findings = []
        all_raw_output = {}
        errors = []

        for scanner_name, scanner in scanners:
            if not scanner.is_available():
                self.logger.warning("scanner_unavailable", scanner=scanner_name)
                errors.append(f"{scanner_name}: not available")
                continue

            try:
                self.logger.info("running_scanner", scanner=scanner_name, target=scan.target)
                result: ScanResult = await scanner.scan(scan.target, scan.options)

                all_raw_output[scanner_name] = result.raw_output

                if result.success:
                    all_findings.extend(result.findings)
                    self.logger.info("scanner_completed", scanner=scanner_name, findings=len(result.findings))
                else:
                    errors.append(f"{scanner_name}: {result.error}")
                    self.logger.error("scanner_failed", scanner=scanner_name, error=result.error)

            except Exception as e:
                self.logger.error("scanner_exception", scanner=scanner_name, error=str(e))
                errors.append(f"{scanner_name}: {str(e)}")

        for finding_data in all_findings:
            finding = Finding(
                scan_id=scan.id,
                title=finding_data.get("title", "Unknown")[:500],
                severity=Severity(finding_data.get("severity", "info")),
                description=finding_data.get("description"),
                evidence=finding_data.get("evidence"),
                recommendation=finding_data.get("recommendation"),
                cve_id=finding_data.get("cve_id"),
                cvss_score=finding_data.get("cvss_score"),
                affected_component=finding_data.get("affected_component"),
                source_tool=finding_data.get("source_tool"),
                raw_data=finding_data.get("raw_data"),
            )
            db.add(finding)

        scan.raw_output = all_raw_output
        scan.completed_at = datetime.now(timezone.utc)

        if errors and not all_findings:
            scan.status = ScanStatus.FAILED
            scan.error_message = "; ".join(errors)
        else:
            scan.status = ScanStatus.COMPLETED
            if errors:
                scan.error_message = f"Partial success. Errors: {'; '.join(errors)}"

        await db.commit()
        await db.refresh(scan)

        self.logger.info(
            "scan_completed",
            scan_id=scan.id,
            status=scan.status.value,
            findings=len(all_findings),
        )

        return scan
