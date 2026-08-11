# Crypto Quest Bot — VIP Channel Bot (Roadmap)

> A sellable Telegram bot template: paid subscriptions + auto channel membership
> + owner admin panel. Sold to VIP channel owners on freelance sites (Fiverr,
> CodeCanyon, Sellix, Gumroad).

---

## Business model
- **We (builder/seller)** build a configurable Telegram bot template.
- **Buyer (VIP channel owner)** purchases the bot, puts their own settings in
  `.env` (token, wallet, channel id), runs it, and earns from their own
  subscribers.
- Each buyer's payments go to **their own** wallet. The bot is a template:
  everything is configured via `.env`.

---

## Phase 1 — Base (DONE ✅)
| Feature | Status |
|---------|--------|
| English inline menu | ✅ |
| Free / Premium subscription | ✅ |
| Manual crypto payment (BSC / Ethereum / Polygon) | ✅ |
| NOWPayments auto gateway (optional) | ✅ |
| Configurable via `.env` (token, wallet, price, NOWPayments) | ✅ |
| `.env.example` + clean code | ✅ |
| Stale-update drain (fixes 400), fast polling | ✅ |
| `subscribers.json` gitignored (runtime data) | ✅ |

## Phase 2 — Auto channel membership (DONE ✅)
- Bot must be an **admin of the channel** (owner adds it).
- On payment confirmed -> bot automatically **adds member** to VIP channel.
- On subscription expiry -> bot **removes** member.
- Periodic cron check for expiring subscriptions.

## Phase 3 — Owner admin panel (DONE ✅)
- Owner commands: `/stats`, `/broadcast`, `/add_member`, `/kick`, `/set_price`
- View subscriber count and revenue
- Broadcast to all subscribers
- Manual member management

## Phase 4 — Quality refactor (DONE ✅)
- Split monolith `bot.py` into single-responsibility modules
  (`config.py`, `lang.py`, `admin.py`, `channel_access.py`, `nowpayments.py`, `broadcast.py`)
- **No hard-coded UI text in logic** — all strings in `lang.py`
- **No duplicated `.env` loading** — all modules import `config.py`
- `ARCHITECTURE.md` — human-friendly developer guide
- Verified: all modules compile + functional smoke test + live `getMe` ✅

## Phase 5 — Sales package (NEXT)
- **README install guide** (step-by-step for the buyer)
- Deliverable: source + `.env.example` + install guide
- Publish on: Fiverr, CodeCanyon, Sellix, Gumroad

---

## Suggested pricing
| Package | Includes | Price |
|---------|----------|-------|
| Basic | Phase 1 | $20–$40 |
| Standard | Phase 1+2 (auto membership) | $50–$80 |
| Full | Phase 1+2+3 (admin panel) | $80–$150 |

## Sales platforms
- **Fiverr** — gig "Telegram VIP subscription bot"
- **CodeCanyon** — source code marketplace
- **Sellix / Gumroad** — direct sale with crypto/card payment
