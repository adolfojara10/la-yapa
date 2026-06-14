# ✅ checklist.md — La Yapa manual QA runbook

Session-by-session manual testing checklist. Tick items off as features land;
treat the `🔒` markers as "don't bother yet — feature isn't built."

> Companion docs: [`AGENTS.md`](./AGENTS.md) (how to work in the repo),
> [`PROGRESS.md`](./PROGRESS.md) (what's actually built today),
> [`MASTER_VISION.md`](./MASTER_VISION.md) (product spec).

**Conventions**

- `[ ]` — testable today. Run it, tick it.
- `🔒 (pending: <feature>)` — not yet built. Tracked here so the runbook stays
  forward-looking; do **not** waste time trying these against current main.
- A section's red-flag list applies whether items are `[ ]` or `🔒` — they're
  forward-looking guardrails.

---

## 🧪 General Testing Principles (Apply to Every Session)

Before starting the next session, ALWAYS verify:

1. ✅ **Code runs without errors** (no console errors, no Python tracebacks)
2. ✅ **Automated tests pass** (`pytest`, `npm test`)
3. ✅ **Linters pass** (no warnings ignored)
4. ✅ **Manual smoke test** of the new feature
5. ✅ **Git committed** with clean message
6. ✅ **No secrets exposed** in code or commits
7. ✅ **Documentation updated** (README, PROGRESS.md)

---

## 📋 Session-by-Session Testing Checklists

### 🏗️ **SESSION 1 — Foundation (Prompts 2.1 + 2.2 + 2.3)**

#### 🔧 Setup Tests

- [ ] `pnpm install` runs without errors
- [ ] `docker-compose up` starts Postgres + Redis successfully
- [ ] `pnpm dev` runs all 3 apps in parallel
- [ ] Backend: `python manage.py runserver` → loads on `localhost:8000`
- [ ] Backend: `localhost:8000/admin` shows Django admin login
- [ ] Mobile: Expo dev server starts, app loads in **Android dev client**
      (not Expo Go — see `AGENTS.md` §4)
- [ ] Admin (Next.js): `localhost:3000` loads default page
- [ ] Git: `.gitignore` excludes `.env`, `node_modules`, `__pycache__`

#### 🗄️ Database Tests

- [ ] `python manage.py migrate` runs cleanly
- [ ] `python manage.py seed_demo_data` creates demo data
- [ ] Open Django Admin → see all models registered (users, businesses, bags, orders, etc.)
- [ ] Connect to Postgres → verify tables exist
- [ ] `pytest apps/api/` → all model tests pass

#### 🎨 Design System Tests

- [ ] Open mobile app → custom fonts load (Poppins, Inter, Fraunces)
- [ ] Toggle light/dark mode → colors switch correctly
- [ ] Render test screen with: Button, Input, Card, Avatar, Badge → all styled correctly
- [ ] Yapi placeholder SVG renders without errors
- [ ] Logo placeholder displays

#### 🚨 Red Flags

- ❌ Migration errors → fix before continuing
- ❌ Import errors in any app → fix
- ❌ Color tokens not exported → fix
- ❌ "FAILED" in CI logs → investigate

---

### 🔐 **SESSION 2 — Auth + Consumer Core (Prompts 2.4 + 2.5 + 2.6 + 2.7)**

#### 🔑 Auth Tests _(Session 6 — backend complete, mobile screens implemented)_

- [ ] Register new user via email/password → success (`POST /api/v1/auth/register`)
- [ ] Email verification code arrives in MailHog (`http://localhost:8025`)
- [ ] Enter the 6-digit code on `(auth)/verify-email` → routed to onboarding
- [ ] Complete 4-step onboarding (name → language → location → dietary)
      → land in `(consumer)` placeholder
- [ ] Wrong code 5× → "Demasiados intentos" error, "Reenviar código" works
- [ ] Login with credentials → returns JWT, lands in `(consumer)` directly
- [ ] Login with role=business_owner → lands in `(business)` placeholder
- 🔒 (pending: GOOGLE_OAUTH_CLIENT_IDS provisioned) Login with Google → works
- 🔒 (pending: Apple Developer account + iOS device) Login with Apple → works
- [ ] Forgot password → email arrives in MailHog with deep-link → tap →
      `(auth)/reset-password` opens with token → reset succeeds
- [ ] Force-expire access token: edit `SIMPLE_JWT.ACCESS_TOKEN_LIFETIME` to
      `timedelta(seconds=5)` in `dev.py`, wait 5s, hit any authed endpoint →
      Axios silently refreshes, request succeeds
- [ ] Logout → second use of the same refresh returns 401
- [ ] Cold-launch with invalid tokens in SecureStore → falls back to welcome
- [x] `pytest apps/api/apps/users/` passes (69 tests, 94% coverage)

#### 📦 Browse Tests _(Session 7 — backend + mobile complete)_

- [ ] Home screen (Explorar tab) loads with bags from `seed_demo_data`
- [ ] List view shows bag cards correctly (image, business, price, strikethrough, discount %, distance, rating, pickup window)
- [ ] Heart button toggles favorite, persists across reload (server-backed)
- [ ] Tap a card → bag detail opens with carousel + description + chips
- [ ] Pull to refresh works (list view)
- [ ] Infinite scroll loads the next page when scrolling near the bottom
- [ ] Filters sheet opens: pick "Vegano" + "Sin gluten" → list shrinks (AND semantics)
- [ ] "Evitar alérgenos: gluten" removes bags with gluten warning
- [ ] Distance picker (1/3/5/10 km) refreshes the list
- [ ] Filter count badge on the filter button reflects active count
- [ ] Search bar `q` filters bags by title/business name as you type
- [ ] Sticky "Reservar por $X.XX" CTA on detail shows the "checkout next session" toast
- [ ] Empty state ("No hay bolsas con esos filtros") shows when filters return zero
- [ ] Map view shows real OpenStreetMap tiles
- [ ] Markers cluster by location with a count badge
- [ ] Tap marker → bottom sheet opens with that location's bags
- 🔒 (pending: real Yapi artwork) Empty state shows Yapi sleepy illustration

#### 💳 Checkout Tests _(Session 8 — backend + mobile complete; provider integration unverified)_

**Tests passing today against `FakePaymentProvider` (USE_FAKE_PAYMENT_PROVIDER=True)**:

- [x] `pytest apps/payments/ apps/orders/ apps/consumer/tests/test_orders_endpoints.py` → 162 backend tests pass at 90% coverage
- [x] Checkout screen renders order summary (image, business, title, pickup window, total)
- [x] Payment method selector toggles between PayPhone / DeUna
- [x] "Donar como comida suspendida" toggle persists into the POST body
- [x] Terms checkbox gates the pay button (disabled until checked)
- [x] Pay → creates order in `pending_payment`, decrements bag inventory atomically
- [x] WebView opens with the fake provider's URL (no real network)
- [x] Order detail shows "Esperando confirmación de pago" banner while pending
- [x] Order detail polls `/orders/{id}` every 2s; flips to QR+PIN block once status → `paid`
- [x] Cancel >1h before pickup → routes through refund flow → status `refunded` (fake provider is sync)
- [x] Cancel ≤1h before pickup → blocked with "Ya pasó la ventana de cancelación" (409 from API)
- [x] Active-order banner appears on Explorar tab for non-terminal orders
- [x] Order history (Perfil → "Mis pedidos") lists all orders with status badges
- [x] Bonus credit redemption: `POST /consumer/orders/{id}/redeem-credit` reduces `total_paid` by credit amount (clamped)

**🔒 Real-provider smoke — REQUIRES SANDBOX ACCOUNTS BEFORE THIS CAN BE EXERCISED**:

> ⚠️ **BLOCKER**: PayPhone + DeUna sandbox accounts have not been provisioned.
> All backend tests pass against `FakePaymentProvider`, but the FIRST REAL
> PAYMENT will be the first time PayPhone's / DeUna's actual webhook payload
> shapes are validated. The provider classes use defensive field lookups
> (camelCase + PascalCase), but real-world divergence is likely.
> See AGENTS.md §4 "Provisioning payment providers" for setup steps.
>
> Once accounts are provisioned, capture sample webhook payloads from each
> provider's sandbox and add fixture-based unit tests so the dispatcher
> stays correct against real schemas.

- 🔒 (pending: PayPhone sandbox account + `PAYPHONE_API_KEY` / `PAYPHONE_SECRET` / `PAYPHONE_WEBHOOK_SECRET`) PayPhone WebView opens with sandbox card form
- 🔒 (pending: PayPhone test card) Card payment succeeds in PayPhone sandbox
- 🔒 (pending: ngrok + PayPhone dashboard webhook URL) Webhook arrives → order flips to `paid`
- 🔒 (pending: PayPhone refund API call) Cancel paid order → refund webhook → status flips to `refunded`
- 🔒 (pending: DeUna sandbox account + `DEUNA_PUBLIC_KEY` / `DEUNA_SECRET_KEY` / `DEUNA_WEBHOOK_SECRET`) DeUna WebView opens with sandbox QR
- 🔒 (pending: DeUna webhook delivery) DeUna payment webhook arrives → order flips to `paid`
- 🔒 (pending: DeUna refund API call) DeUna refund flow completes end-to-end
- 🔒 (pending: real Expo push token from device) Push notification arrives on payment.succeeded
- 🔒 (pending: provider response fixtures) Add unit tests with captured real-provider webhook bodies so any schema drift fails CI

**Code changes likely needed once sandbox accounts land**:

- 🔒 Adjust `parse_event` field-name lookups in `apps/payments/providers/payphone.py` and `de_una.py` to match real payload keys
- 🔒 Populate `PAYMENT_WEBHOOK_IP_ALLOWLIST` in `prod.py` with provider source CIDRs
- 🔒 Verify HMAC algorithm + header name match each provider's actual docs (currently HMAC-SHA256 + `X-PayPhone-Signature` / `X-DeUna-Signature`)
- 🔒 Capture real-provider success + failure webhook samples, add as fixtures under `apps/payments/tests/fixtures/`

#### 🎫 Pickup Tests _(Session 9 — full pickup loop: business app + scanner + Celery + push)_

> **Quickstart**: `cd apps/api && source .venv/bin/activate && python manage.py migrate && python manage.py seed_demo_data --reset`
>
> The seed prints test credentials at the end. **Password for every user is `test-pass-123`.**
>
> **Test accounts created by the seed:**
>
> | Email               | Role           | What they have                                                 |
> | ------------------- | -------------- | -------------------------------------------------------------- |
> | `owner@layapa.test` | business_owner | Owns "Panadería La Esperanza" with 2 active PAID orders + bags |
> | `mateo@layapa.test` | consumer       | Has a PAID order ready for pickup (will show QR + PIN)         |
> | `nora@layapa.test`  | consumer       | Has a PAID order ready for pickup                              |
> | `sofia@layapa.test` | consumer       | Generic browsing persona                                       |
> | `donor@layapa.test` | consumer       | Made a $3.00 general-pool suspended-meal donation              |
>
> The seed also prints each PAID order's `PIN`, `QR token`, and `order_id` so you can drive the API with curl without going through Django admin.

##### Creating more test data on demand

Repeat-running tests often requires fresh PAID orders + donations because once confirmed, an order is terminal (status=COMPLETED is irreversible). To regenerate:

```bash
# Wipe + re-seed (idempotent — `owner@layapa.test` retains the same email).
python manage.py seed_demo_data --reset

# Or create ad-hoc test data from the shell:
python manage.py shell <<'EOF'
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from apps.bags.factories import BagFactory
from apps.businesses.models import Business
from apps.orders.models import OrderStatus
from apps.orders.services import create_order
from apps.users.factories import ConsumerProfileFactory, UserFactory
from apps.suspended_meals.models import SuspendedMealDonation, DonationStatus

# Get the seeded business's first location.
loc = Business.objects.get(name="Panadería La Esperanza").locations.first()

# Make a fresh PAID order with a 2-hour pickup window starting now.
consumer = UserFactory(email="ad-hoc@layapa.test", is_email_verified=True)
ConsumerProfileFactory(user=consumer, first_name="AdHoc")
bag = BagFactory(
    business_location=loc,
    original_price=Decimal("12.00"),
    sale_price=Decimal("4.50"),
    quantity_available=3,
    pickup_window_start=timezone.now() + timedelta(minutes=5),
    pickup_window_end=timezone.now() + timedelta(hours=2),
)
order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
order.status = OrderStatus.PAID
order.save(update_fields=["status"])
print(f"Order {order.id} | PIN {order.pickup_code} | QR {order.pickup_qr_token}")

# Make a fresh suspended-meal donation.
donor = UserFactory(email=f"donor-{timezone.now().timestamp():.0f}@layapa.test")
SuspendedMealDonation.objects.create(
    donor=donor, amount=Decimal("3.00"), bag=None,
    status=DonationStatus.ACTIVE, is_anonymous=True,
)
EOF
```

##### 🔁 Backend smoke (curl / httpie — no mobile required)

Run against `manage.py runserver` after seeding. Get a JWT for the business owner first:

```bash
# 1. Login as the business owner — captures access token.
ACCESS=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@layapa.test","password":"test-pass-123"}' \
  | python -c 'import json,sys;print(json.load(sys.stdin)["tokens"]["access"])')
echo "Access: $ACCESS"

# 2. Dashboard summary.
curl -s http://localhost:8000/api/v1/business/dashboard \
  -H "Authorization: Bearer $ACCESS" | python -m json.tool

# 3. List active orders (use the order_id from one of these for the
#    confirm-pickup tests below).
curl -s http://localhost:8000/api/v1/business/orders/active \
  -H "Authorization: Bearer $ACCESS" | python -m json.tool

# 4. Confirm via QR (use a QR token printed by the seed).
QR='<paste QR token here>'
curl -s -X POST http://localhost:8000/api/v1/business/orders/confirm-pickup-by-scan \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d "{\"qr_token\":\"$QR\"}" | python -m json.tool
# Expected: 200 + order with status="completed".

# 5. Replay the same QR → should be 404 (single-use rotation).
curl -s -X POST http://localhost:8000/api/v1/business/orders/confirm-pickup-by-scan \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d "{\"qr_token\":\"$QR\"}" -w "\nHTTP %{http_code}\n"

# 6. Confirm via PIN against a different order. PIN + business_location_id
#    are required. business_location_id is in the order list above.
PIN='<paste PIN from seed output>'
LOC=<paste business_location_id>
curl -s -X POST http://localhost:8000/api/v1/business/orders/confirm-pickup-by-pin \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d "{\"business_location_id\":$LOC,\"pin\":\"$PIN\"}" | python -m json.tool

# 7. PIN lockout: hit it 5 times with the wrong PIN, then watch the
#    correct PIN bounce with 423.
WRONG='0000'  # change if your seed accidentally generated this as a real PIN
for i in 1 2 3 4 5; do
  curl -s -X POST http://localhost:8000/api/v1/business/orders/confirm-pickup-by-pin \
    -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
    -d "{\"business_location_id\":$LOC,\"pin\":\"$WRONG\"}" -w "\nHTTP %{http_code}\n"
done
# Now the right PIN returns 423.
curl -s -X POST http://localhost:8000/api/v1/business/orders/confirm-pickup-by-pin \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d "{\"business_location_id\":$LOC,\"pin\":\"$PIN\"}" -w "\nHTTP %{http_code}\n"

# 8. Suspended-meal dispatch.
curl -s http://localhost:8000/api/v1/business/suspended-meals/active \
  -H "Authorization: Bearer $ACCESS" | python -m json.tool

DONATION='<paste donation id from above>'
curl -s -X POST http://localhost:8000/api/v1/business/suspended-meals/dispatch \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d "{\"donation_id\":\"$DONATION\",\"business_location_id\":$LOC,\"notes\":\"Cliente recurrente\"}" \
  | python -m json.tool
```

##### Backend assertions (must hold)

- [ ] `python manage.py seed_demo_data --reset` runs to completion + prints test credentials
- [ ] `GET /business/dashboard` returns `active_orders_count: 2`, `suspended_meals_available: 1`
- [ ] `GET /business/orders/active` returns the 2 PAID orders sorted by `pickup_window_start`, each with `consumer_first_name`, `pickup_code`, `is_within_pickup_window: true`
- [ ] `GET /business/orders/active` as `sofia@layapa.test` (consumer role) returns 403
- [ ] `POST /confirm-pickup-by-scan` with valid QR → 200, order completed, `pickup_qr_token` rotated to new UUID
- [ ] Replay original QR → 404 `qr_invalid`
- [ ] `POST /confirm-pickup-by-pin` with correct PIN → 200, order completed
- [ ] 5x wrong PIN → 6th attempt with CORRECT PIN returns 423 `pin_locked`
- [ ] After lockout, QR scan still works (verify by creating a fresh order + locking it via PIN miss + scanning the QR)
- [ ] `POST /suspended-meals/dispatch` → 200, `claim_id` returned, donation no longer in `/suspended-meals/active`
- [ ] 6th dispatch in 24h at same location → 429 `dispatch_rate_limit_exceeded`
- [ ] `pytest apps/business/ apps/orders/ apps/suspended_meals/ apps/notifications/` passes (202 tests at 90%)

##### 📱 Mobile smoke (Android dev client — `pnpm --filter @layapa/mobile dev`)

**One-time setup if you added native deps since last build:**

```bash
pnpm --filter @layapa/mobile exec expo run:android --device
# expo-camera and expo-notifications are native modules; first run after
# install requires this rebuild. Documented in AGENTS.md §5.
```

**Business app — log in as `owner@layapa.test`:**

- [ ] App lands on `(business)/(tabs)` dashboard automatically (routing guard)
- [ ] Header reads "Tus pedidos de hoy · 2 activos · 0 completados · 1 suspendidas disponibles"
- [ ] Action row shows "Escanear QR" + "Ingresar PIN"
- [ ] Active orders list shows Mateo + Nora's bags with the PIN displayed in large green text
- [ ] Tap "Escanear QR" → grants camera permission (first time) → camera preview shows
- [ ] Open consumer app on a SECOND device (or use a phone in dev + a real device for vendor), log in as `mateo@layapa.test`, navigate to `/(consumer)/orders/<id>`, point business app camera at the QR
- [ ] Scanner detects QR → "¡Pedido confirmado!" toast → navigates to business order detail with COMPLETED badge
- [ ] On the consumer device, the order detail polls and within ~2s flips from "Esperando" to a completed state
- [ ] Tap "Ingresar PIN" → bottom sheet with 4-digit OTP input → type Nora's pickup code → "Confirmar retiro" → success
- [ ] Type a wrong PIN → "PIN incorrecto" toast
- [ ] Repeat 5 wrong PINs → 6th attempt with correct PIN → "PIN bloqueado — usa el QR" toast
- [ ] Switch to Suspendidas tab → shows Sofía's $3.00 anonymous donation in "Pool general"
- [ ] Tap donation → bottom sheet with notes input → type a note → "Confirmar dispatch" → success toast + list updates
- [ ] Repeat dispatch 5 times (use `seed_demo_data --reset` + recreate donations in shell as needed) → 6th attempt → `Alert.alert` "Límite diario alcanzado"
- [ ] Profile tab → "Cerrar sesión" → back to welcome screen

**Consumer app — log in as `mateo@layapa.test`:**

- [ ] App lands on `(consumer)/(tabs)` with the active-order banner pinned at top
- [ ] Tap banner → order detail with QR code + 4-digit PIN displayed
- [ ] After business confirms (above), this screen polls and updates within ~2s

##### 🔔 Push notification smoke (requires Celery worker running)

The pickup-ready push fires at `pickup_window_start`, and reminders fire 1h + 30min before `pickup_window_end`. For the seeded orders these are 10-110 minutes out, so to test push delivery you need to either wait or create an order with a tighter window.

**Start the worker + beat** (two terminals, both with `.venv` activated):

```bash
# Terminal 1 — worker
cd apps/api && source .venv/bin/activate
celery -A config worker -l info

# Terminal 2 — beat (only needed for the hourly expire_stale_pending sweep)
cd apps/api && source .venv/bin/activate
celery -A config beat -l info -s /tmp/celerybeat-schedule
```

**Trigger a push in 2 minutes** via the shell:

```bash
python manage.py shell <<'EOF'
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from apps.bags.factories import BagFactory
from apps.businesses.models import Business
from apps.orders.models import OrderStatus
from apps.orders.services import create_order
from apps.users.factories import ConsumerProfileFactory, UserFactory
from apps.orders.tasks import send_pickup_ready

loc = Business.objects.get(name="Panadería La Esperanza").locations.first()
consumer = UserFactory(email=f"pushtest-{timezone.now().timestamp():.0f}@layapa.test", is_email_verified=True)
ConsumerProfileFactory(user=consumer, first_name="Test")
bag = BagFactory(
    business_location=loc,
    original_price=Decimal("12.00"), sale_price=Decimal("4.50"),
    quantity_available=1,
    pickup_window_start=timezone.now() + timedelta(minutes=2),
    pickup_window_end=timezone.now() + timedelta(hours=1),
)
order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
order.status = OrderStatus.PAID
order.save(update_fields=["status"])
# Schedule manually since we bypassed the payment webhook.
send_pickup_ready.apply_async(args=[str(order.id)], eta=bag.pickup_window_start)
print(f"Scheduled push for {bag.pickup_window_start}")
EOF
```

- [ ] Celery worker log shows the task accepted with `eta=`
- [ ] At T+2min, worker log shows `Task apps.orders.tasks.send_pickup_ready[...] succeeded`
- 🔒 (pending: device logged in with push permission granted + real Expo push token) Notification arrives on device — currently the push hits Expo's API with the registered token but actual delivery requires a real device + a real (not simulator) push token
- 🔒 (pending: real device test) Tapping the notification deep-links to `/(consumer)/orders/<id>`

##### 🔔 Push token registration sub-smoke

- [ ] Log into mobile app on a real Android device → first cold-start triggers `useRegisterPushToken` → `apps.notifications.models.PushToken` row appears for the user (verify via Django admin → Notifications → Push tokens)
- [ ] Token is `ExponentPushToken[...]` format
- [ ] Logging out and back in as a different user → second `PushToken` row appears (different user, same token if same device)
- [ ] `POST /api/v1/notifications/register-token` is idempotent — re-posting same body doesn't duplicate rows

##### Anti-fraud assertions (security-critical)

- [ ] **QR single-use**: confirmed by smoke step 5 above
- [ ] **PIN per-order lockout**: confirmed by smoke step 7
- [ ] **Cross-business isolation**: create a second business owner via shell, attempt to confirm `owner@layapa.test`'s order → 404 (not 403; we intentionally don't leak existence)

```bash
python manage.py shell <<'EOF'
from apps.users.factories import BusinessOwnerFactory
from apps.businesses.factories import BusinessFactory, BusinessLocationFactory
attacker = BusinessOwnerFactory(email="attacker@layapa.test", is_email_verified=True)
biz = BusinessFactory(owner=attacker, name="Attacker Foods")
BusinessLocationFactory(business=biz)
print("Login as attacker@layapa.test / test-pass-123 and try to confirm another business's order.")
EOF
```

- [ ] **Window grace bounds** (60min early / 15min late): default seed bags have pickup_window_start = now + 10min, so they're already in the early grace window. Edit a bag in Django admin to `pickup_window_start = now + 3h` and re-test → 409 `outside_pickup_window`. Set it to `now - 3h` end → 409 again.
- [ ] **Cross-business PIN-lock DoS sealed**: as `attacker@layapa.test`, hit `/confirm-pickup-by-pin` 5x with `owner@layapa.test`'s location_id + a guessed PIN → check via Django admin that the target order's `pin_attempts` is STILL 0 (the service-layer ownership check prevents the bump)

#### 🚨 Red Flags

- ❌ JWT not refreshing → fix interceptor
- ❌ OSM tiles not rendering → check network access, `react-native-maps` rebuild, and tile overlay
- ❌ Payment webhook fails → check signature validation
- ❌ Push notifications not arriving → check Expo push token registration

---

### 🏪 **SESSION 3 — Business + Admin (Prompts 2.8 + 2.9)**

#### 👔 Business Onboarding Tests

- 🔒 (pending: business signup wizard + R2 upload) Business signup formal tier → all docs upload to R2
- 🔒 (pending: informal-tier signup variant) Business signup informal tier (mercado) → simplified flow works
- 🔒 (pending: selfie+cédula upload screen) Selfie with cédula uploads correctly
- 🔒 (pending: pending-review screen) Status=pending shows "En revisión" screen
- 🔒 (pending: food-safety acceptance gate) Food safety terms accepted, stored with timestamp

#### 📦 Bag Management Tests

- 🔒 (pending: bag-create screen) Create surprise bag → validates price (sale ≤ 50% of original, ≥ $1.50)
- 🔒 (pending: specific-bag photo upload) Create specific bag with photos → uploads work
- 🔒 (pending: bag-edit screen) Edit bag (not yet sold) → updates work
- 🔒 (pending: edit-after-sold guard) Try editing sold bag → blocked
- 🔒 (pending: 1-tap relist action) Duplicate bag (1-tap relist) → works
- 🔒 (pending: template save/load) Save as template → retrievable
- 🔒 (pending: multi-location bag assignment) Multi-location: add second location → bag can be assigned
- 🔒 (pending: pickup-window validator) Pickup window in past → blocked
- 🔒 (pending: quantity-zero auto-inactive) Set quantity to 0 → bag inactive

#### 🔍 Pickup Confirmation Tests

- 🔒 (pending: business orders screen) Business app shows active orders sorted by pickup window
- 🔒 (pending: QR scanner screen) Scan QR (from consumer's app) → order confirmed
- 🔒 (pending: PIN entry fallback) Manual PIN entry fallback works
- 🔒 (pending: PIN retry lockout) Wrong PIN 5 times → blocked
- 🔒 (pending: pickup-window grace window logic) Confirm pickup outside window → blocked (allow ±15min grace)
- 🔒 (pending: `Order.complete()` service) Order status updates to "completed"
- 🔒 (pending: post-pickup push) Consumer receives "Thanks!" push notification
- 🔒 (pending: impact signal idempotency fix) Consumer's impact stats update (meals saved, CO₂, money)
- 🔒 (pending: suspended-meals dispatch flow) Suspended meal dispatch (no QR) → marks claimed

#### 🖥️ Admin Panel Tests

- 🔒 (pending: admin role + login) Admin login works (separate role)
- 🔒 (pending: pending-businesses queue page) Pending businesses queue displays
- 🔒 (pending: document preview component) Document preview (PDF, images) renders
- 🔒 (pending: approve action) Approve business → status updates, notification sent
- 🔒 (pending: reject-with-reason action) Reject business → reason saved, notification sent
- 🔒 (pending: KPI dashboard) Dashboard KPIs show correct numbers
- 🔒 (pending: payout queue page) Payout queue shows pending payouts
- 🔒 (pending: payout CSV export) Generate CSV → downloads valid file with bank details
- 🔒 (pending: payout mark-paid action) Mark payout as paid → status updates
- 🔒 (pending: dispute list page) Dispute list loads
- 🔒 (pending: dispute resolution flow) Resolve dispute → both parties notified
- 🔒 (pending: user management page) User management: search, suspend works
- 🔒 (pending: push-campaign composer) Push campaign composer → sends test push to admin

#### 🧊 Deferred Admin Scope

- 🔒 (pending later: bags moderation) Admin bags moderation queue
- 🔒 (pending later: reviews moderation) Admin reviews moderation queue
- 🔒 (pending later: suspended meals admin) Suspended meals pool + history admin views
- 🔒 (pending later: gamification admin) Badges and levels admin screens
- 🔒 (pending later: admin settings) Commission rates and platform config screens

#### 💰 Payout Calculation Tests (Critical!)

- 🔒 (pending: payout calc service) Business with 10 orders → payout = sum(sale_price - commission) - refunds - bonus credits
- 🔒 (pending: payout calc service) Cancelled order doesn't count
- 🔒 (pending: payout calc service) Refunded order deducted correctly
- 🔒 (pending: payout calc service) Business-cancelled order with bonus credit → deducted from payout
- 🔒 (pending: weekly payout Celery beat) Weekly payout triggered Monday for previous Mon-Sun
- 🔒 (pending: monthly payout Celery beat) Monthly payout triggered on 1st for previous month
- 🔒 (pending: 24h dispute-window guard) 24h dispute window respected (orders < 24h old not included)

#### 🚨 Red Flags

- ❌ Document uploads fail → check R2 credentials
- ❌ Payout calculation wrong by even $0.01 → fix immediately
- ❌ Business sees other businesses' data → critical security bug

---

### 🎮 **SESSION 4 — Polish (Prompts 2.10 + 2.11 + 2.12 + 2.13)**

#### 🏆 Gamification Tests

- 🔒 (pending: badge-award signal) Complete first order → "Primer Rescate" badge awarded
- 🔒 (pending: XP table + signal) XP added correctly per action (50 XP per bag, 25 per review, etc.)
- 🔒 (pending: level-up celebration screen) Level up triggers celebration animation
- 🔒 (pending: badges seed data) All 30 badges in DB and discoverable
- 🔒 (pending: badge progress UI) Badge progress shown for locked badges
- 🔒 (pending: leaderboard opt-in toggle) Leaderboard opt-in works (default OFF)
- 🔒 (pending: leaderboard endpoint + screen) Leaderboard shows correct rankings

#### 🌍 Impact Tracker Tests

- 🔒 (pending: impact stats screen) After 1 order, profile shows: 1 meal, 1.5kg, 3.75kg CO₂, $X saved
- 🔒 (pending: impact stats screen) After 10 orders, numbers multiply correctly
- 🔒 (pending: IG Stories share-image generator) Share to Instagram Stories generates correct image
- 🔒 (pending: monthly recap Celery beat) Monthly recap push arrives on 1st of month

#### 🤝 Suspended Meals Tests

- 🔒 (pending: checkout suspended-meal toggle) Toggle "Donate as suspended meal" during checkout
- 🔒 (pending: `SuspendedMealDonation` create-on-checkout) Donation tracked in DB as suspended
- 🔒 (pending: public counter endpoint + widget) Public counter increments
- 🔒 (pending: business suspended-meals queue) Business sees "Suspended meals available: X"
- 🔒 (pending: vendor dispatch action) Vendor dispatches (no QR) → counter updates
- 🔒 (pending: anonymous donor push) Donor receives anonymous "Your gift fed someone 🌱" push
- 🔒 (pending: per-business daily cap) Max 5 per business per day enforced

#### 👥 Referral Tests

- 🔒 (pending: referral code generation) Each user has unique referral code
- 🔒 (pending: deep-link handler) Share via deep link → opens app with code pre-filled
- 🔒 (pending: signup code-capture field) Referee signs up with code → both linked
- 🔒 (pending: referral reward signal) Referee makes first purchase → both get $2 credit
- 🔒 (pending: store credit ledger) Credit applied to next purchase
- 🔒 (pending: profile referrals stat) Profile shows "X friends invited"

#### 🌐 i18n Tests

- 🔒 (pending: i18next init + translation files) Switch language to English → ALL strings translate
- 🔒 (pending: i18next strict mode) No "missing translation" warnings in console
- 🔒 (pending: locale-aware formatters) Date/numbers format correctly per locale
- 🔒 (pending: django-modeltranslation wiring) Backend serves English content with Accept-Language: en
- 🔒 (pending: AsyncStorage persist for locale) App restart preserves language choice

#### 🧪 CI/CD Tests

- [ ] PR triggers GitHub Actions
- [ ] Lint, type-check, tests all run
- [ ] Failed test blocks merge
- 🔒 (pending: Railway staging deploy hook) Merge to main deploys to Railway staging
- 🔒 (pending: Sentry DSN wiring) Sentry catches a test error
- 🔒 (pending: PostHog API key wiring) PostHog logs a test event
- 🔒 (pending: backup Celery beat + R2 bucket) Backup runs and uploads to R2

#### 📄 Legal & Store Tests

- 🔒 (pending: legal docs + settings screen route) Privacy Policy accessible from settings + signup
- 🔒 (pending: legal docs + settings screen route) Terms accessible
- 🔒 (pending: ES + EN legal copy) All legal docs in ES + EN
- 🔒 (pending: real app icon assets) App icon displays correctly on home screen (iOS + Android)
- 🔒 (pending: real splash asset) Splash screen shows logo
- 🔒 (pending: permission justification copy in `app.json`) App permissions prompts have justification text
- 🔒 (pending: ATT prompt + copy) App tracking transparency prompt (iOS) shows
- 🔒 (pending: Apple Developer account + EAS Build) TestFlight build uploaded successfully
- 🔒 (pending: Play Console setup + EAS Build) Google Play internal testing track build uploaded

#### 🚨 Red Flags

- ❌ Translation keys appearing as literal text → fix i18n config
- ❌ Sentry not capturing errors → check DSN
- ❌ App icon blurry → regenerate at correct sizes

---

## 📝 Universal "Definition of Done" Checklist

Before EACH session ends, check:

```markdown
## Session [X] — Done Checklist

### Code Quality

- [ ] No console.errors or Python tracebacks
- [ ] Linter passes (ESLint + Ruff)
- [ ] TypeScript: 0 errors
- [ ] All tests pass (`pytest` + `npm test`)
- [ ] Test coverage didn't decrease

### Functionality

- [ ] All features in session work end-to-end
- [ ] Manual smoke test completed
- [ ] Tested on iOS simulator + Android emulator
- [ ] Edge cases handled (empty, error, loading states)

### Security

- [ ] No secrets in code
- [ ] .env.example updated with new vars
- [ ] Auth/permissions verified on new endpoints

### Documentation

- [ ] PROGRESS.md updated with session summary
- [ ] README updated if setup changed
- [ ] API docs auto-generated (Swagger)
- [ ] Inline code comments where complex

### Git

- [ ] All changes committed
- [ ] Branch merged to main (or PR opened)
- [ ] Tagged release if major milestone

### Deployment

- [ ] Staging deployment successful
- [ ] Smoke test on staging URL
- [ ] No errors in Sentry
```

---

## 🛠️ Recommended Testing Tools

| Purpose                | Tool                              | When to Use              |
| ---------------------- | --------------------------------- | ------------------------ |
| **Backend unit tests** | `pytest` + `pytest-django`        | Every session            |
| **Mobile unit tests**  | `Jest` + RTL                      | Every session            |
| **API testing**        | Postman/Insomnia/Bruno            | Manual testing endpoints |
| **E2E mobile**         | Maestro                           | Sessions 2, 3, 4         |
| **E2E admin**          | Playwright                        | Session 3                |
| **Load testing**       | k6 or Artillery                   | Before launch            |
| **Manual QA**          | TestFlight + Google Play Internal | Session 4                |
| **Bug tracking**       | GitHub Issues or Linear           | Throughout               |

---

## 💡 Pro Recommendation

After each session:

1. **Run automated tests** (5-10 min)
2. **Manual smoke test** the new features (15-20 min)
3. **Write session summary** in PROGRESS.md (10 min)
4. **Deploy to staging** + smoke test there (10 min)
5. **Take a break** ☕ — don't immediately start next session

**Total testing time per session: ~45-60 min**

This investment prevents weeks of debugging later. **Trust me — broken
foundations compound badly.** 🏚️
