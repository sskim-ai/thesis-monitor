# Price-Only AI Evidence Egress Audit

## Result

`APPROVED_VARIABLE_AI_RUNTIME = AVAILABLE_WITH_FIELD_RESTRICTIONS`

`PRICE_ONLY_EVIDENCE_EGRESS = PASS`

The route is the signed-in local Codex CLI used only for this archive trial. No new provider,
subscription, or API key was added. Allowed fields are ticker/security identity, market/currency,
cutoff, adjusted public OHLCV, deterministic candle features, canonical pivot/zone IDs, and bounded
segment summaries. User/account/portfolio/thesis/Telegram/auth fields and precomputed Fibonacci are
blocked.

| Ticker | Audit | Bytes | Violations |
|---|---|---|---|
| 000660 | PASS | 214790 | [] |
| 003690 | PASS | 203030 | [] |
| 005490 | PASS | 217169 | [] |
| 005930 | PASS | 218581 | [] |
| 010120 | PASS | 234391 | [] |
| 012450 | PASS | 233751 | [] |
| 086280 | PASS | 242561 | [] |
| CORZ | PASS | 191170 | [] |
| CRCL | PASS | 180365 | [] |
| GOOGL | PASS | 217501 | [] |
| HUT | PASS | 209641 | [] |
| IBM | PASS | 214196 | [] |
| MU | PASS | 184413 | [] |
| RXRX | PASS | 221752 | [] |
| SKHY | PASS | 28538 | [] |
| SNDK | PASS | 147269 | [] |
| TSLA | PASS | 197471 | [] |
| TSM | PASS | 216846 | [] |
| WRD | PASS | 168986 | [] |
| WULF | PASS | 162639 | [] |

Private-field egress: `0`; secret egress: `0`; unrelated-thesis egress: `0`.
The sanitized packet examples are in `20260826-variable-ai-anchor-price-only-evidence.json`.
