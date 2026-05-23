"""Seed demo data for local development.

Usage:
    python manage.py seed_demo_data           # default counts
    python manage.py seed_demo_data --reset   # wipe relevant tables first

Creates:
  - 5 approved businesses (one of each type, 1 location each)
  - 20 bags (4 per business) with realistic price discounts
  - 3 consumers (eco-conscious personas)
  - A handful of badges to display in the UI
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.bags.factories import BagFactory
from apps.bags.models import AllergenTag, Bag
from apps.businesses.factories import (
    BusinessFactory,
    BusinessLocationFactory,
    BusinessVerificationFactory,
)
from apps.businesses.models import Business, BusinessType
from apps.gamification.models import Badge, BadgeCategory, BadgeRarity
from apps.users.factories import ConsumerProfileFactory, UserFactory
from apps.users.models import DietaryTag, User


class Command(BaseCommand):
    help = "Seed demo data: 5 businesses, 20 bags, 3 consumers, badges."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Wipe existing demo data before seeding.",
        )

    def handle(self, *args, **opts):
        if opts["reset"]:
            self.stdout.write(self.style.WARNING("Wiping demo data..."))
            Bag.objects.all().delete()
            Business.objects.all().delete()
            User.objects.filter(email__endswith="@layapa.test").delete()
            DietaryTag.objects.all().delete()
            AllergenTag.objects.all().delete()
            Badge.objects.all().delete()

        self._seed_tags()
        self._seed_badges()
        consumers = self._seed_consumers()
        businesses = self._seed_businesses()
        self._seed_bags(businesses)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Seeded: {len(businesses)} businesses, "
                f"{Bag.objects.count()} bags, {len(consumers)} consumers."
            )
        )

    # ----------------------------------------------------------------------

    def _seed_tags(self) -> None:
        self.stdout.write("Seeding dietary + allergen tags...")
        dietary = [
            ("vegetarian", "Vegetariano"),
            ("vegan", "Vegano"),
            ("gluten_free", "Sin gluten"),
            ("sin_lactosa", "Sin lactosa"),
            ("organico", "Orgánico"),
        ]
        for name, label in dietary:
            DietaryTag.objects.get_or_create(name=name, defaults={"label_es": label})

        allergens = [
            ("mani", "Maní"),
            ("gluten", "Gluten"),
            ("lacteos", "Lácteos"),
            ("frutos_secos", "Frutos secos"),
            ("mariscos", "Mariscos"),
        ]
        for name, label in allergens:
            AllergenTag.objects.get_or_create(name=name, defaults={"label_es": label})

    def _seed_badges(self) -> None:
        self.stdout.write("Seeding badges...")
        defs = [
            (
                "Primera Yapa",
                "Tu primera bolsa rescatada",
                BadgeCategory.SAVER,
                BadgeRarity.COMMON,
                {"meals_saved": 1},
            ),
            (
                "Eco-héroe x10",
                "10 bolsas rescatadas",
                BadgeCategory.SAVER,
                BadgeRarity.RARE,
                {"meals_saved": 10},
            ),
            (
                "Defensor del Páramo",
                "100 bolsas rescatadas",
                BadgeCategory.SAVER,
                BadgeRarity.EPIC,
                {"meals_saved": 100},
            ),
            (
                "Racha de 4 semanas",
                "Compra una bolsa cada semana por un mes",
                BadgeCategory.STREAK,
                BadgeRarity.RARE,
                {"streak_weeks": 4},
            ),
            (
                "Explorador de Cuenca",
                "5 negocios distintos",
                BadgeCategory.EXPLORER,
                BadgeRarity.COMMON,
                {"unique_businesses": 5},
            ),
        ]
        for name, desc, cat, rarity, criteria in defs:
            Badge.objects.get_or_create(
                name=name,
                defaults={
                    "description": desc,
                    "category": cat,
                    "rarity": rarity,
                    "criteria": criteria,
                },
            )

    def _seed_consumers(self) -> list[User]:
        self.stdout.write("Seeding consumers...")
        personas = [
            ("sofia@layapa.test", "Sofía", "Pérez"),
            ("camila@layapa.test", "Camila", "Vega"),
            ("matias@layapa.test", "Matías", "Ruiz"),
        ]
        users = []
        for email, first, last in personas:
            user = UserFactory(email=email, username=email.split("@")[0])
            ConsumerProfileFactory(user=user, first_name=first, last_name=last)
            users.append(user)
        return users

    def _seed_businesses(self) -> list[Business]:
        self.stdout.write("Seeding businesses...")
        names = [
            ("Panadería La Esperanza", BusinessType.BAKERY),
            ("Restaurante El Mirador", BusinessType.RESTAURANT),
            ("Supermercado Andino", BusinessType.SUPERMARKET),
            ("Hotel Cuenca Real", BusinessType.HOTEL),
            ("Mercado 10 de Agosto · Puesto 42", BusinessType.MERCADO),
        ]
        businesses = []
        for name, btype in names:
            biz = BusinessFactory(name=name, business_type=btype)
            BusinessLocationFactory(business=biz, name="Sucursal Principal")
            BusinessVerificationFactory(business=biz)
            businesses.append(biz)
        return businesses

    def _seed_bags(self, businesses: list[Business]) -> None:
        self.stdout.write("Seeding bags...")
        for biz in businesses:
            loc = biz.locations.first()
            for i in range(4):
                start = timezone.now() + timedelta(hours=2 + i)
                BagFactory(
                    business_location=loc,
                    title=f"Bolsa Sorpresa {biz.name} #{i + 1}",
                    original_price=Decimal("12.00"),
                    sale_price=Decimal("4.50"),
                    quantity_available=5,
                    pickup_window_start=start,
                    pickup_window_end=start + timedelta(hours=2),
                )
