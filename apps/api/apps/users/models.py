"""Custom user model — set up early to avoid painful migrations later."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """La Yapa user.

    Email is the canonical identifier; username is kept for Django admin compatibility
    but is auto-generated from the email.
    """

    class Role(models.TextChoices):
        CONSUMER = "consumer", "Consumer"
        BUSINESS = "business", "Business"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CONSUMER)
    phone = models.CharField(max_length=20, blank=True)
    locale = models.CharField(max_length=5, default="es")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email
