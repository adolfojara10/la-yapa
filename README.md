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
| Mobile        | React Native 0.81 + Expo SDK 54 + Expo Router 6      |
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

The repo is supported on **macOS 13+** and **Ubuntu 22.04 / 24.04 LTS**.
Other Linux distros will likely work but aren't tested by CI.

You need the following versions installed before running `pnpm install`:

| Tool     | Version | Notes                                                  |
| -------- | ------- | ------------------------------------------------------ |
| Node.js  | ≥ 20    | LTS required (matches CI)                              |
| pnpm     | ≥ 9     | Managed by `corepack` — don't install via npm globally |
| Python   | 3.12    | Exact 3.12.x; Django + stubs are pinned                |
| Docker   | latest  | Engine + Compose v2 plugin                             |
| Watchman | latest  | Optional on Linux, recommended on macOS                |

For running the mobile app on a phone or emulator (see
[Mobile dev workflow](#-mobile-dev-workflow-android) below):

- **Android Studio + JDK 17** — required on Linux & Windows; recommended on
  macOS. The project does **not** run in App Store Expo Go (see warning
  below), so a dev client is the only path.
- **Xcode 15+** — required for iOS local builds; macOS only. iOS device
  testing without a Mac requires an Apple Developer account ($99/yr) +
  EAS Build and is currently **deferred**.

---

### 🍎 macOS (Homebrew)

```bash
# Install Homebrew first if needed: https://brew.sh

brew install node@20 pnpm python@3.12 watchman
brew install --cask docker          # Docker Desktop

corepack enable                     # pins pnpm to the repo's packageManager
```

Launch Docker Desktop once and let it finish starting before running
`docker compose up`. If you juggle Node versions across projects, install
[nvm](https://github.com/nvm-sh/nvm) instead of `node@20`.

---

### 🐧 Ubuntu 22.04 / 24.04 LTS

```bash
# --- System packages ---
sudo apt update
sudo apt install -y build-essential curl git ca-certificates gnupg \
                    libpq-dev pkg-config lsb-release

# --- Node.js 20 (NodeSource — apt's default is too old) ---
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# --- pnpm via corepack (ships with Node 20) ---
sudo corepack enable

# --- Python 3.12 ---
# Ubuntu 24.04: already in apt
sudo apt install -y python3.12 python3.12-venv python3.12-dev
# Ubuntu 22.04 only: enable deadsnakes first
#   sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt update
#   sudo apt install -y python3.12 python3.12-venv python3.12-dev

# --- Docker Engine + Compose plugin (official repo) ---
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
                    docker-buildx-plugin docker-compose-plugin

# Run docker without sudo (log out + back in, or run `newgrp docker`)
sudo usermod -aG docker $USER

# --- Raise inotify limits so Expo / Metro doesn't crash on file watches ---
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

Notes / gotchas on Linux:

- **Watchman** has no apt package and building from source is heavy. Skip it
  — Expo falls back to polling, which is fine for typical sessions. If you
  hit Metro file-watching issues, install it via
  [Homebrew on Linux](https://docs.brew.sh/Homebrew-on-Linux).
- **Docker group**: `usermod -aG docker $USER` only takes effect after a new
  login shell. Use `newgrp docker` to apply it in the current terminal.
- **`libpq-dev` + `pkg-config`** aren't strictly required (the `psycopg`
  wheel is binary) but prevent surprises if pip ever falls back to a source
  build.
- **Docker Desktop for Linux** also works if you prefer it over Engine — but
  Engine is lighter and what most contributors use.

---

### 🔎 Verify your install

```bash
node -v               # v20.x
pnpm -v               # 9.x
python3.12 --version  # Python 3.12.x
docker compose version
```

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
- Mobile: Expo Dev Server — **see [Mobile dev workflow](#-mobile-dev-workflow-android) below.**
  The App Store **Expo Go app does not work** with this project (SDK 54 +
  Reanimated 4 + New Architecture are newer than Go's bundled native modules).
  You need a one-time Android dev build; after that JS reloads are instant.
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

## 🏃 Quick Start / Daily Workflow

Once you've done the first-time setup, here is what you need to run every day to develop:

**Terminal 1: Start Databases & Services**

```bash
docker compose up
```

**Terminal 2: Start Django API + Web Admin + Mobile Metro Server**

```bash
source apps/api/.venv/bin/activate
pnpm dev
```

**Terminal 3: Launch Mobile App on Emulator**
Open Android Studio, start your emulator, then run:

```bash
pnpm --filter @layapa/mobile exec expo run:android --device
```

_(After the first time it compiles, you can just press `a` in Terminal 2 instead of running Terminal 3 again)._

---

## 📱 Mobile dev workflow (Android)

> **Why no Expo Go?** This project is on Expo SDK 54 + RN 0.81 + Reanimated 4
>
> - the New Architecture. The Expo Go app on the App Store / Play Store
>   bundles a fixed set of native modules at older versions, so the first
>   `import` of `react-native-gesture-handler` (or anything else that touches
>   Reanimated worklets) crashes with `Exception in HostFunction: <unknown>`.
>   The fix is a **development build** — your own debug APK / IPA with the
>   exact native versions this project pins. Same hot-reload UX as Expo Go;
>   you just build it once.
>
> **iOS device testing is currently deferred.** It requires either a Mac
> (`expo run:ios`) or an Apple Developer account ($99/yr) + EAS Build.
> Android is the inner-loop platform for now; iOS QA will happen via EAS
> once the Apple account is provisioned.

### 1. Install Android Studio + SDK + JDK

#### macOS

```bash
brew install --cask android-studio
brew install --cask temurin@17        # JDK 17
```

Open Android Studio once → **More Actions → SDK Manager** → install:

- **Android SDK Platform 34** (or latest stable)
- **Android SDK Build-Tools 34.x**
- **Android SDK Platform-Tools** (gives you `adb`)
- **Android Emulator** (only if you want an emulator)

#### Ubuntu 22.04 / 24.04 LTS

```bash
sudo apt install -y openjdk-17-jdk           # JDK 17
sudo snap install android-studio --classic   # easiest install path
```

If you don't want snap, download the tarball from
<https://developer.android.com/studio> and extract into `~/android-studio`,
then run `~/android-studio/bin/studio.sh` once to complete setup.

In Android Studio, same as macOS: **More Actions → SDK Manager** → install
Platform 34 + Build-Tools 34.x + Platform-Tools + (optionally) Emulator.

#### Environment variables (both OSes)

Add to `~/.zshrc` / `~/.bashrc`:

```bash
# macOS
export ANDROID_HOME="$HOME/Library/Android/sdk"
# Linux
export ANDROID_HOME="$HOME/Android/Sdk"

export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$ANDROID_HOME/cmdline-tools/latest/bin"
```

Reload the shell, then verify:

```bash
adb version          # Android Debug Bridge version 1.0.41+
emulator -list-avds  # empty until you create one
```

---

### 2. Pick one: emulator OR physical device

#### Option A — Emulator (fastest to set up, no hardware needed)

Create an AVD (Android Virtual Device) once:

1. Android Studio → **More Actions → Virtual Device Manager → Create device**.
2. Pick **Pixel 7** (or any phone profile).
3. System image: **API 34** (Android 14), `x86_64` on Intel/AMD, `arm64` on
   Apple Silicon — **`Google Play` variant** so push notifications work.
4. Finish → click ▶ to boot it. Leave it running.

CLI alternative (after the SDK is installed):

```bash
sdkmanager "system-images;android-34;google_apis_playstore;x86_64"
avdmanager create avd -n layapa -k "system-images;android-34;google_apis_playstore;x86_64" -d pixel_7
emulator -avd layapa &
```

Verify `adb` sees the emulator:

```bash
adb devices
# emulator-5554   device
```

#### Option B — Physical Android device

On the phone:

1. **Settings → About phone** → tap **Build number** 7 times to unlock
   Developer Options.
2. **Settings → System → Developer options** → enable **USB debugging**.
3. Plug into the dev machine with a data-capable USB cable (some "charge
   only" cables won't work).
4. The phone will prompt **"Allow USB debugging from this computer?"** →
   tap **Allow** (check the "always" box).

Verify:

```bash
adb devices
# R52NA0XXXX   device     ← physical device
```

If it shows `unauthorized`, you missed the on-phone prompt — unplug, replug,
and watch the phone screen.

Linux only: if `adb devices` shows nothing, you likely need a udev rule.
The easiest fix is `sudo apt install -y android-sdk-platform-tools-common`
(installs `/lib/udev/rules.d/51-android.rules`); then `sudo udevadm control
--reload-rules && sudo udevadm trigger`, and replug the phone.

---

### 3. First build (creates the dev client)

```bash
# from the repo root, with Metro NOT running
pnpm --filter @layapa/mobile exec expo run:android --device
```

What this does:

- Generates the native `android/` project (gitignored — regenerated on demand).
- Compiles a debug APK with this project's exact native deps (Reanimated 4,
  gesture-handler 2.28, etc.).
- Installs the APK on the connected emulator/device.
- Starts Metro and connects the dev client to it.

**First build takes 5–15 minutes** (Gradle downloads, NDK compiles). Subsequent
builds are incremental and ~30 s.

Re-run `expo run:android` **only** after changing native config:

- `app.json` `plugins` block
- adding a native dependency (anything with `ios/` or `android/` folders)
- bumping Expo SDK / RN / Reanimated versions

For 99% of work (JS, React components, screens, styles, business logic) you
**do not** rebuild — just reload the JS bundle.

> 🗺️ **Mapbox Warning:** To compile the Android app with the map features, you **MUST** export a Mapbox Secret Token with `downloads:read` scope before running the build command:
> `export MAPBOX_DOWNLOAD_TOKEN="sk.your_token..."`
> If you do not have a Mapbox token, the build will fail with `Could not find com.mapbox.maps`. You can temporarily remove `@rnmapbox/maps` from `package.json` and `app.json` to bypass this while developing other features.

---

### 4. Daily inner loop

Once the dev client is installed:

```bash
pnpm --filter @layapa/mobile dev     # starts Metro; press `a` to launch the dev client
# or just: pnpm dev (runs api + admin + mobile in parallel)
```

- **JS edit → save** → bundle reloads in ~1 s on the device.
- **Shake the device** (or `adb shell input keyevent 82` for emulator) →
  opens the dev menu (Reload, Toggle Inspector, Performance Monitor, etc.).
- **R + R** on the emulator keyboard → manual reload.
- If Metro and the device get out of sync, kill Metro and restart with
  `pnpm --filter @layapa/mobile exec expo start -c` (the `-c` clears the
  Metro cache — needed after editing `babel.config.js`, `metro.config.js`,
  or `app.json`).

---

### 5. Troubleshooting

| Symptom                                                        | Likely cause / fix                                                                                                             |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `Exception in HostFunction: <unknown>` on first import         | Running in App Store Expo Go (not supported) — build a dev client. Or stale Babel cache after a config edit — `expo start -c`. |
| `adb: command not found`                                       | `ANDROID_HOME` / `PATH` not exported — see §1.                                                                                 |
| `adb devices` shows `unauthorized`                             | Tap **Allow** on the phone's "USB debugging" prompt; replug if missed.                                                         |
| `adb devices` shows nothing on Linux                           | Missing udev rules — `sudo apt install android-sdk-platform-tools-common`, then replug.                                        |
| Gradle build fails with `SDK location not found`               | Re-export `ANDROID_HOME` and restart the shell.                                                                                |
| Emulator boots but `pnpm dev` says "no devices"                | `adb kill-server && adb start-server`, then `adb devices`.                                                                     |
| "Unable to load script" red screen                             | Metro isn't running, or the phone can't reach it. Shake → **Settings → Debug server host** → set to `<your-machine-ip>:8081`.  |
| Build is fine but app crashes on launch with no useful message | `adb logcat ReactNativeJS:V ReactNative:V *:S` to stream JS-side errors.                                                       |

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
pnpm --filter @layapa/mobile dev                       # Metro server (connects to your dev client)
pnpm --filter @layapa/mobile exec expo run:android     # rebuild & install Android dev client
# pnpm --filter @layapa/mobile exec expo run:ios       # macOS only; iOS deferred (see Mobile dev workflow)
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

### ✉️ Testing Emails Locally (MailHog)

In the development environment, no actual emails are sent to the outside world. Instead, the backend routes all outgoing emails (including verification codes, password resets, and order receipts) into **MailHog**.

To view intercepted emails:

1. Ensure your Docker services are running (`docker compose up`).
2. Open your browser and go to **[http://localhost:8025](http://localhost:8025)**.
3. You will see the MailHog web interface with your verification emails and OTP codes sitting in the inbox.

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
| `DATABASE_URL`              | api     | `postgres://layapa:layapa@localhost:5433/layapa` |
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
