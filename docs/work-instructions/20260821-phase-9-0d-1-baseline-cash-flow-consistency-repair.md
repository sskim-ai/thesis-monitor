# thesis-monitor — Phase 9.0D.1 Work Instruction

## Metadata

- Phase: `9.0D.1`
- Title: `Baseline Cash-Flow Sign / Period / Scope Consistency Repair`
- Instruction version: `1.0`
- Date: `2026-08-21 KST`
- Repository: `sskim-ai/thesis-monitor`
- Intended base/main/operating at instruction creation: `3d6cfab1d881c336ff64c66466d12068aa51d1e4`
- Natural evidence source: `2026-08-21-us-run-30-5a3b7c1c4390`
- Natural canary: `cf-canary-f5ce3f836df99c546cf6f696`
- Natural canary status: `COMPLETE_PASS`
- Current phase gate: `PHASE_9_0E_READY = NO`
- Blocking issue: one open material baseline/canonical cash-flow consistency issue on TSLA
- Production Assist: `OFF`
- Cash-flow user-visible integration: `OFF`
- Objective: close the single bounded sign/period/scope consistency gap and re-decide `PHASE_9_0E_READY` without requiring another arbitrary natural run.

---

# 0. Work-instruction repository protocol

Store this instruction at:

`docs/work-instructions/20260821-phase-9-0d-1-baseline-cash-flow-consistency-repair.md`

Before implementation:

1. `git fetch origin`
2. Verify current `origin/main`, operating HEAD, and clean working trees.
3. Commit/push this work instruction as a **docs-only instruction commit** before implementation.
4. Record:
   - `instruction_path`
   - `instruction_commit_sha`
   - `instruction_version`
5. Create the implementation branch from the latest safe main descendant containing the instruction commit.
6. If main drift exists, reconcile explicitly; do not blindly reset or rebase history.
7. Do not silently edit this instruction after implementation begins. A material change requires a new committed instruction version.

Recommended branch:

`codex/phase-9-0d-1-baseline-cash-flow-consistency-repair`

Completion report must cite the exact instruction commit SHA.

---

# 1. Source evidence

The 2026-08-21 natural US review established:

## Natural production

- Packet: `2026-08-21-us-run-30-5a3b7c1c4390`
- Production AI candidate: not sent
- Production delivery: deterministic fallback
- Delivery: `14/14`
- Pending: `0`
- Duplicate: `0`
- Exactly-once: PASS

## Natural cash-flow canary

- Canary: `cf-canary-f5ce3f836df99c546cf6f696`
- Status: `COMPLETE_PASS`
- Full FCF: `9`
- OCF-only: `1`
- Formal-lagging-provisional/context-only: `2`
- Blocked: `1`
- Numeric binding: automatic `10`; manual/rejected/unresolved `0`
- PIT errors: `0`
- lineage errors: `0`
- arithmetic errors: `0`
- semantic errors: `0`
- runtime-quality errors: `0`
- production influence: `0`

Therefore **Phase 9.0D runtime shadow plumbing itself is LIVE PASS**.

The only material integration defect found by human cross-artifact review is the following TSLA baseline contradiction.

---

# 2. Exact TSLA conflict

Production fallback currently states, in substance:

> 현재는 매출·인도 회복에도 영업이익률 저하와 FCF 적자로 투자 논리에 초기 균열이 있으며 ... FCF 흑자 전환이 증명되어야 한다.

The natural current-formal canonical cash-flow evidence states:

- Ticker: `TSLA`
- Period: `2026 H1 YTD`
- OCF: `+$8.634B`
- PPE CAPEX: `$8.282B`
- PPE-only derived FCF: `+$352M`
- Canonical FCF Fact ID: `cashflow:68666c261434dab50ab88a8d`
- Current-formal status: valid for the natural canary
- PIT: PASS

The review could not identify another period or a management-defined FCF scope that would support the production fallback's unqualified current-state phrase `FCF 적자`.

The automated Unknown-resolution/cash-flow semantic gate did not catch this cross-artifact contradiction.

Current review classification was:

- P0 open: `0`
- material P1 open: `1`
- `PHASE_9_0E_READY = NO`

This phase must **not assume that the issue is P1**. Root cause determines final severity.

---

# 3. Phase purpose

This is a bounded consistency repair.

The task must answer:

1. Where exactly did the baseline/fallback `FCF 적자` claim originate?
2. What metric semantic did it mean?
3. What period did it refer to?
4. What FCF scope did it refer to?
5. What source/provenance supported it?
6. Was it stale, unsupported, differently scoped, or merely under-qualified?
7. Why did the automated consistency/Unknown-resolution gate fail to detect it?
8. Are there similar qualitative cash-flow claims elsewhere in the current monitored universe?
9. Can the system deterministically prevent a current baseline cash-flow claim from contradicting a comparable current-formal canonical fact?
10. Can this be fixed **without prematurely exposing canonical OCF/CAPEX/FCF numbers to production messages before Phase 9.0E**?

The target architecture is:

```text
Baseline qualitative cash-flow claim
        ↓
Claim semantic / sign / period / scope / provenance
        ↓
Canonical current-formal cash-flow context
        ↓
Comparability check
        ↓
CONSISTENT
QUALIFIER_REQUIRED
STALE_CONFLICT
UNSUPPORTED_CLAIM
NOT_COMPARABLE
NO_CANONICAL_CHECK_AVAILABLE
        ↓
Render / suppress / relabel
        ↓
Cross-artifact validator
```

---

# 4. Critical scope boundary

This phase **may repair incorrect or unsupported production baseline prose**.

It must **not** yet perform Phase 9.0E user-visible cash-flow integration.

That means:

Allowed:

- suppress a stale/unsupported `FCF 적자` clause
- add a period/scope qualifier to a legitimately supported historical/different-scope claim
- prevent contradictory baseline cash-flow state claims from rendering
- add cross-artifact validation
- preserve an accurate non-cash-flow investment-logic statement after removing a bad cash-flow clause

Not allowed:

- add `+$352M` to the actual production message merely because canonical FCF exists
- add OCF/CAPEX/FCF tables to Telegram
- turn the canary sidecar into production context
- broadly rewrite user-visible messages with Phase 9.0E features

The repair should make current production **less wrong**, not prematurely richer.

---

# 5. Hard prohibitions

Do not:

- hard-code TSLA
- hard-code `$352M`
- hard-code 2026 H1
- replace `FCF 적자` with `FCF 흑자` without provenance analysis
- assume generic `FCF` means PPE-only backend FCF
- assume generic `FCF` means management-defined FCF
- compare unlike period/scope as if conflicting
- overwrite stored thesis history
- rewrite prior assessment history
- mutate DB manually
- manually execute Scheduled Tasks
- manually send Telegram
- mutate Pilot
- enable Production Assist
- modify KRX telemetry
- implement KR OpenDART period recovery
- implement CCC/ROIC
- implement FCF Yield / FCF per share / EV-FCF / P-FCF
- change Public Action `0.4.5`
- change schema `4`
- loosen semantic/runtime quality thresholds
- disable the 9.0D runtime shadow canary
- count a manual replay as new natural proof
- require another arbitrary natural run solely because this retrospective repair changed prose

---

# 6. Read before coding

Read:

## Natural review evidence
- `20260821-phase9-0d-natural-us-canary-review.md`
- `20260821-phase9-0d-natural-us-canary-review.json`
- artifact index if present
- exact run-30 production fallback artifact
- exact canary sidecar / bound output / validation / receipt
- production delivery result and receipt

## Cash-flow architecture
- `CASH_FLOW_CAPITAL_EFFICIENCY.md`
- Phase 9.0B canonical implementation docs
- Phase 9.0C shadow-consumption docs
- `CASH_FLOW_RUNTIME_SHADOW_CANARY.md`

## Existing financial safety
- financial-lineage-v2
- financial-quality-taint-v2
- security-identity-v2
- numeric-fact-ref
- earnings-quality reasoning contracts
- runtime-reasoning-ownership
- final-language gate
- runtime message-quality gate

## Persistent state
- `docs/MASTER_WORKFLOW.md`
- `docs/project-state.json`
- `docs/PROJECT_HANDOFF.md`
- `docs/NEXT_SESSION_PROMPT.md`
- `docs/BRANCH_DEPENDENCY.md`

Repository artifacts are source of truth.

---

# 7. Trace the TSLA baseline claim exactly

Identify the exact origin of both semantic claims:

1. `FCF 적자`
2. `FCF 흑자 전환이 증명되어야 한다`

Trace through:

```text
stored monitored investment logic?
stored assessment?
legacy initial thesis prose?
fallback template?
current review candidate?
renderer?
prompt-generated prose?
other?
```

Record:

- source file/table/field
- origin object/record
- version/date
- section
- text_ref
- generator/template path
- source evidence refs, if any
- whether it is persisted or synthesized at runtime

No guessing.

---

# 8. Determine claim semantics

For each qualitative baseline cash-flow claim, derive or recover structured semantics.

Minimum dimensions:

- `metric_semantic`
  - OCF
  - PPE-only backend FCF
  - management/company-defined FCF
  - generic/unknown FCF
  - cash burn
  - cash conversion
  - CAPEX burden
  - other

- `polarity/state`
  - positive
  - negative
  - deficit/loss-like
  - improvement
  - deterioration
  - turn-positive required
  - unavailable
  - unknown

- `period`
- `period_type`
  - QTD / YTD / FY / TTM / other / unknown

- `scope`
  - backend PPE-only
  - management-defined
  - unknown

- `entity_scope`
- `currency`
- `source availability / filing date`
- `claim currentness`
  - explicit current
  - implied current
  - historical qualified
  - future condition
  - unknown

- `provenance refs`

Use existing repository vocabulary where available.

Do not invent precise metadata from prose when it is not provable; mark Unknown.

---

# 9. Implied current-state claims matter

The gate must not only catch literal phrases like:

`FCF 적자`

It must also catch phrases that logically imply a current state, such as:

`FCF 흑자 전환이 필요하다`

when used without a valid historical/future qualifier.

The repair should distinguish:

- an explicit current negative-FCF assertion
- a historically negative FCF statement with period qualifier
- a future target derived from a valid prior period
- generic "FCF improvement needs confirmation" wording that does not assert current sign

Do not use broad sentiment NLP. Prefer structured origin metadata and narrow deterministic semantics.

---

# 10. Preferred architecture — structured claim metadata

Preferred solution:

Attach structured financial-state metadata **before final prose** where possible.

Conceptual contract:

`baseline-cash-flow-claim-consistency-v1`

Possible fields:

```text
claim_id
ticker
text_ref
section
owner
origin_type
origin_version

metric_semantic
state_or_sign
period_start
period_end
period_type
scope

claim_currentness

source_fact_ids
source_event_ids
source_document_refs
source_available_at

canonical_comparison_fact_id
comparability
consistency_result

render_action
suppression_reason
required_qualifier
```

Actual naming follows repository conventions.

Do not create a parallel financial truth store.

---

# 11. Legacy prose handling

If some existing baseline claims only exist as legacy prose:

- inventory them deterministically
- use narrow, explicit cash-flow phrase recognition only as a compatibility layer
- do not build a broad free-form financial NLP engine
- do not silently assign period/scope where none exists

Legacy unqualified current-state claims without supporting provenance should fail closed.

---

# 12. Canonical comparison rules

Only compare baseline claim vs canonical cash-flow Fact when economically comparable.

Required dimensions:

- same issuer
- compatible metric semantic
- compatible scope
- compatible period meaning
- currentness
- entity scope
- source availability
- freshness/current-formal status

A numeric/sign difference across different scopes is **not automatically a conflict**.

Examples:

- management-defined FCF vs backend PPE-only FCF → `NOT_COMPARABLE` unless definitions are proven compatible
- FY historical FCF vs current H1 YTD FCF → not the same current-state claim
- prior-quarter negative FCF vs current H1 positive FCF → valid history only if period qualifier is explicit
- unqualified "current FCF deficit" vs current-formal comparable positive FCF → conflict

---

# 13. Consistency result states

Use existing vocabulary or equivalents for:

- `CONSISTENT`
- `QUALIFIER_REQUIRED`
- `STALE_CONFLICT`
- `UNSUPPORTED_CLAIM`
- `NOT_COMPARABLE`
- `NO_CANONICAL_CHECK_AVAILABLE`

Do not reduce every mismatch to generic conflict.

---

# 14. Render actions

For each result:

## CONSISTENT
Keep claim.

## QUALIFIER_REQUIRED
Keep only if the valid period/scope qualifier can be deterministically added from provenance.

Do not fabricate qualifier.

## STALE_CONFLICT
Suppress/update the stale qualitative baseline clause.

Do not expose the new canonical number in this phase.

## UNSUPPORTED_CLAIM
Suppress the unsupported current-state cash-flow assertion.

Preserve the rest of the investment logic if independently supported.

## NOT_COMPARABLE
Do not claim conflict.
If the baseline claim lacks its own scope qualifier, require qualifier or suppress.

## NO_CANONICAL_CHECK_AVAILABLE
Preserve only if the baseline claim itself has valid provenance.
Otherwise fail closed.

---

# 15. TSLA required root-cause branches

The task must classify TSLA into exactly one evidence-supported branch or an equivalent precise result.

## Branch A — valid different period/scope exists
Example:
a documented prior period or management-defined FCF is genuinely negative.

Then:
- severity usually P1
- retain historical/different-scope fact only with explicit qualifier
- remove implied current negative-FCF wording
- no direct contradiction with current-formal PPE-only FCF

## Branch B — stale same-semantic claim
The `FCF 적자` claim once had support but is no longer current.

Then:
- classify severity using Phase Advancement Rule
- because user-visible current financial condition is stale, consider P0 if it materially misstates the current comparable metric
- suppress/update stale current-state wording

## Branch C — provenance unsupported
No source supports the current `FCF 적자` state.

Then:
- classify as P0 candidate
- suppress unsupported current financial-state claim
- document why it was previously allowed

## Branch D — another actual root cause
Document exact evidence and classify severity.

Do not force a P1 conclusion because the prior review labeled it P1.

---

# 16. Severity classification rule

Final classification must follow evidence.

## P0
Use P0 when the production user-visible message contains a current financial-state claim that is:

- unsupported by provenance, or
- directly wrong versus a comparable validated current-formal canonical Fact, or
- stale but presented as current in a way that materially changes financial-condition interpretation.

## P1
Use P1 when:

- the underlying fact is valid but period/scope/currentness qualifiers are missing or ambiguous,
- the cross-artifact consistency gate is structurally incomplete,
- analysis integrity is affected without a fabricated/incorrect comparable current number.

## P2
Only for non-material wording/presentation after correctness is closed.

Completion report must explain final severity.

---

# 17. Cross-universe baseline claim inventory

Do not stop at TSLA.

Scan the current monitored universe and recent production fallback/current-baseline prose for qualitative cash-flow claims, including explicit or implied:

- FCF positive / negative
- FCF deficit
- FCF turn-positive requirement
- FCF improvement / deterioration
- OCF positive / negative
- cash burn
- cash conversion improvement / weakness
- CAPEX pressure / burden where cash-flow semantics are implied
- "현금흐름이 없다/확인되지 않는다"

Produce a claim inventory.

This is a safety audit, not a broad rewrite.

---

# 18. Claim inventory required fields

For every detected current/recent claim:

- ticker
- section
- exact short claim span
- origin
- metric semantic
- sign/state
- period qualifier
- scope qualifier
- provenance available YES/NO
- comparable canonical Fact available YES/NO
- consistency result
- render action
- severity if problematic

Avoid quoting long copyrighted/source text; repository-generated message snippets can be included as needed for internal audit.

---

# 19. Required negative controls

At minimum test naturally relevant classes from run-30:

## Negative FCF
Examples such as CORZ / RXRX / WULF where canonical PPE-only FCF is negative.

Ensure valid negative-FCF reasoning is not suppressed simply because TSLA is positive.

## Positive FCF
TSLA and other positive current-formal cases.

Ensure current negative baseline claims cannot survive without comparable support.

## OCF-only
HUT-like case.

Do not manufacture FCF consistency state.

## Freshness context-only
TSM / WRD-like behavior.

Do not use older canonical cash-flow to rewrite current baseline as if current.

## Blocked
SKHY-like case.

No canonical current claim may be invented.

## Financial/N/A
If a relevant insurance/general-FCF N/A case is audited, generic FCF assertions should remain suppressed/not applicable.

---

# 20. Unknown-resolution gate extension

The previous gate checked:

- "Fact exists but message says unavailable"

It must now also check qualitative state consistency.

Extend it conceptually to:

```text
Availability consistency
+
Sign/state consistency
+
Period consistency
+
Scope consistency
+
Currentness consistency
```

A fresh canonical Fact and a baseline current claim must not disagree on a comparable state.

---

# 21. Cross-artifact consistency gate

The gate must compare:

- production baseline/fallback qualitative cash-flow claims
- canonical cash-flow context eligible at the same packet cutoff
- shadow canary interpretation

It should catch a contradiction even if:

- the shadow canary itself is internally valid
- production baseline itself contains no exact cash-flow number
- the conflicting claim is qualitative (`적자`, `흑자 전환 필요`)

This is the exact blind spot exposed by run-30.

---

# 22. No premature canonical number injection

Important:

The consistency gate may use canonical current-formal cash-flow Facts to validate/suppress baseline prose.

But production output in Phase 9.0D.1 must not automatically add:

- OCF amount
- PPE CAPEX amount
- FCF amount

Those remain Phase 9.0E consumption.

For TSLA, a valid repair may simply remove or qualify the stale/unsupported FCF clause while keeping independently supported margin/Robotaxi/other investment-logic content.

---

# 23. Investment-logic history preservation

Do not rewrite historical stored thesis versions.

If the source of the problematic claim is a stored thesis/history object:

- preserve stored history
- fix current user-visible interpretation/rendering or claim metadata
- optionally record that the historical claim is stale/resolved
- do not erase provenance/history

Monitoring history remains immutable.

---

# 24. No automatic thesis-state mutation

Even if current canonical FCF is positive:

- do not auto-strengthen TSLA
- do not auto-close warnings
- do not auto-change valuation
- do not persist assessment delta

This phase repairs consistency, not investment-state logic.

---

# 25. Run-30 immutable replay

Use the exact immutable run:

`2026-08-21-us-run-30-5a3b7c1c4390`

Do not rewrite original artifacts.

Generate a repaired preview separately.

Required:

- original production baseline claim inventory
- canonical cash-flow comparison context
- consistency results
- repaired fallback/current-baseline preview
- canary shadow preview
- final cross-artifact consistency result

---

# 26. TSLA replay acceptance

After repair:

- unqualified current `FCF 적자` conflicting with comparable positive current-formal Fact: `0`
- unqualified `FCF 흑자 전환 필요` implying unsupported current negative FCF: `0`
- canonical `+$352M` added to actual production preview merely to fix the bug: `0` unless the preview is explicitly 9.0E-only and non-production; default should be no production injection
- margin/Robotaxi/other independently supported reasoning preserved
- cross-artifact consistency gate: PASS

---

# 27. Cross-universe replay acceptance

For all detected baseline cash-flow claims:

- unsupported current-state claims: `0`
- stale-as-current qualitative cash-flow claims: `0`
- false conflicts across different scope/period: `0`
- valid negative-FCF claims incorrectly suppressed: `0`
- OCF-only incorrectly treated as FCF: `0`
- blocked/stale canonical facts used as current: `0`

---

# 28. Canary regression

The deployed 9.0D canary remains enabled.

Regression must preserve:

- `COMPLETE_PASS` semantics
- production influence `0`
- PIT
- freshness
- full FCF
- OCF-only
- numeric provenance
- quality
- idempotency

Do not change canary scheduling or production isolation unless the consistency gate needs a read-only comparison hook.

If a hook is required, it must not alter canary/production isolation.

---

# 29. Production fallback regression

The repair may touch baseline/fallback rendering.

Therefore explicitly test:

- fallback still sends exactly once
- no message count change unless a message would otherwise become empty
- no empty core section
- no accidental deletion of unrelated investment logic
- no duplicate fallback
- no receipt change
- no deadline/fallback-eligibility change

The consistency repair must not delay delivery.

---

# 30. AI production candidate regression

If the same baseline prose source is also used by AI candidates:

- apply the consistency rule at a shared safe layer if appropriate
- do not fix fallback while leaving AI current-state baseline contradictory
- preserve current numeric/semantic/quality gates

No prompt-only TSLA patch.

---

# 31. Current-cash-flow claim validator tests

Required test fixtures:

1. current comparable FCF positive + baseline says current FCF negative
   - reject/suppress

2. current comparable FCF negative + baseline says current FCF negative
   - allow

3. prior-period negative FCF + current positive FCF + explicit historical period
   - allow as history

4. prior-period negative FCF + current positive FCF + no period qualifier
   - qualifier required or suppress

5. management-defined negative FCF + PPE-only positive FCF with proven definitions
   - not directly comparable; require scope qualifier

6. generic unknown-scope FCF negative with no provenance
   - suppress

7. OCF negative but FCF unavailable
   - do not translate to FCF negative

8. stale old positive/negative FCF while newer formal period is blocked
   - not current substitute

9. current canonical FCF missing
   - only provenance-backed baseline claim may survive

10. implied state phrase such as `FCF 흑자 전환 필요`
    - detect current-negative implication when unqualified

---

# 32. Cash-flow label/scope tests

Verify:

- backend FCF remains `OCF - PPE CAPEX`
- management FCF remains separately scoped
- generic "FCF" with unknown scope is not silently mapped
- no FCF yield/share/EV-FCF introduced
- currency and entity basis remain intact

---

# 33. Prior repair regression

Preserve:

- Phase 8.5.5 reasoning ownership
- Phase 8.5.5.1 numeric-summary / typed repetition
- Phase 8.5.5.2 structured-field repetition
- run-27
- run-28
- run-29
- RXRX/WULF PBR ownership
- CORZ typed valuation
- dynamic price context
- RR overlap guard
- confirmation lifecycle
- night-futures session/calendar
- fallback parity
- exactly-once / receipt
- KRX telemetry
- Phase 9.0B canonical core
- Phase 9.0C shadow consumption
- Phase 9.0D natural canary isolation

---

# 34. Full validation

Required:

- focused 9.0D.1 consistency tests: PASS
- run-30 immutable replay: PASS
- cross-universe baseline claim audit: PASS
- 9.0D canary regression: PASS
- fallback isolation/exactly-once: PASS
- full pytest: PASS
- operating smoke: PASS
- Ruff: PASS
- `git diff --check`: PASS
- Investment Knowledge parity: PASS
- Chart Knowledge parity: PASS
- Public Action: `0.4.5`
- operationId: `20/20 unique`
- schema: `4`
- exact implementation SHA GitHub Actions Test/Lint: PASS
- exact final SHA GitHub Actions Test/Lint: PASS

---

# 35. Runtime/user-visible boundary

Unlike 9.0A–9.0D, this repair may produce a **small user-visible baseline wording correction** if the production baseline is proven stale/unsupported.

Report exact user-visible diff.

Allowed:

- removal/qualification of incorrect cash-flow qualitative prose

Not allowed:

- broad new cash-flow numbers
- new cash-flow sections
- 9.0E rollout
- new user-visible OCF/CAPEX/FCF table

If user-visible diff is zero because the conflict is fixed upstream only for future integration, explain why current production is still safe. If current fallback remains wrong, the phase cannot PASS.

---

# 36. P0/P1 closure

After implementation, explicitly report:

- root-cause severity before repair
- final open P0 count
- final open P1 count

Acceptance target:

```text
Open P0 = 0
Open material P1 = 0
```

P2 may remain.

---

# 37. PHASE_9_0E_READY re-decision

This phase must explicitly set:

`PHASE_9_0E_READY = YES` or `NO`

## YES conditions

- run-30 natural canary evidence remains valid
- full-FCF natural path already OBSERVED_PASS
- production isolation remains PASS
- TSLA baseline/canonical consistency defect closed
- cross-universe current cash-flow claim audit PASS
- P0 open = 0
- material P1 open = 0
- numeric/PIT/freshness/semantic/quality regression PASS
- no canary Telegram exposure
- 9.0E selective subset remains identifiable

**Do not require another natural run solely because 9.0D.1 was a bounded consistency repair.**

The valid run-30 natural canary proof is not erased by this retrospective consistency repair.

## NO conditions

Only for concrete remaining P0/material P1.

If NO, provide exact bounded blocker.

P2 cannot produce NO.

---

# 38. Recommended 9.0E scope if READY

Do not implement 9.0E here.

Recommend:

`Phase 9.0E — Selective Cash-Flow User-Visible Integration`

Initial rollout should remain narrow.

Preferred constraints:

- current-formal full-FCF consumption only
- material-improvement / decision-relevant subset
- production baseline cash-flow consistency gate enabled
- exact numeric ownership in business/earnings-quality section
- replace/suppress resolved contradictory baseline prose instead of append-only duplication
- KR excluded initially
- formal-lagging-provisional current numeric display excluded
- OCF-only rollout separately gated if desired
- no broad all-ticker cash-flow dump

Eligibility remains dynamic, not ticker hard-coded.

---

# 39. KRX read-only status

Do not modify KRX.

You may include current known natural evidence in completion report:

- 2026-08-20 16:05: provider pending / 0 rows
- 2026-08-21 08:05: provider complete
  - KOSPI stocks 942
  - KOSDAQ stocks 1,821
  - KOSPI indices 51
  - KOSDAQ indices 40

Actual artifacts are authoritative.

KRX status does not block 9.0E.

No new provider calls.

---

# 40. Natural AI-assisted track

Keep independent.

Run-30 production used deterministic fallback because the production AI path had unrelated late/semantic issues.

Do not require overall Natural AI-Assisted Delivery PASS for 9.0E.

If this task discovers a production P0 unrelated to cash-flow consistency, classify separately under Phase Advancement Rule.

---

# 41. Reports

Create:

`docs/architecture/CASH_FLOW_BASELINE_CONSISTENCY.md`

Create reports:

1. `docs/reports/20260821-phase9-0d-1-tsla-cash-flow-root-cause.md`
2. `docs/reports/20260821-phase9-0d-1-baseline-cash-flow-claim-inventory.md`
3. `docs/reports/20260821-phase9-0d-1-run30-repaired-preview.md`
4. `docs/reports/20260821-phase9-0d-1-cross-artifact-consistency-audit.md`
5. `docs/reports/20260821-phase9-0d-1-validation.md`
6. `docs/reports/20260821-phase9-0e-readiness.md`

Recommended JSON:

- `docs/reports/20260821-phase9-0d-1-baseline-cash-flow-claim-inventory.json`
- `docs/reports/20260821-phase9-0e-readiness.json`

---

# 42. Result delivery

Preferred:

Commit/push sanitized reports to the implementation branch.

Completion report must provide GitHub URLs.

If one ZIP is easier, additionally or alternatively create:

`20260821-phase9-0d-1-complete-report-bundle.zip`

Include the reports/JSON, not raw secret-bearing runtime data.

Report ZIP SHA-256.

---

# 43. Operating promotion

Promotion is allowed only after all acceptance criteria pass.

Before promotion:

```bash
git fetch origin
```

Check main drift.

If clean linear descendant:
- fast-forward promotion

If drift:
- explicit integration
- no blind overwrite
- no force push

After promotion:

- main SHA
- operating SHA
- working trees clean
- API restart only if required
- health PASS
- AI task schedules unchanged
- KRX telemetry unchanged
- Production Assist OFF

---

# 44. Scheduled-task safety

Existing tasks remain unchanged:

- US primary 08:15
- US backup 08:30
- KR primary 16:15
- KR backup 16:55

Manual execution:

`0`

KRX:

- 08:05
- 16:05

unchanged.

---

# 45. Persistent-state update

On PASS:

```text
Phase 9.0D:
LIVE_PASS_SELECTIVE_SUBSET

Phase 9.0D.1:
BASELINE_CASH_FLOW_CONSISTENCY_CLOSED

Cash Flow Runtime Shadow:
LIVE_PASS_SELECTIVE_SUBSET

Cash Flow User Visible:
NOT_ENABLED

KR OpenDART Period Recovery:
MEDIUM_FOLLOWUP

CCC:
DEFERRED

ROIC:
DEFERRED
```

Then:

`PHASE_9_0E_READY = YES`

if gate conditions are met.

Natural AI-Assisted Delivery keeps its independent actual state.

---

# 46. MASTER_WORKFLOW update

Record:

- 9.0D natural canary LIVE PASS
- run-30 production isolation PASS
- full FCF / OCF-only / freshness behavior observed
- baseline/canonical TSLA contradiction
- 9.0D.1 root cause and closure
- final severity
- Phase 9.0E readiness
- no second natural-run requirement for this bounded repair

---

# 47. Completion report format

## Work instruction
- path
- instruction commit SHA
- version
- deviations YES/NO

## Repository
- branch
- base
- implementation
- final
- main
- operating
- push
- working trees

## TSLA root cause
- exact origin
- source field/version
- metric semantic
- sign
- period
- scope
- provenance
- final classification A/B/C/D
- severity P0/P1/P2

## Before / after
- original TSLA baseline wording
- repaired wording
- what was suppressed/qualified
- whether any canonical number became user-visible

## Cross-universe claim inventory
- total claims
- consistent
- qualifier required
- stale conflict
- unsupported
- not comparable
- no canonical comparison

## Validator
- availability contradictions
- sign contradictions
- period contradictions
- scope contradictions
- currentness contradictions

## Run-30 replay
- production baseline
- repaired baseline
- natural canary
- cross-artifact result

## Regression
- negative-FCF controls
- OCF-only
- stale/context-only
- blocked
- prior Phase 8.5/9.0 repairs

## Validation
- focused
- replay
- full pytest
- smoke
- Ruff
- diff
- Knowledge
- Action
- operationId
- Actions

## Operating safety
- user-visible diff
- Telegram
- task
- Pilot
- DB
- archive/receipt
- Production Assist

## P0/P1/P2
- root-cause severity
- open P0
- open P1
- P2 backlog

## Final gate
- `PHASE_9_0E_READY = YES/NO`
- exact reason
- recommended 9.0E scope if YES
- bounded blocker if NO

## Result files
- Git URLs
- optional ZIP
- ZIP SHA-256

---

# 48. Final philosophy

The defect exposed by run-30 is not that the canonical FCF engine is wrong.

The canonical engine and natural canary passed.

The defect is that an older qualitative baseline can continue to say:

```text
FCF 적자
```

while a comparable current-formal canonical cash-flow fact says otherwise.

This creates a new requirement:

```text
Canonical numeric correctness
        is not enough.

Current qualitative baseline
        must also be consistent
        with canonical current-formal evidence.
```

But consistency does not mean blindly replacing old prose with the newest number.

First determine:

```text
What metric?
What sign?
What period?
What scope?
What source?
What currentness?
```

Then compare only like with like.

If an older negative FCF is valid history, preserve it as history.

If a management-defined FCF is genuinely different from PPE-only backend FCF, label the scope.

If a current claim is stale, suppress the stale current wording.

If a claim has no provenance, do not let it remain a current financial-state assertion.

And most importantly:

**do not expose the new canonical FCF number to production merely to fix this bug.**

Phase 9.0D.1 closes the baseline-consistency gate.

Phase 9.0E is where selective canonical cash-flow evidence becomes intentionally user-visible.

The valid run-30 natural canary already proved runtime isolation, full-FCF consumption, OCF-only behavior, freshness suppression, provenance, semantics, and quality.

Therefore, once this single bounded P0/P1 consistency defect is closed retrospectively with zero regression:

**do not wait for another arbitrary natural run.**

Re-decide `PHASE_9_0E_READY` immediately from the accumulated evidence.
