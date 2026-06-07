"""Django project entry. Importing Celery here ensures @shared_task is
registered when Django starts (so e.g. `python manage.py shell` can call
tasks)."""

from .celery import app as celery_app

__all__ = ("celery_app",)
