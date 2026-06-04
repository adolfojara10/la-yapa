"""Cloudflare Image Resizing URL rewriter."""

from __future__ import annotations

from apps.consumer.images import thumb


def test_empty_url_returns_empty_string():
    assert thumb("") == ""
    assert thumb(None) == ""


def test_unknown_host_passes_through():
    url = "https://images.unsplash.com/photo-xyz?w=800"
    assert thumb(url, width=400) == url


def test_known_host_gets_cdn_cgi_prefix():
    out = thumb("https://cdn.layapa.ec/bags/abc.jpg", width=400)
    assert (
        out == "https://cdn.layapa.ec/cdn-cgi/image/width=400,quality=70,format=auto/bags/abc.jpg"
    )


def test_already_transformed_url_is_not_double_wrapped():
    already = "https://cdn.layapa.ec/cdn-cgi/image/width=200,quality=70,format=auto/x.jpg"
    assert thumb(already, width=400) == already


def test_query_string_preserved():
    out = thumb("https://cdn.layapa.ec/bags/abc.jpg?v=2", width=400)
    assert out.endswith("/bags/abc.jpg?v=2")
