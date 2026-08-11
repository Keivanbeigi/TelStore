#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NOWPayments integration for Crypto Quest bot
=============================================
Creates crypto payment invoices so customers can pay with 230+ coins
(USDT/BSC, USDT/TRC20, BTC, ETH, etc.) and the money settles to YOUR wallet.

HOW TO ACTIVATE (you must do this - Iran-friendly account needed):
  1. Register at https://nowpayments.io and create an account.
  2. In the dashboard, get your API key (Settings -> API Keys).
  3. Put it in the .env file next to this script as:
        NOWPAYMENTS_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  4. (Recommended) Set a payout wallet in the dashboard so settled funds
     go straight to your address.
  5. For automatic confirmation, expose the webhook (see below) so the bot
     gets notified when a payment completes. If you can't host a public
     webhook, the bot still works: the customer pays, you confirm manually.

API reference: https://documenter.getpostman.com/view/7908511/SVYdfCq2
"""
import json
import urllib.request
import urllib.parse

import config

API_URL = "https://api.nowpayments.io/v1"

API_KEY = config.NOWPAYMENTS_API_KEY

def is_configured():
    """True if a NOWPayments API key is set in .env."""
    return bool(API_KEY)

def _post(path, payload):
    """POST to NOWPayments. Returns parsed JSON or None."""
    if not API_KEY:
        return {"ok": False, "error": "NOWPayments API key not configured"}
    url = f"{API_URL}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", "application/json")
    req.add_header("x-api-key", API_KEY)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"ok": False, "statusCode": e.code, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _get(path, params=None):
    """GET from NOWPayments."""
    url = f"{API_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("x-api-key", API_KEY)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"ok": False, "statusCode": e.code, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_payment(price_usd=5.0, pay_currency="usdttrc20", order_id=None, description="Crypto Quest Premium"):
    """
    Create a crypto payment invoice.
    Returns dict with 'payment_id', 'pay_address', 'pay_amount', 'payment_status',
    or an error dict.
    """
    payload = {
        "price_amount": float(price_usd),
        "price_currency": "usd",
        "pay_currency": pay_currency,
        "order_description": description,
    }
    if order_id:
        payload["order_id"] = order_id
    return _post("/payment", payload)

def get_payment_status(payment_id):
    """Check a payment's status."""
    return _get(f"/payment/{payment_id}")

def get_supported_currencies():
    """List supported pay currencies (cached per call)."""
    return _get("/currencies")

def format_payment_instructions(payment):
    """
    Build a customer-facing message with the deposit address/amount.
    `payment` is the dict from create_payment().
    """
    if not payment or payment.get("status") is False:
        return ("Payment service temporarily unavailable. Please try again later, "
                "or use the manual wallet address from the menu.")
    pay_address = payment.get("pay_address", "")
    pay_amount = payment.get("pay_amount", "")
    pay_currency = payment.get("pay_currency", "")
    payment_id = payment.get("payment_id", "")
    status = payment.get("payment_status", "")
    return (
        "🧾 Payment invoice created!\n\n"
        f"💵 Amount: {pay_amount} {pay_currency.upper()}\n"
        f"📮 Send to this address:\n`{pay_address}`\n\n"
        f"🆔 Invoice: {payment_id}\n"
        f"Status: {status}\n\n"
        "✅ Send the exact amount to the address above. "
        "Once confirmed by the network, your Premium activates automatically."
    )


if __name__ == "__main__":
    # Quick self-test
    print("API key configured:", is_configured())
    if is_configured():
        # list a few supported BSC tokens
        cur = get_supported_currencies()
        if isinstance(cur, dict) and "currencies" in cur:
            bsc = [c for c in cur["currencies"] if "bsc" in c.lower()][:10]
            print("Sample BSC tokens:", bsc)
        else:
            print("Could not fetch currencies:", cur)
    else:
        print("Put NOWPAYMENTS_API_KEY in .env to activate.")