"""Google id_token verification.

Mobile flow: native Google Sign-In on the device produces an ID token whose
`aud` claim is one of our configured client IDs. We verify it server-side
against Google's public keys via `google.auth.transport.requests`.

This module deliberately does NOT implement the OAuth web redirect flow —
that lives in `expo-auth-session` on the client. The server only ever sees
already-issued id_tokens.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token


class GoogleAuthError(Exception):
    """Raised when the id_token is invalid, expired, or for the wrong audience."""


@dataclass(frozen=True)
class GoogleProfile:
    sub: str  # Google's stable user ID
    email: str  # always verified by Google before issuing the token
    first_name: str
    last_name: str
    picture: str = ""


def verify_id_token(raw_token: str) -> GoogleProfile:
    """Verify the id_token and return a normalized profile.

    Raises GoogleAuthError with a stable message for the view to surface.
    The list of accepted `aud` values comes from GOOGLE_OAUTH_CLIENT_IDS
    (iOS + Android + Web client IDs), all of which are legitimate audiences
    for a single Google project.
    """
    if not raw_token:
        raise GoogleAuthError("missing_token")

    accepted_audiences = list(settings.GOOGLE_OAUTH_CLIENT_IDS or [])
    if not accepted_audiences:
        raise GoogleAuthError("server_misconfigured")

    try:
        # Passing audience=None disables the built-in aud check; we do it ourselves
        # against the multi-value list.
        claims = google_id_token.verify_oauth2_token(
            raw_token, google_requests.Request(), audience=None
        )
    except ValueError as exc:
        raise GoogleAuthError(f"invalid_token: {exc}") from exc

    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise GoogleAuthError("invalid_issuer")
    if claims.get("aud") not in accepted_audiences:
        raise GoogleAuthError("invalid_audience")
    if not claims.get("email"):
        raise GoogleAuthError("missing_email")
    if not claims.get("email_verified", False):
        raise GoogleAuthError("email_not_verified")

    return GoogleProfile(
        sub=str(claims["sub"]),
        email=str(claims["email"]).lower(),
        first_name=str(claims.get("given_name", "")),
        last_name=str(claims.get("family_name", "")),
        picture=str(claims.get("picture", "")),
    )
