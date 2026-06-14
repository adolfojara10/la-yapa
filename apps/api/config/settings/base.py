"""
Base Django settings for La Yapa API.

Environment-specific settings (dev, test, prod) inherit from this file.
"""

from datetime import timedelta
from pathlib import Path

import environ

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APPS_DIR = BASE_DIR / "apps"

# ---------- Environment ----------
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

# ---------- Core ----------
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ---------- Apps ----------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.gis",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "django_extensions",
    "drf_spectacular",
    "encrypted_model_fields",
    "anymail",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.apple",
]

LOCAL_APPS = [
    "apps.core",
    "apps.users",
    "apps.geo",
    "apps.businesses",
    "apps.bags",
    "apps.orders",
    "apps.payments",
    "apps.reviews",
    "apps.notifications",
    "apps.gamification",
    "apps.suspended_meals",
    "apps.impact",
    "apps.sales",
    "apps.ads",
    "apps.consumer",
    "apps.business",
    "apps.ops",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------- Middleware ----------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

SITE_ID = 1

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# ---------- Templates ----------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------- Database ----------
# Use PostGIS in dev/prod so GeoDjango (PointField, distance lookups) works.
# Tests override to sqlite via config.settings.test.
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgis://layapa:layapa@localhost:5433/layapa",
    ),
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"

# ---------- Cache / Redis ----------
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

# ---------- Celery ----------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_TIMEZONE = "America/Guayaquil"
CELERY_TASK_TRACK_STARTED = True
# Auto-discover tasks under apps.*.tasks (also covered by autodiscover_tasks()).
CELERY_IMPORTS = (
    "apps.orders.tasks",
    "apps.payments.tasks",
)

# ---------- Auth ----------
AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# Allauth — we don't use the HTML pages; allauth provides the SocialAccount
# model + email-uniqueness machinery. JWTs are issued by simplejwt, not allauth.
ACCOUNT_EMAIL_VERIFICATION = "none"  # we handle verification with our own OTP flow
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_UNIQUE_EMAIL = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_QUERY_EMAIL = True

# Social provider credentials (server-side id_token verification, not OAuth web flow)
# CSV of all client IDs (iOS + Android + Web) that are valid `aud` values for Google id_tokens.
GOOGLE_OAUTH_CLIENT_IDS = env.list("GOOGLE_OAUTH_CLIENT_IDS", default=[])
APPLE_BUNDLE_ID = env("APPLE_BUNDLE_ID", default="ec.layapa.app")
APPLE_TEAM_ID = env("APPLE_TEAM_ID", default="")

# Auth flow timing
EMAIL_VERIFICATION_OTP_TTL_MINUTES = env.int("EMAIL_VERIFICATION_OTP_TTL_MINUTES", default=15)
PASSWORD_RESET_TOKEN_TTL_MINUTES = env.int("PASSWORD_RESET_TOKEN_TTL_MINUTES", default=30)
EMAIL_VERIFICATION_MAX_ATTEMPTS = 5

# Frontend URL used to build password-reset links (web + mobile deep-link).
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
MOBILE_DEEP_LINK_SCHEME = env("MOBILE_DEEP_LINK_SCHEME", default="layapa")

# ---------- Payments ----------
# Switch to True for tests + local dev without real provider credentials.
# When True, `apps.payments.providers.get_provider` returns a FakePaymentProvider
# regardless of `provider_name`, so HTTP never leaves the process.
USE_FAKE_PAYMENT_PROVIDER = env.bool("USE_FAKE_PAYMENT_PROVIDER", default=False)

PAYPHONE_API_KEY = env("PAYPHONE_API_KEY", default="")
PAYPHONE_SECRET = env("PAYPHONE_SECRET", default="")
PAYPHONE_WEBHOOK_SECRET = env("PAYPHONE_WEBHOOK_SECRET", default="")
PAYPHONE_BASE_URL = env("PAYPHONE_BASE_URL", default="https://pay.payphonetodoesposible.com")
FAKE_PAYMENT_BASE_URL = env("FAKE_PAYMENT_BASE_URL", default="http://10.0.2.2:8000")

DEUNA_PUBLIC_KEY = env("DEUNA_PUBLIC_KEY", default="")
DEUNA_SECRET_KEY = env("DEUNA_SECRET_KEY", default="")
DEUNA_WEBHOOK_SECRET = env("DEUNA_WEBHOOK_SECRET", default="")
DEUNA_BASE_URL = env("DEUNA_BASE_URL", default="https://api.deuna.com/v1")

# Webhook hardening
PAYMENT_WEBHOOK_REPLAY_WINDOW_SECONDS = env.int(
    "PAYMENT_WEBHOOK_REPLAY_WINDOW_SECONDS", default=600
)
# Per-provider CIDR allowlist. Empty list = allow any (dev / staging).
# Populate from CSV env var:  PAYMENT_WEBHOOK_IPS_PAYPHONE=1.2.3.0/24,5.6.7.0/24
PAYMENT_WEBHOOK_IP_ALLOWLIST = {
    "payphone": env.list("PAYMENT_WEBHOOK_IPS_PAYPHONE", default=[]),
    "de_una": env.list("PAYMENT_WEBHOOK_IPS_DE_UNA", default=[]),
}

# Bonus credit defaults
BUSINESS_CANCELLATION_BONUS_AMOUNT = env("BUSINESS_CANCELLATION_BONUS_AMOUNT", default="1.00")
BUSINESS_CANCELLATION_BONUS_TTL_DAYS = env.int("BUSINESS_CANCELLATION_BONUS_TTL_DAYS", default=90)

# ---------- DRF ----------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "La Yapa API",
    "DESCRIPTION": "Comida rescatada, planeta cuidado.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ---------- CORS ----------
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000", "http://localhost:8081"],
)
CORS_ALLOW_CREDENTIALS = True

# ---------- Geo provider ----------
GEO_PROVIDER_SEARCH_URL = env("GEO_PROVIDER_SEARCH_URL", default="https://photon.komoot.io/api/")
GEO_PROVIDER_REVERSE_URL = env(
    "GEO_PROVIDER_REVERSE_URL", default="https://photon.komoot.io/reverse"
)
GEO_PROVIDER_USER_AGENT = env(
    "GEO_PROVIDER_USER_AGENT",
    default="LaYapaGeoProxy/0.1 (+https://layapa.ec; contact: hola@layapa.ec)",
)
GEO_REQUEST_TIMEOUT_SECONDS = env.int("GEO_REQUEST_TIMEOUT_SECONDS", default=10)
GEO_SEARCH_CACHE_TTL_SECONDS = env.int("GEO_SEARCH_CACHE_TTL_SECONDS", default=600)
GEO_REVERSE_CACHE_TTL_SECONDS = env.int("GEO_REVERSE_CACHE_TTL_SECONDS", default=3600)

# ---------- i18n ----------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Guayaquil"
USE_I18N = True
USE_TZ = True
LANGUAGES = [
    ("es", "Español"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

# ---------- Static / media ----------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

CLOUDFLARE_R2_ACCESS_KEY = env("CLOUDFLARE_R2_ACCESS_KEY", default="")
CLOUDFLARE_R2_SECRET_KEY = env("CLOUDFLARE_R2_SECRET_KEY", default="")
CLOUDFLARE_R2_BUCKET = env("CLOUDFLARE_R2_BUCKET", default="")
CLOUDFLARE_R2_ENDPOINT = env("CLOUDFLARE_R2_ENDPOINT", default="")
CLOUDFLARE_R2_REGION = env("CLOUDFLARE_R2_REGION", default="auto")
CLOUDFLARE_R2_PUBLIC_BASE_URL = env("CLOUDFLARE_R2_PUBLIC_BASE_URL", default="")

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if all(
    [
        CLOUDFLARE_R2_ACCESS_KEY,
        CLOUDFLARE_R2_SECRET_KEY,
        CLOUDFLARE_R2_BUCKET,
        CLOUDFLARE_R2_ENDPOINT,
    ]
):
    AWS_ACCESS_KEY_ID = CLOUDFLARE_R2_ACCESS_KEY
    AWS_SECRET_ACCESS_KEY = CLOUDFLARE_R2_SECRET_KEY
    AWS_STORAGE_BUCKET_NAME = CLOUDFLARE_R2_BUCKET
    AWS_S3_REGION_NAME = CLOUDFLARE_R2_REGION
    AWS_S3_ENDPOINT_URL = CLOUDFLARE_R2_ENDPOINT
    AWS_QUERYSTRING_AUTH = False
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    if CLOUDFLARE_R2_PUBLIC_BASE_URL:
        AWS_S3_CUSTOM_DOMAIN = CLOUDFLARE_R2_PUBLIC_BASE_URL.removeprefix("https://").removeprefix(
            "http://"
        )

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "access_key": AWS_ACCESS_KEY_ID,
            "secret_key": AWS_SECRET_ACCESS_KEY,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "region_name": AWS_S3_REGION_NAME,
            "default_acl": AWS_DEFAULT_ACL,
            "querystring_auth": AWS_QUERYSTRING_AUTH,
            "file_overwrite": AWS_S3_FILE_OVERWRITE,
            "signature_version": AWS_S3_SIGNATURE_VERSION,
            **({"custom_domain": AWS_S3_CUSTOM_DOMAIN} if CLOUDFLARE_R2_PUBLIC_BASE_URL else {}),
        },
    }

# ---------- Default PK ----------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------- Encryption (Fernet symmetric key for encrypted_model_fields) ----------
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Use a real value via env in prod.
# NOTE: This dev-only key is committed because dev DB content is throwaway.
# Generate a real one for prod with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FIELD_ENCRYPTION_KEY = env(
    "FIELD_ENCRYPTION_KEY",
    default="r9ekbzWb0qFttGmJQN05W_u3cedAnRWvKSMmf3DeFCo=",
)

# ---------- Email ----------
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="hola@layapa.ec")
