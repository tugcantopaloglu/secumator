from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import re
import hashlib
from secumator.core import get_logger
from secumator.models.scan import Finding, Severity

logger = get_logger("correlation")


@dataclass
class CorrelatedFinding:
    id: str
    title: str
    severity: Severity
    description: str
    affected_components: list[str] = field(default_factory=list)
    source_tools: list[str] = field(default_factory=list)
    cve_ids: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    raw_findings: list[Finding] = field(default_factory=list)
    confidence: float = 1.0
    first_seen: datetime | None = None
    correlated_count: int = 1


@dataclass
class CorrelationResult:
    correlated_findings: list[CorrelatedFinding]
    total_raw_findings: int
    total_correlated: int
    dedup_ratio: float
    severity_distribution: dict[str, int]
    affected_components: list[str]
    correlation_summary: dict[str, Any]


class VulnerabilityCorrelator:
    SIMILARITY_THRESHOLD = 0.75
    CVE_PATTERN = re.compile(r"CVE-\d{4}-\d+", re.IGNORECASE)

    def __init__(self):
        self._correlation_rules: list[callable] = [
            self._correlate_by_cve,
            self._correlate_by_title_similarity,
            self._correlate_by_component,
            self._correlate_by_weakness_pattern,
        ]

    def correlate(self, findings: list[Finding]) -> CorrelationResult:
        if not findings:
            return CorrelationResult(
                correlated_findings=[],
                total_raw_findings=0,
                total_correlated=0,
                dedup_ratio=1.0,
                severity_distribution={},
                affected_components=[],
                correlation_summary={},
            )

        groups: dict[str, list[Finding]] = defaultdict(list)
        processed: set[int] = set()

        for finding in findings:
            if finding.id in processed:
                continue

            group_key = self._generate_group_key(finding)
            groups[group_key].append(finding)
            processed.add(finding.id)

            for other in findings:
                if other.id in processed:
                    continue
                if self._should_correlate(finding, other):
                    groups[group_key].append(other)
                    processed.add(other.id)

        correlated_findings = []
        for group_key, group_findings in groups.items():
            correlated = self._merge_findings(group_findings)
            correlated_findings.append(correlated)

        correlated_findings.sort(key=lambda f: self._severity_order(f.severity))

        severity_dist = defaultdict(int)
        all_components = set()
        for cf in correlated_findings:
            severity_dist[cf.severity.value] += 1
            all_components.update(cf.affected_components)

        dedup_ratio = len(correlated_findings) / len(findings) if findings else 1.0

        return CorrelationResult(
            correlated_findings=correlated_findings,
            total_raw_findings=len(findings),
            total_correlated=len(correlated_findings),
            dedup_ratio=dedup_ratio,
            severity_distribution=dict(severity_dist),
            affected_components=sorted(all_components),
            correlation_summary={
                "cve_correlations": sum(1 for f in correlated_findings if f.cve_ids),
                "multi_tool_correlations": sum(1 for f in correlated_findings if len(f.source_tools) > 1),
                "high_confidence": sum(1 for f in correlated_findings if f.confidence >= 0.9),
            },
        )

    def _generate_group_key(self, finding: Finding) -> str:
        if finding.cve_id:
            return f"cve:{finding.cve_id.lower()}"

        title_normalized = self._normalize_title(finding.title)
        component = (finding.affected_component or "unknown").lower()
        severity = finding.severity.value

        key_string = f"{title_normalized}:{component}:{severity}"
        return hashlib.md5(key_string.encode()).hexdigest()[:16]

    def _normalize_title(self, title: str) -> str:
        title = title.lower()
        title = re.sub(r"\s+", " ", title)
        title = re.sub(r"[^\w\s-]", "", title)
        title = re.sub(r"\b(v?\d+(\.\d+)*)\b", "", title)
        title = re.sub(r"\b(version|ver|v)\b", "", title)
        return title.strip()

    def _should_correlate(self, f1: Finding, f2: Finding) -> bool:
        for rule in self._correlation_rules:
            if rule(f1, f2):
                return True
        return False

    def _correlate_by_cve(self, f1: Finding, f2: Finding) -> bool:
        if f1.cve_id and f2.cve_id:
            cves1 = set(c.upper() for c in self.CVE_PATTERN.findall(f1.cve_id))
            cves2 = set(c.upper() for c in self.CVE_PATTERN.findall(f2.cve_id))
            return bool(cves1 & cves2)
        return False

    def _correlate_by_title_similarity(self, f1: Finding, f2: Finding) -> bool:
        t1 = self._normalize_title(f1.title)
        t2 = self._normalize_title(f2.title)

        if not t1 or not t2:
            return False

        words1 = set(t1.split())
        words2 = set(t2.split())

        if not words1 or not words2:
            return False

        intersection = len(words1 & words2)
        union = len(words1 | words2)
        similarity = intersection / union if union > 0 else 0

        return similarity >= self.SIMILARITY_THRESHOLD

    def _correlate_by_component(self, f1: Finding, f2: Finding) -> bool:
        if not f1.affected_component or not f2.affected_component:
            return False

        c1 = f1.affected_component.lower()
        c2 = f2.affected_component.lower()

        if c1 == c2 and f1.severity == f2.severity:
            t1 = self._normalize_title(f1.title)
            t2 = self._normalize_title(f2.title)
            words1 = set(t1.split())
            words2 = set(t2.split())
            return bool(words1 & words2)

        return False

    def _correlate_by_weakness_pattern(self, f1: Finding, f2: Finding) -> bool:
        weakness_keywords = {
            "sql_injection": ["sql", "injection", "sqli", "blind sql"],
            "xss": ["xss", "cross-site", "scripting", "reflected", "stored"],
            "rce": ["rce", "remote code", "command injection", "code execution"],
            "ssrf": ["ssrf", "server-side request"],
            "lfi": ["lfi", "local file", "path traversal", "directory traversal"],
            "xxe": ["xxe", "xml external", "entity injection"],
        }

        def get_weakness_type(title: str) -> str | None:
            title_lower = title.lower()
            for weakness, keywords in weakness_keywords.items():
                if any(kw in title_lower for kw in keywords):
                    return weakness
            return None

        w1 = get_weakness_type(f1.title)
        w2 = get_weakness_type(f2.title)

        if w1 and w2 and w1 == w2:
            if f1.affected_component == f2.affected_component:
                return True

        return False

    def _merge_findings(self, findings: list[Finding]) -> CorrelatedFinding:
        highest_severity = max(findings, key=lambda f: self._severity_order(f.severity))

        all_cves = set()
        all_components = set()
        all_tools = set()
        all_evidence = []
        all_recommendations = set()

        for f in findings:
            if f.cve_id:
                for cve in self.CVE_PATTERN.findall(f.cve_id):
                    all_cves.add(cve.upper())
            if f.affected_component:
                all_components.add(f.affected_component)
            if f.source_tool:
                all_tools.add(f.source_tool)
            if f.evidence:
                all_evidence.append(f.evidence)
            if f.recommendation:
                all_recommendations.add(f.recommendation)

        descriptions = [f.description for f in findings if f.description]
        best_description = max(descriptions, key=len) if descriptions else ""

        confidence = min(1.0, 0.5 + (len(all_tools) * 0.2) + (0.1 if all_cves else 0))

        first_seen = min((f.created_at for f in findings), default=datetime.now(timezone.utc))

        corr_id = hashlib.md5(
            f"{highest_severity.title}:{','.join(sorted(all_cves))}:{','.join(sorted(all_components))}".encode()
        ).hexdigest()[:12]

        return CorrelatedFinding(
            id=corr_id,
            title=highest_severity.title,
            severity=highest_severity.severity,
            description=best_description,
            affected_components=sorted(all_components),
            source_tools=sorted(all_tools),
            cve_ids=sorted(all_cves),
            evidence=all_evidence[:5],
            recommendations=sorted(all_recommendations)[:3],
            raw_findings=findings,
            confidence=confidence,
            first_seen=first_seen,
            correlated_count=len(findings),
        )

    @staticmethod
    def _severity_order(severity: Severity) -> int:
        order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        return order.get(severity, 5)


class FindingDeduplicator:
    def __init__(self):
        self._seen: dict[str, Finding] = {}

    def deduplicate(self, findings: list[Finding]) -> list[Finding]:
        unique = []
        for finding in findings:
            key = self._dedup_key(finding)
            if key not in self._seen:
                self._seen[key] = finding
                unique.append(finding)
            else:
                existing = self._seen[key]
                if self._should_replace(existing, finding):
                    self._seen[key] = finding
                    unique = [f for f in unique if self._dedup_key(f) != key]
                    unique.append(finding)
        return unique

    def _dedup_key(self, finding: Finding) -> str:
        title = finding.title.lower().strip()
        component = (finding.affected_component or "").lower().strip()
        cve = (finding.cve_id or "").lower().strip()

        if cve:
            return f"cve:{cve}"

        key_string = f"{title}:{component}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _should_replace(self, existing: Finding, new: Finding) -> bool:
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        existing_order = severity_order.get(existing.severity.value, 5)
        new_order = severity_order.get(new.severity.value, 5)

        if new_order < existing_order:
            return True

        if new_order == existing_order:
            existing_detail = len(existing.description or "") + len(existing.evidence or "")
            new_detail = len(new.description or "") + len(new.evidence or "")
            return new_detail > existing_detail

        return False


vulnerability_correlator = VulnerabilityCorrelator()
finding_deduplicator = FindingDeduplicator()
