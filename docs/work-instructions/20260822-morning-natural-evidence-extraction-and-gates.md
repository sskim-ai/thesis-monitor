# thesis-monitor — 2026-08-22 Morning Natural Evidence Extraction & Gate Review

## Metadata
- Task type: `READ_ONLY_EVIDENCE_EXTRACTION_AND_GATE_REVIEW`
- Instruction version: `1.0`
- Date: `2026-08-22 KST`
- Start: `after 09:15 KST observer completion`
- Repository: `sskim-ai/thesis-monitor`
- Current known main/operating: `f5a956930c1fbc4cbc6c6dc053a1cf2e428d4000`
- Phase 9.0E cash-flow mode: `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Working-capital user-visible mode: `OFF`
- Phase 9.1D: `DEPLOYED_PENDING_NATURAL`
- Night-futures telemetry repair: `DEPLOYED`
- Night observers: `08:45 / 09:15 KST`
- Production Assist: `OFF`
- Public Action: `0.4.5`
- Output schema: `4`
- Runtime policy: `daily-review-v3.10`

This task must extract only naturally generated evidence that already exists. It must not create new production evidence.

---

## 0. Repository protocol

Store at:

`docs/work-instructions/20260822-morning-natural-evidence-extraction-and-gates.md`

Before review:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Commit/push this instruction as a docs-only commit before review.

Recommended branch:

`codex/20260822-morning-natural-evidence-review`

Record instruction path, instruction commit SHA, version, current main/operating SHA and worktree cleanliness.

No force push or history rewrite.

---

## 1. Hard prohibitions

Do not:
- manually run US primary/backup
- manually run KRX telemetry
- manually run night-futures observers
- manually query the provider to recreate past availability
- manually send Telegram
- change feature modes
- change night-futures deadline or observer times
- change Scheduled Task configuration
- mutate Pilot or DB
- rewrite production archive or receipts
- alter Phase 9.1D canary
- enable working-capital user-visible output
- deploy a repair

If evidence is missing, report it as missing.

---

## 2. Questions this review must answer

1. What actually happened in the 2026-08-22 US natural production cycle?
2. Did Phase 9.0E selective user-visible FCF appear naturally and safely?
3. Did Phase 9.1D naturally prove Inventory and/or exact Trade AR?
4. What did night-futures production attempts and 08:45/09:15 observers actually capture?
5. What was the 08:05 KRX publication state?
6. What is actually ready next: Inventory enablement, Trade AR enablement, or more natural proof?

---

## 3. US natural production

Identify the canonical 2026-08-22 US natural run and record:
- packet ID
- packet creation time
- AI candidate completion time
- numeric/semantic/runtime-quality/final-language results
- production terminal time
- Telegram delivery time
- primary/backup path
- expected message count
- actual sent count
- pending/failed/duplicate
- receipt reference
- exactly-once result

If both primary and backup produced artifacts, explain which became canonical and why.

Collect/reference:
1. production packet
2. raw AI candidate
3. numeric validation
4. semantic validation
5. runtime-quality validation
6. final-language validation
7. delivery reason
8. deterministic fallback if used
9. delivery result
10. receipt
11. exactly-once evidence
12. exact sent-message bundle: market digest + all monitored stock messages in actual order

If AI was rejected, include every exact hard error with ticker and section.

---

## 4. Phase 9.0E natural FCF proof

Use actual sent production artifacts, not previews.

For each monitored subject report:
- ticker
- eligible/selected/suppressed
- current-formal/full-FCF status
- materiality
- baseline consistency
- actual FCF rendered YES/NO
- canonical FCF Fact ID
- period
- PPE-only scope
- currency
- AI/fallback delivery path

Set exactly:

`PHASE_9_0E_NATURAL = LIVE_PASS_SELECTIVE_SUBSET / FAIL / NOT_OBSERVED`

A selected example is LIVE_PASS only if:
- exact canonical FCF
- PIT/currentness safe
- correct period/scope/currency
- no contradictory old FCF prose
- numeric binding correct
- no status/valuation mutation from FCF alone
- exactly-once unaffected

Also classify actual FCF message quality:
- MATERIAL_IMPROVEMENT
- MINOR_IMPROVEMENT
- NO_MEANINGFUL_CHANGE
- DEGRADED

Report exact degraded text if any.

---

## 5. Phase 9.1D natural runtime canary

Locate canary receipt(s) linked to the natural US packet.

Record:
- canary ID
- attempt ID
- packet ID
- production receipt SHA
- terminal state
- latency
- production influence
- selected subjects
- selected metric families
- Fact IDs
- relation IDs
- PIT/freshness
- semantic/causal validation
- numeric binding
- shadow AI/fallback state

### Inventory proof
For each naturally selected Inventory subject verify:
- total Inventory semantic
- prior comparable
- relation
- PIT/freshness
- industry applicability
- materiality
- numeric binding
- no component leakage
- no causal overclaim
- production influence = 0

Set:

`INVENTORY_NATURAL_PROOF = LIVE_PASS / FAIL / NOT_OBSERVED`

### Exact Trade AR proof
For each naturally selected Trade AR subject verify:
- exact `trade_accounts_receivable`
- no broad AR substitution
- relation vs Revenue
- PIT/freshness
- materiality
- numeric binding
- no DSO
- no customer-payment causal overclaim
- production influence = 0

Set:

`TRADE_AR_NATURAL_PROOF = LIVE_PASS / FAIL / NOT_OBSERVED`

`NOT_OBSERVED` is not failure.

Hard isolation target:
- Telegram diff = 0
- production AI diff = 0
- production fallback diff = 0
- production receipt diff = 0
- message count diff = 0
- assessment/warning mutation = 0

Any violation is P0.

---

## 6. Night-futures natural evidence

Locate all natural production attempts for the expected latest NIGHT session.

For each attempt record exact:
- timestamp
- expected NIGHT BAS_DD
- expected preceding eligible DAY
- provider HTTP
- returned BAS_DD/session-date inventory
- raw row count
- candidate count
- ready count
- per-product KOSPI200/KOSDAQ150 readiness
- contract/maturity
- rejection reason
- parser/canonicalization status
- provider-change cross-check
- raw ref/SHA
- terminal classification

Do not summarize only as `ready_products=0`.

Verify:

`EXPECTED_SESSION_BASIS = PASS / FAIL`

using `night-futures-session-basis-v1`, XKRX calendar, preceding eligible DAY, same instrument/contract/maturity.

### 08:45 observer
Record:
- scheduled and actual time
- expected NIGHT
- returned session dates
- per-product readiness
- raw rows
- raw ref/SHA
- terminal classification
- production isolation

### 09:15 observer
Record the same fields.

If observer #1 found READY and #2 correctly skipped/no-op, report that as expected.

### First observed availability interval
Using only natural stored evidence:
- 08:20 unavailable + 08:45 ready -> `(08:20, 08:45]`
- 08:45 unavailable + 09:15 ready -> `(08:45, 09:15]`
- 09:15 unavailable -> `UNKNOWN_WITHIN_HORIZON`

Report per product if different.

Set:

`NIGHT_FUTURES_TELEMETRY_GAP = LIVE_EVIDENCE_CAPTURE_PASS / FAIL / NOT_OBSERVED`

PASS requires complete production attempt archive + session-date inventory + per-product readiness + post-deadline observer evidence + production influence 0.

---

## 7. Night-futures deadline verdict

Set exactly one:

- `KEEP_CURRENT_DEADLINE`
- `COLLECT_MORE_NATURAL_EVIDENCE`
- `BOUNDED_DEADLINE_REVIEW_REQUIRED`
- `DEADLINE_UNPROVEN`

Do not change deadline in this task.

Rules:
- one morning alone does not automatically change policy
- if expected pair was ready inside production window, current deadline is likely adequate
- if pair appears only shortly after deadline, a bounded review may be justified
- if still unavailable at 09:15, extending deadline may not help
- preserve US primary/backup delivery SLA

Also report:

`FAIL_CLOSED_SAFETY = PASS / FAIL`

Verify no stale substitution, wrong session pair, contract mismatch, fabricated current value, or unsafe user-visible output.

Re-check:

`STALE_INTERNAL_ITEM_RISK = NONE / LOW / MATERIAL`

Do not repair here.

---

## 8. KRX 08:05 natural telemetry

Locate today's natural 08:05 observation.

Record:
- observation ID
- target XKRX date
- provider date(s)
- HTTP status for supported endpoints
- row counts
- eligible row counts if available
- readiness
- promotability
- scheduler exit
- raw refs/SHA
- duplicates

No provider re-query.

Compare against prior natural 16:05 and 08:05 evidence.

Set:

`KRX_CAPTURE_PLUMBING = PASS / FAIL`

`KRX_PUBLICATION_PATTERN = STRENGTHENED / MIXED / UNCHANGED / CONTRADICTED`

Do not integrate KRX user-visible here.

---

## 9. Current operating-state read-only verification

Verify:
- main SHA
- operating SHA
- API health
- Production Assist
- 9.0E mode
- working-capital user-visible mode
- 9.1D state
- night observer schedules
- US primary/backup schedules
- KR primary/backup schedules
- KRX schedules

No changes.

---

## 10. User-visible enablement gates

Set:

`INVENTORY_USER_VISIBLE_ENABLEMENT_READY = YES / NO_PENDING_NATURAL / NO_OTHER_BLOCKER`

YES requires:
- Inventory natural proof LIVE_PASS
- Phase 9.1E pre-integration ready
- semantic/causal PASS
- AI/fallback parity PASS
- open P0 = 0
- relevant material P1 = 0

Set separately:

`TRADE_AR_USER_VISIBLE_ENABLEMENT_READY = YES / NO_PENDING_NATURAL / NO_OTHER_BLOCKER`

Exact Trade AR natural proof is mandatory.

Do not enable anything in this task.

Set next action:

`PHASE_9_1E_NEXT_ACTION = INVENTORY_ENABLEMENT_ONLY / TRADE_AR_ENABLEMENT_ONLY / COMBINED_ENABLEMENT / WAIT_FOR_MORE_NATURAL_PROOF / BOUNDED_REPAIR_REQUIRED`

---

## 11. Severity classification

Classify all findings as P0 / material P1 / P2.

P0 examples:
- wrong user-visible number
- wrong FCF period/scope
- duplicate Telegram
- exactly-once failure
- 9.1D canary production influence
- wrong/stale night-futures value displayed
- receipt corruption

P1 examples:
- material AI reasoning regression
- 9.1D semantic/causal failure
- telemetry repair failed to capture natural availability
- enablement gate inconsistent with natural proof

P2 examples:
- minor wording
- Trade AR not naturally observed
- deadline still unproven
- KRX publication timing remains provider-dependent

P2 does not block architecture progress.

---

## 12. Required reports

Create:

1. `docs/reports/20260822-us-natural-sent-message-bundle.md`
2. `docs/reports/20260822-us-natural-production-review.md`
3. `docs/reports/20260822-phase9-0e-natural-user-visible-proof.md`
4. `docs/reports/20260822-phase9-1d-natural-runtime-proof.md`
5. `docs/reports/20260822-night-futures-natural-publication-proof.md`
6. `docs/reports/20260822-night-futures-natural-publication-proof.json`
7. `docs/reports/20260822-krx-0805-natural-telemetry-review.md`
8. `docs/reports/20260822-morning-natural-gates.md`
9. `docs/reports/20260822-morning-natural-artifact-index.md`
10. `docs/reports/20260822-morning-natural-review-summary.json`

The sent-message bundle must contain exact actual sent text and order.

Unknown fields must remain null/UNKNOWN.

---

## 13. Required gate report

`docs/reports/20260822-morning-natural-gates.md`

Must include exactly:

```text
PHASE_9_0E_NATURAL = ...

INVENTORY_NATURAL_PROOF = ...
TRADE_AR_NATURAL_PROOF = ...

NIGHT_FUTURES_TELEMETRY_GAP = ...
DEADLINE_VERDICT = ...
FAIL_CLOSED_SAFETY = ...
STALE_INTERNAL_ITEM_RISK = ...

KRX_CAPTURE_PLUMBING = ...
KRX_PUBLICATION_PATTERN = ...

INVENTORY_USER_VISIBLE_ENABLEMENT_READY = ...
TRADE_AR_USER_VISIBLE_ENABLEMENT_READY = ...

PHASE_9_1E_NEXT_ACTION = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...
```

---

## 14. Artifact index

`docs/reports/20260822-morning-natural-artifact-index.md`

Reference:
- US packet
- AI candidate
- validation
- fallback
- receipt
- exact sent bundle
- 9.0E evidence
- 9.1D canary receipt
- night-futures production attempts
- 08:45 observer
- 09:15 observer
- KRX 08:05
- current operating state

For each include:
- type
- path/ref
- SHA if available
- immutable/original status

Do not push secrets.

---

## 15. One final ZIP

Create:

`20260822-morning-natural-evidence-review-bundle.zip`

Include all reports listed above.

Report ZIP SHA-256.

---

## 16. Completion response format

### Work instruction
- path
- instruction commit
- version

### Repository
- main
- operating
- health
- feature modes

### US natural
- packet
- AI/fallback
- sent/expected
- duplicate
- exactly-once

### Phase 9.0E
- natural state
- selected/rendered
- degraded

### Phase 9.1D
- canary state
- Inventory proof
- Trade AR proof
- production influence

### Night futures
- expected session
- production attempts
- 08:45 result
- 09:15 result
- first availability interval
- telemetry-gap state
- deadline verdict
- fail-closed safety

### KRX 08:05
- rows
- readiness
- promotability
- pattern

### Gates
- Inventory enablement
- Trade AR enablement
- next 9.1E action

### Severity
- P0
- material P1
- P2

### Bundle
- report commit
- ZIP
- SHA-256

---

## 17. Final principle

This review extracts evidence; it does not create evidence.

Correct sequence:

```text
natural production
→ immutable artifacts
→ natural canary proof
→ observer proof
→ gate decision
```

Do not manually recreate missing history.

For working capital:
- Inventory and exact Trade AR earn enablement independently.
- NOT_OBSERVED is not failure.

For night futures:
- an observer timestamp gives an availability interval, not exact provider publication time.
- telemetry repair success is separate from deadline policy.

For Phase 9.0E:
- actual sent messages are the source of truth.

The ideal output is one bundle that tells us:
1. what users actually received,
2. which natural proofs are now closed,
3. which remain pending,
4. whether night-futures timing is now answerable,
5. what the next smallest safe implementation should be.
