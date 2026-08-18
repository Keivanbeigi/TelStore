# TelStore Bot v1.0 — Telegram Payment Bot

A complete Telegram bot for selling your digital products / VIP channel
access, with **crypto payments** (NOWPayments + CoinGate). It runs 24/7 on
your own server and is 100% configurable from Telegram — no coding needed.

## Documentation

Everything you need ships in this folder:

- **`INSTALL.md`** — the 2-minute quick-start install
- **`DEPLOY_SERVER.md`** — full 24/7 server deployment (for any buyer)
- **`BUYER_GUIDE.md`** — welcome, first 15 minutes, and common questions
- **`ARCHITECTURE.md`** — how the code is organised
- **`FOR_SELLER.md`** — seller's brief (distribution & build checklist)
- This **`README.md`** — reference index + owner tools

---

## 1. What you just bought

You bought the **bot software itself** (this package). You install it on a
server of your own, connect it to **your** Telegram bot, **your** wallet and
**your** payment accounts, and run it to sell **your own products** to **your
customers**.

> The price you paid to buy this bot is not something inside this package.
> It only shows up on the seller's checkout page.

The values you set up during installation (bot token, wallet, API keys,
prices) are **yours** — for the products *you* sell through the bot.

## Where to buy

You can purchase this bot at either store:

- **SellApp** — https://telstore.sell.app/product/telstore-bot-source-code
- **SellAuth** — https://telstore.sellauth.com/checkout/840291

(You only need to buy it once, at whichever you prefer. The delivered package
and this documentation are identical.)

---

## 2. What you need before you start

Have these ready before you install (all free):

| What | Where to get it |
|------|-----------------|
| **A VPS / server** | Any Ubuntu/Debian machine (or WSL on your PC for testing). It must stay on 24/7 for the bot to keep selling. |
| **A Telegram bot token** | Message [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token. |
| **Your Telegram chat_id** | Message [@userinfobot](https://t.me/userinfobot) — it replies with your number. |
| **A crypto wallet (EVM)** | Any `0x...` wallet (e.g. MetaMask). Cards sent here for manual payments. *(Optional but recommended.)* |
| **A NOWPayments API key** | [nowpayments.io](https://nowpayments.io) → add a payout wallet → **Settings → API Keys**. Powers automatic card/crypto checkout. *(Optional.)* |
| **A CoinGate API token** *(optional — only if you want a 2nd payment page)* | [coingate.com](https://coingate.com) → **Settings → API → Create Auth Token**. The installer won't ask for it; add it to `.env` yourself if you want it. |

> **NowPayments requires a verified payout wallet** in your dashboard for the
> money to actually reach you. Without it, automatic checkout stays off.
> CoinGate is optional — the ready-made installer only asks for the four
> values above; you can add CoinGate to `.env` later.

---

## 3. Step-by-step install (recommended way)

This is the easy path. The installer asks you questions and does everything
for you — it even sets the bot up to auto-start on every reboot.

### Step 1 — Unzip the package on your computer

Right-click the `.zip` you received → **Extract All**. You'll get a folder
named `telstore`. Inside it there is a `scripts/` folder.

### Step 2 — Upload it to your server

Open a terminal on your **own computer** and run:

```bash
scp -r telstore root@YOUR_SERVER_IP:~/
```

Replace `YOUR_SERVER_IP` with your server's IP address. (If you use WinSCP
or FileZilla instead, just drag the whole folder into your home directory.)

### Step 3 — Log in to your server

```bash
ssh root@YOUR_SERVER_IP
```

Then go into the folder:

```bash
cd ~/telstore
```

### Step 4 — Run the installer

```bash
bash scripts/deploy_server.sh
```

The installer now asks you a few questions. Answer with **your own** values:

1. **Telegram bot token** — paste the token from @BotFather.
2. **Your Telegram chat_id** — paste your number (from @userinfobot).
3. **Your crypto wallet address** — paste your `0x...` wallet (just press
   Enter to skip if you don't want manual payments).
4. **NOWPayments API key** — paste it, or press Enter to skip.

When it finishes it prints a green **✅ Bot service is RUNNING.**

> The bot is now installed as a **systemd service** named `telstore-bot`.
> It starts automatically, and it will start again every time the server
> reboots. No extra steps needed.

---

## 4. Verify it's working

Run the built-in health check (optional but recommended):

```bash
bash scripts/check_bot.sh
```

It prints **PASS** or **FAIL** for each check (Python, token validity,
payments, files, service). When everything passes you see:

```
✅ RESULT: ALL CHECKS PASSED — the bot is healthy.
```

Then open Telegram and send `/start` to your bot. It should reply with the
main menu.

---

## 5. Manage the bot day to day

All on the server:

```bash
systemctl status telstore-bot        # is it running?
journalctl -u telstore-bot -f        # live logs (Ctrl+C to exit)
systemctl restart telstore-bot       # restart after a config change
```

---

## 6. Testing on your own PC (no server needed)

If you don't have a server yet (or just want to try it before paying for a
VPS), you can run it on **WSL** (the Ubuntu app on Windows). The bot runs in
the foreground here, so close the window and it stops — that's why a real
24/7 bot needs a server (Steps 2–5).

1. Open **WSL** (Ubuntu) and go into the folder:
   ```bash
   cd ~/telstore
   ```
2. Create your `.env` from the template and fill in **your** values:
   ```bash
   cp scripts/.env.example scripts/.env
   nano scripts/.env
   ```
   Set at least `TELEGRAM_BOT_TOKEN=` and `OWNER_CHAT_ID=` in that file.
3. Start the bot:
   ```bash
   bash scripts/run_bot.sh
   ```
4. Send `/start` to your bot in Telegram — it should answer with the menu.

---

## 7. Configure your own products & prices

This is where **your** business comes in. The bot has no opinion about what
you sell — you set it up as owner from Telegram, no code changes needed.

> **Important:** the prices you set here are the prices **you** sell *your*
> products at. They have nothing to do with the price you paid to buy the
> bot. Your own checkout amounts are whatever you want.

### The Owner Menu (your private admin panel)

Open your bot in Telegram and send `/start`. Because you are the **owner**
(user id set during install), the main menu shows an extra **⚙️ Owner Menu**
button that normal visitors never see. Tap it to manage everything:

- **➕ Add Product** — guided wizard (a few taps) to add a product
- **🗑️ Remove Product** — pick one to delete
- **🛒 List Products** — see your current catalogue
- **How to add** — quick example of the command format

### Command shortcuts (same tools, typed)

If you prefer typing, these work in the owner chat:

- `/products` — show your catalogue
- `/add_product Name | price [| days [| kind]]` — add a product
  e.g. `/add_product VIP Year | 49.99 | 365 | channel`
- `/remove_product <id>` — delete one
- `/set_deliver <id> <text>` — set what the buyer receives after paying

> `kind`: `channel` = grant access to your VIP channel, `digital` = send the
> buyer a message/link. `days`: how long access lasts (0 = lifetime).

### Starting catalogue

The package ships with one example product so the shop isn't empty:
**VIP Channel — 1 Month** at **$12** *($12+ is the minimum the NOWPayments
gateway accepts).* Add your own and remove this one.

### Other owner tools

- **🌐 Website / 🎧 Support / 🔔 Subscription** — tap these as owner to set
  / open / clear links for your customers.
- `/stats` — sales & subscriber numbers
- `/broadcast <text>` — message all subscribers
- `/set_setting <key> <value>` — set store settings (channel, website, ...)
- `/set_price <usd>` — change the default price (current run)

---

## 8. Setting up a VIP channel (optional)

If you sell access to a private Telegram channel:

1. Add your **bot as an admin** of the channel.
2. Get the channel **ID** (a negative number like `-1001234567890`). You can
   set it as owner from Telegram, or add `CHANNEL_ID=` in `.env`.
3. Optional: add a public `CHANNEL_LINK=` so new customers see the invite.

Paying customers get access automatically, and expired subscriptions are
auto-removed.

---

## 9. Files in this package

```
telstore/
├── README.md               This file — reference index + owner tools
├── INSTALL.md              Quick-start install
├── DEPLOY_SERVER.md        Full 24/7 server deployment
├── BUYER_GUIDE.md          Welcome + first 15 minutes
├── ARCHITECTURE.md         How the code is organised
├── FOR_SELLER.md           Seller's brief (distribution & rebuild checklist)
└── scripts/
    ├── bot.py               Main bot (logic only)
    ├── config.py            Loads all settings from .env
    ├── lang.py              Every customer-facing message & button label
    ├── nowpayments.py       NOWPayments card/crypto gateway
    ├── coingate.py          CoinGate web-payment gateway (optional)
    ├── admin.py             Owner admin panel
    ├── channel_access.py    Channel membership control
    ├── broadcast.py         Send messages to subscribers
    ├── deploy_server.sh     One-shot installer (creates the 24/7 service)
    ├── run_bot.sh           Run the bot in the foreground (testing)
    ├── check_bot.sh         Health check / self-test
    ├── requirements.txt     (Standard library only — nothing to install)
    └── .env.example         Copy to .env and fill in your values
```

**No coding required.** The bot uses only Python's standard library, so there
is nothing extra to install. Every message the customers see lives in
`lang.py`; every setting lives in `.env`.

---

## 10. Troubleshooting

| Problem | Fix |
|---------|-----|
| Installer fails with "python3 not found" | Run `apt-get update && apt-get install -y python3`, then re-run. |
| Bot doesn't reply to `/start` | Make sure your token in `.env` is correct (re-check with `check_bot.sh`). |
| NOWPayments button hidden | You left the API key empty during install. Add it to `.env` and restart: `systemctl restart telstore-bot`. |
| Money not reaching you | Check your payout wallet is **verified in your NOWPayments dashboard**. |
| Bot stops when I close the terminal | You used `run_bot.sh` — for 24/7 use run the systemd installer (Step 3–5) on a server. |

## 11. Support

Need help getting your shop running? Contact us:

- **Telegram:** [@k1_adineh](https://t.me/k1_adineh)

We'll help you get setup, configure products, or troubleshoot your bot.

---

_Thank you for choosing TelStore! 🚀_
