"""Test settings — uses SQLite so contributors don't need PostGIS/GDAL locally."""

from .base import *  # noqa: F401, F403
from .base import INSTALLED_APPS

DEBUG = False
SECRET_KEY = "test-insecure"

# Drop django.contrib.gis to avoid the GDAL system-lib requirement in tests.
# Geo fields are swapped to a JSON shim by USE_GEO_SHIM below.
INSTALLED_APPS = [a for a in INSTALLED_APPS if a != "django.contrib.gis"]

# Deterministic Google/Apple client IDs for unit tests (services are mocked anyway).
GOOGLE_OAUTH_CLIENT_IDS = ["test-google-client-id.apps.googleusercontent.com"]
APPLE_BUNDLE_ID = "ec.layapa.app.test"

# Throttling off in tests so we don't have to wait between requests.
RATELIMIT_ENABLE = False

# Payment provider: always use the deterministic fake in tests.
USE_FAKE_PAYMENT_PROVIDER = True
PAYPHONE_WEBHOOK_SECRET = "test-payphone-webhook-secret"
DEUNA_WEBHOOK_SECRET = "test-deuna-webhook-secret"

# Celery: tasks run inline, no worker required.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

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
