# Thesis Monitor — First-Class Typed Financial Evidence Index Implementation & Full Fictional Canary

## 0. Task identity

Suggested work-instruction filename:

```text
20260909-first-class-typed-financial-evidence-index-implementation-and-full-fictional-canary.md
```

Suggested result bundle:

```text
thesis-monitor-20260909-first-class-typed-financial-evidence-index-implementation-full-fictional-canary-report.zip
```

Master-workflow phase:

```text
M12B — First-Class Typed Financial Evidence Index Implementation
        + Full Fictional Financial Canary
```

This task begins only after M12A has completed and frozen:

```text
preferred_grounding_architecture =
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

next_scope =
FIRST_CLASS_TYPED_FINANCIAL_EVIDENCE_INDEX_IMPLEMENTATION
```

M12B implements that frozen architecture and then reruns the full fictional financial-context canary.

M12B must NOT:

```text
change BUY/HOLD/SELL thresholds
change 0.5 balance increments
change HOLD lean
change calibration tie-break
change source mappings
change financial-context selector
change QTD/YTD validator semantics
weaken financial semantic validators
add an output grounding field
add a narrative-lineage bridge
change Price-Timing ownership
change renderer substantive ownership
change source sufficiency
run a fresh real issuer proof
merge/deploy production
resume monitoring schedules
```

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260909-financial-context-output-grounding-architecture-review-report.zip
```

Verified SHA-256:

```text
cef338a297c6a04908d0255f845b3526f78eabb9aa8d8f5d6c12fdcb97e9b227
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest M12A state:

```text
M12G =
BLOCKED_PROMPT_GROUNDING_INSUFFICIENT

M12A =
COMPLETE

preferred grounding architecture =
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

fresh real proof readiness =
NOT_READY

production readiness =
NOT_READY
```

Reported M12A provenance:

```text
base_sha =
6024a1ef226ec176199de48a573ccf1bc541d4c9

work_instruction_commit =
938569446f309376c3519dd63fd33d505c790e57

implementation_commit =
20e5fec5bf0b243e6205c48aa4f875c37b203164

branch =
codex/20260909-financial-context-output-grounding-architecture-review
```

M12A used the established pre-report-commit convention:

```text
report_commit = NOT_MEASURED
final_head_sha = NOT_MEASURED
```

At task start, use actual repository HEAD as authority and record actual M12A final/report state.

M12A artifact integrity:

```text
ZIP SHA-256 = verified
artifact payload index = PASS
```

Recompute the artifact index before trusting the bundle.

---

# 2. M12A architecture finding is frozen

M12A found:

```text
one alias namespace per ticker = true
one catalog per ticker = true

selected typed aliases = 15
selected typed aliases already present in catalog = 15
selected typed aliases present in ordinary evidence[] = 0
```

Current finding:

```text
ALIAS_NAMESPACE_IS_UNIFIED_MODEL_INPUT_EVIDENCE_SURFACE_IS_SPLIT
```

Therefore M12B must NOT create a second alias namespace.

The existing aliases are already usable by:

```text
Directional output evidence_refs
alias resolver
canonical reference validator
```

The missing piece is only:

```text
selected typed financial items
→ ordinary first-class evidence[] projection
```

---

# 3. M12A duplicate-evidence finding is frozen

Across the 8 fictional cases:

```text
selected typed financial refs = 15

NARRATIVE_SUMMARY_DUPLICATE_WITHOUT_LINEAGE = 8

NO_NARRATIVE_DUPLICATE = 4

NARRATIVE_INTERPRETATION_NOT_DUPLICATE = 3

valid financial lineage bridge count = 0
```

Therefore M12B must NOT treat a narrative duplicate as equivalent to typed grounding.

Do not create lineage from text similarity.

Do not delete narrative evidence merely because a typed fact exists.

The frozen principle is:

```text
typed financial fact owns:
what the financial fact is

narrative evidence owns:
why it matters
remaining Unknowns
sector interpretation
business implications
```

---

# 4. Frozen selected architecture

M12A selected:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION
```

Rejected:

```text
PROVENANCE_LINEAGE_BRIDGE
because current producer lineage coverage = 0

STRUCTURED_OUTPUT_FINANCIAL_GROUNDING
because existing evidence_refs/resolver already support the typed aliases
and output-schema cost is unnecessary

HYBRID
because no distinct second problem is proven

NO_CHANGE_PROMPT_ONLY
because M12G already demonstrated repeated prompt-only failure
```

M12B must implement only the selected architecture.

---

# 5. Frozen implementation contract

M12A froze:

```text
evidence_index_behavior =
add selected typed financial items once to ordinary evidence[]
in catalog order

alias_behavior =
reuse existing aliases without renumbering

human_statement_behavior =
deterministic neutral metric/period/comparison statement
no investment verdict

lineage_behavior =
retain existing canonical/source/comparison/derivation lineage

output_schema_impact =
NONE

renderer_impact =
NONE

source_sufficiency_impact =
NONE

migration_artifact_compatibility =
NO_MIGRATION

validator_behavior =
unchanged semantics
direct typed refs remain required
```

Implement exactly this contract unless current repository drift proves it impossible.

---

# 6. User-approved operating constraints

## 6.1 Provider policy

No provider calls.

Required:

```text
provider_source_fetches = 0
```

## 6.2 Existing monitoring remains paused

Observe the same approved 8 monitoring schedule paths at start/end.

Do not automatically resume them.

If one exact approved path unexpectedly becomes active:

```text
pause only that exact path
record mutation
```

## 6.3 Production side effects remain zero

Required:

```text
production DB mutations = 0
monitoring registrations = 0
assessment persistence = 0
warning mutations = 0
notification queue writes = 0
production sends = 0

main merge = 0
deployments = 0
automatic monitoring resume = 0
```

---

# 7. Work-instruction commit first

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Commit this instruction first.

Record:

```text
new_work_instruction_commit
```

Only then implement the first-class evidence projection.

---

# 8. Implementation surface

M12A froze expected modules:

```text
app/services/directional_financial_context_service.py

scripts/directional_core_price_timing_holdout.py

tests/test_directional_financial_context_service.py

tests/test_direction_timing_ownership_service.py

tests/test_directional_financial_context_m12g.py
```

Use the actual current code structure as authority.

Preferred semantic owner:

```text
directional financial-context projection / compact-context builder
```

Do not put first-class projection logic into:

```text
source adapters
renderer
Price-Timing
monitoring lifecycle
```

---

# 9. First-class evidence projection

For every selected:

```text
financial_decision_context.evidence_items[]
```

project exactly one corresponding item into:

```text
DIRECTIONAL_CORE_CONTEXT.evidence[]
```

using its existing alias.

Required:

```text
same alias

same canonical ref

same source ref lineage

same metric identity

same period/comparison semantics

evidence_kind = TYPED_FINANCIAL
```

or the current repository's equivalent field.

Do not generate a new alias.

Do not renumber existing aliases.

Do not create an extra synthetic canonical ref.

---

# 10. Selected-only rule

Only selected financial-decision-context items may be promoted.

Forbidden:

```text
all raw financial_context facts

all accounting facts in packet

all suppressed financial_decision_context items
```

Required:

```text
selected typed financial count
=
first-class typed financial projection count
```

unless a deterministic deduplication rule removes an exact duplicate canonical ref already present as typed first-class evidence.

No raw financial dump.

---

# 11. Catalog order

M12A froze:

```text
add selected typed financial items once to ordinary evidence[]
in catalog order
```

Preserve deterministic ordering.

Do not append in:

```text
hash-map iteration order
selector return randomness
domain bullishness order
```

Required:

```text
same packet
→ same evidence[] order
→ same compact-context hash
```

---

# 12. Human-readable neutral financial statement

Current typed alias-map statements were raw JSON such as:

```text
{"value":"300"}
```

M12B must produce a deterministic neutral statement for the ordinary evidence[] surface.

The statement must express:

```text
what the financial fact is
period / point-in-time context
comparison kind where present
```

without investment interpretation.

Examples of acceptable semantic form:

```text
"Inventory balance is reported at the current point-in-time and is higher than the supplied prior year-end comparison."

"Trade receivables are reported at the current point-in-time with a prior year-end comparison."

"Operating cash flow is reported for the supplied YTD period."

"Complete interest-bearing debt and cash support a derived net-debt fact for the same point-in-time basis."

"Net financial income effect is reported/derived for the supplied period."
```

Exact wording may follow project conventions.

Do NOT emit:

```text
"inventory deterioration"

"weak receivables quality"

"strong cash generation"

"dangerous leverage"

"earnings quality is poor"
```

The evidence statement is factual/provenance-oriented.

Investment interpretation remains model-owned.

---

# 13. Numeric statement policy

Preserve M12/M12G policy:

```text
do not require exact numbers in model prose
```

The first-class evidence statement may include a normalized value only if existing ordinary evidence formatting conventions already support it safely.

Preferred:

```text
human-readable semantic statement
+
structured value/unit/period fields
```

rather than turning the statement into a long accounting dump.

The model should be able to cite the alias without repeating exact values.

---

# 14. First-class evidence fields

A projected typed financial evidence row should expose, according to current ordinary evidence schema:

```text
alias

label

category / domain

statement

value / unit if already supported

as_of

metric_refs if appropriate

evidence_kind = TYPED_FINANCIAL

financial_semantics
```

`financial_semantics` may carry compact non-duplicative metadata such as:

```text
metric
semantic_category
period_type
comparison_kind
evidence_status
quality
```

Do not copy the entire nested FinancialContext into ordinary evidence[].

Detailed typed metadata remains in:

```text
financial_decision_context
```

The first-class evidence projection is the citation/grounding surface.

---

# 15. Alias resolution

Existing alias resolver must continue to map:

```text
E03
→ canonical:...trade-receivables-current
```

etc.

No resolver semantic change should be required.

Required tests:

```text
typed first-class alias resolves to same canonical ref as before

narrative alias resolution unchanged

no duplicate alias IDs
```

If resolver changes are required only for a type tag:

```text
keep change semantic-neutral
```

---

# 16. No output-schema change

M12A froze:

```text
output_schema_change_required = false
```

M12B must preserve current Directional output schema.

Do not add:

```text
material_financial_evidence_refs
financial_grounding_refs
new citation field
```

Existing:

```text
evidence_refs
```

and existing evidence-bearing output fields remain the grounding mechanism.

Required:

```text
output_schema_change_count = 0
```

---

# 17. Narrative evidence remains

Do not delete or suppress narrative evidence solely because it overlaps a typed fact.

FIC-FIN-06 must still contain the narrative rows such as:

```text
inventory and trade receivables have risen since year-end

demand quality / collection timing Unknown

sector context: confirmation point, not automatic negative
```

The model should see:

```text
typed financial fact
+
narrative interpretation
```

on the same first-class evidence surface.

This is intentional.

---

# 18. Evidence double-counting contract

Frozen M12A rule:

```text
one typed canonical_ref
=
one financial anchor
regardless of appearances in evidence[] and financial_decision_context detail metadata
```

The detailed financial_decision_context representation does not count as a second anchor.

Narrative evidence without explicit lineage:

```text
does NOT count as the same typed anchor
```

but the model must be instructed not to count a factual duplicate narrative summary
as a separate independent anchor when it is clearly the same economic fact.

No bullish/bearish weighting.

No score.

---

# 19. Model-facing duplicate control

The prompt may retain the existing M12G grounding instruction.

Add no new broad prompt rewrite.

If a tiny compatibility wording change is required because typed financial facts now appear in ordinary evidence[],
it must only clarify:

```text
TYPED_FINANCIAL evidence rows are first-class evidence aliases.
Use them exactly like other evidence refs when they support a material financial claim.
```

Prefer no prompt change if existing M12G wording already works with the unified surface.

Required artifact:

```text
prompt change justification
```

Expected:

```text
0 or minimal compatibility-only lines
```

Do not re-open the prompt-only repair cycle.

---

# 20. Financial Decision Context remains

Do NOT remove:

```text
financial_decision_context
```

It still provides:

```text
structured detail
comparison lineage
derivation lineage
period metadata
sector routing
limitations
```

M12B changes only the citation/evidence surface.

Required:

```text
financial_decision_context_detail_removed_count = 0
```

---

# 21. Legacy behavior

For a packet with:

```text
financial_context absent
```

M12A froze:

```text
BYTE_EQUIVALENT_PROJECTION_UNCHANGED
```

Required hard gate:

```text
legacy compact Directional context byte-equivalent
```

except for a separately justified static prompt compatibility line if absolutely necessary.

Prefer no legacy context change.

No historical packet migration.

---

# 22. FIC-FIN-07 no-financial-context control

FIC-FIN-07 has no selected typed financial items.

Expected:

```text
ordinary evidence[] unchanged

no fake typed evidence row

no unavailable boilerplate inserted

no bearish penalty

no grounding requirement invented
```

Required:

```text
FIC-FIN-07 first-class typed count = 0
```

---

# 23. FIC-FIN-08 financial-sector control

FIC-FIN-08 is the financial-sector exclusion case.

Expected:

```text
no generic industrial financial typed evidence projected
```

unless the existing sector-valid financial_decision_context selector explicitly selected a safe sector-compatible item.

Do not bypass M12 sector routing just because projection is first-class.

Required:

```text
financial_sector_generic_financial_context_leak_count = 0
```

---

# 24. FIC-FIN-06 focal deterministic proof

Before model calls, build the post-M12B FIC-FIN-06 context.

Required:

```text
E03 trade receivables
appears in ordinary evidence[]

E04 inventory
appears in ordinary evidence[]

existing narrative E01/E06/E07/E08/E09 remain

aliases unchanged

canonical refs unchanged

typed human-readable statements are neutral

financial_decision_context still contains full details

duplicate alias count = 0
```

The context should make E03/E04 as citation-accessible as E01/E07/E08.

---

# 25. Old failed output remains failed

Apply the unchanged financial semantic validator to the old M12G FIC-FIN-06 raw output.

Expected:

```text
FAIL

material_financial_anchor_not_used
working_capital_checkpoint_not_used
narrative_substitution_failure
```

The architecture implementation must NOT retroactively turn the old model output into a pass.

This proves validators were not weakened.

---

# 26. Corrected FIC-FIN-06 fixture remains pass

The deterministic corrected output fixture that cites:

```text
E03 / E04
```

must remain PASS.

This proves new input architecture remains compatible with explicit typed grounding.

---

# 27. FIC-FIN-03 QTD/YTD regression

M12R QTD/YTD validator remains frozen.

Required:

```text
historical FIC-FIN-03 valid raw output = PASS

QTD/YTD positive fixtures = PASS

QTD/YTD negative fixtures = rejected
```

No validator semantic changes.

---

# 28. Typed first-class evidence tests

Add deterministic tests for:

```text
OCF typed evidence promotion

simple cash-conversion typed evidence promotion

debt/liquidity typed evidence promotion

inventory typed evidence promotion

trade receivables typed evidence promotion

non-operating financial effect typed evidence promotion

QTD/YTD operating income typed evidence promotion
```

Each must prove:

```text
same alias
same canonical ref
one ordinary evidence row
neutral statement
no duplicate
```

---

# 29. Suppressed-item negative control

If `financial_decision_context` has:

```text
eligible_input_count > selected_input_count
```

only selected items may enter ordinary evidence[].

Required:

```text
suppressed typed item projection count = 0
```

No hidden raw-data expansion.

---

# 30. Price / technical / supply isolation

The unified evidence surface must not allow:

```text
price
OHLCV
technical indicators
support/resistance
supply/positioning
```

to enter Directional through the financial projection.

Required zero:

```text
typed_financial_price_ref_count
typed_financial_technical_ref_count
typed_financial_supply_ref_count
```

Existing Directional price/supply hard gates remain.

---

# 31. Source sufficiency unchanged

M12B is not a source-gate task.

Required:

```text
source_sufficiency_semantic_change_count = 0
```

Subjects without optional financial context remain eligible under the same existing source-sufficiency rules.

No universal financial-domain requirement.

---

# 32. Daily Delta / monitoring lifecycle unchanged

M3 semantics remain frozen.

First-class financial evidence affects:

```text
current absolute Directional reasoning
```

not:

```text
bootstrap vs Daily Delta
missing refresh
price-only thesis delta
```

Required:

```text
daily_delta_semantic_change_count = 0
monitoring_lifecycle_semantic_change_count = 0
```

---

# 33. Warning semantics unchanged

M12B does not activate warnings.

Required:

```text
warning_semantic_change_count = 0
warning_mutations = 0
```

---

# 34. Renderer ownership unchanged

M12A froze:

```text
renderer_change_required = false
```

M12B must not change renderer substantive analysis.

Required:

```text
renderer_substantive_change_count = 0
```

Primary action wording remains renderer-owned.

AI imperative primary action remains forbidden.

---

# 35. Directional calibration frozen

Required unchanged:

```text
BUY >= 6.0
SELL >= 6.0
otherwise HOLD

0.5 increments

HOLD 5.5:4.5 BUY_LEAN
HOLD 5.0:5.0 NEUTRAL
HOLD 4.5:5.5 SELL_LEAN

adjacent-bucket conservative tie-break toward 5.0
```

Required:

```text
directional_threshold_changed = false
directional_increment_changed = false
hold_lean_contract_changed = false
calibration_tiebreak_changed = false
fixed_financial_score_rule_count = 0
```

---

# 36. Phase A deterministic gate

Before model calls require:

```text
first-class selected-only projection PASS

alias reuse / no renumbering PASS

duplicate alias count = 0

neutral financial evidence statements PASS

financial_decision_context retained PASS

legacy no-financial packet byte-equivalence PASS

FIC-FIN-06 E03/E04 ordinary evidence projection PASS

old FIC-FIN-06 remains FAIL

corrected FIC-FIN-06 remains PASS

FIC-FIN-03 validator regression PASS

suppressed-item negative control PASS

price/technical/supply non-leak PASS

source sufficiency unchanged

Daily Delta unchanged

renderer ownership unchanged

focused pytest PASS

full repository pytest PASS

ruff PASS

git diff --check PASS

production side-effect firewall PASS
```

If any fail:

```text
STOP
NO_MODEL_CALLS
```

---

# 37. Full fictional canary — new generation required

If Phase A passes, create a NEW generation ID.

Use the same frozen 8 cases:

```text
FIC-FIN-01
FIC-FIN-02
FIC-FIN-03
FIC-FIN-04
FIC-FIN-05
FIC-FIN-06
FIC-FIN-07
FIC-FIN-08
```

Do not change case values.

Do not remove narrative duplicates.

Do not reuse M12/M12R/M12G raw outputs in the stability sample.

---

# 38. Full canary topology

Run:

```text
8 subjects
2 shared contexts
4 subjects per context
3 repetitions
```

Total:

```text
6 fictional model calls
24 subject outputs
```

All 6 calls must belong to this new generation.

No selective continuation from prior generations.

---

# 39. Frozen runtime

Use:

```text
model = gpt-5.6-sol
reasoning = xhigh

runtime mode = MODEL_CONTEXT_COUPLED

subjects per context = 4

timeout = 1800 seconds

single authoritative watchdog = true

wrapper auto-retry = 0

batch split = 0
```

Each context requires:

```text
unique invocation ID
unique runtime namespace
unique working directory
unique session identity
```

No namespace reuse.

---

# 40. Whole-generation stop rule

If any hard semantic failure occurs:

```text
stop the generation
preserve emitted outputs
do not selectively continue remaining contexts
```

If runtime fails:

```text
classify runtime separately
do not wrapper-retry
```

Any post-repair full canary must start under a new generation.

Do not stitch samples.

---

# 41. Canary hard semantic gates

Across all completed outputs require zero:

```text
invalid financial evidence refs

material financial claim grounded only in narrative
when relevant selected typed financial evidence exists

working-capital checkpoint ungrounded to typed financial evidence

price / technical / supply Directional refs

partial PPE proxy called FCF

prior-year-end comparison called YoY

partial debt called total debt

total liabilities called debt

normalized / adjusted earnings invented

financial-sector generic industrial financial reasoning

missing optional financial context treated as negative evidence

fixed financial score behavior

AI imperative primary action

QTD/YTD false reject

QTD/YTD false accept
```

---

# 42. Case-specific expectations

Preserve all prior fictional contracts.

## FIC-FIN-01 — strong quality

Expected:

```text
specific positive financial anchor
typed financial ref usage
no FCF invention
```

## FIC-FIN-02 — profit/cash divergence

Expected:

```text
cash-conversion limitation
typed OCF/cash-conversion grounding
no mechanical SELL from one weak cash-flow period
```

## FIC-FIN-03 — QTD/YTD conflict

Expected:

```text
latest-quarter vs cumulative/YTD distinction
both relevant period refs
```

## FIC-FIN-04 — non-operating boost

Expected:

```text
net-income improvement not equated with operating improvement
typed financial-effect grounding
no normalized earnings
```

## FIC-FIN-05 — leverage/liquidity

Expected:

```text
financial resilience limiting anchor
complete debt/cash typed grounding
```

## FIC-FIN-06 — working-capital build

Expected:

```text
working-capital confirmation point
not automatic deterioration
prior-year-end not called YoY

E03 and/or E04 used in a material working-capital claim
according to existing validator contract
```

Narrative evidence may supplement.

Narrative alone must not substitute.

## FIC-FIN-07 — missing optional context

Expected:

```text
no bearish penalty
no fake financial evidence requirement
```

## FIC-FIN-08 — financial-sector exclusion

Expected:

```text
no industrial net debt
no generic operating working-capital reasoning
no interest-income-as-generic-non-operating claim
```

---

# 43. Financial grounding audit

For every subject/repetition report:

```text
selected typed financial refs

first-class typed financial refs

used typed financial refs

material financial anchor refs

narrative duplicate refs

grounding failures
```

Required summary:

```text
selected_typed_financial_ref_count

first_class_typed_financial_ref_count

used_typed_financial_ref_count

material_financial_anchor_grounding_failure_count

working_capital_grounding_failure_count

narrative_substitution_failure_count
```

Do not require every selected item to be used.

The requirement is:

```text
if a selected typed financial fact materially supports the claim,
the claim must be grounded to a relevant typed ref.
```

---

# 44. Evidence double-counting advisory

Audit whether outputs treat:

```text
typed fact
+
duplicate narrative summary
```

as two independent anchors.

Hard-fail only when an explicit duplicate-counting contract violation is deterministically proven.

Otherwise report:

```text
DOUBLE_COUNTING_ADVISORY
```

The primary hard problem remains grounding, not counting sentence quantity.

No scoring.

---

# 45. Formal stability

If all 6 calls complete and pass hard semantics,
run the existing formal stability classifier.

Report:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

Required:

```text
opposite_direction_reversal_count = 0
```

Do not:

```text
majority vote
average balances
change classifier
```

If threshold-adjacent:
use the existing frozen classifier.

---

# 46. Message specificity advisory

If full canary completes,
run the existing advisory for all 24 outputs.

Measure:

```text
typed financial anchor specificity

period specificity

case-specific checkpoint

generic substantive repetition

renderer-introduced repetition
```

Do not rewrite messages inside M12B solely to improve advisory repetition.

---

# 47. No real issuer model calls

Required:

```text
model_calls_real = 0
real_issuer_model_exposure_count = 0
```

Do not run a fresh real cohort in M12B.

The next real proof is authorized only after the full fictional canary passes.

---

# 48. Production side-effect firewall

Required final:

```text
provider_source_fetches = 0

production_db_mutations = 0
monitoring_registrations = 0
assessment_persistence_mutations = 0
warning_mutations = 0
notification_queue_writes = 0
production_sends = 0

main_merges = 0
deployments = 0

automatic_monitoring_resume = 0
```

Expected model calls only:

```text
fictional = 6 if full canary completes
real = 0
judge = 0
```

---

# 49. Required artifacts — provenance / architecture reuse

Produce at least:

```text
01-repository-provenance
02-latest-result-integrity
03-m12b-scope-freeze

04-m12a-architecture-decision-reuse-proof
05-m12a-frozen-implementation-contract-reuse-proof
06-current-vs-first-class-evidence-flow
```

---

# 50. Required artifacts — implementation

Produce:

```text
07-first-class-typed-evidence-projection-contract
08-neutral-financial-evidence-statement-contract
09-evidence-kind-financial-semantics-contract
10-alias-reuse-and-ordering-proof
11-selected-only-projection-proof
12-suppressed-item-negative-control
13-evidence-double-counting-contract-reuse

14-first-class-evidence-implementation-diff
15-directional-context-before-after
16-fic-fin-06-before-after-context
17-legacy-context-compatibility
```

---

# 51. Required semantic regression artifacts

Produce:

```text
18-old-fic-fin-06-remains-fail
19-corrected-fic-fin-06-remains-pass
20-fic-fin-03-qtd-ytd-regression

21-price-technical-supply-non-leak-proof
22-price-timing-no-change-proof
23-renderer-ownership-no-change-proof
24-source-sufficiency-no-change-proof
25-daily-delta-no-change-proof
26-warning-no-change-proof
```

---

# 52. Required deterministic validation artifacts

Produce:

```text
27-focused-test-results
28-full-test-results
29-ruff-and-diff-results
30-phase-a-gate
```

---

# 53. Required full fictional-canary artifacts

If Phase A passes:

```text
31-fictional-canary-generation-manifest
32-fictional-canary-source-lock

33-run-1-context-01
34-run-1-context-02

35-run-2-context-01
36-run-2-context-02

37-run-3-context-01
38-run-3-context-02

39-full-fictional-canary-semantic-audit
40-full-fictional-canary-grounding-audit
41-full-fictional-canary-double-counting-advisory
42-full-fictional-canary-validator-audit
43-full-fictional-canary-stability
44-full-fictional-canary-message-specificity-advisory
45-runtime-observations
```

Preserve for every attempted model call:

```text
prompt
schema
raw output
receipt
transport log
run document
```

---

# 54. Required completion artifacts

Produce:

```text
46-fresh-real-proof-readiness-decision
47-production-no-change
48-schedule-pause-observation
49-master-workflow-update
50-program-completion
```

---

# 55. M12B deterministic acceptance criteria

Pass only if:

```text
all selected typed financial aliases become ordinary first-class evidence aliases

no aliases are renumbered

no duplicate aliases exist

only selected typed items are projected

suppressed items remain absent

neutral human-readable financial statements are deterministic

financial_decision_context detailed metadata remains

legacy no-financial-context projection remains byte-equivalent

output schema unchanged

renderer unchanged

old FIC-FIN-06 still fails

corrected FIC-FIN-06 still passes

FIC-FIN-03 QTD/YTD regression passes

validators are not weakened

threshold/calibration unchanged

source sufficiency unchanged

Daily Delta unchanged

focused/full tests PASS

ruff PASS

git diff --check PASS
```

---

# 56. M12B full-canary acceptance criteria

Pass only if:

```text
6 / 6 model contexts complete successfully

24 / 24 subject outputs schema-valid

invalid financial evidence ref count = 0

material financial anchor grounding failure count = 0

working-capital grounding failure count = 0

narrative substitution failure count = 0

hard financial semantic violation count = 0

QTD/YTD false reject count = 0
QTD/YTD false accept count = 0

price/technical/supply Directional violation count = 0

AI imperative primary action count = 0

opposite-direction reversal count = 0

wrapper retry count = 0

unexpected timeout/capacity/orphan count = 0
```

Formal stability must be measured if all 6 contexts complete.

---

# 57. Failure handling

## If FIC-FIN-06 still grounds only to narrative despite first-class typed evidence

This disproves the sufficiency of Option A.

Set:

```text
next_scope =
DIRECTIONAL_OUTPUT_FINANCIAL_GROUNDING_SCHEMA_REVIEW_OR_IMPLEMENTATION
```

Do not weaken validator.

Do not add another prompt-only sentence.

## If typed grounding passes but another financial semantic failure appears

Use:

```text
BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR
```

with the exact failing contract.

## If semantic hard gates pass but formal stability fails

Separate:

```text
financial evidence interpretation variability
vs
boundary calibration uncertainty
```

Do not change threshold automatically.

## If runtime fails

Classify runtime separately.

Do not call it a semantic failure.

---

# 58. Next-scope decision

## A. Full fictional canary PASS

Set:

```text
fresh_real_proof_readiness = READY
```

Recommended:

```text
next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF
```

Do not start the real proof inside M12B.

## B. First-class evidence projection does not solve grounding

```text
fresh_real_proof_readiness = NOT_READY

next_scope =
DIRECTIONAL_OUTPUT_FINANCIAL_GROUNDING_SCHEMA_REVIEW_OR_IMPLEMENTATION
```

## C. New bounded semantic failure

```text
fresh_real_proof_readiness = NOT_READY

next_scope =
BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR
```

## D. Runtime blocker

Use bounded runtime repair.

---

# 59. Production readiness

Even if M12B passes:

```text
production_readiness = NOT_READY
```

Still required:

```text
fresh unseen real generalization proof
production integration review
explicit user authorization
```

Monitoring schedules remain paused.

---

# 60. Program-completion fields

Include at least:

```text
base_sha
work_instruction_commit
implementation_commit
report_commit
final_head_sha
branch

latest_result_zip_sha256
latest_result_integrity

m12a_status
m12b_status

preferred_grounding_architecture

selected_typed_financial_ref_count
first_class_typed_financial_projection_count
suppressed_typed_projection_count

alias_renumber_count
duplicate_alias_count

neutral_financial_statement_count
financial_decision_context_detail_removed_count

output_schema_change_count
renderer_substantive_change_count

old_fic_fin_06_regression_status
corrected_fic_fin_06_status
fic_fin_03_qtd_ytd_regression_status

financial_semantic_validator_change_count
qtd_ytd_validator_semantic_change_count

directional_prompt_change_count
price_timing_prompt_change_count

directional_threshold_changed
directional_increment_changed
hold_lean_contract_changed
calibration_tiebreak_changed
fixed_financial_score_rule_count

source_sufficiency_semantic_change_count
daily_delta_semantic_change_count
warning_semantic_change_count

fictional_generation_id
fictional_subject_count
fictional_context_count
fictional_repetition_count

model_calls_real
model_calls_fictional
model_calls_judge

model_context_success_count
model_context_failure_count
wrapper_retry_count
timeout_count
capacity_failure_count
orphan_process_count

fictional_output_row_count
fictional_schema_pass_count

invalid_financial_reference_count
hard_financial_semantic_violation_count

used_typed_financial_ref_count
material_financial_anchor_grounding_failure_count
working_capital_grounding_failure_count
narrative_substitution_failure_count

validator_false_reject_count
validator_false_accept_count

fictional_stable_count
fictional_boundary_uncertainty_count
fictional_unstable_count
opposite_direction_reversal_count

double_counting_advisory_status
message_specificity_advisory_status

real_issuer_model_exposure_count

provider_source_fetches

production_db_mutations
monitoring_registrations
assessment_persistence_mutations
warning_mutations
notification_queue_writes
production_sends

main_merges
deployments

observed_paused_schedule_count
scheduler_mutation_count
automatic_monitoring_resume

focused_test_result
full_test_result
ruff_result
git_diff_check

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count

fresh_real_proof_readiness
production_readiness
status
stop_reason
next_scope
```

Anything not measured:

```text
NOT_MEASURED
```

---

# 61. Artifact integrity

Freeze:

```text
program completion
master workflow
all deterministic artifacts
all attempted model-call artifacts
```

before final artifact-index creation.

Index every payload except the index itself.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final ZIP SHA-256.

---

# 62. Final task principle

M12A found that the alias system is already unified.

The failure is narrower:

```text
selected typed financial aliases exist in the catalog
but are visually/structurally secondary because they are absent from ordinary evidence[].
```

The selected architecture is therefore:

```text
selected typed financial item
→ same ordinary first-class evidence surface
→ same alias
→ same resolver
→ same output evidence_refs
```

while retaining:

```text
financial_decision_context
for detailed typed metadata.
```

The correct M12B flow is:

```text
implement first-class selected-only projection
→ prove no alias/schema/lifecycle regressions
→ keep validators strict
→ rerun all 8 fictional cases from a new generation
→ measure full 3-repeat stability
```

Not:

```text
add another prompt-only repair
```

Not:

```text
create a second output grounding field
```

Not:

```text
invent narrative lineage from text similarity
```

Not:

```text
delete narrative interpretation
```

Not:

```text
dump every accounting fact into evidence[]
```

Not:

```text
change thresholds/calibration
```

Not:

```text
run a fresh real cohort before the full fictional canary passes
```

And not:

```text
resume production monitoring
```

Make selected typed financial evidence truly first-class,
then test the model on the same frozen fictional cases.
