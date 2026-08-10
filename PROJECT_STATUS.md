# Crypto Quest Bot — Project Status (saved checkpoint)

> Saved for continuing tomorrow. All work is committed to git and pushed.

## Current state (all DONE and verified ✅)

- **Bot:** `@ADNC_bot` (token id 8913353892) — polling, running on this Windows box.
- **Repo:** `github/` → github.com/Keivanbeigi/crypto-quest-report (master, clean).
- **All code English** (customer-facing + comments). Bot token & settings in `scripts/.env` (gitignored).

## Phases completed

### Phase 1 — Base ✅
- English inline menu (Buy Premium / Free / Status / Help / Unsubscribe)
- Free + Premium subscription model
- Manual crypto payment: BSC (recommended) / Ethereum / Polygon, wallet in `.env`
- NOWPayments gateway module (optional, needs API key)
- Configurable via `.env` (sellable template) — `.env.example` documents all keys
- Stale-update drain (fixes 400), fast polling (sleep 0.3)
- `subscribers.json` gitignored (runtime data)

### Phase 2 — Auto VIP channel membership ✅
- `channel_access.py` — grant/revoke/check/sweep
- Grant on payment, revoke on unsubscribe, periodic sweep every 6h (expired → kicked)
- `CHANNEL_ID` / `CHANNEL_LINK` in `.env` (empty = membership disabled)

### Phase 3 — Owner admin panel ✅
- `admin.py` + owner commands in bot.py:
  - `/stats` — subscriber + revenue summary
  - `/broadcast <text>` — message all subscribers
  - `/add_member <user_id>` — grant premium 30d
  - `/kick <user_id>` — remove subscriber
  - `/set_price <usd>` — change price (current run)
  - `/admin` — list commands
- Owner gated by `OWNER_CHAT_ID` in `.env` (empty = locked)

## Files (scripts/)
- `bot.py` — main bot (polling, menu, payments, owner panel)
- `channel_access.py` — VIP channel membership
- `admin.py` — owner admin panel
- `nowpayments.py` — NOWPayments gateway (optional)
- `.env.example` — configuration template for buyers
- `.env` — real secrets (gitignored)

## Next (tomorrow)
- **Phase 4 — Sales package:**
  - README install guide (step-by-step for buyer)
  - Package for Fiverr / CodeCanyon / Sellix / Gumroad
  - Set OWNER_CHAT_ID, test /stats /broadcast live
  - Get a NOWPayments API key to activate the gateway button

## Verification
- Comprehensive ad-hoc verification scripts run & passed (25–45 checks each).
- Temp scripts cleaned up (`~/AppData/Local/Temp/hermes-verify-*.py` removed).