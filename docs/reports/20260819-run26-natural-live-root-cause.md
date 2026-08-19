# Run-26 Natural Live Root Cause

## Outcome

- Packet: `2026-08-19-us-run-26-cd80a8e4d373`
- AI sent: `0`
- Deterministic fallback sent: `14/14`
- Duplicate fallback: `0`
- Original archive rewrites: `0`
- Telegram replay sends: `0`

## Failure Classes

- RXRX/WULF: `CANONICAL_SEMANTIC_BINDING`
- CORZ: `TYPED_VALUATION_OCCURRENCE`
- Night futures: `PROVIDER_CANONICALIZATION / SESSION_BASIS`
- Fallback: `RENDER_CONTEXT_PARITY`

## Immutable Evidence SHA256

- packet: `7562c45aa4c8c54bd1d8a55a693384779dd1966817251b5c32cd78deb652539c`
- ai_raw_output: `19faad5ec00009c3b1e2979eeb13a48881abddc6ae808250a7a7b14ff13e62a0`
- validation: `27228073ea44cb8aec33fb232a2084e747ddfd10ea6cf2d1c124f4ae956a3b8a`
- six_error_validation: `883a4d54521ffc8456e29593420ede9087db39d26305cd9f3071fef46d1a17c4`
- bound_output: `057dcf5d5d0810ce33925804c60164db3358df0b50a7eb623c5a68f5a10d139f`
- rendered_fallback: `b19e4c741b0893f216d6228aba68739f741b2524939ac67821155b1c4f479ffa`
- runtime_receipt: `0af979769fd1f6521a9e8d498a265cd45197019a2c8c67ffcac60c34f99c9dd9`
- actual_sent_bundle: `08cacca55a6edf01607c785a84f14fff9a37f94289240ef22a3407ede78f6b0a`
- archive_complete: `c6cfd1bcef9e7af95dc4ae2f2fe1522c2dee9600af695235f6e904d86ab9deb3`

## Retrospective Result

- Target six-error attempt before: `6` errors
- Repaired replay after: `0` errors
- Full validator: `PASS`
- Runtime message quality: `passed`
- Natural AI-assisted delivery remains `PARTIAL`; retrospective replay is not a live send.

## Zone / RR Audit

| Ticker | Support | Resistance | Archived RR | Repaired RR |
|---|---|---|---:|---|
| HUT | 80.640825–85.959175 | 84.109809–89.670191 | 0.658648x | `UNAVAILABLE` |
| WULF | 15.552386–16.461814 | 16.001096–17.088904 | 0.422787x | `UNAVAILABLE` |

The selected support and resistance zones overlap. The repaired backend and both
archive-only render paths therefore suppress current RR with
`nearest_support_resistance_overlap`; no zone or ratio is moved by hand.
