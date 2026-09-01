# Track B — Generic Product-Identifier Numeric Provenance

Fix canonical identifier spans generically.

Controls:
- KF-21
- FA-50
- F-35
- B-21
- A320neo
- S&P500
- KOSPI200
- Russell 2000

Digits embedded in a proven canonical identifier are not standalone numeric claims.

But:
- `KF-21 10대` must validate 10
- `FA-50 마진 12%` must validate 12%
- unsupported `ZZ-999` must not become safe
- plain 21-50 remains numeric/range semantics

No ticker-specific allowlist.
No broad hyphen-number exemption.
