"""Factory Boy factories for users + consumer profile."""

from __future__ import annotations

import factory
from factory.django import DjangoModelFactory
from faker import Faker

from .models import ConsumerProfile, DietaryTag, User

fake = Faker("es_ES")


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@layapa.test")
    username = factory.Sequence(lambda n: f"user{n}")
    role = User.Role.CONSUMER
    language = User.Language.SPANISH
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        self.set_password(extracted or "test-pass-123")
        self.save(update_fields=["password"])


class BusinessOwnerFactory(UserFactory):
    role = User.Role.BUSINESS_OWNER


class AdminUserFactory(UserFactory):
    role = User.Role.ADMIN
    is_staff = True
    is_superuser = True


class DietaryTagFactory(DjangoModelFactory):
    class Meta:
        model = DietaryTag
        django_get_or_create = ("name",)

    name = factory.Iterator(
        ["vegetarian", "vegan", "gluten_free", "sin_lactosa", "organico", "halal", "kosher"]
    )
    label_es = factory.LazyAttribute(lambda o: o.name.replace("_", " ").title())
    label_en = factory.LazyAttribute(lambda o: o.name.replace("_", " ").title())


class ConsumerProfileFactory(DjangoModelFactory):
    class Meta:
        model = ConsumerProfile

    user = factory.SubFactory(UserFactory)
    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
