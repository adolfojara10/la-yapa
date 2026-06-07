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
            # Delete in FK order to avoid ProtectedError. Anything that
            # references Bag/Business/Order with on_delete=PROTECT must
            # be deleted first.
            from apps.businesses.models import Favorite
            from apps.orders.models import Dispute, Order
            from apps.payments.models import (
                BonusCredit,
                Invoice,
                PaymentTransaction,
                Payout,
                PayoutLineItem,
                WebhookEventLog,
            )
            from apps.reviews.models import Review
            from apps.suspended_meals.models import (
                SuspendedMealClaim,
                SuspendedMealDonation,
            )

            # Payment side first — they reference Order.
            PayoutLineItem.objects.all().delete()
            Payout.objects.all().delete()
            Invoice.objects.all().delete()
            BonusCredit.objects.all().delete()
            PaymentTransaction.objects.all().delete()
            WebhookEventLog.objects.all().delete()

            # Donations + claims reference Order/Bag/Location.
            SuspendedMealClaim.objects.all().delete()
            SuspendedMealDonation.objects.all().delete()

            # Reviews + disputes reference Order.
            Review.objects.all().delete()
            Dispute.objects.all().delete()

            # Now Order can be deleted (frees up Bag for delete).
            Order.objects.all().delete()
            Favorite.objects.all().delete()

            # Domain entities.
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
        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING("Test credentials (password for all: test-pass-123):")
        )
        self.stdout.write("  Business owner:   owner@layapa.test")
        self.stdout.write("  Consumer #1:      sofia@layapa.test")
        self.stdout.write("  Consumer #2:      camila@layapa.test")
        self.stdout.write("  Consumer #3:      matias@layapa.test")
        self.stdout.write("  PAID-order #1:    mateo@layapa.test  (active order ready for pickup)")
        self.stdout.write("  PAID-order #2:    nora@layapa.test   (active order ready for pickup)")
        self.stdout.write("  Donor:            donor@layapa.test  (made a suspended-meal donation)")
        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "Try the pickup flow: log in as owner@layapa.test and you'll see 2 PAID "
                "orders ready to confirm + 1 active suspended-meal donation."
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
        from apps.users.factories import BusinessOwnerFactory

        # The FIRST business gets a known, email-verified owner that can be
        # used for manual testing of the business app. Email: owner@layapa.test,
        # password: test-pass-123 (UserFactory default — see apps/users/factories.py).
        # The owner is referenced in `checklist.md` Session 9 manual smoke recipe.
        known_owner = BusinessOwnerFactory(
            email="owner@layapa.test",
            username="owner",
            is_email_verified=True,
        )

        names = [
            ("Panadería La Esperanza", BusinessType.BAKERY, known_owner),
            ("Restaurante El Mirador", BusinessType.RESTAURANT, None),
            ("Supermercado Andino", BusinessType.SUPERMARKET, None),
            ("Hotel Cuenca Real", BusinessType.HOTEL, None),
            ("Mercado 10 de Agosto · Puesto 42", BusinessType.MERCADO, None),
        ]
        businesses = []
        for name, btype, owner in names:
            kwargs = {"name": name, "business_type": btype}
            if owner is not None:
                kwargs["owner"] = owner
            biz = BusinessFactory(**kwargs)
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
        self._seed_business_app_data(businesses)

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

    def _seed_business_app_data(self, businesses: list[Business]) -> None:
        """Session 9 additions: a couple PAID orders ready for pickup +
        one ACTIVE suspended-meal donation, so the business dashboard +
        suspended tab have content when a vendor logs in."""
        from datetime import timedelta as _td
        from decimal import Decimal as _D

        from apps.bags.factories import BagFactory
        from apps.orders.models import OrderStatus
        from apps.orders.services import create_order
        from apps.suspended_meals.models import (
            DonationStatus,
            SuspendedMealDonation,
        )
        from apps.users.factories import (
            ConsumerProfileFactory,
            UserFactory,
        )

        self.stdout.write("Seeding business-app demo data (PAID orders + suspended meal)...")
        now = timezone.now()

        # Pick the first business as the "vendor under test" target. This
        # business is owned by owner@layapa.test (seeded above) so logging
        # in as that user shows these orders on the business dashboard.
        target_biz = businesses[0]
        target_loc = target_biz.locations.first()

        # Two consumer personas for the PAID orders.
        seeded_orders = []
        for i, (email, first) in enumerate(
            [("mateo@layapa.test", "Mateo"), ("nora@layapa.test", "Nora")]
        ):
            consumer = UserFactory(
                email=email, username=email.split("@")[0], is_email_verified=True
            )
            ConsumerProfileFactory(user=consumer, first_name=first)

            bag = BagFactory(
                business_location=target_loc,
                title=f"Demo PAID bag #{i + 1}",
                original_price=_D("12.00"),
                sale_price=_D("4.50"),
                quantity_available=3,
                pickup_window_start=now + _td(minutes=10),
                pickup_window_end=now + _td(hours=2),
            )
            order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
            order.status = OrderStatus.PAID
            order.save(update_fields=["status"])
            seeded_orders.append(order)

        # One ACTIVE suspended-meal donation (general pool — dispatchable
        # by any business owner).
        donor = UserFactory(email="donor@layapa.test", username="donor", is_email_verified=True)
        ConsumerProfileFactory(user=donor, first_name="Sofía")
        SuspendedMealDonation.objects.create(
            donor=donor,
            amount=_D("3.00"),
            bag=None,
            status=DonationStatus.ACTIVE,
            is_anonymous=True,
        )

        # Print pickup codes + QR tokens so the manual test recipe in
        # checklist.md can drive the confirm-pickup endpoint with curl
        # without going through Django admin to grab them.
        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING("Seeded PAID orders (Session 9 pickup test data):")
        )
        for order in seeded_orders:
            consumer_name = order.consumer.consumer_profile.first_name
            self.stdout.write(
                f"  {consumer_name:8} · PIN {order.pickup_code} · "
                f"QR {order.pickup_qr_token} · order_id {order.id}"
            )
