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
- 🔒 (pending: Mapbox `pk.*` + `sk.*` tokens) Map view shows real Mapbox tiles
- 🔒 (pending: Mapbox tokens) Markers cluster by location with a count badge
- 🔒 (pending: Mapbox tokens) Tap marker → bottom sheet opens with that location's bags
- 🔒 (pending: real Yapi artwork) Empty state shows Yapi sleepy illustration

#### 💳 Checkout Tests (Use PayPhone/DeUna sandbox/test mode)

- 🔒 (pending: checkout screen) Checkout summary correct (price, taxes if any)
- 🔒 (pending: PayPhone SDK) PayPhone test card → payment succeeds
- 🔒 (pending: DeUna SDK) DeUna sandbox → payment succeeds
- 🔒 (pending: payment webhook handler) Order created in DB with status=paid
- 🔒 (pending: QR/PIN generation on order finalize) QR code + PIN generated
- 🔒 (pending: Expo push wiring) Push notification arrives on payment success
- 🔒 (pending: webhook signature validation) Payment webhook handled correctly (test with curl/Postman)
- 🔒 (pending: failed-payment branch) Failed payment → order status updated, user notified
- 🔒 (pending: refund flow + 1h window check) Cancel within 1h window → refund triggered
- 🔒 (pending: 1h-window enforcement) Cancel after 1h → blocked with error message
- 🔒 (pending: payments app tests) `pytest apps/api/payments/` passes (with mocked providers)

#### 🎫 Pickup Tests

- 🔒 (pending: order detail screen) Order detail shows QR code (scannable) + 4-digit PIN
- 🔒 (pending: pickup-window countdown) Countdown to pickup window displays correctly
- 🔒 (pending: Celery reminder schedule) Pickup reminder push arrives 1h before window closes
- 🔒 (pending: Celery reminder schedule) Pickup reminder push arrives 30min before window closes
- 🔒 (pending: directions deep link) Get directions opens map app
- 🔒 (pending: `Order.complete()` service) After pickup confirmed (next session) → status changes to "completed"

#### 🚨 Red Flags

- ❌ JWT not refreshing → fix interceptor
- ❌ Mapbox not rendering → check API key + permissions
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
