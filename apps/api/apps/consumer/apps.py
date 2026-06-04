from django.apps import AppConfig


class ConsumerConfig(AppConfig):
    """Thin presentation-layer app for the consumer-facing REST surface.

    No models of its own — composes serializers/views over apps.bags,
    apps.businesses, apps.reviews. Mirrors apps.users.auth's structure.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.consumer"
    label = "consumer"
