#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ارسال پیام به تلگرام — نسخه لینوکس/GitHub Actions
از TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID از محیط استفاده می‌کند.
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.parse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("message", nargs="?", help="متن پیام")
    ap.add_argument("--file", help="خواندن از فایل")
    ap.add_argument("--chat", default=os.environ.get("TELEGRAM_CHAT_ID", ""))
    args = ap.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = args.chat

    if not token or not chat_id:
        print("ERROR: TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID تنظیم نشده‌اند", file=sys.stderr)
        sys.exit(1)

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read().strip()
    elif args.message:
        text = args.message
    else:
        text = sys.stdin.read().strip()

    if not text:
        print("ERROR: پیام خالی", file=sys.stderr)
        sys.exit(1)

    # خرد کردن متن طولانی به تکه‌های زیر 4000 (محدودیت تلگرام)
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]

    for chunk in chunks:
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": chunk,
        }).encode("utf-8")
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        req = urllib.request.Request(url, data=data)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if not result.get("ok"):
                    print(f"ERROR: {result}", file=sys.stderr)
                    sys.exit(1)
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

    print("✅ پیام به تلگرام ارسال شد")


if __name__ == "__main__":
    main()