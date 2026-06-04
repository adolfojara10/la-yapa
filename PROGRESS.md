# 📈 La Yapa — Progress Log

Running record of what's built, what's pending, and key decisions that shape
future work. Update at the end of every session.

> Brand & product context: see [`MASTER_VISION.md`](./MASTER_VISION.md).
> AI-agent operating guide: see [`AGENTS.md`](./AGENTS.md).

---

## 🔭 Current state (at a glance)

| Layer                                 | Status                    | Notes                                                                                                                                 |
| ------------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Monorepo (pnpm + Turborepo)           | ✅ Working                | `pnpm install` clean, lockfile committed                                                                                              |
| CI (GitHub Actions)                   | ✅ Green                  | JS job + Django job (PostGIS + Redis service containers)                                                                              |
| Pre-commit hooks                      | ✅ Working                | Husky → Prettier on JS/MD; Python via separate `pre-commit`                                                                           |
| Design system (`@layapa/ui`)          | ✅ v1                     | Tokens single-source, light/dark, type scale, motion                                                                                  |
| Mobile (Expo SDK 54)                  | ✅ Scaffold               | Theme + 11 components + `/design-system` + Yapi/Logo SVGs · Android dev client building on Linux (JDK 17 + ninja + Metro React-dedup) |
| Admin (Next.js 14)                    | ✅ Scaffold               | Tailwind + next-themes + 8 shadcn-style primitives + showcase page                                                                    |
| Django API (`apps/api`)               | ✅ Auth + data + consumer | 30 models · 24 migrations · 102 tests · 91% coverage · enriched seed command                                                          |
| DRF endpoints                         | ✅ Auth + consumer browse | 11 auth endpoints + `/users/me` + 4 consumer endpoints (bags list/detail, reviews, favorites toggle)                                  |
| Auth (JWT + social)                   | ✅ End-to-end             | Email/password + OTP verification + Google + Apple + password reset + 15min access / 7d refresh w/ rotation + blacklist               |
| Mobile features (auth, browse, order) | ✅ Browse done            | List/map toggle, infinite scroll, 6-axis filters, Mapbox markers + bottom sheet, bag detail w/ sticky CTA stub; order next            |
| Admin features (approvals, payouts)   | ⏳ Not started            |                                                                                                                                       |
| Real Yapi artwork                     | ⏳ Placeholder SVGs       | Awaiting illustrator commission                                                                                                       |

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

### Session 6 — Auth system end-to-end

**Built**

- **Backend (`apps/api`):**
  - 11 new endpoints under `/api/v1/auth/` (`register`, `login`, `refresh`,
    `google`, `apple`, `verify-email`, `verify-email/resend`,
    `forgot-password`, `reset-password`, `logout`) + `/api/v1/users/me`
    (GET, PATCH).
  - 2 new models in `apps.users`: `EmailVerificationCode` (6-digit OTP,
    5-attempt lockout, 15-minute TTL) and `PasswordResetToken` (raw token
    emailed, SHA-256 hash persisted, 30-minute TTL). User model gained
    `is_email_verified` + `email_verified_at`. One new migration committed
    (`0002_user_email_verified_at_user_is_email_verified_and_more.py`).
  - Service layer in `apps/users/auth/services/`: `registration.py`
    (email + social find-or-create, `_attach_profile` only for consumers),
    `email_otp.py`, `password_reset.py`, `google.py`
    (verifies via `google.oauth2.id_token.verify_oauth2_token` against
    CSV-configured client IDs), `apple.py` (Apple JWKS fetch + RS256
    verify, 24h key cache, refresh-on-`kid`-miss).
  - 4 role-based DRF permissions (`ConsumerOnly`, `BusinessOwnerOnly`,
    `AdminOnly`, `SalesRepOnly`) + `IsEmailVerified` gate in
    `apps/users/auth/permissions.py` — downstream apps import from there.
  - Simple JWT pinned to **15-minute access / 7-day refresh** with
    rotation + blacklist; `token_blacklist` app + migrations applied.
  - Throttling via `django-ratelimit` on the public surface:
    register 20/h/ip, login 30/m/ip, social 30/m/ip, verify-email 10/h/ip,
    resend 1/min/email + 20/h/ip, forgot-password 3/h/email + 20/h/ip.
  - Email backend wired: MailHog in dev, `anymail.backends.resend.EmailBackend`
    in prod. 6 email templates (verification, reset, welcome × es/en × txt/html).
  - **69 tests passing at 94% coverage** (was 17 at 92%): registration (7),
    login + refresh (5), verify-email + resend (7), password reset (7),
    Google (5, fully mocked `verify_oauth2_token`), Apple (4, fully mocked
    JWKS + `jwt.decode`), logout + blacklist (3), `/users/me` GET + PATCH (7),
    permissions (6), models (3).
  - New deps: `google-auth==2.35.0`, `PyJWT[crypto]==2.9.0`,
    `requests==2.32.3`, `django-anymail[resend]==12.0`,
    `django-ratelimit==4.1.0`.

- **Mobile (`apps/mobile`):**
  - 7 new screens under `app/(auth)/`: `welcome`, `login`, `register`
    (with consumer/business_owner role toggle), `verify-email` (OTP input
    with paste support, 60s resend cooldown), `forgot-password`,
    `reset-password` (deep-link param), `onboarding` (4 steps:
    first_name → language → location permission → dietary tags).
  - Placeholder route groups `(consumer)` + `(business)` so the auth flow
    has somewhere to land. Real consumer/business UIs ship in Sessions 7+.
  - Routing guard in `app/_layout.tsx`: re-runs on every (status, user,
    segments) change. State machine: idle → welcome, authed+unverified →
    verify-email, consumer+!onboarding → onboarding, consumer → (consumer),
    business_owner → (business), admin/sales_rep → forced logout (mobile
    is consumer/business only).
  - `src/api/client.ts` Axios instance with bearer-token request
    interceptor and single-in-flight refresh on 401. Old refresh tokens
    invalidated server-side after rotation; new refresh persisted to
    SecureStore via the `onTokensRotated` callback.
  - `src/auth/secureStorage.ts` wraps `expo-secure-store` with
    `AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY`; web platform falls back to an
    in-memory `Map` (NEVER `AsyncStorage` — see AGENTS.md §5).
  - `src/auth/store.ts` Zustand store with `hydrate()`, `setAuthed()`,
    `refreshMe()`, `logout()`. Boot sequence: hydrate → load tokens →
    `/users/me` → set status='authed' or fall back to idle on stale tokens.
  - `useGoogleSignIn` (expo-auth-session id-token flow) and
    `useAppleSignIn` (expo-apple-authentication, iOS-only with `isAvailable`
    gate).
  - **15 Jest tests** in `apps/mobile/__tests__/`: secureStorage (4),
    auth store transitions (5), Axios interceptors with custom adapters (3),
    OtpInput component (3). Native modules mocked centrally in
    `jest.setup.js`.
  - New deps: `expo-secure-store ~15.0`, `expo-auth-session ~7.0`,
    `expo-apple-authentication ~8.0`, `expo-crypto ~15.0`, `axios ^1.17`,
    `expo-location` (for onboarding step 3), `@testing-library/react-native`
    - `@types/jest` (dev).

- **Shared types (`packages/shared-types`):** `user.ts` expanded with full
  `User` + `ConsumerProfile` + `LatLng` mirroring the new serializers;
  new `auth.ts` covers all 11 endpoint payloads/responses. `AuthTokens`
  moved out of `api.ts` to consolidate.

- **Docs:** `AGENTS.md` §4 gained a "Provisioning social auth credentials"
  section (Google/Apple/Resend setup); §5 documents the secure-store choice
  and the disabled `typedRoutes` setting.

**Decisions**

- **OTP code over magic link** for email verification. Better mobile UX
  (no universal-links infra needed), cleaner test surface, plays nice with
  MailHog in dev. The same code-vs-link tradeoff will likely recur for
  phone verification in Phase 2.
- **Custom `/auth/google` + `/auth/apple` endpoints**, not `dj-rest-auth`'s
  bundled social URLs. allauth provides only the `SocialAccount` model +
  email-uniqueness checks; we own the id_token verification and JWT
  issuance entirely. Trade: a bit more code, but the API surface is shaped
  by us, not by dj-rest-auth's defaults.
- **Refresh rotation ON + blacklist ON**. Old refreshes are dead after a
  refresh call; the mobile client coalesces concurrent 401s onto a single
  refresh promise so they don't invalidate each other.
- **`role` accepted in `POST /auth/register`** (consumer | business_owner).
  Admin + sales_rep rejected — those come through Django admin /
  management commands only.
- **Mandatory onboarding gate** for consumers (first_name + at least one
  dietary tag). Business owners skip the consumer onboarding; their
  onboarding wizard is Session 7.
- **`typedRoutes` disabled** — re-enable once the route tree stabilizes
  (Session 7+); regeneration friction outweighs the type-safety win for
  now.

**Caveats / known gaps**

- **Apple Sign In ships untested on device.** Server JWKS verification is
  unit-tested with mocked keys; mobile `expo-apple-authentication` code
  exists but no iOS hardware + Apple Developer account to run it against
  yet (still tracked in the cross-cutting debt list).
- **Refresh-token rotation invalidates the previous refresh.** A client
  that loses its in-memory state mid-rotation will be forced through
  re-login. The Axios interceptor handles the in-app case; cold-launch
  with a stale refresh just lands on welcome.
- **Resend not wired in prod yet.** Settings select the backend but the
  API key + verified domain need to be provisioned (instructions are in
  AGENTS.md §4).
- **Google client IDs empty in `.env.example`.** Mobile + API will reject
  Google sign-in attempts until the Cloud Console setup in AGENTS.md §4
  is done — that's intentional, not a regression.
- **No E2E (Detox / Playwright) coverage** — still listed in cross-cutting
  debt; deferred to its own session.
- **`pnpm test` at the repo root won't run API pytest** (script invokes
  `pytest` without venv activation). CI runs them correctly in its
  dedicated job; locally, `cd apps/api && source .venv/bin/activate && pytest`.

---

### Session 7 — Consumer bag browsing end-to-end

**Built**

- **Backend (`apps.consumer` — new app, no models, view-layer only):**
  - 4 endpoints under `/api/v1/consumer/`:
    `GET /bags` (filtered + cursor-paginated list),
    `GET /bags/{uuid}` (detail with image gallery, hours, latest 3 reviews,
    accessible even for inactive bags so deep-links work),
    `GET /bags/{uuid}/reviews` (paginated reviews on the bag's location),
    `POST /business-locations/{id}/favorite` (idempotent toggle).
  - Filter surface: `dietary` (AND semantics), `exclude_allergens` (union
    exclusion), `min_price`/`max_price`, `pickup_window` (today/tomorrow/
    this_week), `min_rating`, `q` (title + business name `icontains`),
    `sort` (distance/price/rating/ending_soon), `radius_km`, `lat`/`lng`.
    When `lat`/`lng` missing and no `ConsumerProfile.default_location`,
    sort=distance silently degrades to ending_soon — never returns 400.
  - `BagCursorPagination` (subclass of DRF `CursorPagination`) with
    per-request `ordering` set by the view: `(distance_m, id)` for geo,
    `(pickup_window_end, id)` for ending_soon, `(-rating, id)` for rating.
    Stable under bag activate/expire because `id` (UUID) breaks ties.
  - `geo.py` isolates GeoDjango imports inside functions so the test SQLite
    shim (which excludes `django.contrib.gis`) keeps loading cleanly.
    `annotate_distance` / `filter_within_radius` no-op under the shim;
    `resolve_caller_location` picks request params → profile default → None.
  - `images.thumb(url, width=N)` rewrites Cloudflare-hosted URLs to the
    `/cdn-cgi/image/width=N,quality=70,format=auto/` transform path; passes
    through Unsplash and unknown hosts unchanged. Pure function — 5 tests.
  - `BagListSerializer` (lean card) + `BagDetailSerializer` (extends list
    with description, gallery, hours, latest reviews). Both expose
    annotated `distance_m`, `is_favorited`, `rating_average`,
    `rating_count` from view-supplied annotations.
  - Authorization: `[IsAuthenticated, ConsumerOnly, IsEmailVerified]` —
    composes the role permissions added in Session 6. Business owners +
    unverified consumers get 403 (tested both).
  - Seed enriched: pickup windows spread across today/tomorrow/this week,
    dietary/allergen tags sprinkled, Unsplash food images, 10 reviews
    across business locations so `min_rating` filter has data.
  - **33 new tests + 4 PostGIS-only (skipped under SQLite shim, run in
    CI's PostGIS job).** Total backend tests now 102 at 91% coverage.

- **Mobile (`apps/mobile`):**
  - `(consumer)/` rebuilt as a Stack containing `(tabs)` (Browse, Favoritos,
    Perfil) + a top-level `bag/[id]` route. Logout button moved from the
    old `(consumer)/index` to the new Perfil tab.
  - Browse screen with sticky header (search input, filter button w/ active
    count badge, list/map toggle), `BagListView` (TanStack
    `useInfiniteQuery`, pull-to-refresh, empty state, footer spinner),
    `BagMapView` (`@rnmapbox/maps`, user location pin, count-badge markers,
    client-side cluster by `location_id`), `BagBottomSheet` (40%/85% snap,
    opens on marker tap).
  - `FiltersSheet` exposes all 6 filter axes + sort as chip rows bound to
    the Zustand filter store. "Limpiar" / "Aplicar" affordances. Filter
    changes invalidate the queryKey automatically.
  - `BagCard` with image (expo-image + blurhash placeholder), discount
    badge, heart toggle with optimistic update + server rollback on
    failure, price/strikethrough/distance/rating/pickup-window.
  - `bag/[id]` detail screen with horizontal image carousel, rating +
    distance + pickup countdown header, "Lo que puedes recibir" surprise-
    bag callout, dietary chips, allergen warnings (tinted red), quantity
    selector (only when `quantity_available > 1`), latest 3 reviews inline,
    sticky "Reservar por $X.XX" CTA that shows a "checkout next session"
    toast.
  - `useUserLocation` requests permission, falls back to
    `consumer_profile.default_location`, never blocks the screen on a
    denial (degraded mode shown in the list / map fallback centroid).
  - `useGeocode` debounces Mapbox Geocoding calls with `country=ec` bias;
    returns `[]` gracefully when the access token is empty.
  - **8 new Jest tests** (filter store transitions, query-param serializer,
    BagCard render). Mobile suite now 27 tests across 7 files.
  - New deps: `@rnmapbox/maps ~10.3`, `expo-image ~3.0`, `expo-location ~19.0`
    (auto-installed via `expo install`), `@react-navigation/bottom-tabs`.

- **Shared types:** `bag.ts` rewritten snake_case (mirrors DRF directly,
  no client-side renaming), new `consumer.ts` with `BagListParams`,
  `CursorPage<T>`, `FavoriteToggleResponse`, `PickupWindow`, `BagSort`.

- **Docs:** `AGENTS.md` §4 gained "Provisioning Mapbox" (public + download
  token setup); §5 documents the `@rnmapbox/maps` rebuild-on-install drill.

**Decisions**

- **AND semantics for `dietary`** filter (vegan ∧ gluten-free, not ∨).
  Safety-first: a vegan ∧ gluten-free user picking both chips wants results
  that satisfy both constraints; OR would surface bags that violate one
  of their dietary needs. Allergen exclusion stays union semantics for
  the same reason.
- **Custom `BagCursorPagination` over stock DRF `CursorPagination`**.
  We need different orderings per request (`distance_m` for geo,
  `pickup_window_end` for ending_soon, etc.). The view assigns
  `paginator.ordering` per-request from the actual queryset's `order_by`.
- **`apps.consumer` as a thin presentation app** rather than scattering
  view code into `apps.bags` + `apps.businesses` + `apps.reviews`. Mirrors
  what `apps.users.auth` does for the auth surface. Zero models in the new
  app, no new migrations.
- **PostGIS geo tests skipped under SQLite** — `@pytest.mark.skipif`
  marker keeps local pytest fast and contributors free of GDAL/SpatiaLite.
  CI runs the geo tests against the real PostGIS container.
- **Mapbox tokens left blank in `.env.example`**, documented in `AGENTS.md`
  §4. Same posture as Google OAuth client IDs.
- **Sticky reserve CTA stubbed** — wired visually, tap shows a toast.
  Real reservation flow ships in Session 8 (orders + payments).
- **Filter state in Zustand, not URL/router params.** Mobile users don't
  share URLs, and the list↔map toggle would otherwise re-mount with each
  switch. The store's reactive subscription invalidates the React Query
  queryKey automatically on any filter change.

**Caveats / known gaps**

- **Map tiles render as an empty grid** until both Mapbox tokens are
  provisioned. List view + all filters remain fully functional in that
  degraded state. This is expected Mapbox behavior, not a crash.
- **Min-rating filter uses a subquery** annotation over
  `business_location__reviews`. Fine at MVP scale; if profiling shows the
  rating subquery is hot at >10k bags, consider denormalizing
  `BusinessLocation.rating_average` + `.rating_count` columns updated on
  review save (Phase 2 candidate).
- **Favorites tab is a stub** — heart on cards persists server-side, but
  the dedicated "Favoritos" tab just shows a placeholder. Listing
  favorited businesses is Session 8.
- **Profile tab is a stub** — only the logout button moved here from the
  old `(consumer)/index`. Edit-profile, settings, notifications,
  referrals are Session 8+.
- **Custom Andean Mapbox style not built** — using Mapbox's stock "Light"
  style. Custom style commission deferred alongside Yapi mascot artwork.
- **Search bar uses Mapbox Geocoding directly from the device.** No
  backend proxy + rate-limit yet; defer until we have abuse signals.
- **CI workflow not updated.** `apps.consumer` tests run with the rest
  of the suite; no new CI step needed.

---

## 🎯 Next-up priorities

### Phase 1 — Consumer Core MVP (Weeks 3-6 of the master roadmap)

1. **Orders service layer + checkout** — `Order.create()`,
   `Order.complete()`, `Order.cancel()`, state-machine validation. Wires
   up the sticky CTA stubbed in Session 7. Payments integration (PayPhone,
   DeUna) lands alongside.
2. **Pickup flow** — QR/PIN screens on both consumer and business mobile;
   `POST /orders/{id}/confirm-pickup` viewset.
3. **Favorites list UI** — turn the placeholder Favoritos tab into a
   real list of favorited businesses with their active bags.
4. **Profile tab fleshed out** — edit profile, language toggle, dietary
   preferences edit (re-uses onboarding components), referral code share.
5. **Mapbox geocoding proxy** on the backend with caching, so the mobile
   geocoder isn't hitting Mapbox direct and we get one place to add
   per-user rate limiting.

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
JS / TS files:    ~135 (mobile + admin + packages)
Python files:    ~110 (apps + migrations + config)
Django models:    30 (no new models in Session 7 — apps.consumer is view-layer only)
Migrations:       24
Tests passing:   102 (Python, +4 PostGIS-skipped under SQLite shim), 27 (JS — mobile)
Coverage (API):   91%
CI duration:     ~3 min (JS job) + ~2 min (Django job)
Dependencies:    ~1565 npm packages, ~130 Python packages (with dev extras)
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
