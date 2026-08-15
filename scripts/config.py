#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Central configuration for the Crypto Quest bot
==============================================
All settings live here, loaded from environment variables or the project `.env`
file. This is the single place an owner/buyer edits to configure the bot
(token, wallet, price, owner id, channel, etc.). No hard-coded config values
should live in the handler logic.

Sellable template: each buyer copies `.env.example` to `.env` and sets their
own values here via the .env file. Everything is in English.
"""
import json
import os
import re


# ------------------------------------------------------------
#  Paths
# ------------------------------------------------------------
def _dir():
    return os.path.dirname(os.path.abspath(__file__))

def _env_file():
    """Locate the .env file. Checks scripts/ first, then the project root
    (parent of scripts/), so it works whether the user puts .env next to
    the scripts or in the repo root (as deploy_server.sh does)."""
    env = os.path.join(_dir(), ".env")
    if os.path.exists(env):
        return env
    env = os.path.join(os.path.dirname(_dir()), ".env")
    if os.path.exists(env):
        return env
    # fallback: scripts/.env (create later)
    return os.path.join(_dir(), ".env")

# Runtime data files (gitignored). Kept next to the scripts.
SUBSCRIBERS_FILE = os.path.join(_dir(), "subscribers.json")
PENDING_FILE = os.path.join(_dir(), "pending_payments.json")
WIZARD_FILE = os.path.join(_dir(), "wizard.json")   # add-product step wizard state
SETTINGS_FILE = os.path.join(_dir(), "settings.json")  # owner-editable runtime settings


# ------------------------------------------------------------
#  .env / environment loader
# ------------------------------------------------------------
def _load_env_str(key, default=""):
    """Read a string value from env or the project .env file."""
    val = os.environ.get(key, "").strip()
    if val:
        return val
    env_path = _env_file()
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8-sig") as f:
                m = re.search(rf'^{key}=([^\r\n]+)', f.read(), re.M)
            if m:
                return m.group(1).strip().strip('"').strip("'")
        except Exception:
            pass
    return default

def _load_env_float(key, default=5.0):
    try:
        return float(_load_env_str(key, str(default)))
    except ValueError:
        return default


# ------------------------------------------------------------
#  Telegram
# ------------------------------------------------------------
TOKEN = _load_env_str("TELEGRAM_BOT_TOKEN")

# Owner (gets admin panel access). Empty = admin panel locked.
OWNER_CHAT_ID = _load_env_str("OWNER_CHAT_ID", "").strip()


# ------------------------------------------------------------
#  Payments
# ------------------------------------------------------------
# The payout wallet (EVM). Same address for BSC / Ethereum / Polygon.
# Leave empty in .env = the bot shows no wallet until the buyer sets theirs.
# (A hard-coded default wallet here would wrongly send buyer funds to the author.)
CRYPTO_ADDRESS = _load_env_str("CRYPTO_ADDRESS", "").strip()

# NOWPayments gateway (optional). Empty = button hidden/disabled.
NOWPAYMENTS_API_KEY = _load_env_str("NOWPAYMENTS_API_KEY", "").strip()

# Default coin for NOWPayments invoices (USDT on TRON - low fees, widely used).
NOWPAYMENTS_DEFAULT_CURRENCY = "usdttrc20"

# CoinGate gateway (optional, 2nd payment option). Provides a hosted web
# payment page (payment_url). Empty = the CoinGate button is hidden.
# Get your Auth Token: https://coingate.com -> Settings -> API -> Create token.
COINGATE_AUTH_TOKEN = _load_env_str("COINGATE_AUTH_TOKEN", "").strip()

# Supported manual networks. Only the "recommended" one gets the badge.
CRYPTO_NETWORKS = [
    {
        "name": "BSC",
        "standard": "BEP-20",
        "currency": "USDT (BEP-20) / BNB",
        "recommended": True,
        "note": "Recommended - very low fees and fast",
    },
    {
        "name": "Ethereum",
        "standard": "ERC-20",
        "currency": "USDT (ERC-20) / ETH",
        "recommended": False,
        "note": "Secure but higher gas fees",
    },
    {
        "name": "Polygon",
        "standard": "MATIC",
        "currency": "USDC / POL",
        "recommended": False,
        "note": "Low fees, Layer 2 network",
    },
]


# ------------------------------------------------------------
#  VIP channel membership (optional)
# ------------------------------------------------------------
# These are read from .env first, but can be overridden at runtime by the
# owner from Telegram (/set_setting). Runtime values live in settings.json.
def _load_settings():
    """Load owner-editable runtime settings (settings.json -> dict)."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d if isinstance(d, dict) else {}
        except Exception:
            pass
    return {}


def _get_setting(key):
    """Value: settings.json override if present, else the .env value."""
    s = _load_settings()
    if key in s and s[key] not in (None, ""):
        return str(s[key])
    return _load_env_str(key, "").strip()


CHANNEL_ID = _get_setting("CHANNEL_ID").strip()        # e.g. -1001234567890
CHANNEL_LINK = _get_setting("CHANNEL_LINK").strip()    # optional public link

# Owner website & support contact (shown to customers). Runtime-editable.
WEBSITE_URL = _get_setting("WEBSITE_URL").strip()      # e.g. https://site.com
SUPPORT_URL = _get_setting("SUPPORT_URL").strip()      # e.g. https://t.me/owner  (DM link)


def save_settings(overrides):
    """Merge overrides into settings.json (persists runtime changes) and
    update the in-memory module values so the running bot sees them at once."""
    s = _load_settings()
    s.update(overrides)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)
    # Refresh in-memory module-level values immediately.
    global CHANNEL_ID, CHANNEL_LINK, WEBSITE_URL, SUPPORT_URL
    for k, v in overrides.items():
        v = str(v) if v is not None else ""
        if k == "CHANNEL_ID":
            CHANNEL_ID = v
        elif k == "CHANNEL_LINK":
            CHANNEL_LINK = v
        elif k == "WEBSITE_URL":
            WEBSITE_URL = v
        elif k == "SUPPORT_URL":
            SUPPORT_URL = v


# ------------------------------------------------------------
#  Behaviour
# ------------------------------------------------------------
SWEEP_INTERVAL_SECONDS = 6 * 60 * 60   # kick expired memberships every 6h

# Legacy single-price defaults (kept for backward compat / /set_price).
# The real catalogue the buyer defines lives in PRODUCTS below.
PREMIUM_DAYS = 30                      # default grant length when days=0


# ------------------------------------------------------------
#  Product catalogue (what the owner sells)
#  ------------------------------------------------------------
#  Products are loaded from ``products.json`` (runtime, editable from the bot
#  by the owner with /add_product, /remove_product, /list). If that file is
#  missing, the DEFAULT_PRODUCTS below are used as a starting catalogue.
#
#  Each entry is one thing the owner sells. Prices are per-product, so the
#  owner is free to set any amount.
#
#  Fields:
#    id          unique key used in button callbacks (lowercase, no spaces)
#    name        short button/summary label
#    price_usd   what the customer pays (any amount the owner wants)
#    days        how long access lasts. 0 = lifetime / not time-based.
#    kind        how the product is delivered after payment:
#                  "channel" -> grant access to the VIP channel
#                  "digital" -> send the product's delivery message/link
#    deliver     (kind="digital") message or link sent to the buyer after payment
#    description shown on the product's payment page
#
DEFAULT_PRODUCTS = [
    {
        "id": "vip_monthly",
        "name": "VIP Channel — 1 Month",
        "price_usd": 12.0,  # >= $12 so NOWPayments (USDT-TRC20) accepts it
        "days": 30,
        "kind": "channel",
        "description": "Monthly access to our private VIP channel with exclusive updates.",
    },
]

# Runtime products file (gitignored). The owner can add/remove products from
# Telegram; edits here survive restarts.
PRODUCTS_FILE = os.path.join(_dir(), "products.json")


def _load_products():
    """Load the product catalogue from products.json, or DEFAULT_PRODUCTS."""
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            products = data.get("products", []) if isinstance(data, dict) else data
            if products:
                return products
        except Exception:
            pass
    return list(DEFAULT_PRODUCTS)


PRODUCTS = _load_products()


def save_products():
    """Persist the current PRODUCTS list to products.json (runtime, gitignored)."""
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"products": PRODUCTS}, f, ensure_ascii=False, indent=2)


# Legacy default price for backward compat (used only if PRODUCTS is empty).
PRICE_USD = _load_env_float("PRICE_USD",
                            PRODUCTS[0]["price_usd"] if PRODUCTS else 5.0)


# ------------------------------------------------------------
#  Product helpers (single source of truth for lookups)
#  ------------------------------------------------------------
def get_product(product_id):
    """Return the product dict for an id, or None."""
    for p in PRODUCTS:
        if p.get("id") == product_id:
            return p
    return None


def get_default_product():
    """Return the first product (used when none specified)."""
    return PRODUCTS[0] if PRODUCTS else None


def effective_price(product):
    """Return the price the buyer actually pays after any discount %.
    discount is stored as a percentage (0-100). If absent/0, price is unchanged.
    Rounded to 2 decimals."""
    price = product.get("price_usd", 0.0)
    disc = product.get("discount", 0) or 0
    try:
        disc = float(disc)
    except (TypeError, ValueError):
        disc = 0
    if disc <= 0 or disc >= 100:
        return round(float(price), 2)
    return round(float(price) * (1 - disc / 100.0), 2)


# ------------------------------------------------------------
#  Main-menu buttons
#  ------------------------------------------------------------
#  The main menu is built from MENU_ITEMS (all shown). Adding a button here
#  adds it to the main menu for everyone.
MENU_ITEMS = {
    "shop":          {"btn": "shop",          "label_key": "shop"},
    "sub_free":      {"btn": "sub_free",      "label_key": "free_sub"},
    "status":        {"btn": "status",        "label_key": "status"},
    "help":          {"btn": "help",          "label_key": "help"},
    "website":       {"btn": "website",       "label_key": "website"},
    "support":       {"btn": "support",       "label_key": "support"},
    "account":       {"btn": "account",       "label_key": "account"},
}
