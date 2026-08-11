#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoinGate checkout helper for the Crypto Quest bot
==================================================
Creates a CoinGate payment order so a customer pays in crypto (BTC, ETH,
USDT, etc.) and the funds go straight to YOUR CoinGate-verified wallet — no
bank card or PayPal needed on your side.

Requirements:
  1. Create a free account at https://coingate.com (email only).
     - In Settings -> Payment Settings -> set your payout crypto wallet.
  2. Get your Auth Token: Settings -> API -> create an Auth Token.
  3. Put the token in this script's COINGATE_AUTH_TOKEN (or env var).

Usage:
  python coingate.py create --price 29 --currency USD --title "Crypto Quest Bot"
      -> prints a payment URL + order id you can send to the customer.
  python coingate.py check --id <ORDER_ID>
      -> prints the order status (paid / pending / expired).

API reference: https://developer.coingate.com/docs/remote
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

API_URL = "https://api.coingate.com/v2"

# Get your token here: https://coingate.com/settings/api
COINGATE_AUTH_TOKEN = os.environ.get("COINGATE_AUTH_TOKEN", "").strip()


def _headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Token {COINGATE_AUTH_TOKEN}",
    }


def _request(method, path, payload=None):
    url = API_URL + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
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
    Create a payment order. Returns the order dict with 'id' and 'payment_url'.
    """
    payload = {
        "order_id": order_id or f"crystal-bot-{os.getpid()}",
        "price_amount": str(price_usd),
        "price_currency": price_currency,   # can be USD, EUR, or a crypto
        "receive_currency": "BTC",          # you get paid in BTC by default
        "title": title,
        "description": description,
        "callback_url": "",                 # optional webhook; leave empty
        "success_url": "",
        "cancel_url": "",
    }
    return _request("POST", "/orders", payload)


def get_order(order_id):
    return _request("GET", f"/orders/{order_id}")


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

    if not COINGATE_AUTH_TOKEN:
        print("ERROR: COINGATE_AUTH_TOKEN not set.", file=sys.stderr)
        print("  1) create a free account at https://coingate.com", file=sys.stderr)
        print("  2) Settings -> API -> create an Auth Token", file=sys.stderr)
        print("  3) export COINGATE_AUTH_TOKEN=<your-token>", file=sys.stderr)
        sys.exit(1)

    if args.cmd == "create":
        r = create_order(args.price, args.title, args.desc, price_currency=args.currency)
        if "error" in r or r.get("status") == "invalid":
            print("ORDER ERROR:", json.dumps(r, indent=2))
            sys.exit(1)
        print("✅ ORDER CREATED")
        print(f"  Order id : {r.get('id')}")
        print(f"  Status   : {r.get('status')}")
        print(f"  Payment  : {r.get('payment_url')}")
        print(f"  Pay this  : {r.get('pay_amount')} {r.get('pay_currency')}")
        print("Send the Payment URL to your customer (works with crypto, no card).")
    elif args.cmd == "check":
        r = get_order(args.id)
        if "error" in r:
            print("CHECK ERROR:", json.dumps(r, indent=2))
            sys.exit(1)
        status = r.get("status")
        print(f"Order {args.id}: status = {status}")
        if status == "paid":
            print("  ✅ Payment received in your CoinGate wallet!")
        elif status == "pending":
            print("  ⏳ Waiting for the customer to pay.")
        elif status == "invalid":
            print("  ❌ Order expired / cancelled.")


if __name__ == "__main__":
    main()
