# 🤖 Crypto Quest Telegram Bot

A ready-to-sell **Telegram VIP subscription bot** for channel owners. Sell
Premium memberships to your audience: customers pay in crypto, get Premium, and
are **auto-added** to your private VIP channel. Includes a full owner admin
panel.

---

## ✨ Features

- 🛒 **Multi-product shop** — sell as many products as you want, each with its
  **own price**, added/managed **right from Telegram** (Owner Menu → Add/Remove):
  - **Channel subscriptions** (VIP access, any price/length) and
  - **Digital products** (e-book, course, invite link, anything) auto-delivered.
- 💰 **Manual crypto payment** — BSC (recommended), Ethereum, Polygon. Payouts go
  straight to the **buyer's own wallet**.
- 💳 **NOWPayments gateway (optional)** — card & 230+ crypto coins, auto
  invoices. No card required to receive crypto.
- 🔓 **Auto VIP-channel membership** — paying customers are added via an invite
  link; expired subscriptions are auto-kicked (6h sweep).
- 🛠 **Owner admin panel** — `/stats`, `/products`, `/broadcast`,
  `/add_member`, `/kick`, `/set_price`.
- 🌍 **Configurable via `.env`** (token, wallet, owner) **+ `config.py`
  `PRODUCTS`** (your products & prices).
- 🛡 **No external packages** — runs on plain Python (standard library only),
  works even from restricted networks.
- 📦 **Clean architecture** — `config.py` (settings + products), `lang.py` (all
  text) and `bot.py` (logic) are separated so the buyer or a dev can extend it
  easily.

---

## 🚀 Quick start

```bash
# 1. Put the scripts/ folder anywhere
# 2. Copy the template and fill in YOUR values
cp .env.example .env      # (Windows: copy .env.example .env)

# 3. Set your bot token + wallet in .env

# 4. Run
python bot.py
```

See **[INSTALL.md](INSTALL.md)** for the full step-by-step guide (creating the
bot, the VIP channel, NOWPayments, owner setup, troubleshooting).

---

## 🧩 What you get

```
scripts/
  bot.py             the bot (run: python bot.py)
  config.py          all settings (from .env)
  lang.py            all messages & buttons (reword/translate here)
  admin.py           owner commands
  channel_access.py  auto VIP-channel membership
  nowpayments.py     card/crypto gateway
  broadcast.py       push reports/messages to subscribers
  .env.example       configuration template
INSTALL.md           buyer install guide
ARCHITECTURE.md      developer guide
```

---

## ⚙️ Configuration

**Products** — add/change/remove them **from Telegram** (Owner Menu → Add
Product / Remove Product). No code editing needed. They're stored in
`products.json`. See `INSTALL.md` Step 4b.

**`.env`** — secrets & global settings:

| Key | Description |
|-----|-------------|
| `TELEGRAM_BOT_TOKEN` | your bot token from @BotFather |
| `CRYPTO_ADDRESS` | your wallet (BSC/ETH/Polygon) where payments go |
| `OWNER_CHAT_ID` | your Telegram id — gets the admin panel & Owner Menu |
| `CHANNEL_ID` / `CHANNEL_LINK` | (optional) VIP channel auto-membership |
| `NOWPAYMENTS_API_KEY` | (optional) card/crypto gateway |
| `COINGATE_AUTH_TOKEN` | (optional) web payment page gateway |

> `PRICE_USD` and `PREMIUM_DAYS` are kept only as fallbacks. Your real prices
> and durations are managed from the Telegram Owner Menu (stored in
> `products.json`).

---

## 🛠 Owner commands

`/stats` · `/products` · `/broadcast <text>` · `/add_member <id>` · `/kick <id>` · `/set_price <usd>` · `/admin`

---

## 📄 License / sale terms

This is a **single-site license** (see [LICENSE](LICENSE)).

- The buyer configures their own bot token, wallet, and channel. All customer
  payments go **directly to the buyer's own wallet** — the seller never touches
  funds.
- The buyer may use this bot **for their own channel / shop / business** and
  may modify its configuration freely.
- **Reselling, redistributing, or offering this software (or any modified copy)
  to third parties is NOT permitted.** Each site that runs the bot needs its own
  license.
- For a resellable / multi-site license, contact the author for a separate
  commercial agreement.

*Everything in this package is English and fully self-contained.*
