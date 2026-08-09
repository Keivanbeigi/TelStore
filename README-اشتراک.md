# 💎 سیستم اشتراک پولی کانال — راهنمای کامل

> اشتراک کانال تلگرام با پرداخت **کریپتو + ریالی** برای دریافت گزارش‌های روزانه.

---

## 📁 فایل‌ها

```
github/scripts/
├── bot.py             ← ربات تلگرام (polling) — دستورات را مدیریت می‌کند
├── broadcast.py       ← ارسال گزارش به همه مشترک‌های premium
├── subscribers.json   ← لیست مشترک‌ها
├── generate_smart_report.py  ← ساخت گزارش با OpenRouter AI
└── telegram_send.py   ← (قدیمی) ارسال به یک chat
```

---

## 🤖 اجرای ربات (برای گوش دادن به دستورات)

ربات باید **polling** کند (پیام‌ها را گوش دهد) تا `/subscribe` و `/premium` را بفهمد.

### روی سیستم خودت (ساده):
```bash
cd github/scripts
export TELEGRAM_BOT_TOKEN="توکن-بات"
python bot.py
```
این ربات هرگز متوقف نمی‌شود — در پس‌زمینه اجرا کن.

> ⚠️ **مهم:** ربات polling می‌کند. فقط یک جا باید polling کند (سیستم خودت یا سرور، نه هر دو).

### روی سرور (برای ۲۴/۷):
از `deploy_server.sh` یا یک cron استفاده کن که `bot.py` را همیشه روشن نگه دارد.

---

## 💳 پرداخت کریپتو

### تنظیم آدرس کیف پول (در `bot.py`):
```python
CRYPTO_ADDRESS = "0xYOUR_WALLET_ADDRESS"   # ← کیف پول خودت
CRYPTO_CURRENCY = "USDT (TRC20)"
```

### جریان برای کاربر:
1. کاربر `/premium` می‌زند → آدرس و مبلغ را می‌بیند
2. کاربر کریپتو ارسال می‌کند
3. کاربر `/pay <txhash>` می‌زند
4. ربات Premium را فعال می‌کند (۳۰ روز)

> **نکته:** فعلاً تأیید `/pay` دستی/خودکار ساده است. برای تأیید خودکار تراکنش، به API کیف پول/بلاک‌چین نیاز داری.

---

## 💳 پرداخت ریالی (زرین‌پال)

### تنظیم در `bot.py`:
```python
ZARINPAL_MERCHANT = "YOUR_MERCHANT_ID"   # ← شناسه تجاری زرین‌پال
```

### مراحل:
1. حساب زرین‌پال بساز (https://zarinpal.com)
2. Merchant ID بگیر
3. Callback endpoint راه‌اندازی کن

> ⚠️ فعلاً `/pay_rial` پیام «به زودی» می‌دهد. برای فعال‌سازی کامل، درگاه زرین‌پال + callback لازم است.

---

## 📡 ارسال گزارش (GitHub Actions)

هر ۶ ساعت:
```yaml
# workflow
python3 generate_smart_report.py       # ساخت گزارش با AI
python3 broadcast.py --file report.txt --premium  # به همه premium
```

`broadcast.py`:
- به همه مشترک‌های `premium` می‌فرستد (که منقضی نشده‌اند)
- مشترک‌های `free` فقط یک‌شنبه‌ها (گزارش هفتگی)
- `--test` برای تست ارسال به خودت

---

## 📊 مدیریت مشترک‌ها

`subscribers.json`:
```json
{
  "subscribers": [
    {
      "chat_id": "129735937",
      "username": "k1_adineh",
      "plan": "premium",
      "premium_until": "2026-09-09T00:00:00"
    }
  ]
}
```

- `subscribers.json` باید در GitHub ریپازیتوری **commit** شود تا GitHub Actions بتواند بخواند
- وقتی ربات مشترک جدید اضافه می‌کند، باید آن را commit کند (یا از یک روش همگام‌سازی استفاده شود)

> ⚠️ **چالش مهم:** ربات (`bot.py`) مشترک‌ها را به `subscribers.json` محلی اضافه می‌کند، ولی GitHub Actions از نسخه موجود در ریپازیتوری می‌خواند. برای همگام‌سازی، باید `subscribers.json` را بعد از هر تغییر به GitHub commit کنی.

---

## 🧪 تست

```bash
# تست ارسال به خودت
python scripts/broadcast.py --file report.txt --test

# تست ربات به صورت دستی
export TELEGRAM_BOT_TOKEN="..."
python scripts/bot.py   # سپس در تلگرام /start بزن
```

---

## ⚠️ نکات امنیتی

1. **توکن** را هرگز در کد نگذار — از Environment Variable یا Secret استفاده کن
2. **آدرس کیف پول** — مطمئن شو آدرس درست و امن است
3. **subscribers.json** — اگر شامل اطلاعات حساس است، ریپازیتوری را Private نگه دار
4. **تأیید پرداخت** — برای کریپتو حتماً تراکنش را قبل از فعال‌سازی Premium بررسی کن (حداقل به صورت دستی)