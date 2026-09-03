# Run-53 V2 Production-Equivalent Replay

## Identity

- Packet: `2026-09-03-us-run-53-055ae8ea01f6`
- Immutable packet file SHA-256:
  `969b52387ca9eee504f922fced85f629aaf85bffaf43234514b2ffa2ea5ac7d1`
- Model / effort: `gpt-5.6-sol` / `xhigh`
- Timeout: 1,800 seconds, equal to the natural accepted-V2 runtime
- Namespace: `PACKET_READINESS_REPAIR_20260903_RUN53_TEST_ONLY`
- Production send/state mutation: `0/0`

The repaired readiness gate allowed the frozen packet to reach network preflight, Codex state,
app-server, and the signed-in model. Context, candidate, accepted, and explicit V2 counts are
`14/14/14/14`; fallback is `0`; final message quality is `PASS`.

One model stream disconnect recovered through the existing sampling retry. Strict validation used
one batch schema repair and bounded subject repairs for CRCL, GOOGL, MU, RXRX, SKHY, SNDK, and
WULF. No validator threshold, retry budget, decision policy, or evidence reference was relaxed.

## Accepted Results

| Ticker | Decision | BUY | SELL |
| --- | --- | ---: | ---: |
| CORZ | HOLD | 4.5 | 5.5 |
| CPNG | HOLD | 5 | 5 |
| CRCL | HOLD | 4.5 | 5.5 |
| GOOGL | HOLD | 4.5 | 5.5 |
| HUT | SELL | 3 | 7 |
| IBM | HOLD | 5 | 5 |
| MU | HOLD | 5.5 | 4.5 |
| RXRX | HOLD | 4.5 | 5.5 |
| SKHY | HOLD | 4.5 | 5.5 |
| SNDK | SELL | 4 | 6 |
| TSLA | SELL | 2.5 | 7.5 |
| TSM | HOLD | 4.5 | 5.5 |
| WRD | SELL | 3.5 | 6.5 |
| WULF | SELL | 3 | 7 |

Distribution is HOLD 9 and SELL 5. Every balance sums to 10 and the distribution was not forced.

## GOOGL Ownership

- Candidate: HOLD, BUY 4.5 / SELL 5.5
- Prior accepted decision: BUY
- Adjudication: `KEEP_V2`
- Accepted: HOLD, BUY 4.5 / SELL 5.5
- Accepted evidence fingerprint:
  `v2-accepted-evidence:sha256:710a4481485b965644f4067e5ce54b38220c49fbb0c12f4049e3eedbe2cd977d`
- Accepted decision ID:
  `v2-accepted-decision:sha256:24d380954ac3e176b1314a73d475cc2593842060e178aefaf7926fdf41e3bba3`

The adjudicated accepted plan owns the final block; the raw candidate is not rendered directly.

- `RUN53_NETWORK_PREFLIGHT_REACHED = PASS`
- `RUN53_CODEX_APP_SERVER_REACHED = PASS`
- `RUN53_MODEL_REACHED = PASS`
- `RUN53_FALLBACK_COUNT = 0`
- `ACCEPTED_DECISION_PLAN_REMAINS_AUTHORITY = PASS`

