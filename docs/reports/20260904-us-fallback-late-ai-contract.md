# 2026-09-04 US Fallback and Late AI Contract

The deterministic hard-deadline fallback remains independent of AI claim ownership. It was not removed or delayed by the lease repair.

Controlled tests prove that fallback sends only deterministic payloads when it wins the deadline. A later validated AI result is `archive_only` and invokes no notifier. Re-entering an already delivered AI set also sends no second payload.

| Gate | Result |
|---|---|
| Fallback eligibility after validation failure | `PASS` |
| Late AI sent after fallback | `0` |
| Duplicate sent | `0` |
| Production fallback behavior changed | `0` |
