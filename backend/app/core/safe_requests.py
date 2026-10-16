"""Safe External Request & SSRF Protection Shield.

Protects ProcuraX server-side HTTP fetchers from Server-Side Request Forgery (SSRF),
unintended internal network access, cloud metadata exfiltration, and arbitrary URL fetching.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Set


# Approved public signal and regulatory providers
APPROVED_EXTERNAL_DOMAINS: Set[str] = {
    "api.gdeltproject.org",
    "gdeltproject.org",
    "api.marketaux.com",
    "marketaux.com",
    "www.alphavantage.co",
    "alphavantage.co",
    "newsdata.io",
    "data.sec.gov",
    "www.sec.gov",
    "sec.gov",
}

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local & AWS/GCP/Azure Metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


class SSRFSecurityError(ValueError):
    """Raised when an external request targets a forbidden internal, private, or metadata endpoint."""
    pass


def is_ip_blocked(ip_str: str) -> bool:
    """Check if an IP address belongs to private, loopback, or metadata networks."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in BLOCKED_IP_NETWORKS)
    except ValueError:
        return True


def validate_external_url(url: str, allow_custom_approved: Set[str] | None = None) -> str:
    """Validate that a URL is safe for server-side consumption.
    
    Guarantees:
    1. Scheme must be HTTP or HTTPS.
    2. Hostname must belong to an approved provider domain.
    3. Resolved IP must NOT belong to loopback, private RFC1918, or cloud metadata networks.
    
    Raises:
        SSRFSecurityError if any check fails.
    """
    if not url or not isinstance(url, str):
        raise SSRFSecurityError("Invalid URL: must be a non-empty string.")

    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise SSRFSecurityError(f"Forbidden URL scheme '{parsed.scheme}'. Only 'http' and 'https' are allowed.")

    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        raise SSRFSecurityError("URL must contain a valid hostname.")

    # Check approved domains
    approved = allow_custom_approved or APPROVED_EXTERNAL_DOMAINS
    domain_allowed = False
    for approved_domain in approved:
        if hostname == approved_domain or hostname.endswith("." + approved_domain):
            domain_allowed = True
            break

    if not domain_allowed:
        raise SSRFSecurityError(
            f"SSRF Protection: Hostname '{hostname}' is not in the approved external provider whitelist."
        )

    # DNS Resolution Check
    try:
        # Resolve hostname to IPv4/IPv6 addresses
        addr_info = socket.getaddrinfo(hostname, None)
        ips = {item[4][0] for item in addr_info}
    except Exception as exc:
        raise SSRFSecurityError(f"DNS resolution failed for hostname '{hostname}': {exc}")

    for ip_str in ips:
        if is_ip_blocked(ip_str):
            raise SSRFSecurityError(
                f"SSRF Protection: Hostname '{hostname}' resolved to blocked/private IP '{ip_str}'."
            )

    return url
