"""Test settings."""

from .base import *  # noqa: F401, F403

DEBUG = False
SECRET_KEY = "test-insecure"

# Faster password hashing in tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
