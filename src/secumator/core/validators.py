import ipaddress
import re
import socket
from urllib.parse import urlparse
from typing import Literal
from pydantic import BaseModel
from secumator.core import get_logger

logger = get_logger("validators")


class ValidationResult(BaseModel):
    valid: bool
    target_type: Literal["url", "ip", "cidr", "hostname"] | None = None
    normalized: str | None = None
    error: str | None = None
    warnings: list[str] = []


class TargetValidator:
    PRIVATE_NETWORKS = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fe80::/10"),
        ipaddress.ip_network("fc00::/7"),
    ]

    DANGEROUS_PORTS = {22, 23, 3389, 5900}
    BLOCKED_DOMAINS = {"localhost", "127.0.0.1", "0.0.0.0"}

    URL_REGEX = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,63}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    HOSTNAME_REGEX = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}\.?$"
    )

    def __init__(self, allow_private: bool = False, allow_localhost: bool = False):
        self.allow_private = allow_private
        self.allow_localhost = allow_localhost

    def validate(self, target: str) -> ValidationResult:
        target = target.strip()

        if not target:
            return ValidationResult(valid=False, error="Target cannot be empty")

        if len(target) > 2048:
            return ValidationResult(valid=False, error="Target too long (max 2048 chars)")

        if result := self._validate_url(target):
            return result

        if result := self._validate_ip(target):
            return result

        if result := self._validate_cidr(target):
            return result

        if result := self._validate_hostname(target):
            return result

        return ValidationResult(valid=False, error="Invalid target format")

    def _validate_url(self, target: str) -> ValidationResult | None:
        if not target.startswith(("http://", "https://")):
            return None

        try:
            parsed = urlparse(target)
            if not parsed.netloc:
                return ValidationResult(valid=False, error="Invalid URL: missing host")

            host = parsed.hostname
            warnings = []

            if not self.allow_localhost and host in self.BLOCKED_DOMAINS:
                return ValidationResult(valid=False, error="Localhost targets not allowed")

            if host:
                try:
                    ip = ipaddress.ip_address(host)
                    private_check = self._check_private_ip(ip)
                    if private_check:
                        return private_check
                except ValueError:
                    try:
                        resolved = socket.gethostbyname(host)
                        ip = ipaddress.ip_address(resolved)
                        private_check = self._check_private_ip(ip)
                        if private_check:
                            return private_check
                    except socket.gaierror:
                        warnings.append(f"Could not resolve hostname: {host}")

            if parsed.port in self.DANGEROUS_PORTS:
                warnings.append(f"Targeting potentially dangerous port: {parsed.port}")

            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"
            if parsed.query:
                normalized += f"?{parsed.query}"

            return ValidationResult(
                valid=True,
                target_type="url",
                normalized=normalized,
                warnings=warnings,
            )

        except Exception as e:
            return ValidationResult(valid=False, error=f"Invalid URL: {str(e)}")

    def _validate_ip(self, target: str) -> ValidationResult | None:
        try:
            ip = ipaddress.ip_address(target)
            private_check = self._check_private_ip(ip)
            if private_check:
                return private_check

            return ValidationResult(valid=True, target_type="ip", normalized=str(ip))
        except ValueError:
            return None

    def _validate_cidr(self, target: str) -> ValidationResult | None:
        if "/" not in target:
            return None

        try:
            network = ipaddress.ip_network(target, strict=False)

            if network.num_addresses > 65536:
                return ValidationResult(
                    valid=False, error="CIDR range too large (max /16 for IPv4)"
                )

            warnings = []
            if not self.allow_private:
                for private in self.PRIVATE_NETWORKS:
                    if network.overlaps(private):
                        if self.allow_private:
                            warnings.append("Network overlaps with private address space")
                        else:
                            return ValidationResult(
                                valid=False, error="Private network ranges not allowed"
                            )

            return ValidationResult(
                valid=True,
                target_type="cidr",
                normalized=str(network),
                warnings=warnings,
            )
        except ValueError:
            return None

    def _validate_hostname(self, target: str) -> ValidationResult | None:
        if not self.HOSTNAME_REGEX.match(target):
            return None

        if target.lower() in self.BLOCKED_DOMAINS:
            return ValidationResult(valid=False, error="Blocked hostname")

        warnings = []
        try:
            resolved = socket.gethostbyname(target)
            ip = ipaddress.ip_address(resolved)
            private_check = self._check_private_ip(ip)
            if private_check:
                return private_check
        except socket.gaierror:
            warnings.append(f"Could not resolve hostname: {target}")

        return ValidationResult(
            valid=True, target_type="hostname", normalized=target.lower(), warnings=warnings
        )

    def _check_private_ip(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> ValidationResult | None:
        if not self.allow_private:
            for network in self.PRIVATE_NETWORKS:
                if ip in network:
                    return ValidationResult(
                        valid=False, error=f"Private IP addresses not allowed: {ip}"
                    )

        if not self.allow_localhost and ip.is_loopback:
            return ValidationResult(valid=False, error="Localhost not allowed")

        return None


def validate_target(target: str, allow_private: bool = False, allow_localhost: bool = False) -> ValidationResult:
    validator = TargetValidator(allow_private=allow_private, allow_localhost=allow_localhost)
    return validator.validate(target)
