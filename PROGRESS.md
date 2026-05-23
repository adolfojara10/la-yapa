# 📈 La Yapa — Progress Log

Running record of what's built, what's pending, and key decisions that shape
future work. Update at the end of every session.

> Brand & product context: see [`MASTER_VISION.md`](./MASTER_VISION.md).
> AI-agent operating guide: see [`AGENTS.md`](./AGENTS.md).

---

## 🔭 Current state (at a glance)

| Layer                                 | Status               | Notes                                                              |
| ------------------------------------- | -------------------- | ------------------------------------------------------------------ |
| Monorepo (pnpm + Turborepo)           | ✅ Working           | `pnpm install` clean, lockfile committed                           |
| CI (GitHub Actions)                   | ✅ Green             | JS job + Django job (PostGIS + Redis service containers)           |
| Pre-commit hooks                      | ✅ Working           | Husky → Prettier on JS/MD; Python via separate `pre-commit`        |
| Design system (`@layapa/ui`)          | ✅ v1                | Tokens single-source, light/dark, type scale, motion               |
| Mobile (Expo SDK 51)                  | ✅ Scaffold          | Theme + 11 components + `/design-system` showcase + Yapi/Logo SVGs |
| Admin (Next.js 14)                    | ✅ Scaffold          | Tailwind + next-themes + 8 shadcn-style primitives + showcase page |
| Django API (`apps/api`)               | ✅ Data layer        | 28 models · 23 migrations · 17 tests · 92% coverage · seed command |
| DRF endpoints                         | ⏳ Health-check only | Domain endpoints next                                              |
| Auth (JWT + social)                   | ⏳ Scaffolded        | `simplejwt` wired; allauth installed, not configured               |
| Mobile features (auth, browse, order) | ⏳ Not started       |                                                                    |
| Admin features (approvals, payouts)   | ⏳ Not started       |                                                                    |
| Real Yapi artwork                     | ⏳ Placeholder SVGs  | Awaiting illustrator commission                                    |

---

## 🗓️ Session log

### Session 1 — Monorepo + CI foundation

**Built**

- pnpm 9 + Turborepo 2 workspace; three apps (`api`, `mobile`, `admin`) +
  two packages (`shared-types`, `ui`).
- `apps/api`: Django 5.1 + DRF + split settings (`base`/`dev`/`test`/`prod`),
  custom `User` model, JWT auth scaffolding, `drf-spectacular` OpenAPI docs,
  health-check endpoint.
- `apps/mobile`: Expo SDK 51 + Expo Router + TanStack Query + Zustand.
- `apps/admin`: Next.js 14 (App Router) + Tailwind.
- `docker-compose.yml` with Postgres 16, Redis 7, MailHog.
- `.github/workflows/ci.yml` — two parallel jobs (JS + Django).
- Husky + lint-staged + `.pre-commit-config.yaml`; `.env.example` per app.

**Decisions**

- **Tokens-only `@layapa/ui` package** — no cross-platform components, since RN
  and DOM can't share render code. Tokens travel; components stay home.
- **pnpm version declared once** in `package.json#packageManager`; CI reads it.
- **PostgreSQL 16** chosen over 15 for `MERGE` + better JSON path ops.

**Caveats carried forward**

- `pnpm install` couldn't run until Session 2 (no pnpm locally).
- No real assets (icons, splash, mascot art).

---

### Session 2 — Design system

**Built**

- `packages/ui/src/tokens.ts` — single source of truth: palette, light + dark
  semantic schemes, type scale (h1/h2/h3/body/small/caption), spacing,
  radii, shadows (CSS + RN shapes), motion, z-index. Includes
  `buildTheme(mode)` and `generateCssVariables()`.
- **Admin**: Tailwind config consumes tokens, Google Fonts via `next/font`,
  `next-themes` with `.dark` class toggle, 8 Radix-backed primitives
  (Button, Input, Card, Badge, Avatar, Dialog, Toast, Skeleton).
- **Mobile**: `ThemeProvider` + `useTheme()` with `system|light|dark`,
  Google Fonts via `@expo-google-fonts/*`, 11 components (Text, Button,
  Input, Card, Badge, Avatar, Modal, BottomSheet, Toast, Skeleton, Icon).
- **In-app showcase routes** (`/design-system`) on both admin and mobile.
- **Brand assets**: placeholder Yapi mascot SVGs (8 states) + logo SVGs
  (4 variants) via `react-native-svg-transformer`.

**Decisions**

- **Skipped Storybook** in favor of in-app `/design-system` routes —
  same coverage, no parallel entry point or extra deps.
- **Semantic colors as `var(--color-…)` (not channel triplets)** — single
  source of truth, but Tailwind opacity modifiers (`bg-primary/50`) won't
  work until we migrate to triplet form.
- **shadcn pattern on web only**; mobile components are bespoke.

**Caveats**

- Yapi + logo are obvious placeholders (geometric shapes); commission real
  illustrator artwork before launch.

---

### Session 3 — Database layer

**Built**

- **14 Django apps**, **28 models** matching the schema in
  `MASTER_VISION.md` §"Database Schema":
  `users · businesses · bags · orders · payments · reviews · notifications ·
gamification · suspended_meals · impact · sales · ads · geo · core`.
- **23 migrations** generated and applied.
- **Reusable mixins** (`apps.core.models`): `TimestampedModel`,
  `UUIDPrimaryKeyModel`.
- **Geo shim** (`apps.geo.fields.PointField`): real PostGIS `PointField`
  in dev/prod; JSON `{lat, lng}` in tests. Same model code, no SpatiaLite.
- **Bag price validation** in `clean()`:
  `sale_price ≤ 0.5 × original_price` AND `sale_price ≥ 1.50`,
  plus DB-level `CheckConstraint`s as safety net.
- **UUID PKs** on `Order`, `Bag`, `SuspendedMealDonation`, `Dispute`
  (security: pickup codes & dispute IDs travel in URLs/QR).
- **Auto-generated** `pickup_code` (4-digit, `secrets.randbelow`) and
  `pickup_qr_token` (uuid4) on Order creation.
- **`bank_account` encrypted at rest** via `django-encrypted-model-fields`
  (Fernet/AES); key from `settings.FIELD_ENCRYPTION_KEY`.
- **Custom managers**: `Business.objects.approved()`,
  `Bag.objects.active()` (active + in-stock + within pickup window).
- **`ImpactStat` signal** updates per-user stats atomically with `F()`
  when an Order flips to `COMPLETED`.
- **Django admin** registrations for all 28 models (basic — Jazzmin/Unfold
  later).
- **Factory Boy factories** for the hot-path models
  (User, Business, BusinessLocation, Bag, Order, plus tags).
- **17 model tests** at 92% coverage (creation, validation, signals,
  encrypted round-trip, custom manager filtering).
- **`seed_demo_data` management command** — seeds 5 businesses, 20 bags,
  3 consumer personas, 5 badges, plus dietary/allergen tags.

**Decisions**

- **`django.contrib.gis` excluded from test settings** because loading it
  forces GDAL system libs (heavy install). Tests use the JSON shim;
  CI's PostGIS-backed integration job covers geo queries.
- **`django-encrypted-model-fields`** chosen over the unmaintained
  `django-fernet-fields`.
- **Phase-3 stubs (`SalesRepProfile`, `AdCampaign`)** committed for
  migration discipline but no factories/tests yet.
- **`makemigrations` is the dev's responsibility** — CI doesn't yet enforce
  with `--check`; should be added next pass.

**Caveats**

- Custom `User` regenerated from scratch — destructive but DB never deployed.
- Impact signal is fire-and-forget without idempotency; trusted to be
  called exactly once per Order completion (real fix lives in service layer).
- `bank_account` uses a single Fernet key (rotation = re-saving every row).

---

## 🎯 Next-up priorities

### Phase 1 — Consumer Core MVP (Weeks 3-6 of the master roadmap)

1. **Orders service layer** — `Order.complete()`, `Order.cancel()`,
   refund flow, state-machine validation. Replaces today's "save with
   status=COMPLETED" pattern and gives the impact signal a stable invocation
   point.
2. **DRF viewsets + serializers**:
   - `POST /api/v1/auth/register/`, `POST /auth/login/` (Simple JWT)
   - `GET /api/v1/bags/nearby/?lat&lng&radius_km` (PostGIS `dwithin`)
   - `GET/POST /api/v1/orders/`, `POST /orders/{id}/cancel/`, `POST /orders/{id}/checkout/`
   - `GET /api/v1/businesses/{id}/`
   - `POST /api/v1/businesses/{id}/favorite/`
3. **Mapbox geocoding** in `BusinessLocation.save()` hook.
4. **Social auth** — `django-allauth` + `dj-rest-auth` for Google + Apple.
5. **Mobile auth flow** — login/register screens + secure token storage
   (Expo SecureStore).
6. **Mobile bag discovery** — map screen, list screen, bag detail, reservation,
   pickup code screen.

### Phase 2 — Business core (Weeks 7-9)

7. **Business onboarding flow** (mobile) — RUC/cédula upload, verification
   wizard, food safety acceptance.
8. **Bag creation flow** (mobile) — pickup window picker, dietary/allergen
   tag selector, image upload via Cloudflare R2.
9. **Business dashboard** (mobile) — today's bags, today's orders, scan QR
   to mark picked-up.

### Phase 3 — Admin (Weeks 10-11)

10. **Admin approval workflow** (Next.js) — business pending queue,
    approve/reject with reason, soft suspension.
11. **Payout management** — period close, CSV export.

### Cross-cutting / infra debt

- [ ] Add `python manage.py makemigrations --check --dry-run` to CI.
- [ ] Remove `mypy || true` once `django-stubs` patterns are established.
- [ ] Dockerize the API service so `pnpm dev` doesn't need a venv shell.
- [ ] Wire Sentry (mobile + admin + API) and PostHog (mobile + admin).
- [ ] Replace `bank_account` raw string with typed model + multi-key encryption.
- [ ] Commission real Yapi mascot + logo artwork.
- [ ] Real app icons + splash for both Expo platforms.
- [ ] i18n string extraction (mobile + API).
- [ ] Order completion service with idempotency guard (replaces signal
      trust assumption).

---

## 🔢 Stats snapshot

```
JS / TS files:    ~75 (mobile + admin + packages)
Python files:     ~80 (apps + migrations + config)
Django models:    28
Migrations:       23
Tests passing:    17 (Python), 0 (JS — none authored yet)
Coverage (API):   92%
CI duration:      ~3 min (JS job) + ~2 min (Django job)
Dependencies:     ~1500 npm packages, ~120 Python packages (with dev extras)
```

---

## 📚 Key references for future agents

- [`MASTER_VISION.md`](./MASTER_VISION.md) — product brief, brand, full
  schema spec, roadmap, endpoint categories.
- [`AGENTS.md`](./AGENTS.md) — how to work in this repo as an AI agent.
- [`README.md`](./README.md) — human onboarding & local setup.
- [`packages/ui/README.md`](./packages/ui/README.md) — design-system usage.
- `apps/api/config/settings/base.py` — canonical Django settings.
- `apps/api/apps/*/models.py` — domain models (source of truth for fields).
