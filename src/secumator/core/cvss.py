import re
from dataclasses import dataclass
from enum import Enum
from typing import Any
import httpx
from secumator.core import get_logger

logger = get_logger("cvss")


class CVSSVersion(str, Enum):
    V2 = "2.0"
    V3 = "3.0"
    V31 = "3.1"
    V4 = "4.0"


@dataclass
class CVSSScore:
    version: CVSSVersion
    vector: str
    base_score: float
    severity: str
    impact_score: float | None = None
    exploitability_score: float | None = None


class CVSSCalculator:
    SEVERITY_THRESHOLDS_V3 = [
        (0.0, "None"),
        (0.1, "Low"),
        (4.0, "Medium"),
        (7.0, "High"),
        (9.0, "Critical"),
    ]

    V31_WEIGHTS = {
        "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2},
        "AC": {"L": 0.77, "H": 0.44},
        "PR": {
            "N": {"U": 0.85, "C": 0.85},
            "L": {"U": 0.62, "C": 0.68},
            "H": {"U": 0.27, "C": 0.50},
        },
        "UI": {"N": 0.85, "R": 0.62},
        "S": {"U": 6.42, "C": 7.52},
        "C": {"N": 0, "L": 0.22, "H": 0.56},
        "I": {"N": 0, "L": 0.22, "H": 0.56},
        "A": {"N": 0, "L": 0.22, "H": 0.56},
    }

    def parse_vector(self, vector: str) -> dict[str, str]:
        pattern = r"CVSS:(\d\.\d)/(.+)"
        match = re.match(pattern, vector)
        if not match:
            raise ValueError(f"Invalid CVSS vector: {vector}")

        version = match.group(1)
        metrics_str = match.group(2)

        metrics = {}
        for part in metrics_str.split("/"):
            if ":" in part:
                key, value = part.split(":", 1)
                metrics[key] = value

        metrics["_version"] = version
        return metrics

    def calculate_v31(self, vector: str) -> CVSSScore:
        metrics = self.parse_vector(vector)

        av = self.V31_WEIGHTS["AV"].get(metrics.get("AV", "N"), 0.85)
        ac = self.V31_WEIGHTS["AC"].get(metrics.get("AC", "L"), 0.77)
        scope = metrics.get("S", "U")
        pr = self.V31_WEIGHTS["PR"].get(metrics.get("PR", "N"), {}).get(scope, 0.85)
        ui = self.V31_WEIGHTS["UI"].get(metrics.get("UI", "N"), 0.85)

        c = self.V31_WEIGHTS["C"].get(metrics.get("C", "N"), 0)
        i = self.V31_WEIGHTS["I"].get(metrics.get("I", "N"), 0)
        a = self.V31_WEIGHTS["A"].get(metrics.get("A", "N"), 0)

        isc_base = 1 - (1 - c) * (1 - i) * (1 - a)

        if scope == "U":
            impact = 6.42 * isc_base
        else:
            impact = 7.52 * (isc_base - 0.029) - 3.25 * pow(isc_base - 0.02, 15)

        exploitability = 8.22 * av * ac * pr * ui

        if impact <= 0:
            base_score = 0.0
        else:
            if scope == "U":
                base_score = min(impact + exploitability, 10)
            else:
                base_score = min(1.08 * (impact + exploitability), 10)

        base_score = round(base_score * 10) / 10

        severity = "None"
        for threshold, sev in self.SEVERITY_THRESHOLDS_V3:
            if base_score >= threshold:
                severity = sev

        return CVSSScore(
            version=CVSSVersion.V31,
            vector=vector,
            base_score=base_score,
            severity=severity,
            impact_score=round(impact * 10) / 10 if impact > 0 else 0.0,
            exploitability_score=round(exploitability * 10) / 10,
        )

    def calculate(self, vector: str) -> CVSSScore:
        metrics = self.parse_vector(vector)
        version = metrics.get("_version", "3.1")

        if version in ("3.0", "3.1"):
            return self.calculate_v31(vector)
        else:
            raise ValueError(f"Unsupported CVSS version: {version}")

    @staticmethod
    def severity_from_score(score: float) -> str:
        if score == 0:
            return "none"
        elif score < 4.0:
            return "low"
        elif score < 7.0:
            return "medium"
        elif score < 9.0:
            return "high"
        else:
            return "critical"


class CVELookup:
    NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    CACHE_TTL = 86400

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._cache: dict[str, dict[str, Any]] = {}

    async def lookup(self, cve_id: str) -> dict[str, Any] | None:
        cve_id = cve_id.upper().strip()
        if not re.match(r"^CVE-\d{4}-\d+$", cve_id):
            logger.warning("invalid_cve_format", cve_id=cve_id)
            return None

        if cve_id in self._cache:
            return self._cache[cve_id]

        try:
            headers = {}
            if self.api_key:
                headers["apiKey"] = self.api_key

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.NVD_API_URL,
                    params={"cveId": cve_id},
                    headers=headers,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    vulns = data.get("vulnerabilities", [])
                    if vulns:
                        cve_data = self._parse_nvd_response(vulns[0])
                        self._cache[cve_id] = cve_data
                        return cve_data

                elif response.status_code == 404:
                    logger.info("cve_not_found", cve_id=cve_id)
                else:
                    logger.warning("nvd_api_error", status=response.status_code, cve_id=cve_id)

        except Exception as e:
            logger.error("cve_lookup_error", cve_id=cve_id, error=str(e))

        return None

    def _parse_nvd_response(self, vuln: dict[str, Any]) -> dict[str, Any]:
        cve = vuln.get("cve", {})
        metrics = cve.get("metrics", {})

        cvss_v31 = metrics.get("cvssMetricV31", [{}])[0] if metrics.get("cvssMetricV31") else {}
        cvss_v3 = metrics.get("cvssMetricV30", [{}])[0] if metrics.get("cvssMetricV30") else {}
        cvss_v2 = metrics.get("cvssMetricV2", [{}])[0] if metrics.get("cvssMetricV2") else {}

        cvss_data = cvss_v31.get("cvssData") or cvss_v3.get("cvssData") or cvss_v2.get("cvssData") or {}

        descriptions = cve.get("descriptions", [])
        description = next((d["value"] for d in descriptions if d.get("lang") == "en"), "")

        references = [ref.get("url") for ref in cve.get("references", []) if ref.get("url")]

        weaknesses = []
        for weakness in cve.get("weaknesses", []):
            for desc in weakness.get("description", []):
                if desc.get("lang") == "en":
                    weaknesses.append(desc.get("value"))

        return {
            "cve_id": cve.get("id"),
            "description": description,
            "cvss_version": cvss_data.get("version"),
            "cvss_vector": cvss_data.get("vectorString"),
            "cvss_score": cvss_data.get("baseScore"),
            "severity": cvss_data.get("baseSeverity", "").lower(),
            "exploitability_score": cvss_v31.get("exploitabilityScore") or cvss_v3.get("exploitabilityScore"),
            "impact_score": cvss_v31.get("impactScore") or cvss_v3.get("impactScore"),
            "published": cve.get("published"),
            "last_modified": cve.get("lastModified"),
            "references": references[:10],
            "weaknesses": weaknesses,
        }

    async def bulk_lookup(self, cve_ids: list[str]) -> dict[str, dict[str, Any] | None]:
        results = {}
        for cve_id in cve_ids:
            results[cve_id] = await self.lookup(cve_id)
        return results


cvss_calculator = CVSSCalculator()
cve_lookup = CVELookup()
