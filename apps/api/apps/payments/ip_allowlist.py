"""Per-provider IP allowlist for webhook calls.

Empty list = allow any (dev / staging without IP info). Populated CIDRs in
prod enforce origin. Documented in AGENTS.md §4 "Provisioning payment
providers".
"""

from __future__ import annotations

import ipaddress

from django.conf import settings


def is_allowed(provider_name: str, remote_ip: str) -> bool:
    if not remote_ip:
        return False
    cidrs = getattr(settings, "PAYMENT_WEBHOOK_IP_ALLOWLIST", {}).get(provider_name) or []
    if not cidrs:
        # Empty list ⇒ allow any. Honest dev/staging posture.
        return True
    try:
        ip = ipaddress.ip_address(remote_ip)
    except ValueError:
        return False
    return any(ip in ipaddress.ip_network(c, strict=False) for c in cidrs)


def remote_ip_from_request(request) -> str:
    """Resolve the real client IP, respecting X-Forwarded-For if set
    by a trusted reverse proxy (Railway / Cloudflare both add it)."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "").strip()
    if forwarded:
        # The first hop is the client.
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")
