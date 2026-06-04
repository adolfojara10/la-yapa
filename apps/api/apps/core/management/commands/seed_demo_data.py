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
        # Unsplash food images (`?w=800` returns a reasonable thumb).
        images = [
            "https://images.unsplash.com/photo-1517433670267-08bbd4be890f?w=800",  # pan
            "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=800",  # almuerzo
            "https://images.unsplash.com/photo-1542838132-92c53300491e?w=800",  # frutas
            "https://images.unsplash.com/photo-1502741338009-cac2772e18bc?w=800",  # pastel
            "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800",  # bowl
            "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800",  # pizza
        ]
        dietary_pool = list(DietaryTag.objects.all())
        allergen_pool = list(AllergenTag.objects.all())

        # 6 pickup-window buckets so consumer filters (today/tomorrow/this_week)
        # have non-empty results in dev.
        window_offsets_hours = [2, 5, 24, 30, 48, 96]
        prices = [
            (Decimal("12.00"), Decimal("4.50")),
            (Decimal("10.00"), Decimal("3.00")),
            (Decimal("18.00"), Decimal("6.50")),
            (Decimal("8.00"), Decimal("2.50")),
        ]

        bag_index = 0
        for biz_index, biz in enumerate(businesses):
            loc = biz.locations.first()
            for i in range(4):
                start = timezone.now() + timedelta(
                    hours=window_offsets_hours[(bag_index) % len(window_offsets_hours)]
                )
                original, sale = prices[i % len(prices)]
                bag = BagFactory(
                    business_location=loc,
                    title=f"Bolsa Sorpresa {biz.name} #{i + 1}",
                    description=(
                        "Una selección rotatoria de productos del día — siempre frescos, "
                        "siempre con cariño."
                    ),
                    image_url=images[bag_index % len(images)],
                    original_price=original,
                    sale_price=sale,
                    quantity_available=5,
                    pickup_window_start=start,
                    pickup_window_end=start + timedelta(hours=2),
                )
                # Sprinkle dietary + allergen tags so filters return results.
                if dietary_pool:
                    bag.dietary_tags.add(dietary_pool[(biz_index + i) % len(dietary_pool)])
                if allergen_pool and (i % 2 == 0):
                    bag.allergen_warnings.add(allergen_pool[i % len(allergen_pool)])
                bag_index += 1

        self._seed_reviews(businesses)

    def _seed_reviews(self, businesses: list[Business]) -> None:
        """Add 2 reviews per business location so min_rating filter has data."""
        from apps.orders.factories import OrderFactory
        from apps.reviews.factories import ReviewFactory

        self.stdout.write("Seeding reviews...")
        ratings_cycle = [5, 4, 5, 3, 4, 5]
        idx = 0
        for biz in businesses:
            loc = biz.locations.first()
            for _ in range(2):
                # ReviewFactory creates an Order via SubFactory; we let it
                # build a fresh consumer + bag rather than reusing seed personas
                # (keeps the seed idempotent enough for re-runs).
                order = OrderFactory(business_location=loc)
                ReviewFactory(
                    order=order,
                    consumer=order.consumer,
                    business_location=loc,
                    rating=ratings_cycle[idx % len(ratings_cycle)],
                    comment="Excelente experiencia, repetiré!" if idx % 2 == 0 else "",
                )
                idx += 1
