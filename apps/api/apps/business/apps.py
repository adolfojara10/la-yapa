from django.apps import AppConfig


class BusinessConfig(AppConfig):
    """Presentation-layer app for the /api/v1/business/* REST surface.

    Mirrors apps.consumer: no models, composes serializers/views over the
    domain apps (orders, bags, businesses, suspended_meals).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.business"
    label = "business"
