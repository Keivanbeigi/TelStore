# CoinGate Crypto Checkout — Setup Guide

This lets you sell the bot and **receive crypto (BTC/USDT etc.) directly in
your own wallet — no bank card or PayPal required** on your side.

---

## Step 1 — Create a free CoinGate account
1. Go to **https://coingate.com** and click **Sign up**.
2. Use any email (no card needed). Verify the email.
3. Kosovo/Iran caution: CoinGate requires a payout method. Set your
   **crypto wallet** as the payout (Settings → Payout settings → add a BTC or
   USDT address). That way you receive crypto, not fiat — no bank needed.

## Step 2 — Create an Auth Token
1. In CoinGate: **Settings → API → Create Auth Token**.
2. Copy the token (it looks like a long random string).

## Step 3 — Use the checkout script
With the `scripts/coingate.py` helper (already in the bot repo):

```bash
export COINGATE_AUTH_TOKEN="YOUR_TOKEN_HERE"

# Create a payment for the customer:
python coingate.py create --price 29 --title "Crypto Quest Bot — license" \
    --desc "Source code, English, configurable" --currency USD

# It prints an ORDER ID and a PAYMENT URL.
# Send the PAYMENT URL to the customer. They pay in crypto. Done.
```

To confirm the customer actually paid:
```bash
python coingate.py check --id <ORDER_ID>
# status = paid → you got the crypto in your wallet
```

---

## How to see your money
- Log into CoinGate → **Balances**. Your received crypto shows there.
- You can HODL it, or withdraw it to any of your own crypto wallet addresses
  (CoinGate → Withdraw). No bank ever involved.

---

## Optional: put the payment link on your sales page
`sales-page.html` in the project root has a button marked
`PAYMENT_URL_HERE`. Replace that with a real CoinGate payment URL, or point it
at your Telegram bot, and host the page anywhere free (GitHub Pages, etc.).

---

## Notes / limitations (honest)
- CoinGate itself is fine to use from IR with a crypto payout, but **its sign-up
  may ask for verification** depending on your country/volume. For small sales
  it's usually automatic.
- Crypto is volatile — set your price in USD and CoinGate shows the equivalent
  crypto at checkout, so you get the USD amount in crypto.
- The `coingate.py` helper is a command-line tool. For an automated button, we
  can wire it into the bot later if you want.
