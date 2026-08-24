# thesis-monitor — Macro Digest Temporal Contract Wiring Audit & Conditional Repair

## Metadata

- Workstream: `P1 analysis-integrity audit + conditional bounded repair`
- Instruction version: `1.0`
- Date: `2026-08-24 KST`
- Repository: `sskim-ai/thesis-monitor`
- Last known safe main/operating from prior completed repair: `c873d258bba76dce0df6318417fa3a7bceb0ed97`
- IMPORTANT: before implementation, resolve and use the actual latest safe `origin/main`; do not force the stale SHA above if main has legitimately advanced.
- Triggering natural message: `🌎 미국 종목 점검 · 2026-08-24`
- Triggering issue: a closed/no-new-US-cash-session morning digest used observations from different dates under headings/phrasing such as:
  - `오늘 한 줄`
  - `중요한 변화`
  - `VIX가 +7.5% 움직여...`
  - `WTI가 +2.0% 움직여...`
  - `오늘 신호: ...`
- Current hypothesis: temporal/freshness metadata may already exist in backend layers but may not be fully consumed by macro-regime / today-signal / final market-digest rendering.
- Goal: **first trace and prove whether the temporal contract already exists; if it exists, wire it correctly. If it does not exist or is insufficient, implement the smallest canonical temporal-eligibility contract and then wire it end-to-end.**
- Production Assist: `OFF`
- Public Action: keep current version unless a truly public schema change is required; expected change = `0`
- User-visible target: fix temporal labeling/eligibility in market digest without inventing new market data or changing unrelated investment logic.

---

## 0. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260824-macro-digest-temporal-wiring-audit-and-conditional-repair.md`

Before work:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:
1. verify actual latest safe main/operating SHA
2. commit/push this instruction as a docs-only instruction commit
3. record instruction path, instruction commit SHA, instruction version, implementation base SHA
4. create the implementation branch from the latest safe main descendant containing the instruction commit
5. no force push / history rewrite
6. do not silently edit the instruction after implementation begins

Recommended branch:

`codex/macro-digest-temporal-wiring-audit-repair`

---

## 1. Do not assume the root cause

The first task is an architecture trace, not implementation.

Determine which branch is true:

### Branch A — temporal contract already exists, final consumer ignores it
Example:

```text
raw item has as_of_date
→ canonical macro item has session/freshness classification
→ briefing keeps it
→ today_signal / digest assembler ignores temporal role
→ renderer emits "today change"
```

If true:
perform a **wiring/integration repair only**.

### Branch B — partial contract exists but is insufficient
Example:

```text
quality_status = fresh
as_of_date exists
market_session = closed
but no distinction between:
CURRENT_OBSERVATION
PRIOR_MARKET_SESSION
REFERENCE_LAGGING
STALE_FOR_DAILY_SIGNAL
```

If true:
extend the existing contract minimally.

### Branch C — no usable digest-temporal contract exists
Implement a new canonical contract, suggested:

`macro-digest-temporal-eligibility-v1`

Then wire it through reasoning and rendering.

The final report must state exactly which branch was confirmed.

---

## 2. Hard prohibitions

Do NOT:
- manually rerun the 2026-08-24 production task
- manually send Telegram
- query providers to recreate the original morning state
- rewrite immutable production archives
- rewrite receipts
- change historical source dates
- treat `quality_status=fresh` as equivalent to `today`
- globally suppress all macro data merely because cash market is closed
- change night-futures session-basis logic
- change night-futures deadline
- change KRX publication logic
- change working-capital feature modes
- change Trade AR enablement
- change KR investor-flow logic
- change valuation/price/RR logic
- loosen semantic validators just to make the current message pass
- invent arbitrary recency thresholds without source/role justification

Use stored natural artifacts and repository code first.

---

## 3. Trigger-message immutable replay

Locate the exact natural 2026-08-24 US market-digest artifacts.

Collect/reference:
1. production packet
2. macro briefing snapshot
3. macro regime snapshot
4. macro events/theses inputs if used
5. market-session state
6. each item's observation/as-of date
7. existing freshness/quality fields
8. any `today_signal` / daily delta structure
9. AI input macro context
10. deterministic fallback macro context
11. final sent market-digest text
12. production receipt

Do not modify originals.

Create a separate replay artifact for before/after comparison.

---

## 4. Verify actual source dates from evidence

For every numeric statement used in the triggering message, report the exact source observation date/time from stored evidence.

At minimum verify:
- S&P 500
- Nasdaq
- Russell 2000
- SOXX / semiconductor proxy
- VIX
- WTI
- US 10Y
- real 10Y if used
- breakeven inflation if used
- high-yield spread if used
- dollar index
- USD/KRW if used
- Korean night futures if referenced/suppressed

Do not reuse previously discussed dates as assumptions.

---

## 5. Separate source freshness from digest temporal eligibility

The repair must explicitly distinguish:

```text
source/provider freshness
```

from:

```text
eligibility to be described as a new/current digest signal
```

A source may be valid for its own cadence while still being too old to say:
- `오늘 움직였다`
- `오늘 위험회피가 커졌다`
- `중요한 변화`

This distinction must be machine-readable.

---

## 6. Preferred temporal-role model

If no equivalent model already exists, implement or map to the smallest safe set:

```text
CURRENT_OBSERVATION
PRIOR_MARKET_SESSION
REFERENCE_LAGGING
STALE_FOR_DAILY_SIGNAL
UNAVAILABLE
```

Meaning:

### CURRENT_OBSERVATION
A genuinely new observation/release eligible to influence the current briefing's new-signal/delta interpretation.

### PRIOR_MARKET_SESSION
The latest completed relevant market-session move, useful for context but labeled as prior/last trading session when no new session occurred.

### REFERENCE_LAGGING
A valid slower-moving or older observation useful for regime/background context, but not eligible to create a new daily signal or "important change" sentence by itself.

### STALE_FOR_DAILY_SIGNAL
Too old or temporally mismatched for current daily-change reasoning; may remain archived but should be excluded from current change synthesis.

### UNAVAILABLE
No usable current/reference evidence.

Use repository-equivalent vocabulary if an existing contract already provides this distinction.

---

## 7. Cadence-aware classification

Do not use one universal elapsed-day threshold.

Classification should consider:
- source/series publication cadence
- market-session calendar
- briefing cutoff
- previous briefing cutoff if available
- observation timestamp/as-of date
- whether a new market session occurred
- whether the series itself published a new observation since the last briefing
- role in the message:
  - daily change
  - prior-session context
  - regime/background

A weekly spread series and a daily VIX series must not have identical temporal rules.

---

## 8. Closed-session does not mean no macro data

Do not implement:

```text
if market_session == closed:
    today_signal = none for everything
```

A macro release can occur even if the US cash equity session is closed.

Instead:

```text
per-series new observation since briefing cutoff?
→ yes: may be CURRENT_OBSERVATION
→ no: prior/reference classification
```

For equity-index/session-return facts:
if no new cash session occurred, the last completed return is `PRIOR_MARKET_SESSION`, not a current-session move.

---

## 9. Today-signal contract

Audit how `today_signal` is calculated.

A `today_signal` may only be driven by evidence classified as eligible for **new current briefing signal**.

`PRIOR_MARKET_SESSION` may be used as context but must not silently masquerade as a new observation.

`REFERENCE_LAGGING` must not create a new directional daily signal by itself.

If no eligible new evidence exists:
use repository-equivalent:

```text
today_signal = no_new_signal
```

or user-facing equivalent:
`오늘 신규 신호: 없음`

while preserving the longer-term thesis/regime state.

Do not equate `no_new_signal` with bullish, bearish, or neutral conviction.

---

## 10. Important-changes contract

Audit the source of `📈 중요한 변화`.

Every item must have:
- temporal role
- observation date
- new-since-cutoff status
- allowed label

Rules:

- `CURRENT_OBSERVATION`: may appear under important/current changes.
- `PRIOR_MARKET_SESSION`: only with explicit prior-session wording.
- `REFERENCE_LAGGING`: not as a new important change; may appear under current environment/reference context if material.
- `STALE_FOR_DAILY_SIGNAL`: suppress from current changes.

---

## 11. Heading and language contract

The final renderer must distinguish:
- today/current change
- prior trading session
- recent/reference indicator
- current regime/state

Do not preserve a `오늘` heading if all underlying evidence is prior-session/reference.

If no current observations exist, prefer a message equivalent to:

```text
미국 현물시장은 신규 세션이 없습니다.
직전 거래일 기준 ...
```

Do not hard-code exact prose if the current style has a better concise alternative.

---

## 12. Current one-line summary

Audit `🎯 오늘 한 줄`.

The one-line summary must not claim new deterioration/improvement solely from older observations.

If there is no new eligible evidence:
the summary may describe current regime/state and explicitly say there is no new US cash-session signal.

Do not hard-code one sentence.

---

## 13. Macro regime vs daily delta

Separate:

```text
regime/state
```

from:

```text
new daily delta
```

Older valid observations may continue to support the regime.
They may not automatically become today's change.

Example:

```text
risk regime = mixed
today_signal = no_new_signal
```

is valid.

---

## 14. Market-thesis daily signal

Audit sections such as:

```text
미국 연착륙과 점진적 디스인플레이션
→ 상태: 유지
→ 오늘 신호: 약한 부정
```

Trace which facts caused `약한 부정`.

If those facts are temporally ineligible for a current daily signal:
the daily signal must not be generated from them.

State may remain `유지`.

---

## 15. Macro-to-ticker impact

Audit whether stale/reference-only changes feed:
- ticker macro impacts
- daily business-thesis interpretation
- risk-level changes

A `REFERENCE_LAGGING` fact may support an exposure channel but must not create a false **new daily impact delta**.

Do not alter long-term macro exposure mappings.

---

## 16. AI and deterministic fallback parity

Both AI and fallback market digests must consume the same temporal eligibility result.

Parity dimensions:
- temporal role
- source date
- prior-session/current label
- important-change eligibility
- today-signal eligibility
- suppressed stale/reference items

The AI must not turn a reference item back into a "today" movement.

---

## 17. User-visible date context

Do not clutter every sentence with dates.

When ambiguity matters, expose enough context:
- `직전 거래일(8/21)`
- `8/20 기준 VIX`
- or equivalent compact wording

The exact style should minimize verbosity.

---

## 18. Night-futures interaction

Existing night-futures stale/fail-closed gate remains authoritative.

Do not modify:
- session pairing
- deadline
- observer timing

The macro digest temporal layer should consume that availability classification, not override it.

---

## 19. KRX interaction

This is not the KR Market Digest localization project.

Do not add KRX breadth to user-visible digest here.

Only ensure shared temporal-role logic does not regress KRX/role-target telemetry.

---

## 20. Regression fixture — 2026-08-24 US message

Rebuild the 2026-08-24 digest from the same immutable packet.

Required before/after audit:

### Before
Capture exact sent message.

### After
Produce a non-delivery preview with corrected temporal handling.

Verify:
- no new US cash session is represented as such
- prior-session equity moves are labeled prior-session
- older VIX/WTI/dollar observations do not appear as today's moves
- `today_signal` does not use temporally ineligible items
- regime may remain if still supported
- night-futures caution remains safe

Do not modify original archive.

---

## 21. Normal trading-day regression

Use at least one recent normal US trading-day packet.

Expected:
- actual current-session/prior-close moves still appear as important changes
- valid daily signals remain
- message remains concise

Prevent over-correction.

---

## 22. Weekend/holiday matrix

Test:
- Monday morning after weekend
- US market holiday
- normal weekday
- partial/early-close if supported
- macro release during cash-market closure
- no new series observations
- one new slow-frequency macro release while equity session closed

Classify per item, not with a blanket market-session rule.

---

## 23. Data-source cadence matrix

Create an audit table:

```text
series
source/provider
expected cadence
session-bound or release-bound
latest observation
temporal role
eligible for today_signal
eligible for important_changes
eligible for regime
```

Do not guess cadence if metadata/provider contract supplies it.

Where cadence is unknown:
fail conservatively and report the limitation.

---

## 24. Existing-contract inventory

Search repository for existing fields/concepts such as:
- freshness
- stale
- as_of_date
- observed_at
- market_session
- prior_session
- latest_completed_session
- daily_delta
- today_signal
- currentness
- source_available_at
- publication lag
- macro event effective date

Produce:

```text
existing component
where defined
where populated
where consumed
where dropped
```

This determines Branch A/B/C.

---

## 25. Conditional implementation rule

### If Branch A confirmed
Only:
- wire existing temporal fields into today-signal / important-change / renderer
- add missing validation
- add replay tests

Do not add a redundant temporal contract.

### If Branch B confirmed
Extend existing contract minimally.

### If Branch C confirmed
Implement:

`macro-digest-temporal-eligibility-v1`

and wire end-to-end.

The final report must justify the minimum chosen scope.

---

## 26. Semantic validator

Add/extend validation so a claim like:

```text
VIX가 오늘 +7.5% 움직였다
```

cannot pass if the underlying VIX fact is not eligible as current.

Check:
- metric identity
- source date
- temporal role
- wording role

Also reject unsupported:
- `오늘`
- `간밤`
- `현재 급등/급락`

when the fact only supports prior/reference context.

Allow explicit historical/reference wording.

---

## 27. Runtime quality

Avoid replacing every item with verbose date disclaimers.

Quality target:
- concise
- temporally honest
- no repetitive `~기준` boilerplate
- current/prior/reference understandable at a glance

If no current changes exist, a shorter message is acceptable.

---

## 28. No historical rewrite

If a current daily signal changes from `약한 부정` to `no_new_signal` because prior logic was temporally invalid:
do not rewrite historical assessments.

Only current/replayed comparison artifacts change.

---

## 29. Natural proof

Implementation may be promoted after deterministic replay and full regression.

Do not manually trigger production.

After promotion:

```text
MACRO_TEMPORAL_REPAIR = DEPLOYED_PENDING_NATURAL
```

Do not claim LIVE PASS from replay.

---

## 30. Tests — closed session

Required:
- no new cash session + prior equity return
- no new VIX observation
- no new WTI observation
- reference-only slow series
- `today_signal = no_new_signal` when appropriate
- regime preserved
- prior-session labeling
- no false today wording

---

## 31. Tests — current observation

Required:
- new equity session
- new VIX observation
- new WTI observation
- new macro release during closed equity market
- current only when genuinely new

---

## 32. Tests — mixed timing

Example:

```text
equity = prior session
VIX = current new observation
WTI = reference lagging
```

Expected:
- VIX only current change
- equity prior-session
- WTI reference-only/suppressed from current changes

---

## 33. Tests — today signal

Required:
- current positive
- current negative
- no new signal
- mixed current
- prior-session-only
- reference-only

Prior/reference-only facts must not create a new daily signal.

---

## 34. Tests — AI/fallback parity

For same packet:
- temporal-role mismatch = 0
- today-signal eligibility mismatch = 0
- important-change inclusion mismatch = 0
- prior-session label mismatch = 0
- stale/reference suppression mismatch = 0

Prose may differ.

---

## 35. Regression

Preserve:
- Phase 9.0E cash flow
- Inventory user-visible mode/state
- Trade AR OFF
- KR investor-flow repair
- KR producer repair
- KRX role-target
- night-futures telemetry/session logic
- price/RR
- valuation
- exactly-once
- receipts
- macro exposure mappings

---

## 36. Full validation

Required:
- architecture trace complete
- Branch A/B/C decision documented
- 2026-08-24 immutable replay PASS
- normal trading-day replay PASS
- weekend/holiday matrix PASS
- cadence matrix complete for used series
- semantic temporal validator PASS
- AI/fallback parity PASS
- runtime quality PASS
- full pytest PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- Public Action/schema unchanged unless justified
- exact implementation SHA Actions PASS
- exact final main SHA Actions PASS after promotion

---

## 37. Promotion gate

Set:

`MACRO_TEMPORAL_REPAIR_READY = YES/NO`

YES requires:
- open P0 = 0
- material P1 = 0
- false-current wording removed
- valid trading-day signals preserved
- no stale/reference item creates today_signal
- AI/fallback parity PASS
- full regression PASS
- CI PASS
- main ancestry clean

---

## 38. Required architecture doc

Create:

`docs/architecture/MACRO_DIGEST_TEMPORAL_ELIGIBILITY.md`

Document:
- existing-vs-new contract decision
- temporal roles
- cadence/session logic
- today-signal rules
- important-change rules
- regime-vs-delta separation
- AI/fallback consumption
- validation

---

## 39. Required reports

Create:
1. `docs/reports/20260824-macro-temporal-existing-contract-inventory.md`
2. `docs/reports/20260824-macro-temporal-root-cause.md`
3. `docs/reports/20260824-macro-series-cadence-matrix.md`
4. `docs/reports/20260824-us-digest-temporal-before-after.md`
5. `docs/reports/20260824-macro-today-signal-audit.md`
6. `docs/reports/20260824-macro-ai-fallback-parity.md`
7. `docs/reports/20260824-macro-temporal-validator.md`
8. `docs/reports/20260824-macro-temporal-regression.md`
9. `docs/reports/20260824-macro-temporal-readiness.md`

Recommended JSON:
`docs/reports/20260824-macro-temporal-readiness.json`

---

## 40. Complete bundle

Create:

`20260824-macro-digest-temporal-audit-repair-bundle.zip`

Include sanitized:
- existing contract inventory
- root cause
- cadence matrix
- before/after
- today-signal audit
- parity
- validator
- regression
- readiness JSON

Report ZIP SHA-256.

---

## 41. Completion report

Must include:

### Repository
- instruction path
- instruction commit SHA
- branch
- base
- implementation SHA
- final SHA
- previous main
- final main
- operating
- promotion method
- API health
- worktree
- deviations

### Root cause
Exactly:

```text
ROOT_CAUSE_BRANCH = A / B / C
```

and:
- what metadata already existed
- where it was lost/ignored
- whether a new contract was necessary
- exact files/functions changed

### Triggering replay
- exact source dates for major metrics
- before message
- after message
- relabeled claims
- suppressed current-change claims
- today_signal before/after
- regime before/after
- message-length change

### Safety
- manual Telegram = 0
- manual production task = 0
- provider recreation = 0
- DB/Pilot mutation = 0
- historical archive rewrite = 0
- night-futures config change = 0
- Inventory mode change = 0
- Trade AR change = 0
- Production Assist = OFF

---

## 42. Final state

Successful completion should report:

```text
MACRO_DIGEST_TEMPORAL_CONTRACT = PASS
MACRO_TODAY_SIGNAL_TEMPORAL_GATE = PASS
MACRO_IMPORTANT_CHANGES_TEMPORAL_GATE = PASS
MACRO_AI_FALLBACK_TEMPORAL_PARITY = PASS

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0

MACRO_TEMPORAL_REPAIR = DEPLOYED_PENDING_NATURAL
```

If the problem was only an existing wiring gap, say so explicitly.

If no adequate contract existed and one was implemented, say so explicitly.

---

## 43. Final philosophy

The first question is not:

> What new freshness logic should we invent?

It is:

> What temporal information does the system already know, and where does the final digest stop using it?

Only after that trace should code be added.

A valid market observation can be:
- current,
- prior-session,
- reference-only,

without being stale in the provider sense.

The daily digest must preserve that distinction.

The user should never have to infer whether:

`VIX +7.5%`

means:
- today,
- the prior trading day,
- or several days ago.

Success is:

> the system uses existing temporal metadata wherever possible, adds only the missing contract if necessary, and ensures that "오늘 변화" and "오늘 신호" are driven only by genuinely current evidence while prior/reference data remains useful for regime context.
