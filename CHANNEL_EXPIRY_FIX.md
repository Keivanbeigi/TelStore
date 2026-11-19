# Channel expiry revocation retry fix

When the Telegram channel removal call fails, the expiry sweep now leaves the expired subscription record intact so the next sweep can retry. The record is downgraded to free only after a successful removal. Existing protection against overwriting a concurrently renewed expiry is retained.

Regression coverage includes failure followed by success, repeated API failures, successful removal once, and preservation of a renewed expiry. Tests use mocked Telegram calls and isolated state; they do not contact real users or channels.

This is a bounded bug fix, not a claim that the full security audit is complete. Existing architectural payment limitations remain documented separately.
