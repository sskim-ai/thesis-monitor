# thesis-monitor — Phase 9.0E Work Instruction

## Metadata

- Phase: `9.0E`
- Title: `Selective Current-Formal Full-FCF User-Visible Integration`
- Instruction version: `1.0`
- Date: `2026-08-21 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended base: latest safe `origin/main` containing completed Phase 9.0D.1
- Known prior main/operating abbreviation from completion report: `86f4187`
- Previous phase: `9.0D.1 Baseline Cash-Flow Sign / Period / Scope Consistency Repair`
- Previous gate: `PHASE_9_0E_READY = YES`
- Target scope: `SELECTIVE_CURRENT_FORMAL_FULL_FCF_USER_VISIBLE_INTEGRATION`
- Production Assist: `OFF`
- Public Action: `0.4.5`
- Output schema: `4`
- Policy: `daily-review-v3.10`
- This phase intentionally introduces a **selective user-visible runtime change**.

---

# 0. Work-instruction repository protocol

Store this instruction at:

`docs/work-instructions/20260821-phase-9-0e-selective-cash-flow-user-visible-integration.md`

Before implementation:

1. Run:
   ```bash
   git fetch origin
   git status
   git rev-parse HEAD
   git rev-parse origin/main
   ```
2. Verify latest safe main/operating state and clean working trees.
3. Commit/push this work instruction as a **docs-only instruction commit** before implementation.
4. Record:
   - `instruction_path`
   - `instruction_commit_sha`
   - `instruction_version`
5. Create the implementation branch from the latest safe main descendant containing the instruction commit.
6. If main drift exists, reconcile explicitly.
7. No force push or history rewrite.
8. Do not silently change this instruction after implementation begins. Material changes require a new committed version.

Recommended implementation branch:

`codex/phase-9-0e-selective-cash-flow-user-visible-integration`

The completion report must cite the exact instruction commit SHA.

---

# 1. Phase purpose

Phase 9.0A answered:

> Which OCF / PPE CAPEX / FCF facts can be trusted?

Phase 9.0B implemented:

> Canonical OCF / PPE-CAPEX / PPE-only FCF with exact lineage.

Phase 9.0C answered:

> Which canonical facts are PIT-safe, fresh, material, and actually improve investment reasoning?

Phase 9.0D proved on a natural US packet:

> The cash-flow reasoning can run as an isolated runtime canary without affecting production.

Phase 9.0D.1 closed the final user-visible consistency blocker:

> Unqualified baseline qualitative cash-flow claims cannot contradict comparable current-formal canonical cash-flow evidence.

Now Phase 9.0E introduces **selective user-visible cash-flow integration**.

The objective is not to add a new cash-flow section to every company.

The objective is:

```text
Current-formal canonical cash-flow evidence
        ↓
PIT / freshness
        ↓
Full-FCF eligibility
        ↓
Industry applicability
        ↓
Decision materiality
        ↓
Baseline consistency
        ↓
One controlled user-visible cash-flow insight
        ↓
AI-assisted path
        +
Deterministic fallback path
```

The feature must remain selective, auditable, kill-switchable, and fail-closed.

---

# 2. Primary acceptance principle

The first production rollout must satisfy:

```text
Eligible does not mean visible.

Visible requires:
current-formal
+ full FCF
+ PIT-safe
+ fresh
+ materially useful
+ industry-appropriate
+ baseline-consistent
+ fully provenance-bound
```

A subject may have canonical FCF and still receive no user-visible cash-flow sentence.

---

# 3. Hard exclusions

This phase must NOT implement:

- KR OpenDART cash-flow period recovery
- KR user-visible cash-flow rollout
- OCF-only user-visible broad rollout
- formal-lagging-provisional current numeric display
- stale cash-flow current numeric display
- management-defined FCF reconciliation rollout
- FCF Yield
- FCF/share
- EV/FCF
- P/FCF
- CCC
- DSO
- Inventory Days
- DPO
- Standard ROIC
- ROIC proxy
- arbitrary cash-flow scores
- cash-flow-triggered automatic thesis strengthening/weaking
- cash-flow-triggered warning lifecycle changes
- cash-flow-triggered valuation-context changes
- paid provider integration
- Public Action version change
- output schema version change
- KRX breadth user-visible integration
- Phase 8.3 peer integration
- broad all-ticker cash-flow block
- ticker hard-coded production eligibility

---

# 4. Runtime source of truth

User-visible cash-flow must consume the same chain already validated by 9.0B–9.0D:

```text
Official filing
→ exact occurrence
→ financial lineage
→ canonical OCF
→ canonical PPE CAPEX
→ derived PPE-only FCF
→ PIT
→ freshness
→ comparable-period context
→ industry applicability
→ materiality
→ baseline-cash-flow-claim-consistency-v1
```

Do not create another calculation path for:

- AI
- fallback
- Telegram renderer

There must be one canonical selected user-visible context per ticker/run.

---

# 5. New user-visible contract

Implement a narrow contract, suggested name:

`cash-flow-user-visible-v1`

or extend an existing consumption contract if that is cleaner.

The contract should represent **selected user-visible context**, not raw canonical storage.

Minimum conceptual fields:

```text
contract
ticker
market
status

rollout_mode
selection_state
selection_reason

packet_id
assessment_date
cutoff

primary_period
period_type
filing_date
financial_currency

freshness_state
pit_state
industry_applicability
materiality_reason

primary_metric
primary_fact_ref

secondary_metric
secondary_fact_ref

ocf_fact_ref
ppe_capex_fact_ref
fcf_fact_ref

deterministic_relations

baseline_consistency_state
resolved_unknown_ids
suppressed_baseline_claim_ids

allowed_sections
prohibited_claims

ai_enabled
fallback_enabled
user_visible_enabled
```

Actual naming follows repository style.

---

# 6. Runtime rollout mode / kill switch

Implement or reuse a feature-mode mechanism.

Preferred conceptual modes:

```text
OFF
SELECTIVE_CURRENT_FORMAL_FULL_FCF
```

If an existing runtime feature-flag system exists, use it.

If none exists, add the smallest safe configuration mechanism.

Requirements:

- missing/invalid configuration → `OFF`
- `OFF` disables user-visible cash-flow in both AI and fallback
- `OFF` does NOT disable:
  - canonical OCF/CAPEX/FCF
  - Phase 9.0C archive shadow
  - Phase 9.0D runtime canary
  - baseline cash-flow consistency safety
- `SELECTIVE_CURRENT_FORMAL_FULL_FCF` enables only the initial 9.0E rollout subset
- no ticker list inside the flag

Document exact operator kill-switch procedure.

---

# 7. Kill-switch safety

The kill switch must allow an operator to stop **new user-visible cash-flow enrichment** without reverting canonical data infrastructure.

When set to OFF:

- existing production baseline consistency repair remains active
- stale/unsupported FCF prose must not reappear
- AI cash-flow sidecar is not supplied for user-visible use
- fallback cash-flow supplement is not rendered
- canary may continue
- receipt/exactly-once behavior unchanged

If configuration change requires service restart, document that explicitly.

Do not invent a remote control system purely for this phase.

---

# 8. Initial market scope

Initial 9.0E rollout:

```text
US / supported foreign issuers only
```

KR is excluded from user-visible cash-flow rollout because OpenDART cash-flow period context remains fail-closed.

Do not hard-code Korean tickers.

Use a market/source/eligibility rule.

Korean Re remains outside generic enterprise FCF logic.

---

# 9. Initial eligibility gate

A subject is user-visible eligible only if all required conditions pass.

Minimum:

1. rollout mode = `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
2. market/source allowed by initial rollout
3. canonical full FCF exists
4. OCF Fact valid
5. PPE-CAPEX Fact valid
6. derived FCF Fact valid
7. FCF input Fact lineage complete
8. PIT PASS
9. freshness = current formal
10. not formal-lagging-provisional for current numeric display
11. not stale
12. not blocked
13. not N/A
14. industry applicability allows FCF reasoning
15. baseline consistency has no unresolved conflict
16. cash-flow materiality selector chooses the context
17. user-visible numeric provenance can be resolved
18. no relevant P0/P1 data-quality caution

If one required condition fails:

`user_visible_enabled = false`

for that subject.

---

# 10. No ticker hard-coding

Do not implement:

```python
if ticker in {"GOOGL", "TSLA", ...}
```

for rollout eligibility.

Tickers may appear in tests and reports.

Production selection must be contract-driven.

The eligible subset may change automatically as filing/freshness state changes.

---

# 11. Full-FCF only initial rollout

Initial rollout requires safe full FCF.

OCF-only subjects:

- remain valid internally
- continue 9.0D canary behavior
- are NOT part of initial numeric user-visible rollout

Do not infer FCF from OCF-only.

Do not convert missing CAPEX to zero.

A later phase may decide whether OCF-only user-visible context adds enough value.

---

# 12. Formal-lagging-provisional

Subjects whose latest formal cash-flow period trails newer official provisional earnings must not display the old FCF as if it were current-quarter cash flow.

Initial 9.0E rule:

```text
formal-lagging-provisional
→ current user-visible cash-flow numeric display OFF
```

They may retain pre-existing non-cash-flow earnings context.

Do not add old FCF simply because it is canonical.

---

# 13. Stale / blocked

If a current formal period is blocked or a safe FCF is stale:

- no user-visible FCF number
- no historical substitution as current
- baseline consistency gate still suppresses false current cash-flow claims
- no "FCF unavailable" sentence unless the limitation is decision-relevant and correctly scoped

---

# 14. Materiality selector

Do not show cash flow merely because it is eligible.

Reuse Phase 9.0C materiality logic.

Possible materiality evidence:

- existing monitoring Unknown specifically about OCF/CAPEX/FCF
- existing next check about cash conversion
- thesis driver depends on CAPEX-to-cash conversion
- sign transition is decision-relevant
- earnings/OCF divergence is decision-relevant
- CAPEX burden materially changes earnings-quality interpretation
- industry applicability marks cash flow PRIMARY/SECONDARY
- existing business thesis specifically requires cash generation

Do not create a 0–100 materiality score.

---

# 15. User-visible metric selection

Avoid default three-number dumping.

Default:

- select one primary exact cash-flow metric
- use a second exact metric only when necessary to explain the economically important relation
- do not routinely print OCF + CAPEX + FCF as a tuple

Preferred primary metric for full-FCF rollout:

`PPE-only FCF`

unless an OCF or CAPEX value is more decision-relevant for the actual interpretation.

All selected numbers must be canonical.

---

# 16. User-facing FCF label

The backend metric is:

```text
OCF - PPE CAPEX
```

The user-facing label must not imply management-defined FCF if that is not what it is.

Preferred Korean concept:

`PPE 투자 후 잉여현금흐름`

or:

`잉여현금흐름(OCF-PPE CAPEX 기준)`

Choose the shortest natural wording that preserves scope.

Do not call it:

- company-reported FCF
- management FCF

unless it actually is.

---

# 17. Period label

Every exact user-visible cash-flow number must have sufficient period identity.

Examples conceptually:

- `2026년 상반기 누계`
- `2026년 2분기 누계`
- `2025 회계연도`

Use issuer fiscal period, not assumed calendar period.

If YTD:

do not call it standalone quarter.

Avoid repeating verbose period metadata in every sentence if the section already establishes it.

---

# 18. Currency / unit

Use canonical financial currency.

Do not copy share-price currency.

Do not FX-convert simply for presentation.

Formatter must preserve:

- sign
- currency
- unit scaling

No hidden cross-currency arithmetic.

---

# 19. User-visible placement

Do NOT create a mandatory new cash-flow section for every ticker.

Preferred ownership:

`business_earnings` / earnings-quality portion of the message.

User-facing renderer may implement one of the following, based on existing message architecture:

A. one concise cash-flow sentence inside the existing core/business section

or

B. one optional compact `현금흐름` block only for selected tickers

Choose one consistent implementation after preview.

The choice must minimize duplication and message growth.

Do not scatter the same number across multiple sections.

---

# 20. Exact numeric ownership

Primary exact cash-flow number owner:

`business_earnings` / earnings-quality user-visible slot.

Do not repeat the exact same FCF number in:

- core judgment
- valuation
- price
- observer view
- holder view
- next checks
- warnings

Core judgment may summarize meaning without repeating the number.

---

# 21. Baseline consistency is applied before enrichment

Use:

`baseline-cash-flow-claim-consistency-v1`

before rendering cash-flow enrichment.

Order:

```text
existing baseline qualitative claims
        ↓
consistency check
        ↓
suppress / qualify invalid stale claims
        ↓
select user-visible canonical cash-flow context
        ↓
render enrichment
```

Never append a correct FCF sentence underneath a contradictory old FCF sentence.

---

# 22. TSLA regression requirement

The prior unsupported `FCF 적자` root family must remain suppressed.

When 9.0E is enabled:

- if TSLA is materiality-selected and current-formal eligible, canonical cash-flow may become visible under the 9.0E contract
- if it is not selected, do not force the number
- in either case, unsupported `FCF 적자` must not return
- `FCF 흑자 전환 필요` must not reappear as an implied current-negative state without valid provenance/qualification

No TSLA-specific production code.

---

# 23. Resolved Unknown replacement

When current-formal full FCF is selected:

A message must not simultaneously say:

- OCF unavailable
- CAPEX unavailable
- FCF unavailable

for the same semantic scope.

Resolved Unknowns should be:

- removed
- or replaced with the next decision-relevant Unknown

Examples:

- future durability of FCF
- billing conversion
- margin
- financing
- dilution
- inventory
- customer economics

Only use Unknowns actually supported by packet/thesis context.

---

# 24. Eligible but not selected

If canonical current-formal FCF exists but materiality selector does not select it:

- do not display cash-flow number
- still suppress false "FCF unavailable" baseline claims
- do not add a generic "FCF exists" sentence merely for completeness
- next checks may still monitor FCF trend if it is an existing valid monitoring metric

---

# 25. AI-assisted production path

Add the selected user-visible cash-flow context to the production AI reasoning input only when 9.0E mode is enabled and the subject passes selection.

Do not expose raw filing rows.

Provide:

- selected canonical Fact refs
- period
- freshness/currentness
- safe deterministic relation
- industry/materiality context
- allowed claims
- prohibited claims

The AI is not asked to calculate FCF.

---

# 26. AI prompt policy

The AI must understand:

- cash-flow use is optional and selective
- exact cash-flow numbers require supplied Fact refs
- one useful relation is better than a numeric dump
- negative FCF is not automatically bad
- positive FCF is not automatically good
- FCF alone does not change investment-logic status
- FCF alone does not change valuation context
- CAPEX-heavy businesses require reinvestment context
- memory-cycle FCF is not automatically structural
- biotech negative FCF is cash burn, not automatic invalidation
- unsupported CCC/ROIC/runway calculations are prohibited

Do not change Scheduled Task prompt text/config if policy can be implemented in shared runtime prompt assembly.

Task IDs/times remain unchanged.

---

# 27. AI `facts_used` / ownership

When AI uses user-visible FCF:

- canonical FCF Fact ID must appear in the appropriate reasoning/numeric claim lineage
- if OCF/CAPEX are explicitly mentioned numerically, their Fact IDs must also be present
- do not use raw source IDs as substitutes for canonical Fact refs
- reasoning owner remains business/earnings-quality

---

# 28. AI failure behavior

Cash-flow is optional enrichment, not a reason to bypass safety.

If the AI generates unsupported cash-flow claims:

- existing numeric/semantic validator must reject them
- do not loosen the validator
- production fallback remains available

Do not silently accept an unsupported cash-flow statement to preserve AI-assisted delivery.

---

# 29. Deterministic fallback path

Fallback must use the **same selected user-visible contract** and canonical facts as AI.

Fallback eligibility rules must be identical for:

- current-formal
- freshness
- PIT
- full-FCF requirement
- market rollout
- materiality
- baseline consistency

The fallback renderer may use deterministic prose, but not a separate eligibility calculation.

---

# 30. AI / fallback parity contract

Parity means:

- same selected subjects
- same fact refs
- same period
- same currency
- same FCF scope
- same sign
- same currentness
- same suppression reasons

AI prose and fallback prose need not be identical.

Create an audit key such as:

`cash_flow_user_visible_context_id`

shared by both paths.

Any sign/period/scope mismatch between AI and fallback is a hard failure.

---

# 31. Fallback deterministic wording

Fallback wording should describe one deterministic relation.

Safe patterns may include concepts such as:

- current-formal PPE-investment-after FCF is positive/negative
- OCF remains positive while PPE investment absorbs cash
- FCF sign changed versus a safe comparable period
- FCF remains negative during build-out

Only use relations already supported by the contract.

Do not invent good/bad thresholds.

Do not use "strong" / "weak" purely from amount size without a defined basis.

---

# 32. Optional-enrichment failure isolation

Cash-flow enrichment must not make a safe core fallback undeliverable merely because optional enrichment could not be formed.

If per-ticker cash-flow enrichment fails its selector/formatter:

- omit the enrichment
- record suppression/failure reason
- keep the safe base message

However:

If existing baseline prose contains an unsupported cash-flow claim, the baseline consistency gate must suppress it.

Do not keep a wrong claim just because the new enrichment was omitted.

---

# 33. No user-visible valuation misuse

Do not move FCF into Valuation as:

- FCF Yield
- P/FCF
- EV/FCF

No valuation multiple derives from 9.0E.

Valuation remains existing valuation framework.

Cash flow can influence earnings-quality interpretation, not create a new valuation metric.

---

# 34. No automatic investment-logic state change

Cash-flow enrichment must not itself cause backend:

- strengthened
- weakened
- invalidated
- warning open/close

without the existing broader evidence contract.

AI may interpret cash-flow in prose.

Any status delta still passes the existing state/validation rules.

No automatic DB persistence added in this phase.

---

# 35. Industry-specific reasoning rules

Use Phase 9.0A/9.0C applicability.

## Cloud/platform
Connect CAPEX to operating cash generation and FCF only when periods align.
Do not treat AI CAPEX as automatically negative.

## Software/services
Do not confuse company-defined FCF with backend PPE-only FCF.

## Memory/semiconductor
Interpret FCF with cycle/ASP/margin context.
Do not permanentize peak-cycle cash generation.

## HPC/data-center
Separate:
operating cash generation
vs construction/reinvestment cash absorption.
Negative FCF during build-out is not automatic business failure.

## Biotech
Negative FCF is cash burn.
Do not calculate runway without cash/runway facts.

## Automotive
Connect FCF with operating margin and investment context.
Do not let FCF alone decide Robotaxi/FSD investment logic.

## Foreign issuers
Issuer-level FCF can be shown in financial currency.
Do not create per-share/yield metrics without security/FX basis.

## Insurance
Generic enterprise FCF rollout remains excluded.

---

# 36. Positive/negative sign is not verdict

User-visible renderer/AI may say:

- positive
- negative
- turned positive
- turned negative

when canonical relations support it.

It must not automatically translate sign into:

- good
- bad
- strengthened
- weakened
- cheap
- expensive

Investment interpretation requires business context.

---

# 37. Comparable-period relation

If a safe comparable period exists, 9.0E may use a relation such as:

- negative → positive
- positive → negative
- higher positive
- lower positive
- less negative
- more negative

Do not use misleading percentage growth around zero/negative bases.

If comparable period is not safe:

show current fact only, or omit the comparison.

---

# 38. User-visible numeric binding

All displayed OCF/PPE-CAPEX/FCF values:

- automatic canonical binding: required
- manual: 0
- rejected: 0
- unresolved: 0

FCF numeric claim must bind directly to the canonical derived FCF Fact.

AI arithmetic is prohibited.

---

# 39. Semantic validator extension

Production validation must reject at least:

- cash-flow number without canonical Fact
- future filing
- stale-as-current
- formal-lagging-provisional displayed as current
- wrong period
- YTD described as standalone quarter
- OCF as FCF
- management FCF / backend PPE-only FCF confusion
- CAPEX scope overclaim
- unsupported FCF/share
- FCF Yield
- EV/FCF
- P/FCF
- CCC
- ROIC
- unsupported runway inference
- insurance generic FCF
- KR blocked cash-flow leakage
- baseline current-state contradiction
- duplicate exact cash-flow ownership
- cash-flow-only valuation-context mutation

---

# 40. Runtime quality

Keep existing thresholds.

Detect and prevent new portfolio boilerplate such as:

`OCF X, CAPEX Y, FCF Z입니다.`

for many tickers.

Structured fact tuples may repeat internally.

User-visible analytical prose must remain industry/subject specific.

---

# 41. Numeric-density rule

Do not create a rigid universal numeric cap, but enforce default minimalism.

Default user-visible cash-flow reasoning:

- 1 exact number
- optionally 2 if required for a clear economic relation

Three exact cash-flow numbers in one sentence/block must require explicit material justification in the audit and should be exceptional.

No portfolio-wide triple-number template.

---

# 42. Message-length discipline

For selected subjects:

compare before/after user-visible length.

No arbitrary percent threshold.

But require human audit for:

- significant verbosity increase
- cash-flow detail crowding out business thesis
- repetitive period/scope disclaimers

Cash-flow enrichment should replace resolved Unknown/boilerplate where possible, not only append text.

---

# 43. Exact before/after preview — mandatory

Before production enablement, generate exact message previews for:

A. AI-assisted path
B. deterministic fallback path

Using an immutable recent US packet, preferably run-30 or the latest safe comparable packet.

Preview the full message set, not isolated sentences.

For every subject show:

- before
- after
- selected/not selected
- selected Fact IDs
- reason
- resolved/suppressed old claims
- length delta

---

# 44. Positive-control preview classes

The preview must include naturally available examples of:

- positive current-formal FCF
- negative current-formal FCF
- CAPEX-heavy business
- memory/semiconductor
- biotech/pre-profit
- automotive
- foreign issuer if eligible

Do not force a class if no current-formal full-FCF candidate exists; mark NOT_AVAILABLE.

---

# 45. Negative-control preview classes

Required:

- OCF-only → no initial user-visible FCF
- formal-lagging-provisional → no current numeric display
- stale → no current display
- blocked → no display
- KR OpenDART → no display
- insurance N/A → no generic FCF
- feature mode OFF → no cash-flow enrichment

---

# 46. TSLA exact preview

TSLA preview must demonstrate:

- old unsupported `FCF 적자` does not return
- old implied `FCF 흑자 전환 필요` does not return unsupported
- if TSLA is selected, only canonical current-formal cash-flow reasoning appears
- if not selected, no forced canonical number
- no automatic investment-logic status change from positive FCF
- no valuation change from FCF alone

---

# 47. Unknown-resolution preview

For each selected ticker, compare:

Before:
- cash-flow Unknowns

After:
- resolved
- remaining
- replacement Unknown

Targets:

- fresh selected full FCF + "FCF unavailable" contradiction = 0
- no removal of unrelated valid Unknowns
- no generic cash-flow Unknown retained just to fill a section

---

# 48. AI/fallback parity preview

For each selected subject:

| Field | AI | Fallback |
|---|---|---|
| eligibility | same | same |
| period | same | same |
| currency | same | same |
| FCF scope | same | same |
| FCF sign | same | same |
| Fact ID | same | same |
| baseline suppressions | same | same |

Prose may differ.

Any fact/sign/period/scope mismatch:

FAIL.

---

# 49. Feature-OFF exact regression

With user-visible mode `OFF`:

Production output must equal the post-9.0D.1 baseline for cash-flow enrichment.

Expected:

- no new FCF number
- no new cash-flow block
- existing 9.0D.1 consistency suppression remains active

Use exact or semantically canonical snapshot comparison where repository formatting makes byte equality inappropriate.

Document method.

---

# 50. Feature-ON selective regression

With mode `SELECTIVE_CURRENT_FORMAL_FULL_FCF`:

Only selected eligible subjects change.

Non-selected/ineligible subject cash-flow-visible diff:

`0`

except for already-required baseline consistency suppression.

---

# 51. Kill-switch tests

Required:

1. OFF at startup → no enrichment
2. SELECTIVE mode → eligible enrichment
3. invalid value → fail-safe OFF
4. mode switched OFF → both AI and fallback stop new enrichment
5. canary still runs with user-visible mode OFF
6. baseline consistency still runs with user-visible mode OFF
7. no scheduled-task config changes required beyond existing runtime config mechanism
8. no stale cached selected sidecar leaks after OFF

---

# 52. Kill-switch operating document

Create:

`docs/operations/CASH_FLOW_USER_VISIBLE_KILL_SWITCH.md`

or repository-equivalent operations path.

Document:

- config name/location
- valid modes
- default/fail-safe
- how to disable
- whether restart is required
- how to verify OFF
- what remains active after OFF
- what artifacts prove disablement

No secret values.

---

# 53. Production safety on per-ticker failure

If one ticker's cash-flow selection or rendering fails:

- do not expose unsafe cash-flow
- do not corrupt other tickers
- do not duplicate messages
- do not change message count
- base message should remain deliverable if otherwise safe
- record per-ticker suppression

If the AI itself generates unsupported cash-flow, existing AI rejection/fallback path remains valid.

---

# 54. Production fallback parity on AI rejection

If AI candidate is rejected for any reason:

Fallback must still be able to display the same selected safe cash-flow context.

Therefore cash-flow user-visible value must not depend on AI-assisted delivery success.

This is a critical acceptance criterion.

---

# 55. Production AI success path

If AI candidate passes:

- cash-flow claims must satisfy numeric/semantic/quality gates
- no fallback cash-flow message is sent
- exactly-once remains unchanged

---

# 56. Receipt / archive

Production receipt/archive should record enough internal audit metadata to determine:

- user-visible cash-flow mode
- selected subjects
- selected context IDs
- cash-flow Fact IDs used
- suppressions
- kill-switch state

Do not expose internal metadata to the user.

Do not change receipt semantics in a way that breaks historical verification.

---

# 57. Canary coexistence

Phase 9.0D canary remains active.

After 9.0E enablement:

- production user-visible integration and canary must not recursively feed each other
- canary continues observationally
- canary may compare production cash-flow claims to its expected context
- production delivery must not wait for canary
- canary failure must not affect production

---

# 58. Canary parity extension

If cheap and architecture-compatible, add a canary audit that checks:

```text
production selected cash-flow context
==
canary expected selected context
```

Compare:

- subject selection
- Fact IDs
- period
- scope
- sign
- suppressions

The canary remains post-delivery observational.

---

# 59. Deployment staging

Use staged rollout inside this single phase.

## Stage A — implementation
- code/contract/validator/renderers
- feature mode default OFF

## Stage B — archive previews
- AI before/after
- fallback before/after
- parity
- negative controls
- kill switch

## Stage C — validation
- focused
- regression
- full CI

## Stage D — main/operating promotion
- mode still OFF initially

## Stage E — operating readiness
- health
- task configuration
- canary
- kill-switch verification

## Stage F — selective enablement
- set operating mode to `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- no manual Scheduled Task
- no manual Telegram
- next natural run becomes first user-visible proof

Do not skip stages to catch a same-day run.

---

# 60. Enablement gate

The selective operating mode may be enabled only if:

- Open P0 = 0
- Open material P1 = 0
- AI preview PASS
- fallback preview PASS
- parity PASS
- baseline consistency PASS
- numeric binding PASS
- semantic validation PASS
- runtime quality PASS
- feature-OFF regression PASS
- kill-switch PASS
- full test suite PASS
- exact-SHA CI PASS
- operating health PASS
- existing task configs unchanged

---

# 61. KR afternoon-window safety

Today is 2026-08-21 KST.

Known KR operational window:

- KRX telemetry around 16:05
- KR primary 16:15
- KR backup 16:55

Inspect actual scheduler configuration.

If promotion/enablement cannot be safely completed before the repository-defined pre-run freeze:

- do not deploy mid-cycle
- allow KR natural cycle to complete on prior version
- promote after the protected window

Although KR cash-flow rollout is excluded, shared runtime code may still affect delivery, so the window must be protected.

No manual compensation.

---

# 62. Next US window safety

Protect the configured:

- KRX 08:05
- US primary 08:15
- US backup 08:30

Do not deploy during the repository's protected execution window.

If no explicit freeze contract exists, use the established operational practice from prior phases and document it.

No manual US run.

---

# 63. Natural user-visible proof

After 9.0E enablement, the next natural US production run should be reviewed separately.

Do not wait inside the implementation task.

The implementation completion state can be:

```text
CASH_FLOW_USER_VISIBLE:
ENABLED_SELECTIVE_PENDING_NATURAL
```

The next natural run should verify:

- actual selected subjects
- exact numbers
- AI/fallback path
- production quality
- no contradiction
- no message bloat
- kill-switch not needed

---

# 64. Natural proof does not block unrelated architecture

Under Phase Advancement Rule:

If 9.0E implementation has:

- P0 = 0
- material P1 = 0
- all retrospective/preview/CI gates PASS

then architecture/research for the next major feature may proceed in parallel with user-visible natural observation.

However:

- broader cash-flow rollout should wait for user-visible natural proof
- any new P0 interrupts rollout expansion

---

# 65. Initial user-visible rollout class

The initial rollout class should be described dynamically as:

`SELECTIVE_CURRENT_FORMAL_FULL_FCF`

Optionally further constrained by materiality:

`SELECTIVE_CURRENT_FORMAL_FULL_FCF_MATERIAL`

Do not persist a static ticker whitelist.

---

# 66. No broad cash-flow section

The presence of canonical FCF must not cause:

20 companies
→ 20 cash-flow blocks.

Expected:

selected subset only.

A company with no decision-relevant cash-flow change may have no new cash-flow text.

---

# 67. No daily repetition

If the same current-formal FCF has already been visible and nothing relevant changed:

daily monitoring should not mechanically repeat the same full numeric sentence forever.

Use existing delta-first philosophy.

For the first 9.0E implementation:

Design the metadata needed to distinguish:

- first visible fact
- changed comparable relation
- unchanged current fact

Do not build a complex long-term lifecycle if repository already provides enough assessment history.

At minimum prevent guaranteed every-day numeric boilerplate.

---

# 68. First exposure vs unchanged exposure

Possible internal display reasons:

- FIRST_SAFE_EXPOSURE
- MATERIAL_NEW_FORMAL_PERIOD
- MATERIAL_RELATION_CHANGE
- RESOLVED_PRIOR_UNKNOWN
- SUPPRESSED_NO_DELTA

Use existing vocabulary if available.

Do not add arbitrary time-based cooldown.

---

# 69. Daily delta and first rollout

Because 9.0E is newly enabled, the first natural production after enablement may legitimately display a current-formal FCF to resolve an existing Unknown even if the filing itself is not from that same day.

This must be labeled as:

- current-formal context
- not "today newly reported" unless it was actually newly reported

Do not convert feature rollout into a false news event.

---

# 70. User-facing wording for first safe exposure

If current-formal FCF is older than today's date but still the latest formal period:

Use period-specific wording.

Do not say:

- "오늘 FCF는..."
- "이번에 FCF가..."

unless the filing/update actually occurred today.

The user should understand the evidence period.

---

# 71. Status-delta safety

New user-visible cash-flow context may materially change interpretation, but the rollout itself must not create a false daily business-thesis delta.

If the cash-flow Fact existed before the current daily run and is merely newly integrated into the system:

- treat it as resolved evidence/context
- not as a newly occurred company event

Record such cases as:

`SYSTEM_EVIDENCE_RECOVERY`

or equivalent internal audit state.

Do not call it a new company strengthening signal.

---

# 72. Existing assessment history

Do not rewrite prior `no_material_change` assessments simply because better cash-flow data is now available.

Historical record remains historical.

Current analysis may become more informed without back-editing old assessments.

---

# 73. Fallback-specific placement

The deterministic fallback currently has a compact user-facing structure.

Do not create large expansion.

Preferred:

one sentence in the `핵심`/business context
or one optional compact cash-flow line.

The fallback must still prioritize:

- investment logic
- current price context
- valuation
- next checks

Cash flow should improve earnings-quality interpretation, not dominate the whole message.

---

# 74. AI-specific placement

AI output may integrate cash-flow more naturally into business/earnings reasoning.

But numeric ownership remains singular.

Do not put the same FCF value in:

- core
- business
- next check

all at once.

---

# 75. Fallback deterministic relation library

If adding deterministic fallback templates, keep them typed and minimal.

Possible relation categories:

```text
FCF_POSITIVE
FCF_NEGATIVE
FCF_TURNED_POSITIVE
FCF_TURNED_NEGATIVE
OCF_POSITIVE_FCF_NEGATIVE
CAPEX_DIRECTION_WITH_FCF_CONTEXT
```

Only define categories backed by canonical relations already implemented.

Do not encode investment verdicts into relation names.

---

# 76. No arbitrary magnitude labels

Do not call FCF:

- large
- small
- strong
- weak
- insufficient

based solely on absolute amount.

Such labels require an explicit denominator/comparison.

Initial 9.0E should mostly use:

- sign
- comparable-period relation
- business context

---

# 77. Negative FCF safety

For negative FCF:

Do not automatically render:

`현금흐름이 악화됐다`

unless comparable relation proves deterioration.

Do not automatically render:

`재무 위험 증가`

without balance-sheet/funding evidence.

Use industry context.

---

# 78. Positive FCF safety

Positive FCF does not mean:

- investment logic strengthened
- cheap valuation
- strong balance sheet
- permanent cash generation

unless other evidence supports it.

---

# 79. Quality review — human-readable examples

Create reviewed before/after examples for each selected class.

Each example must answer:

1. What did the old message say?
2. What current-formal cash-flow Fact is now available?
3. Why is it material?
4. What exact sentence changed?
5. Which old Unknown/claim was removed?
6. Did the investment-logic status change?
7. Why/why not?

---

# 80. User-visible parity acceptance

For every selected ticker in preview:

AI and fallback must not disagree on:

- FCF sign
- period
- scope
- currency
- currentness

Target mismatches:

`0`

---

# 81. Public schema boundary

Do not change Public Action schema.

Do not add cash-flow fields to public Action response in 9.0E.

This phase concerns production monitoring message consumption.

Public snapshot exposure can be a separate future decision.

---

# 82. Internal packet boundary

If the production AI packet must gain internal cash-flow context:

- keep schema `4` externally
- use internal sidecar/extension mechanism where possible
- do not break archived packet validation
- record internal contract version

If changing the canonical internal packet is unavoidable, document why and prove backward compatibility.

---

# 83. Receipt metadata

Add only the minimum audit metadata necessary.

Suggested:

```text
cash_flow_user_visible_mode
cash_flow_selected_count
cash_flow_context_ids
cash_flow_fact_ids_used
cash_flow_suppressed_count
```

Do not include huge raw Fact payloads in receipts.

---

# 84. Feature mode in archive

Each production run after implementation should be able to answer:

- was 9.0E OFF or SELECTIVE?
- which subjects were selected?
- which cash-flow facts were actually rendered?
- which were suppressed?

This must be auditable even when actual delivery uses fallback.

---

# 85. Run-30 full replay

Use run-30 as primary immutable replay because it has natural 9.0D full-FCF evidence.

Generate:

A. feature OFF
B. feature SELECTIVE + AI path preview
C. feature SELECTIVE + fallback preview

Compare.

Do not modify original run-30 artifacts.

---

# 86. Run-30 required controls

Must demonstrate:

- full-FCF eligible subset
- OCF-only suppression
- formal-lagging suppression
- blocked suppression
- TSLA consistency
- negative FCF cases
- positive FCF case
- AI/fallback fact parity
- no unsupported metric
- no duplicate exact ownership

---

# 87. KR run-29 negative replay

Run a KR negative control using repaired run-29 context.

Expected:

- user-visible cash-flow added: `0`
- OpenDART blocked cash-flow leakage: `0`
- Korean Re generic FCF: `0`
- existing KR message quality repairs remain PASS

---

# 88. Feature OFF production regression

Replay recent US/KR baselines with mode OFF.

Cash-flow user-visible changes:

`0`

except 9.0D.1 consistency repair is already baseline and remains active.

---

# 89. AI rejection / fallback test

Force/test a fixture where:

- cash-flow selected
- AI candidate fails unrelated quality gate

Expected:

- fallback uses same safe selected cash-flow context
- exactly once
- no lost cash-flow fact due solely to AI failure
- no duplicate AI/fallback message

---

# 90. Cash-flow-specific AI validation failure test

Fixture:

AI invents unsupported FCF claim.

Expected:

- AI rejected or claim safely handled by existing architecture
- unsupported claim never sent
- deterministic fallback remains safe
- production delivery integrity preserved

Do not weaken validator to save AI.

---

# 91. Per-ticker enrichment failure fixture

Fixture:

selector says eligible but renderer encounters an unexpected optional formatting issue.

Expected:

- no unsafe cash-flow text
- subject base message still safe
- no whole-bundle duplicate
- audit records suppression/failure
- baseline consistency still enforced

---

# 92. Kill-switch feature OFF after SELECTIVE cache

Test stale-cache safety:

1. build/select cash-flow context under SELECTIVE
2. switch mode OFF
3. render again

Expected:

no cached user-visible cash-flow leakage.

---

# 93. Production task configuration

Do not change the four task IDs/times:

- US primary 08:15
- US backup 08:30
- KR primary 16:15
- KR backup 16:55

No manual task execution.

If shared runtime prompt assembly changes, Scheduled Task stored prompt/config should still remain unchanged unless absolutely required; any change requires explicit justification.

---

# 94. KRX telemetry

Keep:

- 08:05
- 16:05

unchanged.

9.0E does not integrate KRX breadth.

Read-only latest telemetry may be included in final report.

No new provider call for KRX evidence.

---

# 95. KR OpenDART

Keep:

`KR_OPENDART_PERIOD_RECOVERY_PRIORITY = MEDIUM`

Do not implement it here.

KR remains excluded from initial user-visible cash-flow.

---

# 96. CCC / ROIC

Remain:

- CCC: DEFERRED
- Standard ROIC: DEFERRED

Any new user-visible claim implying these metrics is an error.

---

# 97. Prior natural AI track

`Natural AI-Assisted Delivery` remains independent.

Do not block 9.0E implementation because production sometimes falls back for unrelated AI-quality reasons.

The fallback path must receive the same safe cash-flow value.

---

# 98. Production Assist

Remain:

`OFF`

9.0E user-visible integration is not the same thing as Production Assist.

Do not change that policy.

---

# 99. Tests — selection

Required fixtures:

- US current-formal full FCF + material → selected
- US current-formal full FCF + not material → suppressed
- formal-lagging-provisional → suppressed
- stale → suppressed
- blocked → suppressed
- OCF-only → suppressed from initial numeric rollout
- KR → suppressed
- insurance → N/A
- invalid feature mode → OFF
- valid SELECTIVE mode → contract applied

---

# 100. Tests — period and scope

Required:

- YTD period label correct
- FY label correct
- non-calendar fiscal period correct
- current-formal comparison safe
- management FCF not confused
- PPE-only scope preserved
- currency preserved
- no cross-currency conversion

---

# 101. Tests — numeric provenance

Required:

- selected FCF exact number binds to canonical FCF Fact
- optional OCF/CAPEX number binds to own Fact
- input Fact lineage remains verifiable
- no raw occurrence direct binding
- no AI arithmetic
- negative sign preserved
- formatting stable

Targets:

manual/rejected/unresolved = 0.

---

# 102. Tests — baseline consistency

Required:

- unsupported current negative claim + positive comparable FCF → suppressed
- valid current negative claim + negative comparable FCF → preserved
- historical negative with qualifier → preserved
- historical negative without qualifier → qualified/suppressed
- unknown-scope unsupported FCF claim → suppressed
- false "FCF unavailable" + fresh selected FCF → removed
- no canonical current Fact → provenance-backed baseline only

---

# 103. Tests — AI/fallback parity

For identical selected context:

- subject selection equal
- context ID equal
- FCF Fact ID equal
- period equal
- currency equal
- scope equal
- sign equal
- baseline suppression set equal

Mismatches = 0.

---

# 104. Tests — kill switch

All kill-switch cases from Sections 6–7 and 51–52.

Feature OFF must be a first-class tested production mode.

---

# 105. Tests — message quality

Required:

- no new cash-flow boilerplate family
- no triple-number portfolio template
- exact number primary ownership
- no duplicate FCF number across sections
- Unknown quality
- next-check specificity
- industry specificity
- final Korean language
- no internal accounting metadata leakage

---

# 106. Tests — production delivery safety

Required:

- AI success + selected cash flow
- AI rejection + fallback + selected cash flow
- no eligible cash flow
- per-ticker enrichment suppression
- feature OFF
- kill switch OFF
- backup interaction
- exactly-once
- receipt integrity
- no message-count regression

---

# 107. Regression suite

Must preserve:

- Phase 8.5.5
- 8.5.5.1
- 8.5.5.2
- run-27
- run-28
- run-29
- RXRX/WULF PBR ownership
- CORZ typed valuation
- dynamic price context
- RR overlap
- confirmation lifecycle
- night-futures session/calendar
- fallback parity
- exactly-once
- receipts
- KRX telemetry
- 9.0B canonical core
- 9.0C shadow consumption
- 9.0D canary
- 9.0D.1 baseline consistency

---

# 108. Full validation

Required:

- focused 9.0E selection/rendering suite PASS
- AI/fallback parity PASS
- baseline consistency PASS
- kill-switch PASS
- run-30 previews PASS
- run-29 KR negative control PASS
- full pytest PASS
- operating smoke PASS
- Ruff PASS
- `git diff --check` PASS
- Investment Knowledge parity PASS
- Chart Knowledge parity PASS
- Public Action `0.4.5`
- operationId `20/20 unique`
- schema `4`
- exact implementation SHA Actions Test/Lint PASS
- exact final SHA Actions Test/Lint PASS

---

# 109. P0 / P1 / P2

Continue Phase Advancement Rule.

## P0
Examples:

- wrong FCF number
- wrong period/scope/currency
- stale as current
- blocked KR leakage
- unsupported FCF assertion
- kill switch OFF but cash-flow still visible
- AI/fallback fact mismatch
- duplicate delivery
- receipt/exactly-once damage

P0 blocks enablement.

## P1
Examples:

- material selector causes systematic irrelevant clutter
- CAPEX-heavy interpretation materially distorted
- AI/fallback prose has materially different investment meaning despite same facts
- unresolved cash-flow contradiction in user-visible text

Material P1 blocks enablement.

## P2
Examples:

- small wording polish
- optional section placement preference
- minor message length
- OCF-only not rolled out
- KR excluded
- optional management FCF comparison

P2 does not block enablement.

---

# 110. Rollout readiness decision

Before enabling operating mode, explicitly set:

`CASH_FLOW_USER_VISIBLE_ROLLOUT_READY = YES/NO`

YES requires:

- P0 open = 0
- material P1 open = 0
- selection PASS
- AI preview PASS
- fallback preview PASS
- parity PASS
- baseline consistency PASS
- numeric provenance PASS
- semantic PASS
- quality PASS
- kill-switch PASS
- feature-OFF regression PASS
- full CI PASS
- operating health PASS

P2 cannot produce NO.

---

# 111. Operating promotion

After readiness YES:

1. fetch latest main
2. verify clean ancestry
3. promote implementation cleanly
4. sync operating checkout
5. restart API only if required by changed imported runtime/config behavior
6. health PASS
7. verify AI tasks unchanged
8. verify KRX telemetry unchanged
9. verify Production Assist OFF

Initially verify user-visible mode OFF after deployment.

Then perform selective enablement as a separate controlled config step in the same task.

---

# 112. Selective enablement

Set operating mode to:

`SELECTIVE_CURRENT_FORMAL_FULL_FCF`

or actual implementation-equivalent value.

Record:

- previous mode
- new mode
- config source
- whether restart required
- activation timestamp
- verification method

No manual Scheduled Task.

No manual Telegram.

---

# 113. Post-enable smoke without production send

After enabling:

Use only safe non-delivery smoke/fixtures.

Verify:

- mode recognized
- selector active
- kill switch still works
- Telegram sender not invoked
- no manual natural simulation counted as proof

Do not manually send test messages to production Telegram.

---

# 114. User-visible natural proof state

After implementation/enablement but before next natural run:

```text
Phase 9.0E:
DEPLOYED_SELECTIVE_PENDING_NATURAL

Cash Flow User Visible:
ENABLED_SELECTIVE_PENDING_NATURAL
```

This is a valid completion state.

Do not mark natural user-visible PASS before actual natural delivery.

---

# 115. Next natural review requirements

The next natural US run should review:

- production delivery mode
- selected cash-flow tickers
- actual rendered cash-flow text
- exact Fact IDs
- AI/fallback path
- numeric binding
- baseline consistency
- Unknown resolution
- message length/repetition
- production delivery integrity
- canary parity
- kill-switch necessity

Do not require arbitrary multiple runs.

---

# 116. Emergency natural failure response

If next natural run shows P0 caused by 9.0E:

- set user-visible mode OFF using documented kill switch
- leave canonical core/canary active
- preserve raw evidence
- perform targeted repair
- do not rewrite delivered/archive artifacts

If only P2:

- backlog
- keep selective rollout active unless operator judgment says otherwise

---

# 117. Natural selective rollout success

A single natural US run can be enough to mark:

`CASH_FLOW_USER_VISIBLE_NATURAL = LIVE_PASS_SELECTIVE_SUBSET`

if:

- at least one eligible cash-flow message is actually delivered
- exact number/provenance correct
- period/scope correct
- no P0/material P1
- production delivery unaffected
- no contradiction
- message quality acceptable

Unobserved classes remain excluded.

---

# 118. No mandatory KR natural proof

KR is excluded from initial rollout.

Therefore lack of KR cash-flow visibility is expected.

KR natural run should only prove:

- no leakage
- no shared-runtime regression

It need not delay US selective rollout.

---

# 119. Reports — architecture

Create/update:

`docs/architecture/CASH_FLOW_USER_VISIBLE_INTEGRATION.md`

Include:

- contract
- selection
- feature modes
- AI/fallback parity
- numeric ownership
- baseline consistency
- period/scope labeling
- failure isolation
- initial rollout exclusions

---

# 120. Reports — operations

Create:

`docs/operations/CASH_FLOW_USER_VISIBLE_KILL_SWITCH.md`

Include exact tested procedure.

---

# 121. Reports — selection audit

Create:

`docs/reports/20260821-phase9-0e-selection-audit.md`

Include current replay universe:

- eligible
- selected
- not material
- OCF-only
- lagging provisional
- stale
- blocked
- market excluded
- N/A

with reasons.

---

# 122. Reports — AI/fallback parity

Create:

`docs/reports/20260821-phase9-0e-ai-fallback-parity.md`

Include all selected preview subjects and exact Fact IDs/context IDs.

---

# 123. Reports — before/after

Create:

`docs/reports/20260821-phase9-0e-user-visible-before-after.md`

Include full message previews or links to generated full preview artifacts.

Must include:

- AI-assisted preview
- deterministic fallback preview
- feature OFF baseline

---

# 124. Reports — validator

Create:

`docs/reports/20260821-phase9-0e-user-visible-validation.md`

Include:

- numeric
- semantic
- quality
- baseline consistency
- Unknown resolution
- period/scope
- KR leakage
- unsupported metric checks

---

# 125. Reports — kill switch

Create:

`docs/reports/20260821-phase9-0e-kill-switch-validation.md`

Include all tested mode transitions and fail-safe behavior.

---

# 126. Reports — rollout readiness

Create:

`docs/reports/20260821-phase9-0e-rollout-readiness.md`

Include:

`CASH_FLOW_USER_VISIBLE_ROLLOUT_READY = YES/NO`

and reasons.

---

# 127. Reports — promotion

If promoted/enabled, create:

`docs/reports/20260821-phase9-0e-operating-promotion.md`

Include:

- code promotion
- operating sync
- feature mode enablement
- API
- schedules
- no manual runs
- kill-switch status

---

# 128. Reports — complete bundle

Create one final integrated report:

`docs/reports/20260821-phase9-0e-complete-report.md`

Recommended JSON:

`docs/reports/20260821-phase9-0e-complete-report.json`

Also create one downloadable bundle:

`20260821-phase9-0e-complete-report-bundle.zip`

ZIP should contain sanitized reports/JSON, not secret-bearing raw runtime files.

Report ZIP SHA-256.

Push sanitized reports to the implementation/report branch.

---

# 129. Work-instruction compliance

Completion report must include:

- instruction path
- instruction commit SHA
- instruction version
- implementation base
- deviations from instruction YES/NO
- exact deviation reason and safety impact if any

---

# 130. Completion-report format — repository

Report:

- branch
- instruction commit
- implementation commit
- final commit
- previous main
- final main
- operating SHA
- promotion method
- push
- working trees

---

# 131. Completion-report format — contract

Report:

- user-visible contract/version
- rollout mode enum
- initial market scope
- eligibility rules
- materiality behavior
- user-facing FCF label
- period-label rule

---

# 132. Completion-report format — selection

Report:

- universe
- canonical full FCF
- current-formal
- selected
- suppressed not material
- OCF-only
- lagging provisional
- stale
- blocked
- market excluded
- N/A

List selected tickers for preview/audit only.

---

# 133. Completion-report format — AI

Report:

- selected context count
- exact cash-flow claims
- binding automatic/manual/rejected/unresolved
- semantic errors
- quality
- message length change
- baseline contradictions
- resolved Unknowns

---

# 134. Completion-report format — fallback

Report same items.

Also:

- fallback delivery safety
- same Fact/context parity with AI
- message count
- exactly-once regression

---

# 135. Completion-report format — parity

Report:

- selection mismatch
- Fact-ID mismatch
- period mismatch
- scope mismatch
- sign mismatch
- currency mismatch
- suppression mismatch

Targets all `0`.

---

# 136. Completion-report format — TSLA

Report:

- 9.0D.1 unsupported FCF claim regression
- whether TSLA selected
- if selected: exact canonical fact/period/scope used
- if not: why not
- no status/valuation auto-change

---

# 137. Completion-report format — negative controls

Report:

- HUT/OCF-only class or actual equivalent
- TSM/WRD lagging class or actual equivalent
- SKHY blocked class or actual equivalent
- KR
- insurance
- feature OFF

Use actual current classifications.

---

# 138. Completion-report format — kill switch

Report:

- config key/mode
- default
- fail-safe
- OFF test
- SELECTIVE test
- stale-cache test
- canary behavior under OFF
- baseline consistency under OFF
- restart requirement

---

# 139. Completion-report format — validation

Report:

- focused tests
- parity tests
- kill-switch tests
- regression tests
- full pytest
- operating smoke
- Ruff
- diff
- Knowledge
- docs
- Public Action
- operationId
- schema
- implementation Actions
- final Actions

---

# 140. Completion-report format — operating

Report:

- API health
- API restart yes/no
- policy
- schema
- AI mode
- Production Assist
- AI tasks and schedules
- KRX telemetry
- feature mode before
- feature mode after
- activation time

---

# 141. Completion-report format — safety

Report counts:

- manual Telegram
- manual Scheduled Task
- Pilot mutation
- DB mutation/migration
- archive rewrite
- receipt rewrite
- force push
- history rewrite

Targets: `0`.

---

# 142. Completion-report format — severity

Report:

- Open P0
- Open material P1
- P2 backlog

Enablement requires:

P0 = 0
material P1 = 0.

---

# 143. Final phase state

If implementation + promotion + enablement PASS:

```text
Phase 9.0E:
DEPLOYED_SELECTIVE_PENDING_NATURAL

Cash Flow User Visible:
ENABLED_SELECTIVE_PENDING_NATURAL

Cash Flow Runtime Canary:
LIVE_PASS_SELECTIVE_SUBSET

Baseline Cash-Flow Consistency:
CLOSED

KR OpenDART Period Recovery:
MEDIUM_FOLLOWUP

CCC:
DEFERRED

ROIC:
DEFERRED
```

Natural AI-Assisted Delivery keeps its independent actual state.

---

# 144. Next-roadmap decision

Do not block all further architecture work solely because user-visible natural proof is pending.

Completion report must state:

`NEXT_MAJOR_ARCHITECTURE_READY = YES/NO`

YES if:

- P0 = 0
- material P1 = 0
- 9.0E implementation and enablement safe
- only natural user-visible observation remains

Broader cash-flow user-visible expansion still waits for natural proof.

---

# 145. Next candidate after 9.0E

Do not implement it here.

Based on existing evidence, likely candidates are:

A. `OpenDART Cash-Flow Period Context Recovery`
B. `Working Capital Canonical Core`
C. targeted 9.0E repair if natural rollout fails

Final recommendation should use actual completion evidence.

---

# 146. Final philosophy

Phase 9.0E is the first point where canonical cash-flow evidence intentionally enters the user’s production monitoring message.

That makes this phase qualitatively different from 9.0A–9.0D.

The correct design is not:

```text
FCF exists
→ show FCF everywhere
```

It is:

```text
Canonical FCF
        ↓
Current formal?
        ↓
PIT safe?
        ↓
Fresh?
        ↓
Full FCF?
        ↓
Industry relevant?
        ↓
Decision material?
        ↓
Baseline consistent?
        ↓
One useful user-visible insight
```

The user should not receive more accounting data merely because the backend learned how to calculate it.

The user should receive a better investment interpretation.

Therefore:

- selected cash-flow must resolve a real analytical gap
- exact numbers must remain provenance-bound
- period and PPE scope must be clear
- AI and fallback must share the same facts
- unsupported historical prose must be replaced/suppressed, not appended beside the new truth
- ineligible/stale/KR/OCF-only cases remain fail-closed in the initial rollout
- FCF sign is context, not a verdict
- cash flow is earnings-quality evidence, not a new automatic valuation metric
- one optional feature failure must not compromise delivery
- a kill switch must return the system to safe no-enrichment mode without disabling canonical data or the canary

The initial rollout must be narrow enough that every visible cash-flow statement is explainable.

If the system cannot answer:

```text
Why this ticker?
Why this period?
Why this FCF definition?
Why today’s message?
Which canonical Fact?
What old Unknown did it resolve?
```

then the cash-flow statement should not be shown.

Success is not:

> "We added FCF to production."

Success is:

> "For the small set of companies where current-formal FCF materially improves the analysis, both AI and fallback now show the same safe evidence, with a tested kill switch and zero leakage elsewhere."
