# Payment and delivery fixes (2026-11)

Five defects found in a follow-up audit, each reproduced before the fix and
covered by a regression test that fails if the guard is removed.

## 1. Unverified payments were accepted when the chain head was unavailable

`chaincheck.verify_transaction()` only ran the confirmation check when the
`eth_blockNumber` RPC call returned a value:

```python
if latest_block_hex:                # no else branch
    confirmations = latest_block - tx_block + 1
```

If a public RPC node timed out or returned an empty result during congestion,
the whole confirmations block was skipped and the transaction was reported as
**paid** — so a pending or reorg-able transaction could auto-deliver a product.

Confirmations are now mandatory, and a missing or unparseable chain head returns
`underpaid` with `Unable to verify chain head (confirmations unknown)`. The bot
routes that to manual owner approval instead of delivering.

## 2. A native coin transfer could pay for a token-priced product

The `token_contract` requirement was enforced only inside the ERC-20 log loop.
When a transaction carried no matching ERC-20 transfer, execution fell through
to the native-coin branch and valued the coin amount **1:1 against the USD
price**. On Polygon, sending 5.05 POL (about $1) settled a $5.05 USDT order.

The native-coin fallback now runs only when the merchant has not required a
specific token. Otherwise the result is `not_found` with an explicit
"No ERC-20 transfer of the required token" reason. Merchants who price in native
coin are unaffected.

## 3. The public product description was used as paid delivery

When a digital product's file failed to send and `deliver` was empty, the
delivery text fell back to `product["description"]` — the storefront listing
shown to everyone before payment:

```python
deliver_text = product.get("deliver") or product.get("description", ...)
```

The buyer paid and received the marketing blurb, and the order was marked
delivered. `description` and `name` are no longer treated as fulfillment: only
`deliver` (or a channel invite link) counts. With neither, the order stays
pending and the owner is alerted with a DELIVERY FAILURE notice.

## 4. Buying a digital file extended channel (VIP) access

`_deliver_product()` reused the subscription writer for every product kind, so
the `days` field on a digital product moved the channel expiry. A $1 file with
`days=30` pushed an existing VIP expiry 30 days into the future — and granted
premium status to a buyer who had none.

Expiry and plan are now written only for `kind == "channel"`. Digital purchases
still record the transaction, but never touch `plan` or `premium_until`.

## 5. Clearing a setting reverted to the .env default

`config._get_setting()` ignored an explicitly saved empty value:

```python
if key in s and s[key] not in (None, ""):   # "" treated as unset
    return str(s[key])
return _load_env_str(key, "").strip()
```

An owner who cleared a setting through the admin panel saw the old `.env` value
come back on the next read. A key present in `settings.json` now wins even when
it is empty.

## Verification

- Suite: **196 passed**, 1 skipped (POSIX-only installer check), 1 expected
  failure — up from 189 before these fixes.
- Each regression test was proved to bite: the guard was removed, the test
  failed, and the file was restored with a matching checksum.
- Deployed to the live server and re-probed there: `underpaid`, `not_found`,
  `ok=False`, unchanged expiry, and a persisted empty setting.

This is a bounded set of bug fixes, not a statement that the full security audit
is complete. Architectural payment limitations remain documented in
`REMAINING_RISKS.md`.