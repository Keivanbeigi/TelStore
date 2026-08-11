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
import os
import re


# ------------------------------------------------------------
#  Paths
# ------------------------------------------------------------
def _dir():
    return os.path.dirname(os.path.abspath(__file__))

def _env_file():
    return os.path.join(_dir(), ".env")

# Runtime data files (gitignored). Kept next to the scripts.
SUBSCRIBERS_FILE = os.path.join(_dir(), "subscribers.json")
PENDING_FILE = os.path.join(_dir(), "pending_payments.json")


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
CHANNEL_ID = _load_env_str("CHANNEL_ID", "").strip()        # e.g. -1001234567890
CHANNEL_LINK = _load_env_str("CHANNEL_LINK", "").strip()    # optional public link


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
#  Each entry is one thing the owner sells. The owner/buyer edits this list
#  to set price and behaviour for EACH product. Prices are per-product, so the
#  owner is free to set any amount (not tied to the old PRICE_USD).
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
#  Examples:
#    A single VIP-channel subscription:
#      {"id": "vip", "name": "VIP Channel", "price_usd": 5.0, "days": 30,
#       "kind": "channel", "description": "Monthly access to our private channel"}
#    A digital item (e-book / course / invite link):
#      {"id": "guide", "name": "Crypto Starter Guide", "price_usd": 9.99, "days": 0,
#       "kind": "digital", "deliver": "Here is your file: https://...", ...}
#
PRODUCTS = [
    {
        "id": "vip_monthly",
        "name": "VIP Channel — 1 Month",
        "price_usd": 5.0,
        "days": 30,
        "kind": "channel",
        "description": "Monthly access to our private VIP channel with daily reports.",
    },
]

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
