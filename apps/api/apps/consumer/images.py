"""Cloudflare Image Resizing URL rewriter.

Production plan: images live on Cloudflare R2 behind a CF-fronted domain
(e.g. `https://cdn.layapa.ec/...`). Cloudflare's Image Resizing transform
lets us inject `/cdn-cgi/image/width=N,quality=Q,format=auto/` as a path
prefix to get on-the-fly thumbnails — no SDK, no extra service.

For URLs we don't recognize (Unsplash seeds, externally-hosted demo images),
we return them unchanged so the seed/dev experience keeps working.

This is a pure function on purpose: testable in isolation, no Django imports.
"""

from __future__ import annotations

from urllib.parse import urlparse

# Hosts whose URLs we control via Cloudflare Image Resizing.
# Add more as the storage layer rolls out.
_CF_RESIZE_HOSTS = frozenset(
    {
        "cdn.layapa.ec",
        "cdn.layapa.dev",
    }
)


def thumb(url: str | None, *, width: int = 600, quality: int = 70) -> str:
    """Return a CF-Image-Resizing variant of `url`, or `url` unchanged.

    >>> thumb("https://cdn.layapa.ec/bags/abc.jpg", width=400)
    'https://cdn.layapa.ec/cdn-cgi/image/width=400,quality=70,format=auto/bags/abc.jpg'
    >>> thumb("https://images.unsplash.com/photo-x?w=800")
    'https://images.unsplash.com/photo-x?w=800'
    >>> thumb("")
    ''
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url)
    except ValueError:
        return url
    if parsed.hostname not in _CF_RESIZE_HOSTS:
        return url
    # Guard against double-rewriting if a caller passed an already-transformed URL.
    if parsed.path.startswith("/cdn-cgi/image/"):
        return url
    transform = f"/cdn-cgi/image/width={width},quality={quality},format=auto"
    return f"{parsed.scheme}://{parsed.hostname}{transform}{parsed.path}" + (
        f"?{parsed.query}" if parsed.query else ""
    )
