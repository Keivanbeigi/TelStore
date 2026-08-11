# Crypto Quest Bot — Install Guide for Buyers

> **A ready-to-sell Telegram subscription bot.** Sell Premium memberships to your
> VIP Telegram channel: customers pay in crypto (manual wallet or NOWPayments),
> get Premium, and are auto-added to your private channel. Owner panel included.

This guide is written for a **non-technical buyer**. Follow the steps in order
and you'll have a working bot in ~15 minutes.

---

## Table of contents
1. [What you get](#what-you-get)
2. [Before you start (what you need)](#before-you-start)
3. [Create your Telegram bot](#step-1-create-your-telegram-bot)
4. [Install Python](#step-2-install-python)
5. [Configure the bot](#step-3-configure-the-bot)
6. [Run the bot](#step-4-run-the-bot)
7. [(Optional) Auto VIP channel](#step-5-optional-setup-your-vip-channel)
8. [(Optional) NOWPayments card/crypto gateway](#step-6-optional-enable-nowpayments)
9. [Owner commands](#owner-commands)
10. [Troubleshooting](#troubleshooting)

---

## What you get

```
scripts/
  bot.py             the bot (runs with:  python bot.py)
  config.py          reads all settings from .env
  lang.py            all messages & buttons (reword/translate here)
  admin.py           owner commands
  channel_access.py  auto VIP-channel membership
  nowpayments.py     card/crypto payment gateway
  broadcast.py       push reports/messages to subscribers
  .env.example       template — copy to .env and fill your values
```

## Before you start (what you need)
- A computer that stays on (or a small VPS). The bot must keep running.
- Python 3.8+ installed.
- A Telegram account, a wallet address (BSC/ETH/Polygon), and (optional) a
  Telegram channel.

---

## Step 1 — Create your Telegram bot
1. Open Telegram, search for **@BotFather**.
2. Send `/newbot`, choose a name and a username (must end in `bot`).
3. BotFather gives you a **token** like `123456:ABC-DEF...`. Copy it — you'll
   need it in Step 3.

## Step 2 — Install Python
- Download from https://www.python.org/downloads/ (Windows: tick **"Add python
  to PATH"** during install). Verify with `python --version`.

## Step 3 — Configure the bot
1. Put the `scripts/` folder anywhere (e.g. `C:\crypto-quest-bot\`).
2. In the folder, **copy `.env.example` → name it `.env`**.
3. Open `.env` in a text editor (Notepad is fine) and fill in YOUR values:

```ini
# Your bot token from BotFather (required)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# Your wallet where customers send crypto (required for manual payment)
CRYPTO_ADDRESS=0xYourWalletAddressHere

# Monthly price in USD (optional, default 5)
PRICE_USD=5

# YOUR Telegram chat_id — the owner (gets /stats, /broadcast, etc.)
# Get it from @userinfobot. Leave empty to disable owner panel.
OWNER_CHAT_ID=123456789

# --- Optional: VIP channel auto-membership ---
# Make the bot an ADMIN of your channel (Management > Add admin > your bot,
# with "ban users" permission), then:
CHANNEL_ID=-1001234567890
CHANNEL_LINK=https://t.me/yourchannel

# --- Optional: NOWPayments card/crypto gateway (see Step 6) ---
NOWPAYMENTS_API_KEY=
```

> ⚠️ Never share your `.env` file or your bot token with anyone.

## Step 4 — Run the bot
1. Open a terminal / PowerShell in the `scripts/` folder.
2. Run:
   ```bash
   python bot.py
   ```
3. You'll see `✅ Bot running...`. Open Telegram, DM your bot, and tap
   **Start**. The menu appears.
4. Test **Buy Premium** → pick a network → it shows your wallet address.

> To stop the bot: press `Ctrl+C`. To run it 24/7 on a server, use `screen`,
> `tmux`, or a Windows service / systemd unit (see Troubleshooting).

## Step 5 — (Optional) Set up your VIP channel
1. Create your private channel. Add the bot as **Administrator** with the
   **"Ban users"** permission (so it can remove expired members).
2. Put the channel id in `CHANNEL_ID` (negative number, e.g. `-100...`).
   Find it via @username_to_id_bot or by forwarding a channel post to @getidsbot.
3. Restart `bot.py`. Now paying customers are **auto-added** to the channel via
   an invite link, and **auto-removed** when their subscription expires.

## Step 6 — (Optional) Enable NOWPayments
1. Register at https://nowpayments.io (supports many coins; no card needed for
   payout to crypto).
2. Get an **API key** from *Settings → API Keys*.
3. Put it in `NOWPAYMENTS_API_KEY` in `.env`. Restart the bot.
4. The **"Pay with Card / Crypto (NOWPayments)"** button now appears and creates
   live invoices. Set a payout wallet in the dashboard so funds settle there.

> Note: without a public webhook, a customer's NOWPayments payment is confirmed
> when they tap **"Check payment status"** after paying. This works fine.

---

## Owner commands
DM these to the bot (only your `OWNER_CHAT_ID` can use them):

| Command | Action |
|---------|--------|
| `/stats` | subscriber count + estimated revenue |
| `/broadcast <text>` | send a message to all subscribers |
| `/add_member <user_id>` | grant 30 days Premium manually |
| `/kick <user_id>` | remove a subscriber |
| `/set_price <usd>` | change monthly price (until restart) |
| `/admin` | list all owner commands |

---

## Troubleshooting

**`ERROR: TELEGRAM_BOT_TOKEN not set`** — your `.env` is missing the token, or
you ran the bot from the wrong folder. The `.env` file must be in the same
folder as `bot.py`.

**Bot doesn't reply** — make sure only ONE process is polling your bot. If you
ran it twice, stop one. Telegram only allows one active poller.

**`400 Bad Request`** — usually a stale update. Restart the bot; it auto-drains
stale updates.

**Channel invite not working** — the bot must be an *admin* of the channel with
"ban users" permission, and `CHANNEL_ID` must be the numeric channel id.

**Persian/Arabic text looks wrong** — the bot itself is fine; this is your
terminal font. Use Windows Terminal with a font that supports ligatures
(e.g. Cascadia Code, Vazirmatn) and the DirectWrite shaping engine.

**Run 24/7 for free** — a small Linux VPS or always-on PC with `python bot.py`
inside `screen`/`tmux`, or run as a Windows Scheduled Task.

---

## Extending
See `ARCHITECTURE.md`. The code is split into single-responsibility modules:
change any message in `lang.py`, any setting in `config.py`, and add behaviour
in `bot.py` — no hunting through one big file.

*This is a template/source sale. Buyers configure their own token, wallet, and
channel. All payments go directly to the buyer's own wallet.*
