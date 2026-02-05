import pytest
from secumator.scanners import NucleiScanner, NmapScanner, NiktoScanner


def test_nuclei_scanner_init():
    scanner = NucleiScanner()
    assert scanner.name == "nuclei"


def test_nmap_scanner_init():
    scanner = NmapScanner()
    assert scanner.name == "nmap"


def test_nikto_scanner_init():
    scanner = NiktoScanner()
    assert scanner.name == "nikto"


def test_nuclei_parse_output():
    scanner = NucleiScanner()
    raw = '{"info":{"name":"Test Vuln","severity":"high","description":"Test"},"matched-at":"https://example.com","host":"example.com"}'
    findings = scanner.parse_output(raw)
    assert len(findings) == 1
    assert findings[0]["title"] == "Test Vuln"
    assert findings[0]["severity"] == "high"


def test_nuclei_parse_empty():
    scanner = NucleiScanner()
    findings = scanner.parse_output("")
    assert len(findings) == 0


def test_nmap_parse_output():
    scanner = NmapScanner()
    xml = """<?xml version="1.0"?>
    <nmaprun>
        <host>
            <address addr="192.168.1.1" addrtype="ipv4"/>
            <ports>
                <port protocol="tcp" portid="80">
                    <state state="open"/>
                    <service name="http" product="nginx" version="1.18"/>
                </port>
            </ports>
        </host>
    </nmaprun>"""
    findings = scanner.parse_output(xml)
    assert len(findings) == 1
    assert "Open Port: 80/tcp" in findings[0]["title"]


def test_nikto_parse_output():
    scanner = NiktoScanner()
    json_output = '{"host":"example.com","vulnerabilities":[{"OSVDB":"123","msg":"Test vulnerability","url":"/test"}]}'
    findings = scanner.parse_output(json_output)
    assert len(findings) == 1
    assert "Test vulnerability" in findings[0]["title"]
