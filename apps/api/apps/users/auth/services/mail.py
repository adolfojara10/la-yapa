"""Tiny templated-email helper.

We keep this in-house (rather than pulling a templated-mail lib) because we
only have three templates and want zero magic between the OTP service and
Django's mail API.

Template layout convention (under any `templates/emails/` dir):
    {base}.{lang}.txt          ← plain-text body
    {base}.{lang}.html         ← HTML body (optional but recommended)

The function picks `{lang}` first, falls back to `es`. Subject lines are
passed in directly (the OTP and reset flows already know which subject they
want and it doesn't change per environment).
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string


def _render(template_name: str, context: dict[str, Any]) -> str | None:
    try:
        return render_to_string(template_name, context)
    except TemplateDoesNotExist:
        return None


def send_templated_email(
    *,
    to: str,
    subject_es: str,
    subject_en: str,
    template_base: str,
    context: dict[str, Any],
    language: str = "es",
) -> None:
    """Render and send a templated email. Always returns None; raises only on
    SMTP/HTTP failure, so callers can let it bubble (Celery retries later)
    or catch defensively."""
    lang = language if language in {"es", "en"} else "es"
    subject = subject_es if lang == "es" else subject_en

    text_body = _render(f"{template_base}.{lang}.txt", context) or _render(
        f"{template_base}.es.txt", context
    )
    html_body = _render(f"{template_base}.{lang}.html", context) or _render(
        f"{template_base}.es.html", context
    )

    if text_body is None and html_body is None:
        raise RuntimeError(f"No template found for {template_base!r}")

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body or "",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to],
    )
    if html_body:
        message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)
