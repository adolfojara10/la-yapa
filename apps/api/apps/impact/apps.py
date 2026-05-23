from django.apps import AppConfig


class ImpactConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.impact"
    verbose_name = "Impact"

    def ready(self) -> None:
        from . import signals  # noqa: F401
