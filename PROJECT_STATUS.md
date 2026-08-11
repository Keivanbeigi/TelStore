# Crypto Quest Bot — Project Status (saved checkpoint)

> Refactored for maintainability. All work is committed to git and pushed.

## Current state (all DONE and verified ✅)

- **Bot:** `@ADNC_bot` (token id 8913353892) — polling works, connects to Telegram API.
- **Repo:** `github/` → github.com/Keivanbeigi/crypto-quest-report (master, HEAD c683bab).
- **All code English** (customer-facing + comments). Bot token & settings in `scripts/.env` (gitignored).
- **Sale package:** `E:\My Documents\Crypto Quest\Crypto-Quest-Bot-v2.0.zip` (18 files, ZERO seller secrets — verified by scan).
- **Payments:** NOWPayments ACTIVE with real API key. Cloudflare fix applied (`nowpayments.py` sends browser User-Agent — api returns 403 error 1010 otherwise).
- **Auto-delivery:** `poll_pending_payments()` every 20s — IPN-like delivery WITHOUT a server (verified live with real key).
- **CoinGate:** REJECTED (requires Business verification) — docs/coingate.py kept as optional future option.

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

## Phase 5 — Multi-product shop ✅
- `config.PRODUCTS` catalogue — owner defines any products, each with its
  **own price** (no hard-coded single price).
- Shop menu (`🛒 Shop / Products`) generated automatically from `PRODUCTS`.
- Delivery kinds: `channel` (auto VIP-channel access) and `digital` (auto-send).
- Per-product prices flow through manual crypto and NOWPayments.
- Owner `/products` command lists the configured catalogue.
- Docs updated (`INSTALL.md` Step 4b, `ARCHITECTURE.md`, `README`).
- Verified: 16-check functional suite + live `getMe` + shop keyboard ✅

## Files (scripts/)
```
bot.py            - main bot (imports config + lang; no hard-coded strings)
config.py         - all settings + PRODUCTS catalogue (single source of truth)
lang.py           - all customer-facing text + buttons
admin.py          - owner admin panel (uses config)
channel_access.py - VIP channel membership (uses config)
nowpayments.py    - NOWPayments gateway (uses config, browser UA fix)
coingate.py       - optional CoinGate web gateway (uses config)
broadcast.py      - report broadcast script (uses config)
deploy_server.sh  - one-shot Ubuntu VPS installer (systemd, sudo helper)
check_bot.sh      - health check: 8 checks incl. live getMe + NOWPayments (WSL-verified 8/8)
run_bot.sh        - python3 launcher used by systemd / tasks
.env.example      - configuration template for buyers
.env              - real secrets (gitignored)
```

## Next (Phase 6 — Sales launch, PAUSED by owner)
- Owner decided: **do NOT launch sales yet** — finish later.
- Windows task `CryptoQuestBot` exists but is DISABLED; WSL service also disabled
  (WSL idle-shuts-down, so production should use Windows Task or a VPS).
- Planned price: **$29** (lowest competitive point for this feature set).
- Deploy target when ready: **Ubuntu 24.04 LTS VPS** (deploy_server.sh one-shot).

## Verification
- All modules compile (`py_compile`) ✅
- Full import + functional smoke test passed (menus, keyboards, status, network labels) ✅
- Live Telegram `getMe` check passed (`@ADNC_bot`) ✅
