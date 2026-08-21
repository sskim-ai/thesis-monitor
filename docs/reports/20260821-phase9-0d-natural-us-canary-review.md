# Phase 9.0D Natural US Canary Review

## Decision

The first natural US runtime cash-flow canary existed and completed successfully. Production also
completed safely through deterministic fallback, and the canary influenced production by exactly
zero. Nine current-formal full-FCF paths and one OCF-only path were exercised.

Human cross-artifact review found one material integration defect: the TSLA fallback says the
current thesis has an FCF deficit, while the current-formal canary says 2026 first-half cumulative
PPE-only FCF is positive `$352M`. The automated Unknown-resolution audit did not detect this
period/scope/sign conflict. The canary remains safe because it is not user-visible, but selective
integration should not start until that bounded gate is repaired.

`PHASE_9_0E_READY = NO`

## Work Instruction

- Path: `docs/work-instructions/20260821-phase-9-0d-natural-us-canary-review.md`
- Version: `1.0`
- SHA-256: `b9355f051912f84afb3dd0b426940a1bef80ac9b16e08286222a2a7c61314a99`
- Instruction commit: `509d5b4dde275784f77aee6764d6bd3d3c65cc3a`
- Review branch: `codex/20260821-us-natural-canary-review`
- Base/origin main/operating: `3d6cfab1d881c336ff64c66466d12068aa51d1e4`
- Runtime, main, and operating changes: `0 / 0 / 0`

## Natural US Run

| Field | Evidence |
|---|---|
| Packet | `2026-08-21-us-run-30-5a3b7c1c4390` |
| Assessment | `2026-08-21`, US, `daily-review-v3.10`, output schema `4` |
| Monitor run | `30`, success, 13/13 stocks |
| Monitor completion | stored `2026-08-20 23:06:29` UTC, about `08:06:29 KST` |
| Packet generation | `2026-08-21 08:20:05 KST` |
| Scheduler source | natural `launchd` daily monitor; no manual run |
| US primary/backup | scheduled `08:15/08:30 KST`; exact owner attribution was removed with the completed claim files |
| Late claim IDs | `cc86b0d2-806d-4519-9ef3-274229470386`, `5c8d5ce3-048a-47eb-a8db-931cbb566c6a` |

No duplicate or alternative production packet exists for this assessment date. The canonical run is
run 30. The local 08:30 persisted-delivery retry reported `no_pending_ai_delivery`; it did not rerun
analysis or send anything.

## Production Lifecycle

1. The natural monitor produced the ready packet at 08:20.
2. An AI output arrived after the delivery deadline. Its first validation bound 131 numbers
   automatically but rejected three semantic errors: denied GOOGL and WULF earnings facts and a TSM
   risk/reward direction mismatch.
3. Another late claim was rejected as `stale_claim_output`. A corrected comparison-only output was
   archived at 08:43, after production had already terminated.
4. At 08:40 the deterministic fallback sent the digest plus 13 stock messages.
5. SQLite read-only evidence shows delivery IDs 214-227 all `sent`, each with `attempt_count=1` and
   `fallback_sent`; failed, pending, and duplicate counts are zero.
6. The fallback terminal artifact was finalized after the last send at `08:40:20.687794 KST`.
7. The detached canary started at `08:40:20.904657 KST` and completed at
   `08:40:20.949026 KST`.

Production outcome: AI candidate not sent, deterministic fallback `14/14`, exactly-once PASS.
`Natural AI-Assisted Delivery` remains `PARTIAL`, independently from the canary result.

## Production Isolation

| Influence surface | Count |
|---|---:|
| Telegram content/count | 0 / 0 |
| Fallback eligibility | 0 |
| Exit status / backup trigger | 0 / 0 |
| Production receipt / exactly-once | 0 / 0 |
| Pilot / assessment / warning persistence | 0 / 0 / 0 |
| Canary Telegram deliveries | 0 |

The canary used a detached child process and its own immutable namespace. Its manifest pins the
production delivery SHA `580cf76d6fbb68ef9f8eba4688b2716bbbb9c0515c13614cecbdc3a87858de7f`.
No canary number appears in the deterministic or fallback payload.

## Canary Identity

- Canary: `cf-canary-f5ce3f836df99c546cf6f696`
- Attempt: `attempt-20260820T234020904657Z-816a3625`
- Shadow candidate: `cf-shadow-a45b45e49cf7d3f1a8c06785`
- Policy: `cash-flow-runtime-shadow-canary-v1`
- Consumption contract: `cash-flow-shadow-consumption-v1`
- Invocation: natural deterministic-fallback terminal path
- Status: `COMPLETE_PASS`
- Total child latency: `20.408ms`
- Production influence: `0`

## Coverage

| Category | Count | Tickers |
|---|---:|---|
| Monitored | 13 | CORZ, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF |
| Canonical eligible | 12 | all except SKHY |
| Actually consumed | 10 | CORZ, CRCL, GOOGL, HUT, IBM, MU, RXRX, SNDK, TSLA, WULF |
| Full FCF | 9 | CORZ, CRCL, GOOGL, IBM, MU, RXRX, SNDK, TSLA, WULF |
| OCF only | 1 | HUT |
| Formal-lagging-provisional, context only | 2 | TSM, WRD |
| Blocked | 1 | SKHY |
| N/A | 0 | none in the US packet |

TSM and WRD retained canonical historical facts but were not rendered as current. SKHY had no
canonical issuer cash-flow fact and was suppressed. These are natural freshness and blocked-case
negative controls, both PASS.

## Full-FCF Lineage

Every consumed full-FCF subject had a reported OCF fact, reported PPE-CAPEX fact, and a derived FCF
fact whose two input IDs matched exactly. Period, duration, USD currency/unit, issuer entity scope,
statement basis, and source occurrence were compatible. All source filing dates preceded the packet
cutoff.

| Ticker | OCF | PPE CAPEX | FCF | Period | Result |
|---|---:|---:|---:|---|---|
| CORZ | 230,949,000 | 954,244,000 | -723,295,000 | 2026 H1 YTD | PASS |
| CRCL | 538,505,000 | 10,389,000 | 528,116,000 | 2026 H1 YTD | PASS |
| GOOGL | 84,859,000,000 | 80,598,000,000 | 4,261,000,000 | 2026 H1 YTD | PASS |
| IBM | 7,766,000,000 | 461,000,000 | 7,305,000,000 | 2026 H1 YTD | PASS |
| MU | 45,702,000,000 | 19,602,000,000 | 26,100,000,000 | FY2026 Q3 YTD | PASS |
| RXRX | -187,048,000 | 302,000 | -187,350,000 | 2026 H1 YTD | PASS |
| SNDK | 11,671,000,000 | 177,000,000 | 11,494,000,000 | FY2026, 371 days | PASS |
| TSLA | 8,634,000,000 | 8,282,000,000 | 352,000,000 | 2026 H1 YTD | PASS |
| WULF | -154,300,000 | 1,378,514,000 | -1,532,814,000 | 2026 H1 YTD | PASS |

Lineage, arithmetic, PIT, future-fact, period, currency/unit, entity/basis, occurrence, and AI-side
arithmetic errors: `0 / 0 / 0 / 0 / 0 / 0 / 0 / 0 / 0`.

## OCF-Only Behavior

HUT naturally exercised `OCF_ONLY_CONTEXT`. The sidecar bound `-$32.84M` only to reported OCF,
explicitly said verified PPE acquisition cash outflow was unavailable, and refused to calculate FCF.
Missing CAPEX was not treated as zero. Result: `OBSERVED_PASS`.

## Numeric, Semantic, And Quality

- Cash-flow binding: automatic `10`, manual `0`, rejected `0`, unresolved `0`, formatting failures `0`.
- Canary-local semantic receipt: PASS, error count `0`.
- Unsupported yield/per-share/multiple, CCC, ROIC, runway, valuation, and thesis mutations: `0`.
- Runtime quality: PASS with substantive repetition `0`, template repetition `0`, numeric tuple dumps
  `0`, threshold changes `0`.
- Exact cash-flow numbers are owned by `business_earnings`; there is one exact number per rendered
  subject rather than an OCF/CAPEX/FCF triple dump.

The semantic receipt is correct for the isolated canary output. It does not compare current-formal
cash-flow sign and scope against pre-existing production/fallback prose, which is the P1 found by
this review.

## Unknown Resolution

The automated audit found one explicit cash-flow Unknown, on SNDK, and replaced it with the next
company-specific questions about NAND ASP, data-center demand, inventory, and durability. Automated
counts were before `1`, resolved `1`, still valid `0`, contradictory retained `0`.

Human cross-artifact review found one missed contradiction:

- Production fallback TSLA: "현재는 매출·인도 회복에도 영업이익률 저하와 FCF 적자로 투자
  논리에 초기 균열이 있으며 ... FCF 흑자 전환이 증명되어야 한다."
- Natural canary TSLA: "2026 회계연도 상반기 누계 PPE 재투자 후 잉여현금흐름은 `$352M`로
  양수입니다."
- Canonical fact: `cashflow:68666c261434dab50ab88a8d`, current formal, 2026 H1 YTD.

The baseline does not identify another period or management-defined FCF scope. Adding the canary
sentence without suppressing or relabeling that baseline would create a direct sign contradiction.
Human contradictory-retained count: `1`.

## Earnings-Quality Value Add

| Classification | Tickers | Reason |
|---|---|---|
| MATERIAL_IMPROVEMENT | CORZ, GOOGL, MU, RXRX, SNDK, WULF | Quantified central reinvestment/cash-burn questions with industry-specific cautions |
| MINOR_IMPROVEMENT | CRCL, HUT, IBM | Useful evidence, but secondary applicability, OCF-only scope, or management-FCF reconciliation limits the conclusion |
| NO_MEANINGFUL_CHANGE | none | - |
| DEGRADED | TSLA | Correct canonical sidecar would conflict with retained production FCF-deficit prose |

No thesis-status or valuation-context delta was persisted or proposed by the canary.

## Length And Repetition

- Actual fallback: 14 messages, 12,986 characters, average 927.57.
- Shadow sidecar: 10 snippets, 1,537 characters, average 153.7, 10 numeric claims.
- Hypothetical append-only portfolio increase: 11.84%.
- Actual user-visible increase: 0.

The future integration should replace resolved or conflicting cash-flow prose instead of blindly
appending the entire sidecar. This is rollout design, not a reason to broaden the repair.

## Prior Repair Regression

| Behavior | State | Evidence |
|---|---|---|
| Korean Re depositary false positive | NOT_OBSERVED | Korean Re was not in this US run |
| `chart_risk_reward` industry leakage | OBSERVED_PASS | final candidate kept RR in price positioning; guardrail conflict count 0 |
| Observer/holder ownership | OBSERVED_PASS | 13/13 observer and 13/13 holder texts were distinct |
| Specific Unknowns/next checks | OBSERVED_PASS | all 13 stock reviews supplied subject-specific entries |
| Generic "현재 확인된 핵심 숫자는" | OBSERVED_PASS | exact count 0 |
| Valuation EPS/BVPS in business filler | OBSERVED_PASS | business section leakage count 0 |
| Coarse typed numeric collision | OBSERVED_PASS | final natural output static audit found no collision blocker |
| Non-material RR repetition | OBSERVED_PASS | current RR numeric owner remained `price_positioning`; GOOGL transition was material |
| KR structured supply tuple separation | NOT_OBSERVED | US packet has no KR supply tuple |
| RR cross-section ownership | OBSERVED_PASS | all current RR claims were in `price_positioning` |
| Generic cash-conversion boilerplate | OBSERVED_PASS | canary quality receipt found 0 template/substantive repeats |

The first late candidate's three semantic errors were caught and its corrected text was archived only
after fallback. They were not user-visible and are separate from the 9.0D canary proof.

## Night Futures

Both NIGHT products were unavailable for the expected 2026-08-21 session. They were excluded from
the packet and AI fact catalog, rendered numeric exposure was zero, and the message retained a short
Unknown. Stale substitution and same-date later-DAY misbinding were zero. Result:
`SUPPRESSED_UNAVAILABLE_PASS`.

## KRX 08:05 Telemetry

The natural `NEXT_MORNING_0805` observation exists for target XKRX business date 2026-08-20. All four
endpoints returned HTTP 200 with provider date 2026-08-20:

- KOSPI stocks 942 rows
- KOSDAQ stocks 1,821 rows
- KOSPI indices 51 rows
- KOSDAQ indices 40 rows

Readiness was `PROVIDER_COMPLETE`, `current_snapshot_promotable=true`, scheduler last exit 0. This is
publication-role evidence only; user-visible KRX integration remains off and is not a 9.0E blocker.

## Natural Behavior Matrix

| Behavior | State | Evidence |
|---|---|---|
| Runtime canary plumbing | OBSERVED_PASS | scheduler-derived terminal fallback created one immutable canary |
| Production isolation | OBSERVED_PASS | all influence counts 0 |
| Full FCF consumption | OBSERVED_PASS | 9 current-formal subjects |
| OCF-only consumption | OBSERVED_PASS | HUT, no CAPEX-zero or FCF inference |
| Freshness suppression | OBSERVED_PASS | TSM and WRD context-only, not rendered |
| Blocked/stale suppression | OBSERVED_PASS | SKHY blocked; no old-current substitution |
| Numeric provenance | OBSERVED_PASS | 10/10 automatic, lineage/arithmetic errors 0 |
| Canary-local semantic validation | OBSERVED_PASS | receipt errors 0 |
| Runtime quality | OBSERVED_PASS | repetition and numeric dump counts 0 |
| Unknown resolution across production | OBSERVED_FAIL | TSLA current FCF sign conflict missed |
| KR negative control | NOT_OBSERVED | no natural KR canary had occurred at review time |

## Severity And Next Repair

Open P0: `0`.

Open material P1: `1`.

- TSLA baseline/current-formal FCF sign and scope contradiction is not detected by the cross-artifact
  Unknown-resolution/semantic gate. It is not user-visible today, but would materially distort a
  combined user-visible message.

P2 backlog:

- natural production AI candidate missed the deterministic deadline;
- exact primary/backup claim owner is not retained after completed claim cleanup;
- append-only sidecar integration would add 11.84% and should instead replace existing prose;
- optional management-defined FCF reconciliation;
- KR natural negative control remains unobserved.

Required next task is exactly one bounded repair: extend the cash-flow Unknown-resolution/semantic
gate to compare baseline current FCF sign, period, and scope with current-formal canonical facts.
Conflicting baseline prose must be suppressed or explicitly relabeled. Run-30 TSLA should become an
immutable fixture. The runtime canary need not be disabled because production influence remained 0.

## Artifact Index

All paths below refer to immutable operating evidence. No raw artifact was rewritten or packaged.

| Artifact | Path | SHA-256 |
|---|---|---|
| Production packet | `data/ai_review/inbox/2026-08-21-us-run-30-5a3b7c1c4390.json` | `15cd9a2f112ec2dad21a459ac79c64fcac0bf1955922764351853e6ee61863d2` |
| Corrected late AI output | `data/ai_review/outbox/2026-08-21-us-run-30-5a3b7c1c4390--daily-review-v3.10--559ad45e4dd8.json` | `84acbf01244d2335999be75116a196bc7c93c6e5e43adfa5ebfeaf50b719ad05` |
| First rejected AI output | `data/ai_review/rejected/2026-08-21-us-run-30-5a3b7c1c4390--daily-review-v3.10--559ad45e4dd8.json.1787269270` | `476406d2cab98f35663e157260044bbcd949717fcce90aedb8f3427cecdd5fb9` |
| First validation | `data/ai_review/rejected/2026-08-21-us-run-30-5a3b7c1c4390--daily-review-v3.10--559ad45e4dd8.json.1787269270.validation.json` | `595ba19c863f7e0f2ed600842b21a1bc0c513d60c4491988b9da031cd3e6ac33` |
| Stale late claim | `data/ai_review/rejected/2026-08-21-us-run-30-5a3b7c1c4390--daily-review-v3.10--559ad45e4dd8.json.5c8d5ce3-048a-47eb-a8db-931cbb566c6a.stale_claim_output` | `2a2e5605b48ebc76bdb68dbfc605dbf1f27a08df07ae469cde7897371d90c115` |
| Production validation state | `data/ai_review/pilot/history/2026/08/2026-08-21-us-run-30-5a3b7c1c4390/validation-result.json` | `5a478086ab229a5920436e4a0540f2bc92f80d57aaafd345cee2798f4eea19ce` |
| Deterministic messages | same packet archive, `deterministic-messages.json` | `e266bafd6d8fce38cf7a86d1e6cec3b1213337ef4e74875ad2ee88279962f78c` |
| Fallback messages | same packet archive, `fallback-messages.json` | `11f989274f6fe14d8deeceba56ef5c63b3a935776dd6d1b6ca1130683ac9951b` |
| Delivery result | same packet archive, `delivery-result.json` | `580cf76d6fbb68ef9f8eba4688b2716bbbb9c0515c13614cecbdc3a87858de7f` |
| Canary manifest | canary attempt, `canary-manifest.json` | `f1a8baf7202ccb7c22077781078f55b2f2e8d022f71f60fceb90c9a9e5d85de7` |
| Cash-flow sidecar | canary attempt, `cash-flow-sidecar.json` | `9697283796ee13a6dfba4678948017d9fc982eec6cc078c62ddb80ccadce6517` |
| Shadow input | canary attempt, `shadow-input.json` | `3ae856b60bcbd7b0c48bb940902f77f6eaf3e966ab95557bdad5367ac0419d3d` |
| Raw shadow output | canary attempt, `raw-shadow-output.json` | `c48a4894d28d5e82b0dc4429a4d0315e7e070680634c560f535cd398e60faa2a` |
| Bound shadow output | canary attempt, `bound-shadow-output.json` | `173b8cfa1287d058a71bc87ba55823f92394dd7740701fcf1a1ad8579cf47ad3` |
| Semantic validation | canary attempt, `semantic-validation.json` | `b5a24708e953164d5c08edd5a9081ff6ff1157f2f20d33a295600fec358d323b` |
| Quality receipt | canary attempt, `runtime-quality-receipt.json` | `e6e9088d33811ecc25f749e36697fac166d6eef1e735811e7054c03227e1dd50` |
| Canary receipt | canary attempt, `canary-receipt.json` | `aba7e9a1ef2f56d6de46fd92be5dc8830ce4c9b34d8d8b3e1e30dd0110e0964e` |
| Canary completion | canary root, `canary-complete.json` | `bb26f5c2e5702cdcc923f00a2e8e7652d2c8d44a192a5318e2cf5a4a45170e2f` |
| KRX 08:05 telemetry | `data/telemetry/krx/publication-readiness/2026-08-20.jsonl` | `5ab11b9333332d0ea7f165074dab2334ebabdcb36484688f82c140409b6e84e2` |

The production fallback has no AI message-quality receipt because AI-assisted eligibility was never
reached. Its delivery receipt is the combination of `delivery-result.json`, pilot terminal state,
and immutable read-only database rows 214-227.

## Final Gate

`PHASE_9_0E_READY = NO`

Blocking issue: one material P1, TSLA baseline/current-formal FCF sign/scope contradiction missed by
the cross-artifact gate.

Bounded repair: baseline cash-flow sign/period/scope reconciliation only. No broad research, new
provider, scheduler change, user-visible integration, CCC, ROIC, or KR period recovery belongs in
that repair.
