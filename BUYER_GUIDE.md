# 🤖 TelStore — Buyer Guide (How to Buy & Activate)

> Everything you need to go from *"I want this bot"* to *"my own TelStore bot is
> live on my server accepting payments."*

**TelStore** is a ready-to-sell Telegram bot. You buy it once, install it on
your own server, plug in **your own** bot token / wallet / NOWPayments key, and
start selling VIP channel access or digital products to **your** audience. All
customer payments go **straight to your wallet** — no middleman.

This guide has two parts:

1. [**Part 1 — How to buy**](#part-1--how-to-buy): order + pay in crypto.
2. [**Part 2 — How to activate**](#part-2--how-to-activate): install it on your
   server and run it 24/7.

---

## Part 1 — How to buy

Buying happens inside the seller's Telegram bot — quick, private, no bank card
needed.

### Step 1.1 — Open the bot
Open the TelStore sales bot on Telegram:

```
https://t.me/ADNC_bot
```

> If you're reading this pack, the seller already sent you the bot link. Tap
> **Start** to open the menu. *(Link shown matches the one on the sales page;
> if the seller gave you a different link, use theirs.)*

### Step 1.2 — Pick the product
In the main menu, tap:
**🛒 Shop / Products** → **Source Code License** (currently **$29**, one-time).

The bot shows the payment page with the exact amount and available networks
(BSC / Ethereum / Polygon).

### Step 1.3 — Pay with crypto
1. Card / fast checkout (optional): if the seller enabled **NOWPayments**, tap
   **Pay with Card / Crypto** and follow the hosted payment page.
2. Manual crypto (always available): copy the **wallet address** shown, open your
   crypto wallet (Trust Wallet, MetaMask, OKX, …), and send the exact amount on
   the network shown in the bot.

> ⚠️ Only send to the address the bot shows for **this** sale, on the **exact
> network** it names. Sending on the wrong network can make the payment hard to
> find.

### Step 1.4 — Confirm your payment
After you send the crypto:
- Tap **✅ I paid** in the bot, then send the **transaction hash (TXID)** that
  your wallet gives you.
- The bot checks the payment and notifies the **seller** to verify it manually.

> For NOWPayments purchases the bot **auto-checks** the invoice every ~20
> seconds and confirms it the moment the network confirms the transaction — you
> may not need to do anything.

### Step 1.5 — Receive your product
Once the seller confirms the payment, you'll receive the **TelStore source pack**
directly in Telegram (or a download link + unlock key). This pack you're holding
now is that source — its `scripts/` folder is the bot itself.

---

## Part 2 — How to activate

Now you install and run TelStore on **your** server. Two routes:

### Route A — 24/7 server (recommended, ~$2–5/mo VPS)
Run the ready-made **interactive installer**. It asks for *your* values and sets
up a background service that auto-starts on boot:

```bash
bash scripts/deploy_server.sh
```

See **`DEPLOY_SERVER.md`** for the full walk-through.

### Route B — Your own PC (test / small setup)
Follow **`INSTALL.md`**: create your bot with @BotFather, copy `.env.example` →
`.env`, fill in your token / wallet / owner chat, run `python bot.py`.

> Both routes need the same three things ready:
> 1. **A Telegram bot token** — from [@BotFather](https://t.me/BotFather).
> 2. **A crypto wallet** (BSC/ETH/Polygon) for your payouts.
> 3. **Your Telegram chat_id** — from [@userinfobot](https://t.me/userinfobot)
>    (this is you, the owner).

### First 10 minutes after install
1. Open your new bot, tap **Start**, then **🛒 Shop**.
2. As the owner, add your first product:
   ```
   /add_product VIP Month | 5 | 30 | channel
   ```
3. For a **digital product** (any file/link you sell), add it then set the
   delivery message:
   ```
   /add_product Crypto Course | 19.99 | 0 | digital
   /set_deliver crypto_course <your download link or text>
   ```
4. Test a purchase yourself. Done — your store is live. 🎉

---

## What you get in this pack

```
TelStore/
  README.md            what it is + quick start
  BUYER_GUIDE.md       this file
  INSTALL.md           step-by-step install (non-technical)
  DEPLOY_SERVER.md     run it 24/7 on a VPS (systemd)
  ARCHITECTURE.md      code overview
  sales-page.html      (optional) a simple buy page for your own marketing
  scripts/             the bot itself (see INSTALL.md)
    bot.py             the bot
    config.py          settings + product catalogue
    lang.py            every message & button
    deploy_server.sh   interactive one-command server installer
    install_from_github.sh  install directly from a private GitHub repo
    ...
  LICENSE              single-site license
```

Everything is English, clean, and self-contained — no external packages, runs
on plain Python 3.8+.

---

## Frequently asked questions

**Is this a subscription? Do I keep paying?**
No. You pay **once** for a single-site license. You keep your revenue; the
software is yours to run for your own business.

**Where do payments go?**
Straight to **your wallet**. The seller never touches money.

**Do I need to know how to code?**
No. Configuration is done from Telegram (owner menu) and one `.env` file.
`INSTALL.md` is written for non-technical users.

**What can I sell with it?**
Anything: VIP channel access (auto-added / auto-kicked), e-books, courses,
codes, invites — each with its own price.

**What if I need help?**
Message the seller (they usually reply within a day) — contact details were
sent with your purchase.

**Can I resell it?**
No — it's a **single-site license**. Each site that runs the bot needs its own
license; for multiple sites, contact the seller for a separate commercial
agreement. See `LICENSE`.

---

*© TelStore. Single-site license. Reselling or redistribution of the software
(or modified copies) is not permitted.*