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

# NOWPayments rejects USDT-TRC20 invoices below ~12 USD (AMOUNT_MINIMAL_ERROR).
# We check this BEFORE calling the API so the customer gets a friendly message
# instead of a raw gateway error. Measured empirically: 11.96 USD still rejected,
# 11.97 USD accepted. Different coins may have different minimums.
MIN_PAYMENT_USD = 12.0

# Cloudflare in front of api.nowpayments.io returns 403 (error 1010) for
# Python-urllib's default User-Agent. Send a normal browser User-Agent so the
# request isn't blocked (curl works by default; Python urllib does not).
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

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
    req.add_header("User-Agent", _UA)
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
    req.add_header("User-Agent", _UA)
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

def validate_price(price_usd):
    """
    Return an error string if the price is too low for NOWPayments, else None.
    Minimal is measured for USDT-TRC20; some coins allow less, but we use a
    conservative floor so invoices don't fail at checkout.
    """
    if float(price_usd) <= 0:
        return "Price must be greater than 0."
    if float(price_usd) < MIN_PAYMENT_USD:
        return f"Amount must be at least ${MIN_PAYMENT_USD:.2f} for crypto checkout."
    return None

def create_payment(price_usd=5.0, pay_currency="usdttrc20", order_id=None, description="Crypto Quest Premium"):
    """
    Create a crypto payment invoice (standard API).
    Returns dict with 'payment_id', 'pay_address', 'pay_amount', 'payment_status',
    or an error dict (including a friendly message for too-low amounts).
    """
    err = validate_price(price_usd)
    if err:
        return {"ok": False, "status": False, "code": "AMOUNT_MINIMAL_ERROR",
                "message": err}
    payload = {
        "price_amount": float(price_usd),
        "price_currency": "usd",
        "pay_currency": pay_currency,
        "order_description": description,
    }
    if order_id:
        payload["order_id"] = order_id
    return _post("/payment", payload)


def create_invoice(price_usd=5.0, pay_currency="usdttrc20", order_id=None, description="Crypto Quest Premium"):
    """
    Create a hosted payment page (invoice). The customer opens the invoice_url
    in their browser to pay with card or crypto — no manual address/amount.
    Returns dict with 'invoice_url', 'id', 'token_id' or an error dict.
    """
    err = validate_price(price_usd)
    if err:
        return {"ok": False, "status": False, "code": "AMOUNT_MINIMAL_ERROR",
                "message": err}
    payload = {
        "price_amount": float(price_usd),
        "price_currency": "usd",
        "pay_currency": pay_currency,
        "order_description": description,
    }
    if order_id:
        payload["order_id"] = order_id
    return _post("/invoice", payload)

def get_payment_status(payment_id):
    """Check a payment's status."""
    return _get(f"/payment/{payment_id}")

def get_supported_currencies():
    """List supported pay currencies (cached per call)."""
    return _get("/currencies")

def format_invoice_instructions(invoice, product=None):
    """
    Build a customer-facing message with a clickable payment link.
    The customer opens the link in their browser to pay with card or crypto.
    """
    url = invoice.get("invoice_url", "")
    name = (product or {}).get("name", "Product")
    price = (product or {}).get("price_usd", 0)
    return (
        f"🧾 Payment page ready!\n\n"
        f"📦 {name}\n"
        f"💰 Price: ${price:.2f}\n\n"
        f"🔗 [Open payment page]({url})\n\n"
        "After paying, tap the button below to confirm and receive your product."
    )


def format_payment_instructions(payment):
    """
    Build a customer-facing message with the deposit address/amount.
    If the invoice couldn't be created (e.g. amount too low), show a friendly,
    actionable message instead of a raw gateway error.
    """
    if not payment or payment.get("status") is False:
        code = (payment or {}).get("code", "")
        msg = (payment or {}).get("message", "")
        if code == "AMOUNT_MINIMAL_ERROR" or "minimal" in str(msg).lower():
            clean = msg if msg.startswith("Amount") else "Amount too low for crypto checkout."
            return (f"⚠️ {clean}\n\n"
                    "The product price you selected is below the minimum for "
                    "crypto payment. Please choose a higher-priced product, or "
                    "the owner can raise this product's price in the settings.")
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