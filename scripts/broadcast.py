#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ارسال گزارش به همه مشترک‌های کانال (broadcast)
================================================
این اسکریپت گزارش را به همه مشترک‌ها می‌فرستد:
- مشترک‌های Premium → گزارش روزانه (هر ۶ ساعت)
- مشترک‌های Free → فقط در روزهای مشخص (اختیاری)

استفاده:
  python broadcast.py --file report.txt            # به همه premium + free
  python broadcast.py --file report.txt --premium  # فقط به premium
  python broadcast.py --file report.txt --test     # فقط به خودت (تست)
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.parse
import datetime


def load_token():
    t = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if t:
        return t
    for p in [os.path.expanduser("~/.crypto-quest.env"),
              os.path.expanduser("~/.hermes/.env")]:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    m = re.search(r'^TELEGRAM_BOT_TOKEN=([^\r\n]+)', f.read(), re.M)
                    if m:
                        return m.group(1).strip().strip('"').strip("'")
            except Exception:
                pass
    raise SystemExit("ERROR: TELEGRAM_BOT_TOKEN not found")


def load_subscribers():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subscribers.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("subscribers", [])
    return []


def send_one(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.loads(resp.read().decode())
            return d.get("ok", False)
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--premium", action="store_true", help="فقط به premium")
    ap.add_argument("--test", action="store_true", help="فقط به chat_id از TELEGRAM_CHAT_ID")
    args = ap.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        print("ERROR: empty report", file=sys.stderr)
        sys.exit(1)

    token = load_token()

    if args.test:
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "129735937")
        ok = send_one(token, chat_id, text)
        print(f"✅ test sent to {chat_id}" if ok else "❌ test failed")
        sys.exit(0 if ok else 1)

    subs = load_subscribers()
    if not subs:
        print("❌ no subscribers found")
        sys.exit(1)

    today = datetime.date.today().isoweekday()  # 1=Mon ... 7=Sun
    sent = 0
    for s in subs:
        plan = s.get("plan", "free")
        chat_id = s.get("chat_id")
        if not chat_id:
            continue
        if args.premium and plan != "premium":
            continue
        # free: فقط یک‌شنبه‌ها (7)
        if not args.premium and plan == "free" and today != 7:
            continue
        if send_one(token, chat_id, text):
            sent += 1

    print(f"✅ ارسال به {sent} مشترک انجام شد")
    sys.exit(0 if sent > 0 else 1)


if __name__ == "__main__":
    main()