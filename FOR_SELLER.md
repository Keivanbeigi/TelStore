# TelStore — Seller Distribution Guide

This guide is for the **seller/owner** of TelStore. It explains how to deliver
the bot to a buyer using a **private GitHub repo + a short-lived read-only
token**, so the buyer can install on their own server in a few commands.

> Keep this file out of anything you hand directly to buyers unless you want
> them to see the exact workflow. It contains no secrets, but it is your ops
> playbook.

---

## 1. What each buyer needs

Two things, both of which you generate/choose and send to the buyer:

1. **REPO_URL** — the https address of your private TelStore source repo, e.g.
   `https://github.com/<your-account>/TelStore-source.git`
2. **GITHUB_TOKEN** — a read-only, single-repo GitHub Personal Access Token
   that can clone that repo, which you **revoke after the sale** so it does not
   become a permanent backdoor.

Give the buyer this one command to run on their server:

```bash
export REPO_URL="https://github.com/<your-account>/TelStore-source.git"
export GITHUB_TOKEN="<one-time-token>"
bash install_from_github.sh
```

The script clones the repo, drops the `.git` history (so the token never ends
up in any reflog or on disk), then runs the interactive `deploy_server.sh`
which asks the buyer for **their own** Telegram token / wallet / NOWPayments
key and writes their `.env`.

---

## 2. Creating a read-only token for a sale (2 minutes)

1. GitHub → **Settings → Developer settings → Fine-grained personal access
   tokens → Generate new token**.
2. **Resource owner:** your account.
3. **Repository access:** **Only select repositories** → tick **TelStore-source**.
4. **Permissions → Contents:** set to **Read-only**.
5. **Expiration:** pick a short window (e.g. 1 day / 7 days).
6. Generate and copy the token. Send it to the buyer along with the command
   above.

> ⚠️ **Do not use your main account token.** Use a **fine-grained, read-only,
> limited to the TelStore-source repo only** token. Revoke/expire it after the sale.

---

## 3. Rotating / revoking after the sale

- **Fine-grained token:** Settings → Developer settings → Fine-grained tokens
  → find the token → **Revoke**. It stops working instantly.
- **Classic token:** Settings → Developer settings → Personal access tokens →
  delete/expire it.

Recommended: **rotate per sale** — issue a fresh token for each buyer and revoke
it as soon as they confirm the install worked. This is your "one-time link"
mechanism; GitHub itself has no true single-use download URL, but a revoked
per-sale token is the practical equivalent.

---

## 4. Safety rules for the seller

- The source repo (`TelStore-source`) must stay **private**.
- Never commit `.env`, `*.env`, `subscribers.json`, `products.json`,
  `pending_payments.json`, `settings.json`, or any `.log` — all already in
  `.gitignore`.
- Never paste a live token into code, docs, or the repo.
- Keep `PROJECT_STATUS.md`, local `.bat` launchers, and anything with your real
  chat_id / token id out of the repo (it is gitignored / excluded).
- The sale package must contain only **buyer-clean** files.

---

## 5. Repos overview

| Repo | Visibility | Purpose |
|------|-----------|---------|
| `Keivanbeigi/TelStore` | **PUBLIC** | Sales page + screenshots + docs |
| `Keivanbeigi/TelStore-source` | **PRIVATE** | Bot source code (delivered per-sale via token) |

---

## 6. Updating the bot later

When you improve the bot, commit + push on `master` of the private
`TelStore-source` repo, then tell existing buyers to re-run:

```bash
export REPO_URL="https://github.com/<your-account>/TelStore-source.git"
export GITHUB_TOKEN="<fresh-token>"
bash install_from_github.sh
```

The script replaces `/opt/telstore` with the latest source and re-runs the
interactive config (their `.env` is asked for again).

---

## 7. Reference: files layout

```
Public repo (sales page) — Keivanbeigi/TelStore:
  index.html / sales-page.html    sales page with screenshots
  screenshots/                    before/after-purchase screenshots
  SELLER_DESCRIPTION.md           marketplace description (copy-paste to Sellauth)

Private repo (source) — Keivanbeigi/TelStore-source:
  install_from_github.sh          buyer runs this on their server
  scripts/                        bot source (admin.py, bot.py, config.py, lang.py, ...)
  scripts/.env.example            template — buyer fills in their own values
  scripts/deploy_server.sh        interactive installer + systemd service setup
  scripts/run_bot.sh              entrypoint used by systemd
```