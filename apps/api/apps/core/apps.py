from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self) -> None:
        # Wire impact signal handlers when the app registry is ready.
        from apps.impact import signals  # noqa: F401  (import for side effects)
