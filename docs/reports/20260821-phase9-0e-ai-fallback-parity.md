# Phase 9.0E AI/Fallback Parity

The AI packet and deterministic fallback independently built `cash-flow-user-visible-v1` from the
same assessment and canonical reports. All 13 subjects matched on selection, reason, display state,
evidence signature, period, currency, primary Fact, freshness, and baseline suppression identity.

| Ticker | Context ID | FCF Fact | Period | Currency | Baseline suppressions |
|---|---|---|---|---|---:|
| CORZ | `cf-visible-5a15006d395d5f4da5723f10` | `cashflow:1b8f3742f33dd3b66f8f7673` | 2026-06-30 | USD | 0 |
| CRCL | `cf-visible-2b8960edf1cd08d7ca39788e` | `cashflow:402041c63553616360d17391` | 2026-06-30 | USD | 0 |
| GOOGL | `cf-visible-ff8f5aa957b09eb3dc2d0b20` | `cashflow:ddb47708bf7d36a4c0b0c7d2` | 2026-06-30 | USD | 0 |
| IBM | `cf-visible-9470f30e203c89653449b38c` | `cashflow:a158304539a9269c66f6d2cb` | 2026-06-30 | USD | 0 |
| MU | `cf-visible-3c5b12f7d52fec6986398e4b` | `cashflow:96e9c3b873f3678d4dec0ff3` | 2026-05-28 | USD | 0 |
| RXRX | `cf-visible-5e048de3ef608b2fbec80fa3` | `cashflow:498c289d4304c0822d861ec3` | 2026-06-30 | USD | 0 |
| SNDK | `cf-visible-837a3bf06acd7cf26c38db34` | `cashflow:1b8db0b46c63ae9369231151` | 2026-07-03 | USD | 0 |
| TSLA | `cf-visible-635f92b114431790e8ed87e8` | `cashflow:68666c261434dab50ab88a8d` | 2026-06-30 | USD | 4 |
| WULF | `cf-visible-6704740e6a488541f55e11b6` | `cashflow:6fd003ea029e4d7b03f681f3` | 2026-06-30 | USD | 0 |

Parity mismatches: selection `0`, Fact ID `0`, period `0`, scope `0`, sign `0`, currency `0`, and
suppression identity `0`. A fixture changes a suppressed context's baseline claim ID and proves the
delivery preparation fails before send.

Every selected FCF retains two exact inputs. Reproduction errors are `0`; the fallback uses the
same canonical numeric formatter as AI binding, including CORZ's half-rounding case `$-723.29M`.

