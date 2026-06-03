"""Apple Sign In identity-token verification.

Mobile flow: expo-apple-authentication on iOS hands back a JWT identity_token
signed by Apple (RS256). We verify it against Apple's JWKS at
`https://appleid.apple.com/auth/keys`, with the bundle ID as `aud`.

Caveats (see PROGRESS.md Session 6 entry):
- Apple's identity token only includes `email` on the very first sign-in.
  Subsequent logins for the same user omit it; we fall back to looking up
  the existing SocialAccount by `sub`.
- Apple's "Hide My Email" produces a relay address (`@privaterelay.appleid.com`).
  That's fine — we store it like any other email; Apple forwards mail.
- The user's full name is delivered by the client (expo-apple-authentication
  returns it as a JS object on first sign-in only). Server treats it as
  optional metadata.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from functools import lru_cache

import jwt
import requests
from django.conf import settings

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"
APPLE_JWKS_CACHE_SECONDS = 60 * 60 * 24


class AppleAuthError(Exception):
    """Raised when the identity_token is invalid, expired, or for the wrong audience."""


@dataclass(frozen=True)
class AppleProfile:
    sub: str  # Apple's stable user ID (the only durable identifier)
    email: str  # may be a private-relay address; may be empty on repeat logins
    email_verified: bool


# Module-level cache: (timestamp, jwks_dict). Refreshed every 24h.
_jwks_cache: tuple[float, dict] | None = None


def _fetch_jwks() -> dict:
    """Fetch Apple's JWKS; cached for 24 hours to avoid hammering Apple."""
    global _jwks_cache
    now = time.time()
    if _jwks_cache is not None:
        ts, data = _jwks_cache
        if now - ts < APPLE_JWKS_CACHE_SECONDS:
            return data
    response = requests.get(APPLE_JWKS_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    _jwks_cache = (now, data)
    return data


def _clear_jwks_cache() -> None:
    """Test-only hook."""
    global _jwks_cache
    _jwks_cache = None


@lru_cache(maxsize=1)
def _signing_alg() -> str:
    # Apple signs identity tokens with RS256.
    return "RS256"


def verify_identity_token(raw_token: str) -> AppleProfile:
    """Verify Apple identity_token signature + claims and return a profile."""
    if not raw_token:
        raise AppleAuthError("missing_token")
    if not settings.APPLE_BUNDLE_ID:
        raise AppleAuthError("server_misconfigured")

    # Pull `kid` from the JWT header without verifying so we can pick the right JWK.
    try:
        header = jwt.get_unverified_header(raw_token)
    except jwt.PyJWTError as exc:
        raise AppleAuthError(f"malformed_token: {exc}") from exc

    kid = header.get("kid")
    if not kid:
        raise AppleAuthError("missing_kid")

    jwks = _fetch_jwks()
    jwk = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if jwk is None:
        # Apple rotated keys since our cache; force refresh once.
        _clear_jwks_cache()
        jwks = _fetch_jwks()
        jwk = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if jwk is None:
        raise AppleAuthError("unknown_kid")

    try:
        public_key = jwt.PyJWK(jwk).key
        claims = jwt.decode(
            raw_token,
            public_key,
            algorithms=[_signing_alg()],
            audience=settings.APPLE_BUNDLE_ID,
            issuer=APPLE_ISSUER,
            options={"require": ["sub", "aud", "iss", "exp", "iat"]},
        )
    except jwt.PyJWTError as exc:
        raise AppleAuthError(f"invalid_token: {exc}") from exc

    sub = claims.get("sub")
    if not sub:
        raise AppleAuthError("missing_sub")

    email = (claims.get("email") or "").lower()
    email_verified = bool(claims.get("email_verified")) or bool(claims.get("is_private_email"))

    return AppleProfile(sub=str(sub), email=email, email_verified=email_verified)
