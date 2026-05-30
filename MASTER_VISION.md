Perfect! Generating the **master prompt now**. Buckle up — this is comprehensive. 🚀

---

# 🌱 LA YAPA — MASTER DEVELOPMENT PROMPT

## 📄 PART 1 — MASTER VISION DOCUMENT

> Use this as the foundational context document. Feed this to any AI coding agent (Claude Code, Cursor, Aider, etc.) before any implementation prompt.

---

### 🎯 Project Identity

**Name:** La Yapa  
**Tagline (ES):** _"Comida rescatada, planeta cuidado."_  
**Tagline (EN):** _"Rescued food, planet saved."_  
**Mission:** Reduce food waste in Ecuador by connecting consumers with restaurants, bakeries, supermarkets, hotels, mercados, and farmers offering surplus food at discounted prices via "surprise bags" and specific item listings.

**Vision:** Become Ecuador's leading sustainable food platform, starting in Cuenca and expanding nationwide, eventually integrating delivery, food rescue NGOs, and community-driven impact.

**Inspiration:** Too Good To Go — but better designed, more culturally rooted, with deeper community impact (suspended meals, gamification, impact tracking).

---

### 👥 User Personas

**1. Sofía — Consumer (Eco-conscious millennial, 28, Cuenca)**

- Wants to save money + reduce waste
- Uses iPhone, Apple Pay
- Discovers via Instagram

**2. Don Carlos — Business Owner (Bakery, 52, Cuenca)**

- Throws away 5kg of bread daily
- Wants extra revenue + good karma
- Needs SIMPLE app (not tech-savvy)

**3. María — Mercado Vendor (Vegetables, 45, Mercado 10 de Agosto)**

- No formal RUC
- Sells via cash + DeUna
- Needs ultra-simple onboarding

**4. Pedro — Farmer (Producer, 38, Gualaceo)**

- Has surplus produce weekly
- Wants direct-to-consumer
- Needs flexible scheduling

**5. Ana — Admin/Sales Rep (Internal team)**

- Manages business approvals, disputes, payouts
- Needs powerful dashboard

---

### 🎨 Brand Identity

#### Color Palette (Andean Modern Minimalist)

```css
/* Primary */
--verde-paramo: #2d6a4f; /* Andean deep green - primary */
--terracotta-inti: #d97757; /* Sun terracotta - secondary */
--amarillo-sol: #f4c430; /* Golden yellow - accent */

/* Neutrals */
--algodon: #faf6f0; /* Cream background */
--blanco-puro: #ffffff; /* Pure white */
--tierra: #1b2d2a; /* Dark text */
--niebla: #6b7b78; /* Muted gray text */
--piedra: #e5e1d8; /* Borders/dividers */

/* Dark Mode */
--dark-bg: #0f1a18;
--dark-surface: #1a2a26;
--dark-border: #2a3d38;
--dark-text: #e8e5de;

/* Semantic */
--success-eco: #52b788; /* Eco green */
--warning: #f4a261; /* Warning orange */
--error: #c44536; /* Error red */
--info: #4a90e2; /* Info blue */
```

#### Typography

- **Headers:** Poppins (600, 700)
- **Body:** Inter (400, 500)
- **Accent/Logo:** Fraunces (700)

#### Logo

- **Mark:** Abstract stylized leaf (subtle Andean mountain shape integrated)
- **Wordmark:** "La Yapa" in Poppins Bold
- **Variants:** Full logo, mark only, wordmark only, monochrome

#### Mascot — Yapi 🦙

- **Character:** Friendly minimalist geometric llama
- **Style:** Soft rounded shapes, cream/beige body, terracotta poncho with subtle Andean pattern, golden bag
- **Personality:** Warm, optimistic, helpful, slightly playful
- **Usage:** Empty states, achievements, onboarding, badges, push notifications, marketing
- **NOT in:** App icon, logo, splash screen
- **States needed:** Happy, sleepy, celebrating, sad, chef, runner, eco-warrior

---

### 💰 Monetization Strategy

**Phase 1 (MVP — Months 1-6):**

- 15-20% commission per sale
- FREE for mercado vendors & farmers (first 12 months)

**Phase 2 (Months 6-12):**

- Business Freemium: Free basic / Premium $20-30/mo (analytics, featured placement, multi-location)
- Featured listing boosts: $1-5

**Phase 3 (12+ months):**

- "La Yapa Plus" consumer subscription ($1.99/mo): No ads, 24h early access, exclusive bags, 5% cashback, exclusive badges, monthly free suspended meal donation, priority support
- Ad-supported free tier (eco-aligned brands, clearly marked "Patrocinado")

---

### 🚀 Tech Stack (LOCKED IN)

| Layer                | Choice                                                                                  |
| -------------------- | --------------------------------------------------------------------------------------- |
| Mobile               | React Native 0.81 + Expo SDK 54 + React 19 (New Architecture, Reanimated 4)             |
| State Management     | Zustand + React Query (TanStack Query)                                                  |
| Navigation           | Expo Router (file-based)                                                                |
| Backend              | Django 5.x + Django REST Framework                                                      |
| Database             | PostgreSQL 16                                                                           |
| Authentication       | Django Simple JWT + django-allauth (Google, Apple)                                      |
| Admin Panel          | Django Admin (customized with Jazzmin/Unfold) + custom DRF endpoints for business panel |
| Business Panel       | Next.js 14 (App Router) — web-based                                                     |
| Maps                 | Mapbox (mobile SDK + Geocoding API)                                                     |
| Payments             | PayPhone + DeUna (MVP); Kushki (Phase 2 for Apple/Google Pay + intl cards)              |
| File Storage         | Cloudflare R2 (S3-compatible)                                                           |
| Push Notifications   | Expo Push Notifications                                                                 |
| Email                | Resend                                                                                  |
| Hosting              | Railway (MVP), portable to AWS/GCP via Docker                                           |
| Error Tracking       | Sentry                                                                                  |
| Analytics            | PostHog (cloud free tier)                                                               |
| Electronic Invoicing | Dátil or Contífico (SRI integration)                                                    |
| CI/CD                | GitHub Actions                                                                          |
| Languages            | Spanish (default) + English (i18next on mobile, django-modeltranslation on backend)     |
| Monorepo Tool        | pnpm workspaces + Turborepo                                                             |

---

### 🗂️ Monorepo Structure

```
la-yapa/
├── apps/
│   ├── mobile/                  # React Native + Expo (consumer + business apps)
│   │   ├── src/
│   │   │   ├── app/             # Expo Router routes
│   │   │   ├── components/      # UI components
│   │   │   ├── features/        # Feature-based modules
│   │   │   ├── lib/             # Utilities, API client
│   │   │   ├── hooks/
│   │   │   ├── stores/          # Zustand stores
│   │   │   ├── theme/           # Design tokens, colors
│   │   │   ├── locales/         # i18n (es, en)
│   │   │   └── assets/          # Images, mascot illustrations, fonts
│   │   ├── android/             # Expo prebuild native scaffolding (committed — see posture below)
│   │   ├── ios/                 # Expo prebuild native scaffolding (committed once iOS comes online)
│   │   ├── app.json
│   │   └── package.json
│   │
│   ├── admin/                   # Next.js 14 admin/business dashboard
│   │   ├── src/
│   │   │   ├── app/             # Next.js App Router
│   │   │   ├── components/
│   │   │   ├── lib/
│   │   │   └── styles/
│   │   └── package.json
│   │
│   └── api/                     # Django REST API
│       ├── config/              # Django settings
│       ├── apps/
│       │   ├── users/
│       │   ├── businesses/
│       │   ├── bags/            # Surprise + specific listings
│       │   ├── orders/
│       │   ├── payments/
│       │   ├── reviews/
│       │   ├── notifications/
│       │   ├── gamification/
│       │   ├── suspended_meals/
│       │   ├── impact/
│       │   ├── geo/             # Mapbox integration
│       │   └── core/            # Shared utils
│       ├── manage.py
│       ├── requirements.txt
│       └── Dockerfile
│
├── packages/
│   ├── shared-types/            # TypeScript types shared between mobile/admin
│   ├── ui/                      # Shared design tokens
│   └── eslint-config/
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── design-system.md
│   ├── mascot-guidelines.md
│   ├── deployment.md
│   └── legal/
│       ├── privacy-policy.md
│       ├── terms-of-service.md
│       └── business-agreement.md
│
├── .github/workflows/           # CI/CD
├── docker-compose.yml
├── turbo.json
├── pnpm-workspace.yaml
└── README.md
```

---

### 🤖 Native scaffolding posture

`apps/mobile/android/` (and `apps/mobile/ios/` once iOS comes online) is
**committed to git**, not regenerated per-checkout. Rationale:

- **Reproducibility.** A fresh `git clone && pnpm install && expo run:android`
  builds an identical APK across machines and CI without depending on
  `expo prebuild`'s SDK-version-dependent output.
- **Pinning.** The Gradle wrapper version, AGP version, Kotlin version, NDK
  version, package id (`ec.layapa.app`), debug keystore, splash assets, and
  app icon resources are all canonical — they should not silently change
  when a contributor upgrades Expo CLI locally.
- **Native edit headroom.** When we eventually add custom Kotlin/Swift
  modules (payment SDKs, deep-link handlers, push channels), those edits
  live in `android/`/`ios/` and must be tracked.
- **CI parity.** GitHub Actions builds the same native tree the dev built
  locally; no "works on my machine" gaps.

What's **not** committed (per repo `.gitignore`):

- `apps/mobile/android/.gradle/`, `.kotlin/`, `build/`, `app/build/`,
  `app/.cxx/` — per-build output, regenerated every run.
- `apps/mobile/android/local.properties` — machine-specific SDK paths.
- `apps/mobile/ios/Pods/`, `ios/build/`, `ios/.xcode.env.local` — same
  rationale (CocoaPods install output + per-machine Xcode env).

The `apps/mobile/android/app/debug.keystore` file **is** committed — it's
the canonical Android-wide debug keystore (public key, well-known across
every Android dev environment). It is **not** a production signing key;
release signing keys must never be committed and will live in Expo EAS
secrets when release builds come online.

Regenerating the tree from scratch (e.g. after an Expo SDK upgrade):

```bash
pnpm --filter @layapa/mobile exec expo prebuild --clean --platform android
```

Then review the diff carefully — `--clean` overwrites every file, including
intentional edits.

---

### 📊 Database Schema (Core Models)

```python
# === USERS ===
User(AbstractUser)
    - email (unique, primary login)
    - phone
    - role (consumer | business_owner | admin | sales_rep)
    - language (es | en)
    - is_premium (bool, Phase 3)
    - premium_expires_at
    - created_at

ConsumerProfile (OneToOne with User)
    - first_name, last_name
    - avatar_url
    - default_location (PointField — Mapbox)
    - default_address
    - dietary_preferences (M2M with DietaryTag)
    - notifications_settings (JSON)
    - referral_code (unique)
    - referred_by (FK self, nullable)

# === BUSINESSES ===
Business
    - owner (FK User)
    - name
    - business_type (restaurant | bakery | supermarket | hotel | mercado | farmer | other)
    - tier (formal | informal) # formal = RUC required; informal = mercados/farmers
    - description
    - logo_url, cover_url
    - phone, email, website
    - status (pending | approved | suspended | rejected)
    - rejection_reason
    - approved_by (FK User, nullable)
    - approved_at
    - payout_frequency (weekly | monthly)
    - payout_method (bank_transfer | de_una)
    - bank_account (encrypted JSON)
    - commission_rate (decimal, default 0.18)
    - created_at

BusinessLocation
    - business (FK Business)
    - name (e.g., "Sucursal Centro")
    - address
    - location (PointField)
    - phone
    - is_active
    - hours_of_operation (JSON)

BusinessVerification
    - business (FK Business)
    - ruc_number (nullable)
    - ruc_document_url (nullable)
    - cedula_number
    - cedula_document_url
    - selfie_with_cedula_url (for informal tier)
    - permiso_funcionamiento_url (nullable)
    - arcsa_url (nullable)
    - bank_proof_url
    - business_photo_url (for informal)
    - food_safety_terms_accepted_at

# === BAGS / LISTINGS ===
Bag
    - business_location (FK BusinessLocation)
    - type (surprise | specific)
    - title (auto-generated for surprise, custom for specific)
    - description
    - image_url (multi for specific items)
    - original_price (Decimal)
    - sale_price (Decimal)
    - quantity_available
    - quantity_total (snapshot of initial qty)
    - dietary_tags (M2M)
    - allergen_warnings (M2M)
    - pickup_window_start (DateTime, flexible chosen by business)
    - pickup_window_end (DateTime)
    - is_active
    - is_suspended_meal_eligible (bool)
    - created_at

    # Validation: sale_price <= 0.5 * original_price, sale_price >= 1.50

DietaryTag
    - name (vegetarian, vegan, gluten_free, sin_lactosa, organico, halal, kosher, etc.)
    - icon_name

AllergenTag
    - name (mani, gluten, lacteos, frutos_secos, mariscos, huevo, soya, etc.)
    - icon_name

# === ORDERS ===
Order
    - consumer (FK User)
    - bag (FK Bag)
    - business_location (FK BusinessLocation, snapshot)
    - quantity
    - original_price_snapshot
    - sale_price_snapshot
    - total_paid
    - platform_commission
    - business_payout_amount
    - pickup_code (random 4-digit)
    - pickup_qr_token (UUID)
    - status (pending_payment | paid | ready_for_pickup | completed | cancelled | refunded | expired)
    - cancelled_by (consumer | business | admin | system)
    - cancelled_at
    - cancellation_reason
    - picked_up_at
    - payment_method
    - payment_provider_ref
    - created_at

# === PAYMENTS ===
PaymentTransaction
    - order (FK Order)
    - provider (payphone | de_una | kushki | stripe)
    - provider_transaction_id
    - amount
    - currency (default USD)
    - status (pending | success | failed | refunded)
    - raw_response (JSON)
    - created_at

Payout
    - business (FK Business)
    - period_start, period_end
    - total_amount
    - total_orders
    - status (pending | approved | processing | paid | failed)
    - approved_by (FK User)
    - approved_at
    - paid_at
    - bank_reference
    - created_at

PayoutLineItem
    - payout (FK Payout)
    - order (FK Order)
    - amount
    - type (sale | refund_deduction | bonus_credit_deduction)

# === REVIEWS ===
Review
    - order (FK Order, OneToOne)
    - consumer (FK User)
    - business_location (FK)
    - rating (1-5)
    - comment (optional, max 500 chars)
    - created_at
    - is_visible (admin moderation)

# === NOTIFICATIONS ===
NotificationPreference
    - user (FK User)
    - favorite_business_new_bags (bool)
    - last_minute_deals (bool)
    - pickup_reminders (bool)
    - order_updates (bool)
    - achievements (bool)
    - marketing (bool)

PushToken
    - user (FK User)
    - token
    - platform (ios | android)
    - is_active

# === GAMIFICATION ===
Badge
    - name, description, icon_url
    - category (saver | streak | community | explorer | premium)
    - criteria (JSON, e.g., {meals_saved: 10})
    - rarity (common | rare | epic | legendary)

UserBadge
    - user (FK User)
    - badge (FK Badge)
    - earned_at

UserLevel
    - user (OneToOne User)
    - level_name (bronce | plata | oro | cotopaxi | galapagos)
    - xp_total
    - meals_rescued
    - kg_saved
    - co2_saved_kg
    - money_saved_usd
    - current_streak_weeks
    - longest_streak_weeks

Leaderboard
    - scope (friends | city | nationwide)
    - period (weekly | monthly | all_time)
    # Computed dynamically via queries

# === SUSPENDED MEALS ===
SuspendedMealDonation
    - donor (FK User)
    - amount
    - bag (FK Bag, nullable) # specific bag or general pool
    - status (active | claimed | expired)
    - claimed_by_business (FK BusinessLocation, nullable)
    - claimed_at
    - is_anonymous (bool, default True)
    - created_at

SuspendedMealClaim
    - donation (FK SuspendedMealDonation)
    - business_location (FK)
    - beneficiary_notes (vendor notes, optional)
    - claimed_at

# === FAVORITES ===
Favorite
    - user (FK User)
    - business_location (FK)
    - created_at

# === IMPACT ===
ImpactStat (cached per user, updated on order completion)
    - user
    - meals_rescued
    - kg_food_saved
    - co2_kg_saved (calculated: kg_food * 2.5)
    - money_saved
    - last_calculated_at

# === REFERRALS ===
Referral
    - referrer (FK User)
    - referred (FK User)
    - status (pending | completed) # completed when referred makes first purchase
    - reward_credit_amount
    - completed_at

# === DISPUTES ===
Dispute
    - order (FK Order)
    - opened_by (consumer | business)
    - reason
    - description
    - evidence_urls (JSON list)
    - status (open | under_review | resolved_refund | resolved_no_refund | closed)
    - resolution_notes
    - resolved_by (FK User)
    - resolved_at
    - created_at

# === ADMIN / SALES ===
SalesRepProfile (Phase 2)
    - user (OneToOne)
    - businesses_onboarded (M2M)
    - commission_rate

# === ADS (Phase 3) ===
AdCampaign
    - business (FK)
    - type (featured_listing | banner | sponsored_search)
    - start_date, end_date
    - budget
    - status

# === ELECTRONIC INVOICING ===
Invoice
    - order (FK Order)
    - type (consumer_invoice | platform_commission_invoice)
    - sri_authorization_number
    - sri_xml_url
    - pdf_url
    - status (pending | authorized | rejected)
    - created_at
```

---

### 🔐 Authentication Flow

- Email + password (default)
- Google OAuth
- Apple Sign In
- JWT tokens (access 15min, refresh 7 days)
- Password reset via email
- Email verification required
- Optional phone verification (Phase 2)

---

### 🌐 API Design Principles

- RESTful, versioned: `/api/v1/...`
- JSON responses with consistent envelope:

```json
{
  "success": true,
  "data": {...},
  "message": "...",
  "errors": null
}
```

- Pagination: cursor-based for feeds, offset for admin
- Rate limiting (100 req/min for users, 1000 for businesses)
- All endpoints require auth except `/auth/*`, `/public/*`
- OpenAPI/Swagger auto-generated via drf-spectacular
- Error codes documented (`AUTH_001`, `PAY_002`, etc.)

#### Endpoint Categories

```
/api/v1/auth/                      # Login, register, refresh, password reset
/api/v1/users/me                   # Current user profile
/api/v1/consumer/                  # Consumer-specific
  ├── /bags                        # Browse bags (with filters, geo radius)
  ├── /bags/{id}
  ├── /favorites
  ├── /orders
  ├── /reviews
  ├── /impact
  ├── /referrals
  ├── /badges
  └── /suspended-meals/donate

/api/v1/business/                  # Business-specific (mobile + web)
  ├── /me
  ├── /locations
  ├── /bags                        # CRUD
  ├── /orders                      # Active + history
  ├── /orders/{id}/confirm-pickup  # QR or PIN
  ├── /reviews
  ├── /analytics
  ├── /payouts
  └── /suspended-meals/dispatch    # Mark as dispatched to needy person

/api/v1/admin/                     # Admin panel (sales team)
  ├── /businesses/pending
  ├── /businesses/{id}/approve
  ├── /payouts/pending
  ├── /payouts/{id}/approve
  ├── /disputes
  ├── /users
  └── /analytics/dashboard

/api/v1/payments/                  # Payment provider webhooks
  ├── /payphone/webhook
  ├── /de-una/webhook
  └── /kushki/webhook

/api/v1/geo/                       # Geo + maps
  ├── /search                      # Mapbox proxy
  └── /reverse                     # Reverse geocoding

/api/v1/notifications/
  ├── /register-token
  └── /preferences
```

---

### 🔔 Notifications Strategy

**Push (Expo) — Consumers:**

- 🆕 New bag from favorite business
- ⏰ Last-minute deal (bag expiring in < 2h, auto -50%)
- 📍 Pickup reminder (1h + 30min before window closes)
- ✅ Order confirmation
- 🏆 Badge earned
- 🎁 Suspended meal accepted (anonymous notification: "Your gift fed someone today!")

**Push — Businesses:**

- 🔔 New order (loud, high priority)
- ❌ Order cancelled by user
- ⭐ New review received
- 💰 Payout processed
- 🎁 Suspended meal bag dispatched

**Email (Resend):**

- Welcome email (consumer + business)
- Email verification
- Password reset
- Weekly digest (Phase 2)
- Monthly impact report
- Payout receipts
- Tax documents (annual)

---

### 🗺️ Map & Discovery

- **Default radius:** 3km
- **Location:** Required (graceful fallback to city-level if denied)
- **Map view:** Mapbox with custom Andean-themed style
- **Markers:** Business locations with bag count badge
- **Filters:** Type, dietary tags, allergens, price range, pickup time, rating
- **Sort:** Distance, price, rating, ending soon
- **Search:** Mapbox Geocoding for address/place search

---

### 📱 Mobile App Structure (Expo Router)

```
app/
├── (auth)/
│   ├── welcome.tsx
│   ├── login.tsx
│   ├── register.tsx
│   ├── forgot-password.tsx
│   └── onboarding.tsx
├── (consumer)/
│   ├── _layout.tsx               # Bottom tabs
│   ├── index.tsx                 # Home feed (list + map toggle)
│   ├── map.tsx
│   ├── search.tsx
│   ├── bag/[id].tsx
│   ├── checkout/[bagId].tsx
│   ├── orders/
│   │   ├── index.tsx
│   │   └── [id].tsx              # Order detail with QR + PIN
│   ├── favorites.tsx
│   ├── impact.tsx
│   ├── badges.tsx
│   ├── leaderboard.tsx
│   ├── suspended-meals.tsx
│   └── profile/
│       ├── index.tsx
│       ├── edit.tsx
│       ├── settings.tsx
│       ├── notifications.tsx
│       ├── referrals.tsx
│       └── premium.tsx           # Phase 3
├── (business)/
│   ├── _layout.tsx               # Bottom tabs
│   ├── dashboard.tsx
│   ├── bags/
│   │   ├── index.tsx
│   │   ├── new.tsx
│   │   └── [id].tsx
│   ├── orders/
│   │   ├── index.tsx
│   │   ├── active.tsx
│   │   ├── history.tsx
│   │   └── scanner.tsx           # QR scan + PIN entry
│   ├── analytics.tsx
│   ├── reviews.tsx
│   ├── payouts.tsx
│   └── settings/
│       ├── index.tsx
│       ├── locations.tsx
│       └── profile.tsx
└── _layout.tsx                   # Root layout with theme provider
```

**Role-based routing:** After login, redirect to `(consumer)` or `(business)` based on user role.

---

### 🖥️ Admin Panel (Next.js) Pages

```
/login
/dashboard                        # KPIs overview
/businesses
  /pending
  /approved
  /suspended
  /{id}                           # Detail + actions
/users
  /consumers
  /admins
  /sales-reps                     # Phase 2
/orders                           # Search + filter
/payouts
  /pending
  /history
  /{id}                           # Approve + generate CSV
/disputes
  /open
  /resolved
/bags                             # All bags (moderation)
/reviews                          # Moderation queue
/suspended-meals                  # Pool + history
/gamification
  /badges
  /levels
/content                          # FAQ, banners, push campaigns
/analytics
  /revenue
  /impact
  /users
/settings
  /commission-rates
  /platform-config
```

---

### 🎮 Gamification System

**Levels (XP-based):**
| Level | Name | XP Required | Theme |
|---|---|---|---|
| 1 | Bronce | 0 | Starting |
| 2 | Plata | 500 | First milestones |
| 3 | Oro | 2,000 | Loyal saver |
| 4 | Cotopaxi | 5,000 | Champion |
| 5 | Galápagos | 15,000 | Legendary |

**XP earned per:**

- Bag rescued: 50 XP
- Review left: 25 XP
- Referral completed: 200 XP
- Suspended meal donated: 100 XP
- Weekly streak (4 weeks): 300 XP bonus

**Badges (initial set, ~30):**

- 🌱 _Primer Rescate_ — First bag bought
- 🍞 _Pan de Oro_ — 10 bakery bags
- 🥗 _Veggie Hero_ — 20 vegetarian bags
- 🏃 _Maratón Eco_ — 4-week streak
- 💝 _Corazón Generoso_ — First suspended meal donated
- 🌎 _Salvador del Planeta_ — 50kg CO₂ saved
- 🦙 _Amigo de Yapi_ — Profile completed + 5 bags
- 🌋 _Conquistador del Cotopaxi_ — Reach Cotopaxi level
- 🐢 _Guardián de Galápagos_ — Reach Galápagos level
- 👥 _Embajador_ — 5 referrals completed

**Leaderboards:**

- Friends (Phase 2 — needs friend system)
- City (weekly, monthly, all-time)
- Nationwide (monthly, all-time)
- Opt-in only (privacy default OFF)

---

### 🌍 Impact Tracking

**Per user (and platform-wide aggregated):**

- 🍽️ Meals rescued (bag count)
- ⚖️ Kg of food saved (estimated: surprise bags = 1.5kg avg, specific = manual entry)
- 💨 CO₂ saved (kg_food × 2.5)
- 💰 Money saved (original_price - sale_price)

**Display:**

- Profile screen
- Monthly push: "¡Salvaste 12 comidas este mes!"
- Yearly recap (Spotify Wrapped style with Yapi)
- Shareable Instagram story templates

---

### 🤝 Suspended Meals Flow

1. **Donor:** Buys a bag OR donates fixed amount → marks "Quiero donar"
2. **System:** Marks bag as "suspended" + adds to public counter
3. **Business notified:** "Tienes 1 comida suspendida disponible"
4. **Vendor:** When needy person arrives, taps "Despachar comida suspendida" in business app (no QR/PIN required, honor system)
5. **System:** Marks donation as claimed, anonymous push to donor: "Tu yapa alimentó a alguien hoy 🌱"
6. **Public counter updates:** "12,453 comidas donadas por la comunidad"

**Anti-abuse:**

- Max 5 suspended meals per business location per day
- Admin can flag suspicious businesses
- Random audits via admin panel

---

### 💳 Payment Architecture

**Abstract Provider Pattern:**

```python
# apps/payments/providers/base.py
class PaymentProvider(ABC):
    @abstractmethod
    def create_charge(self, order, payment_method): ...

    @abstractmethod
    def refund(self, transaction_id, amount): ...

    @abstractmethod
    def handle_webhook(self, payload): ...

# apps/payments/providers/payphone.py
class PayPhoneProvider(PaymentProvider): ...

# apps/payments/providers/de_una.py
class DeUnaProvider(PaymentProvider): ...

# apps/payments/providers/kushki.py
class KushkiProvider(PaymentProvider): ...  # Phase 2

# apps/payments/services.py
def process_payment(order, provider_name, payment_method):
    provider = get_provider(provider_name)
    return provider.create_charge(order, payment_method)
```

**Payout Workflow:**

1. Order completed + 24h dispute window passed → credit business balance
2. Cron job runs daily checks for due payouts (weekly Mon / monthly 1st)
3. Generates `Payout` with `status=pending`
4. Admin reviews + approves in admin panel
5. CSV generated for bank upload (MVP)
6. Admin marks as paid + uploads bank reference
7. Business notified

---

### 🧪 Testing Strategy

**Backend (Django):**

- pytest + pytest-django
- 80% coverage minimum for `apps/orders`, `apps/payments`, `apps/businesses`
- Factory Boy for fixtures
- Mock payment providers in tests
- Integration tests for critical flows (signup → order → payout)

**Mobile (React Native):**

- Jest for unit tests
- React Native Testing Library for components
- Detox or Maestro for E2E (key flows: signup, browse, buy, pickup)
- Storybook for design system components

**Admin (Next.js):**

- Jest + Testing Library
- Playwright for E2E

**CI/CD checks:**

- Lint (ESLint + Ruff)
- Type check (TypeScript + mypy)
- Tests
- Build success
- Security scan (npm audit + safety)

---

### 🚢 Deployment & DevOps

**Environments:**

- `development` (local)
- `staging` (Railway, separate project)
- `production` (Railway → AWS/GCP at scale)

**Docker:**

- All services containerized
- `docker-compose.yml` for local dev (Postgres, Redis, MailHog)

**CI/CD (GitHub Actions):**

- PR → Run tests + lint
- Merge to `main` → Deploy to staging
- Tagged release → Deploy to production
- Mobile: EAS Build + EAS Submit (Expo Application Services)

**Monitoring:**

- Sentry (errors)
- Better Stack (uptime + logs)
- PostHog (product analytics)

**Backups:**

- Daily Postgres backups to Cloudflare R2
- 30-day retention

---

### 🔒 Security & Compliance

- HTTPS everywhere
- Encrypted bank details (Fernet)
- Rate limiting + bot protection
- Input validation everywhere (DRF serializers + Zod on mobile)
- SQL injection prevented (ORM)
- XSS protected (DRF + React defaults)
- CORS configured strictly
- Secrets in env vars (never committed)
- GDPR-like data export/deletion endpoints
- Ecuador Ley Orgánica de Protección de Datos Personales (LOPDP) compliance
- Food safety terms accepted by business at signup

---

### 📜 Legal Documents (Placeholders to Generate)

```
docs/legal/
├── privacy-policy-es.md          # Política de Privacidad (LOPDP compliant)
├── privacy-policy-en.md
├── terms-of-service-es.md        # Términos y Condiciones
├── terms-of-service-en.md
├── business-agreement-es.md      # Acuerdo de Socio Comercial
├── food-safety-terms-es.md       # Responsabilidad sobre seguridad alimentaria
├── refund-policy-es.md
└── cookie-policy-es.md
```

⚠️ **Note in code:** "These are placeholder templates. Have a lawyer in Ecuador review before launch."

---

### 📱 App Store Listing

**App Name:** La Yapa  
**Subtitle (ES):** Comida rescatada con yapa  
**Subtitle (EN):** Rescued food, sustainable savings

**Description (ES):**

> 🌱 La Yapa es la primera app de Ecuador para rescatar comida en buen estado a precios increíbles. Conecta con restaurantes, panaderías, supermercados, hoteles, mercados y agricultores locales que venden "bolsas sorpresa" con productos del día a 1/3 de su precio.
>
> ✨ ¿Por qué La Yapa?
> • Ahorra hasta 70% en comida deliciosa
> • Reduce el desperdicio alimentario en Ecuador
> • Apoya negocios locales y mercados tradicionales
> • Comida suspendida: dona una comida para quien lo necesite
> • Rastrea tu impacto: comidas rescatadas, CO₂ evitado, dinero ahorrado
> • Gana logros con Yapi, tu compañero de aventura
>
> Únete a la comunidad que está rescatando el planeta, una yapa a la vez. 🦙🌎

**Keywords (ES):** comida, ecuador, descuento, sustentable, eco, restaurantes, ahorro, desperdicio, cuenca, food, mercados

**Categories:** Food & Drink (primary), Lifestyle (secondary)

---

### 📅 Phased Development Roadmap (3-5 months)

#### **Phase 0 — Foundation (Week 1-2)**

- Monorepo setup (Turborepo + pnpm)
- Backend project (Django + DRF + Postgres + Docker)
- Mobile project (Expo + design system + theme)
- Admin project (Next.js scaffolding)
- CI/CD basic setup
- Design system implementation (colors, typography, components)
- Logo + Yapi mascot illustrations (placeholder, refine later)
- Database models + migrations
- Authentication (email + Google + Apple)

#### **Phase 1 — Consumer Core MVP (Weeks 3-6)**

- Browse bags (list + map view)
- Filters (dietary, allergens, distance, price)
- Bag detail screen
- Favorites
- Checkout flow (PayPhone + DeUna)
- Order management (pending → ready → completed)
- QR + PIN pickup
- Reviews (stars + optional comment)
- Push notifications (Expo)
- Profile + settings
- i18n (ES + EN)

#### **Phase 2 — Business Core MVP (Weeks 7-9)**

- Business onboarding (formal + informal tiers)
- Business mobile app (bag CRUD, order management, scanner)
- Sales rep admin flow (create businesses)
- Manual approval workflow in admin panel
- Payout balance calculation
- Business analytics (basic)

#### **Phase 3 — Admin & Operations (Weeks 10-11)**

- Admin dashboard (Next.js)
- Business approval queue
- Payout approval + CSV export
- Dispute management
- User management
- Platform analytics

#### **Phase 4 — Community & Engagement (Weeks 12-14)**

- Suspended meals (donate + dispatch)
- Gamification (badges, levels, XP)
- Impact tracker (personal + platform-wide)
- Leaderboards
- Referral program

#### **Phase 5 — Polish & Launch (Weeks 15-18)**

- Electronic invoicing integration (Dátil/Contífico)
- Performance optimization
- E2E testing
- App Store + Play Store submission
- Beta testing in Cuenca (50 users + 10 businesses)
- Marketing site (landing page)
- Press kit + launch campaign

#### **Phase 6 — Post-Launch (Months 5-6+)**

- Loyalty program
- In-app chat with business
- Kushki integration (Apple/Google Pay)
- Sales rep individual logins + attribution
- "La Yapa Plus" subscription
- Ad placements
- City expansion (Quito, Guayaquil)

---

### ✅ Definition of Done for MVP

- [ ] Consumer can register, login, browse, buy, and pickup a bag end-to-end
- [ ] Business can register, get approved, post bags, receive orders, confirm pickup
- [ ] Admin can approve businesses, process payouts, manage disputes
- [ ] Payment via PayPhone + DeUna works in production
- [ ] Push notifications work on iOS + Android
- [ ] Map shows nearby bags within 3km
- [ ] Suspended meals can be donated + dispatched
- [ ] Reviews + ratings functional
- [ ] Impact tracker shows personal stats
- [ ] Dark mode + light mode work
- [ ] ES + EN translations complete for core flows
- [ ] All legal docs in place
- [ ] App approved on App Store + Play Store
- [ ] Sentry capturing errors
- [ ] At least 80% test coverage on payments + orders
- [ ] Privacy policy + terms accessible in app
