#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoinGate payment gateway for the TelStore bot
==================================================
Optional 2nd payment option. Creates a CoinGate order and returns a **hosted
web payment page** (``payment_url``) the customer opens in their browser —
better UX than a bare wallet address. Funds go straight to the owner's
CoinGate-verified wallet (no bank card needed).

Requirements (the bot OWNER sets these):
  1. Create a free account at https://coingate.com
     - Settings -> Payment Settings -> set your payout crypto wallet.
  2. Get an Auth Token: Settings -> API -> Create Auth Token.
  3. Put it in `.env` as COINGATE_AUTH_TOKEN (see .env.example).

All config (token) comes from ``config.py`` — the single source of truth.

API reference: https://developer.coingate.com/docs/remote

Usage (CLI, for the owner to test):
  python coingate.py create --price 29 --title "Bot license"
  python coingate.py check --id <ORDER_ID>
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

import config

API_URL = "https://api.coingate.com/v2"

# Read the Auth Token from config (empty until the owner sets COINGATE_AUTH_TOKEN
# in .env). The gateway stays hidden/disabled until then.
AUTH_TOKEN = config.COINGATE_AUTH_TOKEN


def is_configured():
    """True if a CoinGate Auth Token is set in .env."""
    return bool(AUTH_TOKEN)


def _headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Token {AUTH_TOKEN}",
    }


def _request(method, path, payload=None):
    url = API_URL + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return {"error": json.loads(e.read().decode()), "http": e.code}
        except Exception:
            return {"error": str(e), "http": e.code}
    except Exception as e:
        return {"error": str(e)}


def create_order(price_usd, title, description="", order_id=None, price_currency="USD"):
    """
    Create a CoinGate payment order.

    Returns the order dict with 'id' and 'payment_url' (the hosted web page),
    or {'error': ...} on failure.
    """
    payload = {
        "order_id": order_id or f"cq-{os.getpid()}",
        "price_amount": str(price_usd),
        "price_currency": price_currency,   # USD keeps the price stable
        "receive_currency": "BTC",          # owner is paid in BTC by default
        "title": title,
        "description": description,
        "callback_url": "",
        "success_url": "",
        "cancel_url": "",
    }
    return _request("POST", "/orders", payload)


def get_order(order_id):
    """Get a CoinGate order's current status (paid / pending / invalid)."""
    return _request("GET", f"/orders/{order_id}")


def format_payment_message(order):
    """Build a customer-facing message with the hosted payment URL."""
    url = order.get("payment_url", "")
    oid = order.get("id", "")
    status = order.get("status", "")
    return (
        "💳 Pay online with crypto (CoinGate)\n\n"
        f"💰 Amount: {order.get('price_amount')} {order.get('price_currency', 'USD')}\n"
        f"🆔 Order: {oid}\n\n"
        f"🔗 Open this payment page in your browser:\n{url}\n\n"
        f"Status: {status}\n\n"
        "Pay with BTC, ETH, USDT and 70+ coins. Funds go straight to the "
        "seller's wallet — no account needed on your side."
    )


def main():
    ap = argparse.ArgumentParser(description="CoinGate crypto checkout")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("create", help="create a payment order")
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--desc", default="")
    p.add_argument("--currency", default="USD")
    c = sub.add_parser("check", help="check an order status")
    c.add_argument("--id", required=True)
    args = ap.parse_args()

    if not AUTH_TOKEN:
        print("ERROR: COINGATE_AUTH_TOKEN not set in .env.", file=sys.stderr)
        print("  1) create a free account at https://coingate.com", file=sys.stderr)
        print("  2) Settings -> API -> create an Auth Token", file=sys.stderr)
        print("  3) put it in .env as COINGATE_AUTH_TOKEN=...", file=sys.stderr)
        sys.exit(1)

    if args.cmd == "create":
        r = create_order(args.price, args.title, args.desc, price_currency=args.currency)
        if "error" in r:
            print("ORDER ERROR:", json.dumps(r, indent=2)); sys.exit(1)
        print("✅ ORDER CREATED")
        print(f"  Order id : {r.get('id')}")
        print(f"  Status   : {r.get('status')}")
        print(f"  Payment  : {r.get('payment_url')}")
        print("Send the Payment URL to your customer (they open it in a browser).")
    elif args.cmd == "check":
        r = get_order(args.id)
        if "error" in r:
            print("CHECK ERROR:", json.dumps(r, indent=2)); sys.exit(1)
        print(f"Order {args.id}: status = {r.get('status')}")


if __name__ == "__main__":
    main()