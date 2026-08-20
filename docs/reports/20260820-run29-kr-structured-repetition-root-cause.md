# Run-29 KR Structured Repetition Root Cause

Date: 2026-08-20
Packet: `2026-08-20-kr-run-29-6e8809e1e944`

## Immutable Outcome

The final AI candidate passed numeric/semantic validation and rendered-language checks, then failed
only `runtime_message_quality_gate_failed`. Rejected AI messages sent: `0`. Deterministic fallback
delivered `8/8`; pending `0`. Original archive and receipt rewrites: `0`.

## Exact Root Cause

1. The detector treated stable foreign/institution 1/5/20-day canonical supply rows as ordinary
   portfolio prose. They are now typed as `canonical-supply-flow-tuple-v1`; adjacent interpretation
   remains quality-checked.
2. Exact current-price RR was bound in both `core_judgment.text` and
   `price_positioning.text`. `numeric-primary-owner-v1` retains only the price owner when the
   secondary occurrence is mechanically and safely removable.
3. One common financial-period/statement-basis warning repeated across three stocks although each
   following sentence already named a company-specific missing driver.
4. `재고·CAPEX 이후 FCF·ROIC` repeated as a generic watch item across memory and steel stocks even
   though their first watch, Unknown, and next check were already specific.

## Evidence Integrity

- Packet SHA-256: `2f07d5ca1e805fa68bba42f9a27a76dc41ecd8547da6027425a959845b6d4cba`
- Bound output SHA-256: `85882b60f3cae52445e9bd04bfc11813bfa8d1c05fa90f6059a894fa983a0e08`
- Original quality receipt SHA-256: `8972b53e3e5c1affc8ede7a1ddea6fd312aaf4359a6c17136510f52e76bad6fc`
- Delivery result SHA-256: `25dde177480d27f2dc61287b18c18d08fd3d326c3b67ecb32b51bb0aafbda527`
