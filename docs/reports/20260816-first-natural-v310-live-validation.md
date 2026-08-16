# First Natural daily-review-v3.10 Live Validation

## Disposition

**Message-quality FAIL; operational pipeline PASS and already counted.**

The natural US session completed the automated contract: the final validator passed, all 14
AI-assisted messages were delivered once, the required archive hashes verified, and the completion
marker preceded the exactly-once Pilot record. The persisted runtime count therefore changed from
US 1/5 to US 2/5 while KR stayed 2/5.

The required human review does not approve this session as a quality success. CRCL contains an
internally inconsistent confirmation transition, SKHY describes its verified ADS identity as
unverified instead of limiting the warning to denominator/share/currency basis, and all 13 US stock
messages mechanically use the same Korean-style daily/short/medium investor-flow frame. This audit
did not edit the already-persisted count because manual counter mutation is prohibited. The mismatch
between runtime US 2/5 and human quality approval requires an explicit follow-up decision.

## Repository And Runtime

| Item | Verified state |
|---|---|
| `origin/main` | `d0daa6816e171288e24baf59bb5894a1415e0bff` |
| Development checkout | same, clean before audit documentation |
| Operating checkout | same, clean before audit documentation |
| Policy/schema | `daily-review-v3.10` / 4 |
| Structure/Pilot/renderer | v2 / v3 / v3 |
| Security identity | `security-identity-v2` |
| Financial quality | `financial-quality-taint-v2` |
| AI mode | `shadow` |
| Production Assist | disabled |
| API/US/KR health | API healthy; US packet completed and passed; no KR packet yet |

All four Scheduled Tasks remain ACTIVE at 08:15, 08:30, 16:15, and 16:55 KST, target the operating
checkout, and retain policy v3.10. No task was changed or duplicated during this audit.

## Natural Session

| Field | Value |
|---|---|
| Market/date/run | US / 2026-08-16 / 20 |
| Packet | `2026-08-16-us-run-20-6c15d0003955` |
| Claim | `b2d53426-1a78-4bbd-83bb-c6314b8014c1` |
| Source run | success, 13/13 tickers, zero failures |
| Packet readiness | ready, immutable, normal session |
| Primary | claimed by `codex-us-primary` |
| Backup | `no_pending_packet`; no second analysis |
| Active/packet/output/rendered | 13/13/13/13 |
| Logical messages/chunks | 14/14; every message fit one chunk |

The Primary completed one allowed correction cycle. The initial draft bound 162 references and was
rejected with nine errors covering denied valuation facts plus two unbound HUT prose numbers. The
correction removed or reworded the unsafe uses. The final output retained the same claim identity and
passed with 158 canonical bindings.

## Numeric And Validator

| Check | Result |
|---|---|
| Automatic bindings | 158 |
| Manual bindings | 0 |
| Rejected final bindings | 0 |
| Formatter errors | 0 |
| Unresolved placeholders | 0 |
| Numeric-label duplication | 0 |
| Source/instrument mismatch | 0 |
| Final validator | PASS, 0 errors |
| Rejected draft sent | no |

The final quality telemetry was `flagged`, not hard-failed. SKHY had insufficient core numeric
grounding; SNDK had insufficient core and valuation grounding; WRD had insufficient core grounding.
Those omissions were safe, but they also prevent the stock set from satisfying the requested
two-number relational standard uniformly.

## Security And Financial Safety

- GOOGL is `verified_non_depositary` with Tier A SEC evidence. Current PER 12.4x, market-estimated
  fPER 19.29x, current PBR 6.61x, and historical PER percentile 13% were exposed through eligible
  lineage only.
- SKHY is `verified_depositary`, security type ADS, with official ratio 0.1 ordinary share per ADS.
  Its current-security denominator/share/currency basis remains insufficient, so PER/PBR/fPER and
  ADR conversion stayed absent.
- TSM kept TWD issuer financial amounts and USD security price separate. No ADR conversion was made.
- TSM and WRD resolved to `unknown` identity in the natural packet even though the deployment
  cross-section recorded `verified_depositary`. The live database rows remain inferred
  `local+openfigi`; no overnight lower-tier row overwrite was found. This is a deployment-audit versus
  packet-resolution consistency gap, while the resulting multiple withholding is fail-closed.
- CORZ, GOOGL, HUT, IBM, and WULF retained Tier A common-equity identity with null ADR ratio and
  direction. No unsafe numeric or qualitative valuation leakage was found.

## Message Review

### Market

PASS. The market message uses verified oil, breakeven inflation, real yield, VIX, relative-sector,
and night-futures facts. It treats KOSPI200/KOSDAQ150 night futures only as Korean opening context,
does not infer missing breadth or market-wide flow, connects four portfolio transmission candidates,
and gives three concrete next checks without method narration.

### Blocking Findings

1. **AI_REASONING / VALIDATION - CRCL transition contradiction.** The core judgment says the
   confirmation breakout transitioned to `failed_breakout`; the price section and packet delta say
   `failed_breakout_to_not_reached`. The current state cannot be both transitions in the same review.
2. **AI_REASONING / VALIDATION - SKHY identity wording.** The packet verifies ADS identity and the
   official 0.1 ratio, but the message says the security identity itself is unverified. The correct
   limitation is the current-security denominator/share/currency basis. The conservative conclusion
   is safe, but its stated reason is false.
3. **KNOWLEDGE_ROUTING / AI_REASONING - US supply boilerplate.** All 13 stock messages begin their
   supply section with the same daily/short/medium investor-flow frame. That is the KR horizon model
   mechanically applied to US stocks and is substantive cross-stock repetition.

### Other Gaps

- **CANONICALIZATION / PACKET / DATA:** TSM and WRD packet identity state differs from the deployed
  identity cross-section. Values remain safely withheld, but the contract evidence is inconsistent.
- **PERSISTENCE:** runtime recorded US 2/5 before this mandatory human quality review. Exactly-once
  mechanics worked, but the quality gate and persisted count now disagree.

### Per-Stock Review

| Ticker | Result | Notes |
|---|---|---|
| CORZ | pass with common supply issue | Earnings growth, negative EPS/PBR context, structure and RR are connected. |
| CRCL | fail | Confirmation transition contradicts the packet delta and its own price section. |
| GOOGL | pass with common supply issue | Tier A identity and relational valuation are correctly used. |
| HUT | pass with common supply issue | Unsafe $0.59 was removed; consensus fPER and PBR are correctly framed. |
| IBM | pass with common supply issue | Earnings, valuation, dynamic structure and next evidence are connected. |
| MU | pass with common supply issue | Low forward multiple is correctly fenced by memory-cycle peak risk. |
| RXRX | pass with common supply issue | PER is not forced; clinical, runway and dilution framework is used. |
| SKHY | fail | Safe withholding, but the explanation incorrectly denies verified ADS identity. |
| SNDK | caution | Safe financial-quality withholding; core and valuation grounding were flagged. |
| TSLA | pass with common supply issue | High expectations are linked to margin/FCF execution; no unsafe amount leaks. |
| TSM | caution | TWD/USD separation is correct; packet identity is unexpectedly `unknown`. |
| WRD | caution | Unsafe amounts/multiples remain absent; packet identity is unexpectedly `unknown`. |
| WULF | pass with common supply issue | PBR percentile meaning and capital-intensive execution checks are correct. |

Observer and holder sentences are distinct for 13/13 stocks. Current Strong/Medium dynamic
structure is primary, missing support does not borrow registered support, RR is omitted when
unavailable, and crossed confirmation is never automatically promoted to support.

## Delivery And Archive

The persisted delivery service sent market delivery 104 followed by stock deliveries 105-117. Each
database payload's final text matches the immutable archive text and content hash. All 14 rows are
`sent`, each has one Telegram chunk, and no deterministic fallback was sent. The Primary left the
validated set pending; the bounded 08:30 persisted-delivery retry sent that exact set without packet
regeneration, analysis rerun, or renderer rerun. Backup then found no pending packet.

`archive-complete.json` verifies 13/13 required artifact hashes. Nanosecond file times establish the
required sequence: `delivery-result.json` -> `archive-complete.json` -> `state-v3.json`. The packet ID
and assessment date each occur once in Pilot state.

The exact delivered text is preserved in
[20260816-first-natural-v310-live-telegram-preview.md](20260816-first-natural-v310-live-telegram-preview.md).
The machine audit is in
[20260816-first-natural-v310-live-audit.json](20260816-first-natural-v310-live-audit.json).

## Pilot And Safety

- Runtime before: KR 2/5, US 1/5.
- Persisted runtime after natural processing: KR 2/5, US 2/5.
- Human quality disposition: FAIL.
- Audit-triggered Telegram, DB, archive, assessment, Pilot, or Scheduled Task mutation: zero.
- Production Assist remains disabled.

No counter correction was made. A separate decision is required to reconcile the already-persisted
US 2/5 with this failed human quality review before another session is treated as an approved Pilot
advance.

## Remaining Gaps

1. Correct the CRCL transition interpretation without weakening deterministic validation.
2. Bind identity-aware Unknown wording so verified depositary identity is not conflated with an
   unverified current-security denominator.
3. Remove the KR 1/5/20-style investor-flow frame from US stock reasoning when no US flow contract
   exists.
4. Reconcile TSM/WRD deployment identity evidence with live packet resolution.
5. Decide how human quality rejection affects an automatically recorded Pilot success; do not edit
   the counter ad hoc.
