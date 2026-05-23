"""Test settings — uses SQLite so contributors don't need PostGIS/GDAL locally."""

from .base import *  # noqa: F401, F403
from .base import INSTALLED_APPS

DEBUG = False
SECRET_KEY = "test-insecure"

# Drop django.contrib.gis to avoid the GDAL system-lib requirement in tests.
# Geo fields are swapped to a JSON shim by USE_GEO_SHIM below.
INSTALLED_APPS = [a for a in INSTALLED_APPS if a != "django.contrib.gis"]

# SQLite for unit tests.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Tell apps.geo.fields to use the shim.
USE_GEO_SHIM = True

# Faster password hashing in tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Fernet key for encrypted fields in tests (real 32-byte URL-safe base64).
FIELD_ENCRYPTION_KEY = "PL0oRfe-KREXmIboWVRlJmCAavUSBi9JmwEAlRozoks="
