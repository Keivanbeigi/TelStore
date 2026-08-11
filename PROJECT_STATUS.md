# Crypto Quest Bot — Project Status (saved checkpoint)

> Refactored for maintainability. All work is committed to git and pushed.

## Current state (all DONE and verified ✅)

- **Bot:** `@ADNC_bot` (token id 8913353892) — polling works, connects to Telegram API.
- **Repo:** `github/` → github.com/Keivanbeigi/crypto-quest-report (master).
- **All code English** (customer-facing + comments). Bot token & settings in `scripts/.env` (gitignored).

## Architecture refactor (Phase "Quality" — DONE ✅)

The codebase was refactored into single-responsibility modules so a human can
extend it without hunting through one big file. **No customer-facing string or
config value is hard-coded in bot.py anymore.**

| File | Responsibility | Edit this to… |
|------|----------------|---------------|
| `config.py` | Every setting, loaded from `.env` | change token, price, wallet, owner, channel, networks |
| `lang.py` | Every customer message + button label | reword / translate the bot |
| `bot.py` | Telegram logic only (polling, menu, payment) | add/change behaviour |
| `admin.py` | Owner admin commands | change stats/broadcast/member mgmt |
| `channel_access.py` | VIP channel membership | how channel access is granted/revoked |
| `nowpayments.py` | NOWPayments gateway | change card/crypto payment integration |
| `broadcast.py` | Send reports to subscribers (cron) | change report delivery logic |

Key rules enforced:
- **No hard-coded UI text in bot.py** — all strings live in `lang.TXT` / `lang.BTN`.
- **No duplicated config/`.env` loading** — all modules import `config`.
- **No duplicated channel-grant logic** — one shared `grant_channel_access()` in bot.py.
- **Adding a network = edit `config.CRYPTO_NETWORKS` only** — buttons/keys auto-generate.

## Features (all ✅)
- English inline menu (Buy Premium / Free / Status / Help / Unsubscribe)
- Free + Premium subscription model
- Manual crypto payment: BSC (recommended) / Ethereum / Polygon, wallet in `.env`
- NOWPayments gateway module (optional, needs API key)
- Auto VIP channel membership (grant on payment, revoke on expiry, 6h sweep)
- Owner admin panel: `/stats`, `/broadcast`, `/add_member`, `/kick`, `/set_price`, `/admin`
- Stale-update drain (fixes 400), fast polling (sleep 0.3)

## Files (scripts/)
```
bot.py            - main bot (imports config + lang; no hard-coded strings)
config.py         - all settings from .env (single source of truth)
lang.py           - all customer-facing text + buttons
admin.py          - owner admin panel (uses config)
channel_access.py - VIP channel membership (uses config)
nowpayments.py    - NOWPayments gateway (uses config)
broadcast.py      - report broadcast script (uses config)
.env.example      - configuration template for buyers
.env              - real secrets (gitignored)
```

## Next (Phase 4 — Sales package)
- README install guide (step-by-step for buyer)
- Package for Fiverr / CodeCanyon / Sellix / Gumroad
- Set OWNER_CHAT_ID, test /stats /broadcast live
- Get a NOWPayments API key to activate the gateway button

## Verification
- All modules compile (`py_compile`) ✅
- Full import + functional smoke test passed (menus, keyboards, status, network labels) ✅
- Live Telegram `getMe` check passed (`@ADNC_bot`) ✅
