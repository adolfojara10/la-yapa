# 🌱 La Yapa

> **Comida rescatada, planeta cuidado.**
> Reducing food waste in Ecuador by connecting consumers with restaurants, bakeries,
> supermarkets, hotels, mercados, and farmers offering surplus food.

This is the La Yapa monorepo. It contains the consumer/business mobile app, the
admin web dashboard, the Django REST API, and shared TypeScript packages.

---

## 📦 Monorepo layout

```
la-yapa/
├── apps/
│   ├── api/            # Django 5 + DRF + PostgreSQL 16
│   ├── mobile/         # Expo SDK 51 (Expo Router) — consumer + business
│   └── admin/          # Next.js 14 (App Router) — internal + business panel
├── packages/
│   ├── shared-types/   # TS types shared by mobile + admin (mirror DRF schema)
│   └── ui/             # Design tokens: colors, typography, spacing, radii
├── docker-compose.yml  # Postgres 16 + Redis 7 + MailHog
└── turbo.json          # Pipeline definitions
```

---

## 🚀 Tech stack

| Layer         | Choice                                               |
| ------------- | ---------------------------------------------------- |
| Monorepo      | pnpm 9 workspaces + Turborepo 2                      |
| Mobile        | React Native 0.74 + Expo SDK 51 + Expo Router        |
| Web admin     | Next.js 14 (App Router) + Tailwind CSS               |
| State         | Zustand + TanStack Query                             |
| Backend       | Django 5.1 + DRF + Simple JWT                        |
| Database      | PostgreSQL 16                                        |
| Cache / queue | Redis 7 + Celery                                     |
| Email (dev)   | MailHog (`http://localhost:8025`)                    |
| Lint / format | Ruff + Black + mypy (Python); ESLint + Prettier (TS) |
| Tests         | pytest (API); Jest (mobile + admin)                  |
| CI            | GitHub Actions                                       |

---

## ✅ Prerequisites

Install these once on your machine:

| Tool     | Version | Install                                                           |
| -------- | ------- | ----------------------------------------------------------------- |
| Node.js  | ≥ 20    | `brew install node` or [nvm](https://github.com/nvm-sh/nvm)       |
| pnpm     | ≥ 9     | `npm install -g pnpm` or `brew install pnpm`                      |
| Python   | 3.12    | `brew install python@3.12`                                        |
| Docker   | latest  | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| Watchman | latest  | `brew install watchman` (recommended for Expo)                    |

Optional (only if you want native iOS/Android builds):

- Xcode 15+ (iOS)
- Android Studio + JDK 17 (Android)

---

## 🏁 First-time setup

```bash
# 1. Clone & enter
git clone <repo-url> la-yapa
cd la-yapa

# 2. Install JS dependencies (mobile, admin, packages)
pnpm install

# 3. Copy env files
cp apps/api/.env.example   apps/api/.env
cp apps/mobile/.env.example apps/mobile/.env
cp apps/admin/.env.example  apps/admin/.env

# 4. Start backing services (Postgres, Redis, MailHog)
docker compose up -d

# 5. Set up the Django API
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py createsuperuser   # optional
deactivate
cd ../..

# 6. Verify everything is wired up
pnpm dev
```

`pnpm dev` runs `apps/api`, `apps/mobile`, and `apps/admin` in parallel via Turborepo:

- API: http://localhost:8000 (admin at `/admin`, docs at `/api/docs/`)
- Admin: http://localhost:3000
- Mobile: Expo Dev Server (scan QR with Expo Go or press `i`/`a`)
- MailHog: http://localhost:8025

> ⚠️ `pnpm dev` will only start the API correctly if `apps/api/.venv` is activated
> in your shell, **or** if you uncomment the `api` service in `docker-compose.yml`
> and run the API in a container instead. Most contributors prefer:
>
> ```bash
> # Terminal 1
> docker compose up
> # Terminal 2
> source apps/api/.venv/bin/activate && pnpm dev
> ```

---

## 🧰 Common commands

From the repo root:

```bash
pnpm dev              # run all apps in parallel
pnpm build            # build all apps
pnpm lint             # lint everything (TS + Python via per-app scripts)
pnpm test             # run all test suites
pnpm type-check       # tsc/mypy across the workspace
pnpm format           # prettier write
pnpm format:check     # prettier check (CI uses this)
```

Per-app:

```bash
pnpm --filter @layapa/api  migrate
pnpm --filter @layapa/api  makemigrations
pnpm --filter @layapa/api  createsuperuser
pnpm --filter @layapa/mobile ios
pnpm --filter @layapa/mobile android
pnpm --filter @layapa/admin dev
```

---

## 🧪 Testing

```bash
# API
cd apps/api && source .venv/bin/activate && pytest

# Mobile
pnpm --filter @layapa/mobile test

# Admin
pnpm --filter @layapa/admin test
```

---

## 🪝 Git hooks

Husky + lint-staged are configured automatically on `pnpm install` (via the
`prepare` script). On commit:

- `*.{ts,tsx,js,jsx,json,md,yml,yaml,css}` → Prettier

Python formatting (Ruff + Black) is **not** wired into Husky on purpose —
it would break commits for frontend contributors who don't have a Python
environment set up. API contributors should install the Python-native
`pre-commit` framework instead (it manages its own isolated env):

```bash
cd apps/api && source .venv/bin/activate
pip install pre-commit
pre-commit install   # installs the hooks defined in .pre-commit-config.yaml
```

CI runs Ruff + Black on every PR regardless, so unformatted Python can never
land in `main`.

---

## 🌎 Environment variables

Each app reads its own `.env` file (gitignored). Templates live next to them
(`apps/*/​.env.example`). The most important ones:

| Var                         | Used by | Default (dev)                                    |
| --------------------------- | ------- | ------------------------------------------------ |
| `DATABASE_URL`              | api     | `postgres://layapa:layapa@localhost:5432/layapa` |
| `REDIS_URL`                 | api     | `redis://localhost:6379/0`                       |
| `EMAIL_HOST` / `EMAIL_PORT` | api     | `localhost` / `1025` (MailHog)                   |
| `EXPO_PUBLIC_API_BASE_URL`  | mobile  | `http://localhost:8000/api/v1`                   |
| `NEXT_PUBLIC_API_BASE_URL`  | admin   | `http://localhost:8000/api/v1`                   |

---

## 📚 Further reading

- [`MASTER_VISION.md`](./MASTER_VISION.md) — full product + design brief
- [`apps/api/README.md`](./apps/api) — API conventions (TBD)
- [`apps/mobile/README.md`](./apps/mobile) — mobile conventions (TBD)
- [`apps/admin/README.md`](./apps/admin) — admin conventions (TBD)

---

## 📄 License

Proprietary — © La Yapa, 2025. All rights reserved.
