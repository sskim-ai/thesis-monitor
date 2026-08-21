# thesis-monitor — 2026-08-21 Combined Natural Review
## KR Natural Production + KRX 16:05 + Phase 9.1 Promotion Gate + US Morning Night-Futures Availability Audit

### Metadata

- Task type: `READ_ONLY_NATURAL_REVIEW_AND_PROMOTION_GATE`
- Instruction version: `2.0`
- Date: `2026-08-21 KST`
- Start review: `after 17:05 KST`
- Repository: `sskim-ai/thesis-monitor`
- Current safe main/operating before KR natural cycle:
  `33c2f8be376b2cbb2961ecf9dc3c873715e0a034`
- Phase 9.1A final:
  `d4a4daf08ff5f68bc1072cc065e69ca5de5da145`
- Phase 9.1B final:
  `2ea8c43c6ec5ef986c23ea15ea707b5e93a720f6`
- Phase 9.1C final:
  `d0dc76a2446ee5ef9188d1b06dcb241df004c143`
- Current Phase 9.0E mode:
  `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Production Assist: `OFF`
- Public Action: `0.4.5`
- Output schema: `4`
- Runtime policy: `daily-review-v3.10`

This instruction supersedes the earlier 2026-08-21 KR-natural-review-only instruction for the post-17:05 review.

The combined review must answer four independent questions:

1. Did the untouched KR natural production cycle remain safe?
2. What did KRX naturally publish at the 16:05 observation?
3. Is the zero-runtime-diff Phase 9.1A→9.1B→9.1C chain safe to promote?
4. Why was the US morning market summary unable to use the latest night-futures data, and was the suppression behavior correct?

---

# 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260821-kr-natural-review-phase9-1-promotion-gate-and-night-futures.md`

If the earlier review instruction has already been committed:

- do not silently edit it
- commit this file as a new v2 instruction
- mark the earlier instruction `SUPERSEDED_BY_V2` in the completion report
- implementation/review work must cite this v2 instruction commit SHA

Before review:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Record:

- instruction path
- instruction commit SHA
- instruction version `2.0`
- review branch
- current main SHA
- current operating SHA

Recommended review branch:

`codex/20260821-combined-natural-review-promotion-gate`

No force push / history rewrite.

---

# 1. Hard prohibitions

Until the review and severity classification are complete, do NOT:

- manually run KR primary
- manually run KR backup
- manually run US primary/backup
- manually send Telegram
- mutate Pilot
- mutate DB
- rewrite production archive
- rewrite receipts
- change Phase 9.0E mode
- change AI Scheduled Task configuration
- change KRX telemetry configuration
- change night-futures collector configuration
- deploy a repair
- call a provider to "recreate" historical availability timing

For both KRX and night-futures timing, use only naturally captured artifacts, stored raw responses, cached provider payloads, scheduler logs, receipts, and immutable archives.

A live query performed after the fact cannot prove what was available at 08:06–08:20 or 16:05, so it must not be used as evidence of first publication time.

---

# 2. Track A — exact KR natural production run

Identify the canonical 2026-08-21 KR natural production run.

Record:

- packet ID
- assessment date
- market
- policy
- schema
- packet creation time
- AI candidate completion time
- validation completion time
- production terminal time
- Telegram delivery time
- primary/backup source
- expected message count
- actual message count
- archive reference
- receipt reference
- SHA-256 where available

If both primary and backup artifacts exist, explain which one became canonical and why.

---

# 3. Track A — required KR production artifacts

Collect/reference the exact natural artifacts:

1. production packet
2. raw AI candidate
3. numeric validation result
4. semantic validation result
5. runtime message-quality result
6. final-language result
7. delivery-reason artifact
8. deterministic fallback artifact if used
9. delivery-result artifact
10. final receipt
11. exactly-once/duplicate evidence
12. actual sent-message bundle:
   - KR market digest 1
   - stock messages 7
   - actual order
   - exact sent text

Do not rewrite originals.

Sanitized copies may be generated only for the review bundle.

---

# 4. Track A — production outcome review

Report:

- AI candidate generated: YES/NO
- AI validation: PASS/FAIL
- exact hard validation errors
- runtime quality: PASS/FAIL
- final language: PASS/FAIL
- delivery mode: AI-assisted / deterministic fallback / actual repository vocabulary
- sent / expected
- pending
- failed
- duplicate
- receipt integrity
- exactly-once
- backup behavior

If AI was rejected, include each exact hard error string with ticker + section.

---

# 5. Track A — prior repair regressions

Check whether any previously repaired issue recurred:

- depositary/security false positive
- `chart_risk_reward` framework leakage
- generic numeric-summary repetition
- business/valuation numeric ownership leakage
- structured supply tuple repetition
- RR cross-section duplication
- current-vs-history valuation ownership
- crossed confirmation future-trigger leakage
- RR support/resistance overlap
- Korean final-language defects
- generic cash-flow boilerplate

Classify each:

- `OBSERVED_PASS`
- `OBSERVED_FAIL`
- `NOT_OBSERVED`

---

# 6. Track A — Phase 9.0E KR negative control

KR is excluded from the initial user-visible cash-flow rollout.

Verify:

- operating mode remained `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- KR user-visible cash-flow selected count = `0`
- actual KR messages with new OCF/PPE-CAPEX/FCF enrichment = `0/7`
- OpenDART blocked cash-flow leakage = `0`
- Korean Re generic enterprise FCF leakage = `0`
- Phase 9.0D.1 baseline-consistency repair created no KR regression
- cash-flow kill-switch/config unchanged
- message count/delivery semantics unchanged

Any actual KR cash-flow user-visible leakage is P0.

---

# 7. Track A — price / supply / valuation review

For all 7 KR stock messages review:

- dynamic support/resistance
- RR overlap suppression
- confirmation lifecycle
- crossed-confirmation future-trigger leakage
- structured supply tuple
- supply as-of-date
- current-vs-history valuation ownership
- security/share-basis fail-closed
- no fabricated support/resistance/valuation

Report exact anomalies.

---

# 8. Track B — KRX 16:05 natural telemetry

Locate the exact natural `2026-08-21 16:05 KST` telemetry observation.

Record:

- observation ID
- scheduler source
- scheduled slot
- actual start/end
- role-proof eligibility
- target XKRX business date
- HTTP status
- provider business date(s)
- stock/index row counts for each supported endpoint
- eligible row counts if available
- publication readiness enum
- raw payload refs
- raw SHA-256
- scheduler exit status
- duplicate observation count

Do not make another provider call.

---

# 9. Track B — KRX publication-pattern comparison

Compare only natural stored evidence:

- prior natural 16:05 observation(s)
- 2026-08-21 08:05 observation
- 2026-08-21 16:05 observation

Summarize:

```text
same-day 16:05 behavior
vs
next-morning 08:05 behavior
```

Classify independently:

- telemetry capture plumbing
- provider publication completeness
- current-snapshot promotability
- whether the evidence strengthens or weakens the pattern:
  `16:05 provider pending → 08:05 provider complete`

Do not invent a required number of observations.

Do not integrate KRX into the user-visible digest in this task.

---

# 10. Track C — US morning night-futures incident scope

Review the 2026-08-21 US morning market-summary night-futures path.

The morning runtime reportedly behaved approximately as follows:

```text
first attempt around 08:06:30 KST
multiple retries
last attempt around 08:20:05 KST
last_error = none
ready_products = 0
latest expected NIGHT pair not usable
older validated NIGHT pair existed
older pair was not substituted as current
user-visible night-futures summary suppressed
```

Treat these as claims to VERIFY against repository evidence, not assumptions.

Also verify whether the morning runtime recorded the expected latest session as:

`2026-08-21 NIGHT`

and whether that expectation was actually correct under the provider's BAS_DD / NIGHT session-date convention.

This verification is critical.

---

# 11. Track C — exact night-futures artifacts

Locate/reference, if present:

1. US morning market-summary packet
2. night-futures preflight result
3. collector attempt logs
4. retry timeline
5. provider raw-response/cache artifacts for each attempt
6. session-basis/calendar derivation artifact
7. instrument/contract matching result
8. preceding eligible DAY selection result
9. provider raw-change cross-check result
10. stale/availability classification
11. AI dispatch gate or hold reason
12. market-summary final rendered output
13. latest prior successfully validated NIGHT pair
14. any later naturally captured artifact showing the previously missing NIGHT session

Do not manually query the provider to recreate the missing morning window.

---

# 12. Track C — reconstruct the 08:06–08:20 timeline

Create a precise timeline table:

| Time KST | Attempt | Expected NIGHT session | Provider HTTP/result | Row count | Candidate products | Ready products | Error | Classification |
|---|---:|---|---|---:|---:|---:|---|---|

Use exact times from logs.

Report:

- first request time
- retry count
- retry spacing
- final deadline/cutoff
- latest provider business/session date actually returned
- whether rows were absent vs present-but-not-ready
- whether contract/instrument rows were found
- whether parse/canonicalization ran
- whether session matching failed
- whether data was simply unavailable

No inferred timestamps.

---

# 13. Track C — verify session-date semantics

This is the most important diagnostic step.

Determine what the provider means by NIGHT `BAS_DD`.

Verify, from existing code/tests/raw natural evidence:

```text
NIGHT BAS_DD
→ which overnight trading session?
→ which preceding eligible DAY should it pair with?
```

Check specifically whether the correct morning expectation at 08:06–08:20 KST was truly:

`2026-08-21 NIGHT`

or whether provider semantics imply a different BAS_DD label.

Do not assume the date merely from wall-clock date.

Use:

- `night-futures-session-basis-v1`
- `Phase 8.5.4.2` calendar traversal logic
- existing natural/historical raw provider evidence
- XKRX eligible-day calendar

If the expectation itself was wrong, classify that separately from provider delay.

---

# 14. Track C — regression against Phase 8.5.4.2

Explicitly verify no recurrence of:

- same-BAS_DD DAY/NIGHT pairing
- calendar-day subtraction
- failure to skip XKRX holiday/weekend
- future DAY pairing
- wrong preceding eligible DAY
- instrument mismatch
- contract mismatch
- maturity/rollover mismatch
- provider raw-change conflict ignored

For any pair that reached canonicalization, confirm:

```text
NIGHT
→ preceding eligible XKRX DAY
→ same instrument
→ same contract/maturity
→ deterministic point/% change
→ provider cross-check
```

Classify each control PASS/FAIL/NOT_REACHED.

---

# 15. Track C — stale prior pair

If an older validated NIGHT pair was present, record:

- NIGHT BAS_DD
- preceding DAY BAS_DD
- product
- contract
- NIGHT close/value
- DAY close/value
- computed point change
- computed percentage change
- why it was stale relative to morning expectation
- whether it was correctly suppressed from user-visible output

Do not treat the older pair as a substitute current value.

The stale suppression should be classified independently from the root cause of missing current data.

---

# 16. Track C — later publication evidence

Search only stored/natural artifacts after the morning deadline to determine whether the missing expected NIGHT session later appeared.

If a later stored observation exists, record:

- first naturally observed available timestamp
- BAS_DD
- products available
- raw source reference
- source SHA
- whether both KOSPI200 and KOSDAQ150 were available
- whether exact contract/maturity matched
- whether canonical pairing would pass

If no stored observation proves first availability:

state:

`FIRST_PROVIDER_AVAILABILITY_TIME = UNKNOWN`

Do not infer it from a later successful query time.

---

# 17. Track C — root-cause classification

Classify the incident using one or more of:

```text
PROVIDER_PUBLICATION_DELAY
EXPECTED_SESSION_DATE_BASIS_MISMATCH
COLLECTOR_DEADLINE_TOO_EARLY
TELEMETRY_CAPTURE_GAP
PARSER_OR_CANONICALIZATION_ERROR
CALENDAR_TRAVERSAL_REGRESSION
CONTRACT_OR_ROLLOVER_MISMATCH
PROVIDER_DATA_CONFLICT
EXPECTED_NO_LATEST_SESSION
UNKNOWN_INSUFFICIENT_EVIDENCE
```

For each selected class:

- confirmed facts
- interpretation
- unknowns
- evidence paths

Do not collapse provider delay and wrong expected-session semantics into one cause.

---

# 18. Track C — deadline adequacy

Evaluate whether the `~08:20 KST` final deadline is operationally appropriate.

Do NOT change it in this review.

Use evidence only.

Classify:

```text
DEADLINE_ADEQUATE
DEADLINE_TOO_EARLY
DEADLINE_UNPROVEN
```

Consider:

- historical naturally captured provider publication times if available
- whether 08:20 repeatedly misses valid later data
- morning message delivery SLA
- whether waiting longer would jeopardize the 08:15/08:30 task architecture
- fallback behavior
- stale-data safety

Do not recommend a later deadline solely because one incident occurred.

---

# 19. Track C — user-facing safety assessment

Assess separately:

## Availability quality
Was latest night-futures context unavailable?

## Safety behavior
Did the system correctly avoid:

- stale substitution
- wrong-session substitution
- fabricated pair
- last-known-value presentation as current

A provider availability issue can coexist with a safety PASS.

Report:

```text
NIGHT_FUTURES_LATEST_AVAILABILITY = ...
NIGHT_FUTURES_FAIL_CLOSED_SAFETY = PASS/FAIL
```

---

# 20. Track C — internal stale-item leakage risk

Inspect whether stale night-futures observations are retained in internal market-environment items after the dispatch gate suppresses user-visible output.

Determine:

- archive retention behavior
- candidate/rendering boundary
- whether another renderer could accidentally consume stale items
- whether user-visible candidate construction already has a hard freshness gate

Classify:

```text
STALE_INTERNAL_ITEM_RISK = NONE / LOW / MATERIAL
```

Do not modify code in this review.

If a narrow hardening is desirable but no current leakage exists, classify P2 unless it presents material cross-renderer safety risk.

---

# 21. Track C — no manual repair during review

This task is diagnostic.

Do not:

- extend retry window
- change expected BAS_DD logic
- change XKRX calendar logic
- alter collector polling
- change AI gate
- alter user-facing summary

If a defect is confirmed, recommend a bounded repair instruction after review.

---

# 22. Combined P0 / P1 / P2 classification

Classify findings across KR production, KRX, night futures, and promotion.

## P0 examples

- wrong user-visible numeric fact
- KR 9.0E cash-flow leakage
- duplicate Telegram
- receipt/exactly-once break
- wrong night-futures session actually displayed
- stale night-futures data displayed as current
- wrong contract/maturity used
- production corruption
- unsafe valuation/security basis

P0 blocks Phase 9.1 promotion.

## P1 examples

- night-futures expected-session logic is wrong but fail-closed prevented user-visible misinformation
- repeated provider-publication mismatch materially degrades morning market context
- material AI reasoning/ownership regression
- shared runtime defect relevant to 9.1 safety
- internal stale-candidate path has material leakage risk

Material P1 gets bounded repair before affected feature expansion.

## P2 examples

- one-off provider delay with correct fail-closed behavior
- minor wording
- optional telemetry improvement
- KRX publication timing still incomplete
- stale archive item exists but cannot reach user-visible renderers

P2 does not block Phase 9.1 promotion.

---

# 23. Phase 9.1 dependent-chain promotion gate

Verify the exact chain:

```text
main/operating
→ Phase 9.1A final d4a4...
→ Phase 9.1B final 2ea8...
→ Phase 9.1C final d0dc...
```

Confirm:

- ancestry clean
- all instruction commits present
- all final branch CI PASS
- 9.1A P0/P1 = `0/0`
- 9.1B P0/P1 = `0/0`
- 9.1C P0/P1 = `0/0`
- all three runtime/user-visible diff = `0`
- current KR natural has no blocking P0
- current KR natural has no shared-runtime material P1 relevant to 9.1
- night-futures finding does not indicate a shared regression that makes promotion unsafe
- main drift is understood

Do not promote before this gate is explicit.

---

# 24. Promotion decision

Set exactly:

`PHASE_9_1_CHAIN_PROMOTION_READY = YES/NO`

YES requires:

- KR natural P0 = 0
- relevant material P1 affecting shared runtime = 0
- 9.0E KR negative control PASS
- delivery/exactly-once PASS
- 9.1A/B/C validated
- runtime/user-visible diff = 0
- ancestry safe
- no night-futures finding that makes shared runtime promotion unsafe

Important:

A night-futures P2 provider timing issue with fail-closed safety PASS does **not** block the zero-runtime-diff Phase 9.1 chain.

A confirmed night-futures P1 may be parallel if isolated from 9.1/shared promotion safety; state that explicitly.

---

# 25. If promotion gate = YES

Promotion may be performed as the final part of this task.

Preferred:

```text
origin/main
→ 9.1A
→ 9.1B
→ 9.1C
```

via clean fast-forward if ancestry remains linear.

If main drift exists:
perform explicit clean integration.

After promotion record:

- final main SHA
- operating SHA
- worktrees clean
- API restart yes/no
- API health
- Phase 9.0E mode unchanged
- AI schedules unchanged
- KRX telemetry unchanged
- night-futures collector config unchanged
- Production Assist OFF

No manual natural run.

---

# 26. If promotion gate = NO

Do not partially cherry-pick the Phase 9.1 chain.

Preserve all branch evidence.

State:

- blocker
- severity
- affected subsystem
- whether bounded repair is:
  - KR production
  - night futures
  - shared runtime
  - Phase 9.1 itself

Recommend exactly one next repair instruction.

---

# 27. Post-promotion smoke

If promoted, run read-only smoke covering:

- 9.1 canonical working-capital core
- 9.1C shadow-only boundary
- Phase 9.0E user-visible cash flow unchanged
- baseline cash-flow consistency
- fallback/exactly-once
- night-futures config unchanged
- KRX telemetry config unchanged
- Public Action/schema unchanged

No Telegram.

No manual Scheduled Task.

---

# 28. Required report — actual KR sent messages

Create:

`docs/reports/20260821-kr-natural-sent-message-bundle.md`

Include exact actual sent text:

- market digest
- 7 stock messages
- sent order
- packet ID
- delivery mode
- send time

This is mandatory for human review.

---

# 29. Required report — KR production

Create:

`docs/reports/20260821-kr-natural-production-review.md`

Include:

- lifecycle
- AI validation
- fallback
- runtime quality
- final language
- delivery
- exactly-once
- P0/P1/P2

---

# 30. Required report — 9.0E KR negative control

Create:

`docs/reports/20260821-phase9-0e-kr-negative-control.md`

Include:

- mode
- selector result
- cash-flow user-visible count
- OpenDART leakage
- Korean Re generic FCF leakage
- shared-runtime regressions
- PASS/FAIL

---

# 31. Required report — KRX 16:05

Create:

`docs/reports/20260821-krx-1605-natural-telemetry-review.md`

Include:

- observation
- row counts
- provider date
- readiness
- raw refs/SHA
- comparison to 08:05
- publication-pattern interpretation

---

# 32. Required report — US night-futures availability review

Create:

`docs/reports/20260821-us-morning-night-futures-availability-review.md`

Mandatory sections:

1. morning summary impact
2. expected latest session
3. exact retry timeline
4. raw provider availability
5. session-date semantics
6. Phase 8.5.4.2 regression controls
7. stale prior pair
8. later publication evidence
9. root-cause classification
10. deadline adequacy
11. fail-closed safety
12. stale internal-item risk
13. P0/P1/P2
14. repair recommendation, if any

---

# 33. Required report — night-futures timeline JSON

Create:

`docs/reports/20260821-us-morning-night-futures-timeline.json`

Recommended fields:

```text
review_date

morning_packet_id
first_attempt_at
last_attempt_at
retry_count

attempts:
  - timestamp
    expected_session
    provider_result
    returned_session_dates
    rows
    candidate_products
    ready_products
    error
    raw_ref
    raw_sha

expected_session_recorded
expected_session_verified
session_basis_verdict

stale_prior_pairs:
  ...

first_later_natural_availability:
  timestamp
  session
  raw_ref
  confidence

root_cause
deadline_verdict
fail_closed_safety
stale_internal_item_risk
```

If a field cannot be proven, use null/UNKNOWN rather than inference.

---

# 34. Required artifact index

Create:

`docs/reports/20260821-combined-natural-review-artifact-index.md`

Reference:

- KR packet
- KR AI candidate
- KR validation
- KR fallback
- KR receipt
- actual KR sent bundle
- KRX 16:05 telemetry
- US morning packet
- night-futures preflight
- night-futures attempt logs
- night-futures raw payloads
- prior valid NIGHT pair
- later natural availability evidence
- Phase 9.1 A/B/C finals

For each:

- type
- path/ref
- SHA if available
- original/immutable status

Do not push secret-bearing raw files.

---

# 35. Required Phase 9.1 promotion report

Create:

`docs/reports/20260821-phase9-1-chain-promotion-gate.md`

Include:

- KR natural severity
- 9.0E negative control
- KRX telemetry
- night-futures review impact on promotion
- 9.1A/B/C status
- ancestry
- CI
- final gate
- promotion result

---

# 36. Required combined summary JSON

Create:

`docs/reports/20260821-combined-natural-review-summary.json`

Recommended keys:

```text
kr:
  packet_id
  delivery_mode
  ai_validation
  runtime_quality
  sent
  expected
  duplicates
  p0
  p1
  p2

phase_9_0e_kr:
  mode
  selected_count
  injection_count
  leakage_count
  result

krx_1605:
  observation_id
  http_status
  provider_date
  row_counts
  readiness

night_futures:
  morning_packet_id
  expected_session_recorded
  expected_session_verified
  first_attempt_at
  last_attempt_at
  retry_count
  ready_products
  first_later_natural_availability
  root_cause
  deadline_verdict
  fail_closed_safety
  stale_internal_item_risk

phase_9_1:
  a_final
  b_final
  c_final
  promotion_ready
  promotion_performed
  final_main
  operating
```

---

# 37. One final ZIP

Create exactly one sanitized review bundle:

`20260821-combined-natural-review-and-promotion-gate-bundle.zip`

Include at minimum:

```text
20260821-kr-natural-sent-message-bundle.md
20260821-kr-natural-production-review.md
20260821-phase9-0e-kr-negative-control.md
20260821-krx-1605-natural-telemetry-review.md
20260821-us-morning-night-futures-availability-review.md
20260821-us-morning-night-futures-timeline.json
20260821-combined-natural-review-artifact-index.md
20260821-phase9-1-chain-promotion-gate.md
20260821-combined-natural-review-summary.json
```

If promotion occurs, also include:

`20260821-phase9-1-operating-promotion.md`

Report ZIP SHA-256.

---

# 38. Completion response format

## Work instruction
- path
- v2 instruction commit SHA
- prior instruction superseded YES/NO

## Repository before review
- main
- operating
- clean state

## KR natural
- packet ID
- timestamps
- AI/fallback
- validation errors
- sent/expected
- duplicates
- receipt

## Actual sent messages
- bundle link/path

## Phase 9.0E KR negative control
- selected
- injection
- leakage
- PASS/FAIL

## KRX 16:05
- observation
- rows
- readiness
- 08:05 comparison

## US morning night futures
- expected session recorded
- expected session verified
- retry timeline
- provider result
- prior stale pair
- later natural availability
- root cause
- deadline verdict
- fail-closed safety
- stale internal-item risk
- severity

## P0/P1/P2
- exact counts/issues

## Phase 9.1 chain
- A/B/C finals
- ancestry
- CI
- zero-runtime-diff

## Promotion
- `PHASE_9_1_CHAIN_PROMOTION_READY = YES/NO`
- performed YES/NO
- final main
- operating
- health

## Bundle
- ZIP path
- SHA-256
- Git report URLs

---

# 39. Final decision principles

Do not conflate "missing latest data" with "unsafe behavior."

For night futures, answer two separate questions:

```text
Was the latest valid NIGHT session available?
```

and:

```text
Did the system behave safely when it was not available?
```

The correct system may produce:

```text
availability = unavailable
safety = PASS
```

Likewise, a wrong expected session-date basis can be a real defect even when fail-closed suppression prevents misinformation.

For KRX, distinguish:

```text
capture plumbing
vs
provider publication timing
```

For Phase 9.1, remember that A/B/C are zero-runtime-diff work. A P2 night-futures publication-timing issue should not be used as an excuse to delay the clean 9.1 chain.

Promotion should be blocked only by a real P0 or a material P1 that makes shared production safety uncertain.

The combined review should leave us with:

1. the exact KR messages actually sent,
2. a clean KR natural safety verdict,
3. the exact KRX 16:05 publication state,
4. a factual explanation for the missing morning night-futures summary,
5. a verified session-date-basis verdict,
6. a decision on whether the 08:20 deadline is actually the problem,
7. a Phase 9.1 promotion decision,
8. one bounded repair recommendation only if evidence requires it.
