# 🤖 AGENTS.md — Working in this repo as an AI agent

This file teaches AI coding agents (Claude Code, Cursor, OpenCode, Aider, etc.)
how to be productive in the La Yapa monorepo without breaking things.

**Read in this order:** this file → `PROGRESS.md` (current state) →
`MASTER_VISION.md` (product brief). Don't skip; the repo encodes opinions that
aren't obvious from the code alone.

---

## 1. Repo layout (memorize this)

```
la-yapa/
├── apps/
│   ├── api/        Django 5.1 + DRF + Postgres 16 + Redis
│   ├── admin/      Next.js 14 (App Router) + Tailwind + shadcn-style UI
│   └── mobile/     Expo SDK 51 + Expo Router + RN 0.74
├── packages/
│   ├── ui/             Design tokens (TS) — single source of truth
│   └── shared-types/   TS types mirroring DRF serializers (manually maintained for now)
├── docker-compose.yml  Postgres (postgis/postgis:16-3.4) + Redis 7 + MailHog
├── .github/workflows/ci.yml
└── pnpm-workspace.yaml + turbo.json
```

Run scripts via Turborepo:

```bash
pnpm dev              # all apps in parallel
pnpm lint             # all workspaces
pnpm test
pnpm type-check
pnpm format           # write
pnpm format:check     # CI uses this
```

Per-app filters: `pnpm --filter @layapa/mobile <script>` /
`pnpm --filter @layapa/api migrate` etc.

---

## 2. Tech stack (locked in — do not propose alternatives)

| Layer            | Choice                                                        |
| ---------------- | ------------------------------------------------------------- |
| Monorepo         | pnpm 9 workspaces + Turborepo 2                               |
| Mobile           | RN 0.81 + React 19 + Expo SDK 54 + Expo Router 6 (file-based) |
| Mobile animation | Reanimated 4 + `react-native-worklets` 0.8 (New Architecture) |
| Mobile state     | Zustand + TanStack Query                                      |
| Web admin        | Next.js 14 (App Router) + React 18 + Tailwind                 |
| Backend          | Django 5.1 + DRF 3.15 + Simple JWT (Python 3.12)              |
| Database         | PostgreSQL 16 + PostGIS 3.4                                   |
| Cache / queue    | Redis 7 + Celery 5                                            |
| File storage     | Cloudflare R2 (S3 API)                                        |
| Maps             | Mapbox                                                        |
| Payments         | PayPhone + DeUna (MVP); Kushki (Phase 2)                      |
| Push             | Expo Push Notifications                                       |
| Email            | Resend (prod); MailHog (dev)                                  |
| Auth (social)    | django-allauth (Google, Apple)                                |
| Hosting          | Railway (MVP), portable via Docker                            |
| Errors           | Sentry                                                        |
| Analytics        | PostHog                                                       |
| i18n             | i18next (mobile), django-modeltranslation (API)               |

If a task requires deviating from this stack, **ask first**.

> ⚠️ **Mobile cannot run in App Store Expo Go.** Reanimated 4 + RN 0.81 + New
> Architecture are newer than the native modules baked into the public Expo
> Go binary, so any worklet-touching import (gesture-handler, reanimated,
> bottom-sheet) crashes with `Exception in HostFunction: <unknown>`. See
> §4 "Mobile dev workflow" for the dev-client setup.

---

## 3. Non-negotiable conventions

### TypeScript

- **Strict mode everywhere.** Don't add `// @ts-ignore` or `any` without
  a comment explaining why.
- **Import path aliases**: `@/` → `src/` in each app. Use them.
- **No default exports** in shared packages.

### Python / Django

- **Black** (line length 100) + **Ruff** (rules in `apps/api/pyproject.toml`)
  - **mypy** (currently soft-failing).
- Every model inherits **`apps.core.models.TimestampedModel`**. UUID PKs
  via **`UUIDPrimaryKeyModel`** for anything whose ID travels in URLs.
- New domain models go in a **new app** under `apps/api/apps/`. Don't
  pile multiple aggregates into one app.
- **PointFields** → `apps.geo.fields.PointField` (the shim). Never
  import from `django.contrib.gis.db.models` directly in app code.
- **Encrypted fields** → `encrypted_model_fields.fields.EncryptedCharField`.
- **Don't add fields to the existing `User` model casually** — it's an
  `AbstractUser` swap; migrations cascade everywhere. Prefer
  `ConsumerProfile` / `BusinessOwnerProfile` / etc.
- **Migrations are committed.** Run `makemigrations` after model changes
  and commit the result.

### React / RN components

- **Mobile components consume `useTheme()`** — never hard-code colors,
  spacing, or radii. The token namespace is `theme.colors.*`,
  `theme.spacing.{0..16}`, `theme.radii.*`, `theme.type.*`.
- **Admin components use Tailwind semantic classes** (`bg-primary`,
  `text-foreground`, `border-border`) — never raw hex. Brand palette
  utilities (`bg-verde-paramo`) are for marketing surfaces only.
- **shadcn-style on admin** (Radix primitive + `cva` + `cn()` helper).
  **Bespoke on mobile** — no shadcn-for-RN libraries.

### Git

- **Conventional Commits**: `feat(api): …`, `fix(mobile): …`,
  `chore(ci): …`, `docs(ui): …`.
- **Commit only when tests pass locally** for the touched workspace.
- **Never commit `.env` files**; only `.env.example`.

---

## 4. Common workflows

### Adding a Django model

1. Pick or create an app under `apps/api/apps/<domain>/`.
2. Add the model, inherit `TimestampedModel` (+ `UUIDPrimaryKeyModel` if its
   ID is sensitive).
3. Add to `apps/<domain>/admin.py` — at minimum `@admin.register` with
   `list_display`, `search_fields`, `raw_id_fields` for FKs.
4. Add a factory in `apps/<domain>/factories.py` (`DjangoModelFactory`).
5. Add tests in `apps/<domain>/tests.py` (pytest, `@pytest.mark.django_db`).
6. Run `python manage.py makemigrations` and commit the generated file.
7. Run `pytest` — must stay green.

### Adding a DRF endpoint

1. Serializer in `apps/<domain>/serializers.py`.
2. ViewSet in `apps/<domain>/views.py`.
3. URL in `apps/<domain>/urls.py`, included from `config/urls.py` under
   `api/v1/`.
4. Test in `apps/<domain>/tests/test_<endpoint>.py` using `APIClient`.
5. Mirror the response shape in `packages/shared-types/src/<domain>.ts`.

### Mobile dev workflow (running the app)

**Do not use App Store Expo Go** — see warning in §2. The project's RN/Expo/Reanimated
versions are newer than the public Expo Go binary supports.

**Inner loop (recommended): Android dev client on Linux**

```bash
# One-time prerequisites:
#   - JDK 17 (Ubuntu: `sudo apt install openjdk-17-jdk`). RN 0.81 / AGP 8.x
#       require JDK 17 specifically — JRE 8 fails with "No Java compiler found"
#       and JDK 21+ is not yet supported by AGP. Export JAVA_HOME in ~/.bashrc:
#         export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
#         export PATH="$JAVA_HOME/bin:$PATH"
#   - Android Studio + Platform Tools (sdkmanager, adb)
#   - ANDROID_HOME exported, ~/Android/Sdk/platform-tools in PATH
#   - Either an emulator (AVD) booted OR a USB device with USB-debugging on
pnpm --filter @layapa/mobile exec expo run:android --device   # first build (~5–15 min)
pnpm --filter @layapa/mobile dev                              # subsequent runs
```

`expo run:android` produces a debug APK installed on the device. From then on,
JS reloads are instant — the dev client connects to Metro identically to Expo Go.
Re-run `expo run:android` only after editing native config (`app.json` plugins,
new native deps, version bumps).

**iOS testing (deferred):** requires a Mac for local builds OR a paid Apple
Developer account ($99/yr) + EAS Build for cloud builds. No Linux-native path
for iOS device testing exists. Plan: ship Android-first for the dev inner loop,
do iOS QA via EAS once Apple account is provisioned.

**Web preview (`expo start` then press `w`):** works for layout sanity-checking
only — native modules (gesture-handler, reanimated worklets, push, geolocation,
payments) either stub out or render incorrectly.

**Babel/Metro caveats:**

- `babel.config.js` declares **only `babel-preset-expo`** — the preset
  auto-injects `react-native-worklets/plugin` when Reanimated 4 is installed.
  Do **not** add `react-native-reanimated/plugin` (the legacy v3 plugin); it
  conflicts with the v4 worklets transform and produces
  `Exception in HostFunction: <unknown>` at first import.
- After editing `babel.config.js`, `metro.config.js`, or `app.json`, clear
  caches: `rm -rf apps/mobile/.expo apps/mobile/node_modules/.cache` and
  restart with `expo start -c`.

### Adding a mobile screen

1. New route file under `apps/mobile/app/…` (Expo Router convention).
2. Pull data with TanStack Query; mutate via Zustand stores only for
   local UI state.
3. Wrap in `useSafeAreaInsets()` for padding; never hard-code 44px.
4. Use components from `@/components/ui` only. If you need a new one,
   build it under `@/components/ui/` first.

### Adding an admin page

1. New route under `apps/admin/src/app/…`.
2. Server components for data fetching; `'use client'` only when needed.
3. Use components from `@/components/ui`.

---

## 5. Things that look wrong but are correct

These trip up agents repeatedly. **Don't "fix" them.**

| Pattern                                                                              | Why                                                                                                                                                                                                                                                                                           |
| ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/mobile/metro.config.js` uses CommonJS (`require`, `__dirname`)                 | Metro requires CJS for the resolver config. ESLint override handles it.                                                                                                                                                                                                                       |
| `apps/api/apps/users/models.py` has `REQUIRED_FIELDS = ["username"]` as a plain list | Django framework attribute, not a typo. Ruff's `RUF012` is globally suppressed in `pyproject.toml`.                                                                                                                                                                                           |
| `# noqa: BLE001` on `except Exception:` in `core/views.py` health check              | Health checks must always return — broad except is intentional.                                                                                                                                                                                                                               |
| `apps/admin/tailwind.config.ts` uses `var(--color-…)` not channel triplets           | Single-source tokens, no preprocessing. Opacity utilities (`bg-primary/50`) won't work — that's a documented trade-off in `packages/ui/README.md`.                                                                                                                                            |
| Bag `save()` calls `self.full_clean()`                                               | Enforces price validation at the model layer, not just the form/serializer. Keep it.                                                                                                                                                                                                          |
| `django.contrib.gis` removed from `INSTALLED_APPS` in `test.py`                      | Avoids GDAL system-lib requirement. The geo shim handles field types.                                                                                                                                                                                                                         |
| `apps/api/.husky/pre-commit` has no shebang or `husky.sh` source line                | Husky v9 deprecated the old format; new format is just the command.                                                                                                                                                                                                                           |
| `pnpm/action-setup@v4` has no `version:` input in CI                                 | It reads `packageManager` from `package.json` to avoid drift.                                                                                                                                                                                                                                 |
| `pnpm-lock.yaml` is 14k lines and committed                                          | Required by `pnpm install --frozen-lockfile` and `setup-node` cache.                                                                                                                                                                                                                          |
| `apps/mobile/metro.config.js` redirects `react` / `react-dom` to the workspace root  | pnpm hoists `react@19` (mobile/RN 0.81) at the root but nests `react@18` under deps with `^18 \|\| ^19` peer ranges (e.g. `@tanstack/react-query`). Without the redirect, Metro bundles two React copies → "Invalid hook call". Mobile-only; admin (Next 14) still uses `react@18` correctly. |

---

## 6. Things that ARE wrong and want fixing

Live TODO list — feel free to grab any of these:

- **mypy is soft-failed** (`|| true` in CI). Remove the `|| true` once
  `django-stubs` patterns are wired across apps.
- **No `makemigrations --check`** in CI. Add it so PRs that change models
  without committing migrations get caught.
- **Impact signal lacks idempotency.** Move completion logic into an
  `Order.complete()` service method.
- **`bank_account` uses one Fernet key**, no rotation strategy.
- **Yapi mascot + logo are obviously placeholder SVGs** — commission real
  art.
- **No real app icons / splash** for Expo.
- **No E2E tests** (Detox, Playwright).
- **No CodeQL / Dependabot.**

---

## 7. How to read this codebase quickly

1. **Start at `MASTER_VISION.md`** for product context. The §Database Schema
   section is the canonical spec for models.
2. **Then `PROGRESS.md`** for what's actually built vs. spec.
3. **Then the relevant app's `models.py` + `admin.py` + `tests.py`** as a
   triad — they document each other.
4. **For design questions**, `packages/ui/src/tokens.ts` is the source of
   truth; nothing else gets to define a color or spacing value.
5. **For QA / release verification**, `checklist.md` is the manual-testing
   runbook — session-by-session, with `🔒` markers for features not yet built.

---

## 8. Running tests + checks locally

```bash
# Full JS pipeline (matches CI)
pnpm format:check && pnpm lint && pnpm type-check && pnpm test

# Django (after activating venv)
cd apps/api
source .venv/bin/activate
ruff check . && black --check . && pytest

# Seed local data for manual testing
python manage.py migrate
python manage.py seed_demo_data
python manage.py createsuperuser
python manage.py runserver
```

If any of these fail locally, **don't push** — CI will fail the same way.

---

## 9. Communication norms when answering the user

This is a sole-developer + AI-agent shop. The user wants:

- **Direct answers, not validation.** If they're wrong, say so with evidence.
- **Caveats up front**, not buried at the end.
- **One-question-at-a-time** when you genuinely need a decision; group
  questions when they're related.
- **Concise rationale** for non-obvious choices (one sentence is enough).
- **File paths as `file:line` references** so they can click through.
- **No emojis in code/docs** unless explicitly asked.

When summarizing work, list **what changed** and **what to watch out for** —
not what you intended to do.

---

## 10. Out-of-scope without explicit approval

Don't do these without asking:

- Add a new dependency to any `package.json` or `requirements.txt`.
- Change the tech stack (§2).
- Edit migrations after they've been committed.
- Add or modify GitHub Actions workflows.
- Introduce a new framework, ORM, or testing tool.
- Restructure the monorepo layout.
- Implement features outside the current phase per `PROGRESS.md`.

If a task seems to require any of the above, **stop and ask** with a brief
rationale and 2-3 options.
