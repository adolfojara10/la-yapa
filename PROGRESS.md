# 📈 La Yapa — Progress Log

Running record of what's built, what's pending, and key decisions that shape
future work. Update at the end of every session.

> Brand & product context: see [`MASTER_VISION.md`](./MASTER_VISION.md).
> AI-agent operating guide: see [`AGENTS.md`](./AGENTS.md).

---

## 🔭 Current state (at a glance)

| Layer                                 | Status               | Notes                                                                                                                                 |
| ------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Monorepo (pnpm + Turborepo)           | ✅ Working           | `pnpm install` clean, lockfile committed                                                                                              |
| CI (GitHub Actions)                   | ✅ Green             | JS job + Django job (PostGIS + Redis service containers)                                                                              |
| Pre-commit hooks                      | ✅ Working           | Husky → Prettier on JS/MD; Python via separate `pre-commit`                                                                           |
| Design system (`@layapa/ui`)          | ✅ v1                | Tokens single-source, light/dark, type scale, motion                                                                                  |
| Mobile (Expo SDK 54)                  | ✅ Scaffold          | Theme + 11 components + `/design-system` + Yapi/Logo SVGs · Android dev client building on Linux (JDK 17 + ninja + Metro React-dedup) |
| Admin (Next.js 14)                    | ✅ Scaffold          | Tailwind + next-themes + 8 shadcn-style primitives + showcase page                                                                    |
| Django API (`apps/api`)               | ✅ Data layer        | 28 models · 23 migrations · 17 tests · 92% coverage · seed command                                                                    |
| DRF endpoints                         | ⏳ Health-check only | Domain endpoints next                                                                                                                 |
| Auth (JWT + social)                   | ⏳ Scaffolded        | `simplejwt` wired; allauth installed, not configured                                                                                  |
| Mobile features (auth, browse, order) | ⏳ Not started       |                                                                                                                                       |
| Admin features (approvals, payouts)   | ⏳ Not started       |                                                                                                                                       |
| Real Yapi artwork                     | ⏳ Placeholder SVGs  | Awaiting illustrator commission                                                                                                       |

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
  (Later upgraded to SDK 54 — see Session 4.)
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

### Session 4 — Mobile SDK 54 upgrade (Expo Go incompatibility)

**Built / changed**

- **Bumped mobile to Expo SDK 54** to test on a physical iPhone:
  - `expo` `~54.0.35` (was `~51.x`)
  - `react-native` `0.81.5` (was `0.74.x`)
  - `react` / `react-dom` `19.1.0` (was `18.x`)
  - `react-native-reanimated` `~4.1.7` (was `~3.x`) + new peer
    `react-native-worklets` `0.8.3`
  - `expo-router` `~6.0.24` (was `~3.x`)
  - All `expo-*`, `@react-navigation/*`, `react-native-screens`,
    `react-native-safe-area-context`, `react-native-gesture-handler`,
    `react-native-svg` aligned to SDK 54-compatible versions.
- **`apps/mobile/babel.config.js`**: removed manual `react-native-reanimated/plugin`.
  `babel-preset-expo` (54.0.11) auto-injects `react-native-worklets/plugin`
  when Reanimated 4 is detected; the legacy plugin conflicts with it and
  produces `Exception in HostFunction: <unknown>` at first import of any
  reanimated/gesture-handler module.

**Decisions**

- **Inner-loop platform = Android dev client on Linux.** The App Store
  Expo Go binary does not match this project's native module versions
  (Reanimated 4 / RN 0.81 / New Arch), so any worklet-touching import
  crashes immediately. iOS device testing is **deferred** until an
  Apple Developer account ($99/yr) + EAS Build are in place; no Linux-
  native path exists for iOS local builds.
- **Web preview** (`expo start` → `w`) kept available for pure layout
  sanity-checks only; native modules degrade or stub out there.

**Caveats**

- Need to install/configure **Android Studio + platform-tools + an AVD
  or USB-debug device** before the dev loop is usable. Not yet done.
- `app.json` does not explicitly set `newArchEnabled` — relying on SDK
  54's default (on). If we ever need to disable it, add it explicitly.
- First Android build via `expo run:android` will be slow (~5–15 min);
  subsequent JS reloads are instant.

---

### Session 5 — Android dev client unblocked (Linux)

**Built / changed**

- **JDK 17 + ninja installed** on the dev machine
  (`sudo apt install openjdk-17-jdk ninja-build`);
  `JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64` exported in `~/.bashrc`.
  RN 0.81 / AGP 8.x cannot build under JRE 8;
  `react-native-worklets` CMake config requires Ninja on PATH.
- **`expo run:android` first build succeeded** against a booted emulator
  (`emulator-5554`); APK installed.
- **`apps/mobile/metro.config.js`** — added `extraNodeModules` +
  `resolveRequest` redirects forcing `react` and `react-dom` imports to
  resolve to `<workspace-root>/node_modules/react` (and `react-dom`). Fixes
  the "Invalid hook call / Cannot read property 'useEffect' of null" at
  `_layout.tsx:61` (`QueryClientProvider`) caused by
  `@tanstack/react-query` resolving to a pnpm-nested `react@18.3.1` while
  the rest of the bundle uses root-hoisted `react@19.1.0`. Mobile-only —
  admin (Next 14) still resolves React 18 normally.
- **`AGENTS.md` §4** updated with JDK 17 prerequisite
  (`sudo apt install openjdk-17-jdk` + `JAVA_HOME` export).
- **`AGENTS.md` §5** documents the metro-config React redirect so future
  contributors don't revert it.
- **`checklist.md`** added at repo root — manual QA runbook keyed to
  roadmap sessions, with `🔒` markers for unbuilt features.

**Mobile dev-client smoke checklist** (validates the dedup fix end-to-end
on the device — run after a fresh `expo start -c`):

- [ ] App launches without red box (proves React dedup worked)
- [ ] Splash hides cleanly after Google Fonts load
- [ ] Status bar adapts to light/dark theme
- [ ] Fast Refresh works (edit a string in `app/index.tsx`, see it update)
- [ ] Logo + Mascot SVGs render (proves `react-native-svg-transformer` path)
- [ ] Navigation to `/design-system` works (expo-router)
- [ ] Theme toggle button switches all themed surfaces
- [ ] Buttons (all 7 variants + 3 sizes) press states animate (Reanimated 4 worklets)
- [ ] Inputs accept text, password eye-toggle works, search variant renders icon
- [ ] Skeleton shimmer animates (worklet path)
- [ ] Modal opens with backdrop, dismisses cleanly
- [ ] **BottomSheet opens, drags between snap points (40%/85%), closes** —
      highest-value test; proves `@gorhom/bottom-sheet` + Reanimated 4 +
      gesture-handler + new arch all wire together
- [ ] Toast slides in, auto-dismisses, queues

**Decisions**

- **JDK via apt over Temurin** — one command, no extra repo, auto-updates
  via `apt`.
- **`JAVA_HOME` per-shell in `~/.bashrc`** (not system-wide
  `update-alternatives`) — leaves system defaults alone for anything else
  that may depend on JRE 8.
- **Metro resolver redirect over pnpm `overrides`** — admin (Next 14)
  genuinely needs React 18 and mobile (RN 0.81) needs React 19. They must
  coexist in the workspace; per-app bundlers isolate. A workspace-wide
  override would break admin.
- **Don't clear `~/.gradle/caches`** unless a stale-plugin error surfaces.
  The cache survives the JDK switch cleanly in practice.

**Caveats**

- **Runtime fix is assumed-valid until the smoke checklist above passes.**
  Native build succeeded; the React-dedup redirect was applied after the
  APK was installed, so a fresh `expo start -c` is required to validate.
- **`cmdline-tools` is emitting "SDK XML v4" warnings** — benign for now
  (build completed past them), but a sign cmdline-tools is older than the
  installed SDK packages. Update cmdline-tools next time something fails
  around `sdkmanager`.
- **`AndroidManifest.xml` package-attribute warnings** from
  `@react-native-async-storage/async-storage` and
  `react-native-safe-area-context` — upstream lib issues, not ours; AGP
  ignores the value cleanly.
- **iOS still deferred** (no Mac, no paid Apple Developer account).

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

- [x] **Install Android Studio + SDK + AVD on dev machine** so
      `expo run:android` works; that's the inner loop for mobile until iOS
      is unblocked. _(Session 5: JDK 17 + ninja + emulator green; first build succeeds.)_
- [ ] **Provision Apple Developer account ($99/yr) + EAS Build profile**
      for iOS device testing once mobile features stabilize.
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
- [`checklist.md`](./checklist.md) — manual QA runbook (session-by-session,
  `🔒` markers for features not yet built).
