#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات تلگرام کانال — مدیریت اشتراک‌ها
=====================================
این ربات پیام‌های تلگرام را گوش می‌دهد (polling) و دستورات اشتراک را مدیریت می‌کند.

دستورات:
  /start        - شروع و راهنما
  /subscribe    - ثبت‌نام رایگان (گزارش هفتگی)
  /premium      - اشتراک پولی (گزارش روزانه هر ۶ ساعت)
  /unsubscribe  - لغو اشتراک
  /status       - وضعیت اشتراک
  /help         - راهنما

نیازمندی‌ها:
  TELEGRAM_BOT_TOKEN (از .env یا متغیر محیطی)
  python-telegram-bot  (pip install python-telegram-bot)

اجرا:
  python bot.py
"""
import json
import os
import re
import sys
import time
import datetime

# ------------------------------------------------------------
#  تنظیمات
# ------------------------------------------------------------
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
SUBSCRIBERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subscribers.json")

# قیمت‌ها
PRICE_CRYPTO_USD = 5          # $5/ماه
PRICE_RIALS = 200000          # ۲۰۰ هزار تومن/ماه

# کیف پول کریپتو — چندشبکه‌ای
CRYPTO_ADDRESS = "0xB20c44e0C5deef5c7ba5293D6eBE4Af278B836cD"

# شبکه‌های پشتیبانی‌شده (BSC اول و پیشنهادی)
# هر شبکه: نام، استاندارد توکن، پیشنهادی یا نه، و توضیح
CRYPTO_NETWORKS = [
    {
        "name": "BSC",
        "standard": "BEP-20",
        "currency": "USDT (BEP-20) / BNB",
        "recommended": True,
        "note": "پیشنهادی — کارمزد بسیار پایین و سریع",
        "recommended_label": "⭐ پیشنهادی"
    },
    {
        "name": "Ethereum",
        "standard": "ERC-20",
        "currency": "USDT (ERC-20) / ETH",
        "recommended": False,
        "note": "امن اما کارمزد (گس) بالا",
        "recommended_label": ""
    },
    {
        "name": "Polygon",
        "standard": "MATIC",
        "currency": "USDC / POL",
        "recommended": False,
        "note": "کارمزد کم، شبکه لایه ۲",
        "recommended_label": ""
    }
]

def get_recommended_network():
    """شبکه پیشنهادی (BSC) را برمی‌گرداند."""
    for n in CRYPTO_NETWORKS:
        if n.get("recommended"):
            return n
    return CRYPTO_NETWORKS[0]

def format_crypto_payment():
    """متن کامل راهنمای پرداخت چندشبکه‌ای را می‌سازد."""
    lines = [f"💰 قیمت: ${PRICE_CRYPTO_USD}/ماه\n",
             "🌐 شبکه‌های پشتیبانی‌شده:"]
    for n in CRYPTO_NETWORKS:
        flag = n.get("recommended_label", "")
        lines.append(f"  {flag}{n['name']} ({n['standard']}): {n['currency']}")
        lines.append(f"      {n['note']}")
    lines.append("")
    lines.append(f"🏦 آدرس کیف پول (همه شبکه‌ها):")
    lines.append(f"  `{CRYPTO_ADDRESS}`")
    lines.append("")
    lines.append("💡 برای کارمزد کمتر، از شبکه BSC استفاده کن.")
    lines.append("")
    lines.append("بعد از پرداخت، هش تراکنش را با این فرمت بفرست:")
    lines.append("  /pay <txhash>")
    lines.append("")
    lines.append("📲 پرداخت ریالی: /pay_rial")
    return "\n".join(lines)

ZARINPAL_MERCHANT = ""        # ← Merchant ID زرین‌پال (اختیاری)

# ------------------------------------------------------------
#  ذخیره/بارگذاری مشترک‌ها
# ------------------------------------------------------------
def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        try:
            with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"subscribers": []}

def save_subscribers(data):
    with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_subscriber(data, chat_id):
    for s in data["subscribers"]:
        if str(s.get("chat_id")) == str(chat_id):
            return s
    return None

# ------------------------------------------------------------
#  پردازش پیام (بدون python-telegram-bot — با raw API)
# ------------------------------------------------------------
import urllib.request
import urllib.parse

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print("send error:", e)
        return None

def get_updates(offset):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?timeout=25&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode()).get("result", [])
    except Exception as e:
        print("getUpdates error:", e)
        return []

# ------------------------------------------------------------
#  هندلر دستورات
# ------------------------------------------------------------
def handle_command(chat_id, username, command):
    data = load_subscribers()
    sub = find_subscriber(data, chat_id)

    if command == "/start":
        text = ("👋 سلام! به کانال Crypto Quest خوش آمدی!\n\n"
                "از اینجا گزارش‌های روزانه ماموریت‌های فارمینگ XP را دریافت کن.\n\n"
                "دستورات:\n"
                "🆓 /subscribe — ثبت‌نام رایگان (گزارش هفتگی)\n"
                "💎 /premium — اشتراک پولی (گزارش روزانه هر ۶ ساعت)\n"
                "🚫 /unsubscribe — لغو اشتراک\n"
                "📊 /status — وضعیت اشتراک\n"
                "❓ /help — راهنما")
        send_message(chat_id, text)

    elif command == "/subscribe":
        if sub:
            send_message(chat_id, "✅ شما قبلاً مشترک هستید! برای مشاهده وضعیت /status بزنید.")
        else:
            data["subscribers"].append({
                "chat_id": str(chat_id),
                "username": username or "",
                "plan": "free",
                "subscribed_at": datetime.datetime.now().isoformat(),
                "premium_until": None,
                "payment_method": None,
            })
            save_subscribers(data)
            send_message(chat_id, "✅ اشتراک رایگان فعال شد! گزارش هفتگی دریافت می‌کنید.\nبرای گزارش روزانه، /premium بزنید.")

    elif command == "/premium":
        if sub and sub.get("plan") == "premium":
            until = sub.get("premium_until", "نامشخص")
            send_message(chat_id, f"💎 شما Premium هستید تا {until}\nبرای مدیریت /status بزنید.")
        else:
            text = (f"💎 اشتراک Premium — گزارش روزانه هر ۶ ساعت\n\n"
                    f"{format_crypto_payment()}")
            send_message(chat_id, text)

    elif command.startswith("/pay "):
        txhash = command.split(" ", 1)[1].strip()
        if not sub or sub.get("plan") != "premium":
            data = load_subscribers()
            sub = find_subscriber(data, chat_id)
            if not sub:
                data["subscribers"].append({
                    "chat_id": str(chat_id), "username": username or "",
                    "plan": "premium", "subscribed_at": datetime.datetime.now().isoformat(),
                    "premium_until": (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat(),
                    "payment_method": "crypto",
                })
            else:
                sub["plan"] = "premium"
                sub["premium_until"] = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
                sub["payment_method"] = "crypto"
            save_subscribers(data)
        send_message(chat_id, f"✅ پرداخت کریپتو ثبت شد! (tx: {txhash[:20]}...)\n"
                              f"Premium شما به مدت ۳۰ روز فعال شد. منتظر بررسی نهایی باشید.")

    elif command == "/pay_rial":
        send_message(chat_id, "💳 لینک پرداخت ریالی به زودی در دسترس است. (درگاه زرین‌پال در حال راه‌اندازی)")

    elif command == "/unsubscribe":
        if sub:
            data["subscribers"] = [s for s in data["subscribers"] if str(s.get("chat_id")) != str(chat_id)]
            save_subscribers(data)
            send_message(chat_id, "🚫 اشتراک شما لغو شد.")
        else:
            send_message(chat_id, "شما مشترک نیستید.")

    elif command == "/status":
        if not sub:
            send_message(chat_id, "شما مشترک نیستید. /subscribe بزنید.")
        else:
            plan = "💎 Premium" if sub.get("plan") == "premium" else "🆓 Free"
            until = sub.get("premium_until", "—")
            send_message(chat_id, f"📊 وضعیت اشتراک:\n\nپلن: {plan}\nتاریخ عضویت: {sub.get('subscribed_at','—')[:10]}\nPremium تا: {until}")

    elif command == "/help":
        send_message(chat_id, ("❓ راهنما:\n"
                               "🆓 /subscribe — ثبت‌نام رایگان\n"
                               "💎 /premium — اشتراک پولی\n"
                               "🚫 /unsubscribe — لغو\n"
                               "📊 /status — وضعیت\n"
                               "❓ /help — راهنما"))

    else:
        send_message(chat_id, "❓ دستور ناشناخته. /help بزنید.")

# ------------------------------------------------------------
#  حلقه اصلی (polling)
# ------------------------------------------------------------
def main():
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    print("✅ ربات در حال اجرا... (polling)")
    offset = 0
    while True:
        try:
            updates = get_updates(offset)
            for upd in updates:
                update_id = upd.get("update_id", 0)
                offset = update_id + 1
                msg = upd.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                username = msg.get("from", {}).get("username", "")
                text = msg.get("text", "").strip()
                if chat_id and text:
                    handle_command(chat_id, username, text)
        except Exception as e:
            print("loop error:", e)
        time.sleep(1)

if __name__ == "__main__":
    main()