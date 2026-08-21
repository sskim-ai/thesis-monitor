# thesis-monitor — Night-Futures Publication Telemetry Repair Work Instruction

## Metadata

- Repair title:
  `Night-Futures Natural Publication-Time Telemetry & Attempt Archive`
- Workstream:
  `Independent bounded P1 repair`
- Instruction version: `1.0`
- Date: `2026-08-21 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended base/main/operating:
  `d0dc76a2446ee5ef9188d1b06dcb241df004c143`
- Confirmed review state:
  - expected NIGHT session-date semantics: PASS
  - `2026-08-21 NIGHT` expectation: verified
  - attempts: 4
  - window: approximately `08:06:30–08:20:05 KST`
  - ready products: 0
  - prior `2026-08-20 NIGHT` pair: stale and correctly suppressed
  - later natural availability: UNKNOWN
  - deadline verdict: `DEADLINE_UNPROVEN`
  - fail-closed safety: PASS
  - stale internal-item risk: LOW
- Current P1:
  `night-futures publication-time / attempt telemetry gap`
- Public/user-visible behavior change in this repair:
  `0`
- Production deadline change:
  `0`
- Session-basis logic change:
  `0`

---

# 0. Work-instruction repository protocol

Store this instruction at:

`docs/work-instructions/20260821-night-futures-publication-telemetry-repair.md`

Before implementation:

1. Run:
   ```bash
   git fetch origin
   git status
   git rev-parse HEAD
   git rev-parse origin/main
   ```
2. Verify current safe main/operating.
3. Commit/push this instruction as a docs-only instruction commit.
4. Record:
   - instruction path
   - instruction commit SHA
   - instruction version
   - implementation base SHA
5. Create a separate repair branch from latest safe main.
6. If Phase 9.1D lands first, reconcile onto latest main before promotion.
7. No force push / history rewrite.
8. Do not silently edit this instruction.

Recommended branch:

`codex/night-futures-publication-telemetry-repair`

This branch must remain independent from Phase 9.1D.

---

# 1. Repair purpose

The 2026-08-21 review proved:

```text
Expected NIGHT session-date logic     PASS
XKRX preceding-DAY pairing            PASS
stale prior pair suppression          PASS
user-visible fail-closed safety       PASS

latest expected NIGHT by 08:20        unavailable
first later natural availability      UNKNOWN
08:20 deadline adequacy               UNPROVEN
```

Therefore the current problem is not a known pricing/session bug.

It is an observability gap.

The repair must make future mornings answer:

```text
What exact session did production expect?

What did each natural attempt receive?

Were rows absent, stale, mismatched, or present-but-not-ready?

When was the expected session first naturally observed after the production deadline?

Was it early enough that production could reasonably have used it?
```

Do not change user-visible behavior before this evidence exists.

---

# 2. Hard non-goals

Do NOT change:

- `night-futures-session-basis-v1`
- XKRX preceding-eligible-DAY logic
- same instrument/contract/maturity matching
- provider raw-change cross-check
- production morning retry deadline
- US primary schedule
- US backup schedule
- AI dispatch gate
- stale suppression
- fallback behavior
- user-visible market summary
- Telegram
- Phase 9.1D
- KRX telemetry
- Public Action/schema

No "try 08:25 instead" change is allowed in this repair.

---

# 3. New telemetry contracts

Implement two internal versioned contracts, suggested:

1. `night-futures-attempt-archive-v1`
2. `night-futures-publication-telemetry-v1`

They may be represented by existing telemetry infrastructure if cleanly extensible.

---

# 4. Attempt archive — purpose

Every natural production attempt must become auditable.

For each attempt record:

```text
attempt_id
run_id
market_packet_id

timestamp_start
timestamp_end
role
production_or_observer

expected_night_bas_dd
expected_preceding_day_bas_dd
xkrx_calendar_basis

provider_http_status
provider_business_dates_returned
raw_row_count

candidate_product_count
ready_product_count

per_product:
  product
  instrument
  contract
  maturity
  returned_night_bas_dd
  matched_day_bas_dd
  row_state
  readiness
  rejection_reason

parser_status
canonicalization_status
provider_change_crosscheck_status

error
raw_ref
raw_sha256

terminal_classification
```

No secret-bearing request headers/tokens.

---

# 5. Attempt classifications

Use structured classifications, e.g.:

- `EXPECTED_SESSION_ABSENT`
- `EXPECTED_SESSION_PRESENT_NO_MATCHING_DAY`
- `EXPECTED_SESSION_PRESENT_CONTRACT_MISMATCH`
- `EXPECTED_SESSION_PRESENT_PROVIDER_CONFLICT`
- `EXPECTED_SESSION_PRESENT_READY`
- `PROVIDER_EMPTY`
- `PROVIDER_ERROR`
- `PARSER_ERROR`
- `CANONICALIZATION_ERROR`

Use repository equivalents if existing.

Do not reduce everything to `ready_products=0`.

---

# 6. Preserve raw session-date inventory

For every attempt, record the distinct NIGHT BAS_DD/session dates returned by provider payload.

This lets future review distinguish:

```text
provider returned only yesterday
vs
provider returned expected date but matching failed
vs
provider returned no rows
```

This is mandatory.

---

# 7. Per-product readiness

Record KOSPI200/KOSDAQ150 or actual supported products independently.

One product may become available before the other.

Do not make `ready_products=0/2` the only evidence.

Persist:

- product identifier
- contract
- maturity
- expected session
- returned session
- rejection reason

---

# 8. Production attempt instrumentation

Instrument the current natural production collector attempts.

Requirements:

- no change to retry count
- no change to timing
- no change to deadline
- no change to provider requests unless metadata capture requires it
- no new production dependency
- telemetry write failure must not fail production

Observability is secondary to delivery.

---

# 9. Backup-path instrumentation

If the US backup path performs night-futures collection, archive those attempts too.

If backup does not perform a provider attempt because production is already terminal, record that fact.

Do not add a new production query merely to populate telemetry.

---

# 10. Detached post-deadline publication observer

Add a **telemetry-only** observer that is completely disconnected from production rendering.

Purpose:

estimate the first naturally observed provider availability after the production deadline.

It must:

- use the same expected-session derivation
- use the same provider/parser/canonicalizer
- never write a value into the production market-summary candidate
- never trigger Telegram
- never alter production receipt
- never change fallback
- never change deadline

---

# 11. Observer scheduling principle

Do not blindly hard-code an observation schedule without inspecting the actual morning lifecycle.

Codex must determine the earliest non-interfering post-deadline observation slots by reviewing:

- last production provider attempt
- US primary lifecycle
- US backup lifecycle
- provider concurrency/rate-limit behavior
- existing scheduler framework

Requirements:

- start only after the production attempt deadline
- avoid interfering with primary/backup production
- use a small bounded number of observations
- stop once the expected NIGHT pair becomes ready
- stop at a documented morning horizon
- no continuous high-frequency polling

Preferred architecture:
reuse existing LaunchAgent/telemetry framework.

---

# 12. Minimum observer evidence

The deployed observer must be capable of generating at least:

- one first post-deadline observation
- one later observation if expected session is still unavailable
- one terminal result when ready or horizon exhausted

If existing backup natural attempts already cover one of these points, reuse them instead of duplicate provider calls.

---

# 13. Observer horizon

Do not choose horizon from intuition alone.

Codex must inspect:

- current morning market-summary SLA
- historical natural provider evidence
- current US backup terminal timing
- rate limits

Choose the smallest horizon that can answer whether availability is:
- shortly after deadline
- meaningfully later
- still absent

Document exact selected slots/horizon and rationale.

The horizon itself must not alter production.

---

# 14. First naturally observed availability

Persist:

```text
target_expected_session
first_observed_ready_at
first_observed_products
raw_ref
raw_sha
previous_observation_at
previous_observation_state
availability_interval
```

If observations show:

```text
08:20 unavailable
08:45 ready
```

then the evidence is:

`first availability occurred sometime in (08:20, 08:45]`

Do not claim exact publication at 08:45.

---

# 15. Unknown is valid

If the expected pair never becomes ready by observer horizon:

persist:

`FIRST_PROVIDER_AVAILABILITY_TIME = UNKNOWN_WITHIN_HORIZON`

Do not infer provider failure beyond observed facts.

---

# 16. Session-basis regression guard

Even though session-date logic already passed, every observer attempt must use the same verified path:

```text
expected NIGHT BAS_DD
→ XKRX calendar
→ preceding eligible DAY
→ same instrument
→ same contract/maturity
→ deterministic change
→ provider cross-check
```

Do not create a telemetry-only shortcut that pairs differently from production.

---

# 17. No stale substitution

Observer may see prior NIGHT rows.

They remain evidence of provider state, not a substitute current pair.

Record them as:

`STALE_PRIOR_SESSION_PRESENT`

or equivalent.

Never surface them user-visible.

---

# 18. Internal stale-item hardening

The previous review classified stale internal-item risk as LOW.

Audit whether stale observations can enter any user-facing candidate path.

If a hard freshness gate already exists:
document and test it.

If there is a narrow safe hardening that prevents stale archive items from being included in user-facing candidate construction without changing valid output:
implement only if it is clearly behavior-preserving.

Otherwise leave as P2.

Do not redesign market-environment rendering.

---

# 19. Telemetry write isolation

Telemetry failure must not:

- fail market summary
- delay dispatch
- alter AI
- change fallback
- alter receipt
- alter exactly-once

If archive write fails:
log/record best-effort failure and continue production.

---

# 20. Storage

Prefer existing local telemetry/evidence storage.

No DB migration unless strictly necessary.

No manual DB mutation.

If files:
use deterministic paths/IDs and atomic writes.

If DB:
reuse existing telemetry table/model if safe.

---

# 21. Raw evidence retention

Keep only sanitized/raw payload references consistent with repository policy.

Never store:
- API keys
- Authorization headers
- secrets

Record raw SHA where existing raw payload is archived.

---

# 22. Attempt idempotency

Same natural attempt should not produce duplicate logical telemetry rows.

Observer retries should have distinct attempt IDs under one publication-observation group.

---

# 23. Publication-observation identity

Suggested:

```text
observation_group_id
target_night_bas_dd
market_date
production_run_id
```

All post-deadline probes for one target session belong to one group.

---

# 24. Deadline verdict remains unchanged by implementation

Immediately after repair deployment:

`DEADLINE_VERDICT = DEADLINE_UNPROVEN`

The implementation itself does not prove the deadline.

Only future natural evidence may change this.

---

# 25. Natural evidence classification

After natural observations, classify each morning:

- `READY_WITHIN_PRODUCTION_WINDOW`
- `READY_SHORTLY_AFTER_DEADLINE`
- `READY_ONLY_AFTER_BACKUP_WINDOW`
- `NOT_READY_WITHIN_OBSERVER_HORIZON`
- `PROVIDER_ERROR`
- `UNKNOWN_TELEMETRY_FAILURE`

Do not translate one day directly into a permanent deadline policy.

---

# 26. Multi-day evidence

Do not require an arbitrary number of days to deploy the repair.

But a deadline policy change should normally require more than one clean observation unless a deterministic defect is found.

The completion report should distinguish:

- telemetry repair implementation
- natural evidence accumulation
- deadline-policy decision

---

# 27. P1 lifecycle

Current P1:

`publication-time / attempt telemetry gap`

After implementation + deterministic validation:

```text
P1_TELEMETRY_GAP =
REPAIR_DEPLOYED_PENDING_NATURAL
```

After first natural morning with complete attempt archive + post-deadline observation:

```text
P1_TELEMETRY_GAP =
LIVE_EVIDENCE_CAPTURE_PASS
```

The separate question:

`deadline too early?`

may remain OPEN/UNPROVEN.

Do not conflate them.

---

# 28. Tests — attempt archive

Required:

- empty provider result
- stale prior session only
- expected session present
- one product ready
- both products ready
- contract mismatch
- maturity/rollover mismatch
- provider conflict
- parser error
- canonicalization error
- provider error

Each produces structured telemetry.

---

# 29. Tests — session inventory

Required:

raw provider rows with multiple BAS_DD values
→ telemetry lists all relevant returned session dates.

No parser loss.

---

# 30. Tests — observer isolation

Required:

- production success + observer success
- production success + observer failure
- observer ready
- observer horizon exhausted
- duplicate observer invocation
- telemetry storage failure

Production output/receipt must remain identical.

---

# 31. Tests — observer stop condition

When expected pair becomes ready:

- terminal publication observation recorded
- later scheduled probes skipped/no-op
- no extra provider call if architecture can safely suppress it

Do not keep polling after success.

---

# 32. Tests — stale behavior

Required:

- stale prior pair archived
- stale prior pair never becomes current candidate
- stale item cannot leak user-visible
- correct suppression reason

---

# 33. Tests — exact session-basis path

Regression tests for:

- holiday skip
- weekend skip
- same-BAS_DD rejection
- future DAY rejection
- contract match
- rollover mismatch
- provider change cross-check

These must reuse existing Phase 8.5.4.2 logic.

---

# 34. Tests — no deadline change

Assert configuration/schedule:

- production retry deadline unchanged
- primary/backup schedules unchanged
- AI/fallback behavior unchanged

---

# 35. Regression

Preserve:

- Phase 8.5.4.2 night-futures fix
- 8.5.5.x
- Phase 9.0E
- Phase 9.1A/B/C
- 9.1D if already merged
- KRX telemetry
- exactly-once
- market summary fallback

---

# 36. Full validation

Required:

- focused telemetry tests PASS
- isolation PASS
- session-basis regression PASS
- stale suppression PASS
- observer scheduling/config validation PASS
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment/Chart Knowledge parity PASS
- Public Action `0.4.5`
- operationId `20/20 unique`
- schema `4`
- exact implementation SHA Actions PASS
- final/main SHA Actions PASS after promotion

---

# 37. Promotion

This repair may be promoted after deterministic validation because it is observability-only.

Before promotion:

- P0 = 0
- material implementation P1 = 0
- production behavior diff = 0
- deadline unchanged
- session-basis unchanged
- isolation PASS
- CI PASS

If Phase 9.1D lands first:
integrate onto latest main safely.

---

# 38. Protect next morning window

Do not deploy during the morning production/backup execution window.

Protect:

- KRX around 08:05
- US primary 08:15
- US backup 08:30
- actual terminal lifecycle

If promotion is not complete before the repository-defined freeze, defer until after the morning cycle.

Do not rush to obtain telemetry.

---

# 39. Required architecture doc

Create:

`docs/architecture/NIGHT_FUTURES_PUBLICATION_TELEMETRY.md`

Include:

- attempt archive
- publication observation group
- production isolation
- observer lifecycle
- session-basis reuse
- stale behavior
- evidence semantics
- deadline-policy separation

---

# 40. Required reports

Create:

1. `docs/reports/20260821-night-futures-telemetry-implementation.md`
2. `docs/reports/20260821-night-futures-attempt-archive-validation.md`
3. `docs/reports/20260821-night-futures-observer-isolation.md`
4. `docs/reports/20260821-night-futures-session-regression.md`
5. `docs/reports/20260821-night-futures-stale-path-audit.md`
6. `docs/reports/20260821-night-futures-telemetry-readiness.md`
7. `docs/reports/20260821-night-futures-natural-proof-plan.md`

Recommended JSON:

`docs/reports/20260821-night-futures-telemetry-readiness.json`

---

# 41. Natural proof report template

Prepare a template/script that after the next natural morning can produce:

`docs/reports/<date>-night-futures-natural-publication-proof.md`

It should include:

- expected NIGHT
- production attempts
- returned BAS_DD inventory
- per-product readiness
- production deadline
- observer attempts
- first observed ready interval
- fail-closed behavior
- deadline verdict
- P1 telemetry status

Do not manually trigger it against provider historical timing.

---

# 42. Complete report bundle

Create:

`20260821-night-futures-publication-telemetry-repair-bundle.zip`

Include sanitized:

- implementation report
- archive validation
- observer isolation
- session regression
- stale audit
- readiness
- natural-proof plan
- JSON readiness

Report SHA-256.

---

# 43. Completion report — repository

Report:

- instruction path
- instruction commit
- branch
- base
- implementation
- final
- previous/final main
- operating
- promotion
- worktrees
- deviations

---

# 44. Completion report — telemetry

Report:

- production attempt fields captured
- per-product fields
- session-date inventory
- raw refs/SHA
- telemetry write failures in tests
- idempotency

---

# 45. Completion report — observer

Report:

- selected observer architecture
- exact natural slots/horizon
- rationale
- production overlap analysis
- stop condition
- provider-call bound
- failure isolation

---

# 46. Completion report — unchanged production behavior

Report:

- production retry count
- production first/last attempt logic
- deadline
- primary schedule
- backup schedule
- session-basis version
- stale suppression
- user-visible diff

All unchanged.

---

# 47. Completion report — current P1

At completion:

```text
NIGHT_FUTURES_TELEMETRY_REPAIR_DEPLOYED = YES/NO

P1_TELEMETRY_GAP =
REPAIR_DEPLOYED_PENDING_NATURAL
or actual state

DEADLINE_VERDICT =
DEADLINE_UNPROVEN
unless new natural evidence legitimately exists

FAIL_CLOSED_SAFETY =
PASS
```

Do not close the natural-evidence P1 prematurely.

---

# 48. Natural promotion criteria for P1 closure

After the next natural morning, telemetry gap can become:

`LIVE_EVIDENCE_CAPTURE_PASS`

if:

- every production attempt archived
- session-date inventory present
- per-product readiness present
- at least one post-deadline natural observation captured or production/backup evidence fully bounds availability
- production behavior unchanged

This closes the telemetry gap.

It does not automatically change the deadline.

---

# 49. Deadline-policy follow-up

After natural evidence, recommend one of:

- `KEEP_CURRENT_DEADLINE`
- `COLLECT_MORE_NATURAL_EVIDENCE`
- `BOUNDED_DEADLINE_REVIEW_REQUIRED`

Only a later dedicated repair may change production timing.

No timing change in this task.

---

# 50. P0 / P1 / P2

## P0
- telemetry changes production result
- observer feeds user-visible values
- wrong session-basis logic introduced
- stale data displayed current
- duplicate delivery

## P1
- attempt archive incomplete
- observer cannot distinguish absence vs mismatch
- telemetry causes provider interference
- natural evidence still impossible to reconstruct

## P2
- optional dashboard
- additional visualization
- low-risk stale archive cleanup
- finer publication-time granularity after core observer works

---

# 51. Final philosophy

The 2026-08-21 morning behavior was safe.

The system did not make up a night-futures value and did not substitute an older validated session as current.

The unresolved problem is:

```text
We know it was unavailable by the deadline.
We do not know when it became available later.
```

Do not solve an evidence problem by changing the production deadline.

First make the system prove:

```text
attempt 1: what exact dates/rows existed?
attempt 2: what changed?
attempt 3: what changed?
attempt 4: what changed?
post-deadline observer: when did the expected pair first become naturally visible?
```

Only then should deadline policy be revisited.

Success is:

> Every natural attempt and post-deadline observation becomes reconstructable, while production timing, session semantics, fail-closed safety, and user-visible behavior remain unchanged.
