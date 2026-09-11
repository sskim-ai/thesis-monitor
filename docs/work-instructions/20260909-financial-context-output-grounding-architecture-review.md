# Thesis Monitor — Financial Context Output Grounding Architecture Review

## 0. Task identity

Suggested work-instruction filename:

```text
20260909-financial-context-output-grounding-architecture-review.md
```

Suggested result bundle:

```text
thesis-monitor-20260909-financial-context-output-grounding-architecture-review-report.zip
```

Master-workflow phase:

```text
M12A — Financial Context Output Grounding Architecture Review
```

This task begins only after M12G stopped with:

```text
status = M12G_CANARY_FAIL
stop_reason = PROMPT_GROUNDING_INSUFFICIENT
next_scope = FINANCIAL_CONTEXT_OUTPUT_GROUNDING_ARCHITECTURE_REVIEW
```

M12G proved that one additional prompt-grounding clarification was insufficient.

M12A must NOT attempt another prompt-only repair.

M12A is a **model-free architecture review + offline prototype comparison**.

Its purpose is to decide how typed financial evidence should become a first-class,
traceable basis for Directional output without:

```text
forcing every selected financial item to be used
double-counting narrative + typed evidence
weakening validators
turning evidence grounding into a fixed scorecard
```

No model calls in M12A.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260909-bounded-directional-financial-anchor-grounding-repair-full-fictional-canary-report.zip
```

Verified SHA-256:

```text
69fc255d836d3dd886882754c21a233d82541c86ff627a5a5c8342249012aa68
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Latest M12G state:

```text
M1–M11 = COMPLETE

M12 =
DETERMINISTIC_COMPLETE_CANARY_BLOCKED

M12R =
BLOCKED
but QTD/YTD validator repair = PASS

M12G =
BLOCKED

fresh_real_proof_readiness =
NOT_READY

production_readiness =
NOT_READY
```

Reported M12G provenance:

```text
base_sha =
6a870cd34dd9ec7825559dc3ad964021b7cea64a

work_instruction_commit =
7e3fac6385760e3356213eab81c67e957d1c55d6

implementation_commit =
63aaf9f72cc7ee021c0bf70a746ba5ae5472b218

branch =
codex/20260909-bounded-directional-financial-anchor-grounding-repair-full-fictional-canary
```

M12G used the established pre-report-commit artifact convention:

```text
report_commit = NOT_MEASURED
final_head_sha = NOT_MEASURED
```

At task start use actual repository HEAD as authority and record actual M12G final/report state.

Latest artifact integrity:

```text
indexed payload count = 160
hash mismatch count = 0
size mismatch count = 0
secret scan failure count = 0
```

---

# 2. M12G deterministic repair result is preserved

M12G Phase A passed:

```text
old FIC-FIN-03 remains PASS

old FIC-FIN-06 remains FAIL
for typed financial grounding

corrected FIC-FIN-06 test fixture PASS

positive grounding fixtures = 6 / 6 PASS

negative grounding fixtures = 3 / 3 rejected

focused tests PASS
full tests PASS
ruff PASS
git diff --check PASS

validator semantic change count = 0

financial-context selector change count = 0

fictional case change count = 0

schema change count = 0
```

Do not reopen these results merely because the model later failed grounding.

---

# 3. M12G model result — authoritative root cause

New generation:

```text
20260909-m12g-fictional-20260909T054736Z-63aaf9f72cc7
```

Completed before fail-closed:

```text
run-1 context-01 = transport PASS
run-1 context-02 = transport PASS

fictional model calls = 2
subject outputs = 8
schema PASS = 8 / 8

timeout = 0
capacity failure = 0
orphan = 0
wrapper retry = 0
```

Generic financial safety remained clean:

```text
invalid financial ref = 0

price / technical / supply Directional refs = 0

partial PPE called FCF = 0

prior-year-end called YoY = 0

partial debt called total debt = 0

normalized earnings claim = 0

financial-sector generic misuse = 0

fixed financial score = 0

QTD/YTD validator false reject = 0
QTD/YTD validator false accept = 0
```

The blocker remained:

```text
FIC-FIN-06

material_financial_anchor_grounding_failure = 1

working_capital_grounding_failure = 1

narrative_substitution_failure = 1
```

The same financial topic was correctly discussed in prose,
but selected typed financial refs were not used.

---

# 4. Structural evidence discovered in M12G

For FIC-FIN-06, the alias map contains both narrative and typed aliases.

Narrative aliases include:

```text
E01 structural-risk
"Inventory and trade receivables have risen since year-end."

E06 business-thesis
"Sales growth is intact, with working-capital quality needing confirmation."

E07 remaining-unknown
"Demand quality and collection timing are not established by balances alone."

E08 sector-context
"Inventory and receivables are confirmation points, not automatic negatives."
```

Typed financial aliases include:

```text
E03 trade_accounts_receivable
canonical:fictional:FIC-FIN-06:trade-receivables-current

E04 inventory
canonical:fictional:FIC-FIN-06:inventory-current
```

The model-facing `DIRECTIONAL_CORE_CONTEXT` currently presents them through two different structures:

```text
evidence[]
```

contains the narrative evidence.

```text
financial_decision_context.evidence_items[]
```

contains the typed financial evidence.

For FIC-FIN-06 the model cited:

```text
E01
E07
E08
E09
...
```

but never:

```text
E03
E04
```

even after the M12G prompt said:

```text
Ground material financial_decision_context claims in 1–3 typed refs,
not narrative alone.
```

This split evidence surface is the primary architecture question.

M12A must verify this pattern across all completed M12/M12R/M12G outputs,
not assume FIC-FIN-06 is the only example.

---

# 5. M12A primary question

Answer:

```text
How should a typed financial fact participate in the same evidence-grounding contract
as business/narrative evidence so the model does not have to learn
two different citation surfaces?
```

The architecture must preserve:

```text
typed provenance
human-readable investment reasoning
optional financial evidence
sector routing
period/basis safety
validator enforceability
backward compatibility
```

---

# 6. Operating constraints

M12A is offline.

Required:

```text
model_calls_real = 0
model_calls_fictional = 0
model_calls_judge = 0

provider_source_fetches = 0
```

Production side effects:

```text
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

Existing approved schedules remain paused.

---

# 7. Work-instruction commit first

Before review/tooling:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Commit this instruction.

Record:

```text
new_work_instruction_commit
```

Only then add review/prototype tooling.

---

# 8. Preserve current semantic contracts

M12A must NOT change production/shared semantics for:

```text
BUY / HOLD / SELL thresholds

0.5 balance increments

HOLD lean

calibration tie-break

financial-context selector

M5–M11 accounting mappings

QTD/YTD validator

financial semantic validators

source sufficiency

Daily Delta

warnings

Price-Timing

renderer ownership
```

M12A may create offline prototype representations.

Do not activate a prototype in the real Directional runner.

---

# 9. Architecture Option A — Unified First-Class Evidence Index

Evaluate an architecture where every selected typed financial item is projected into the same first-class evidence index used by other Directional evidence.

Conceptually:

```text
evidence:
  E01 narrative structural risk
  E02 expectation
  E03 typed trade receivables
  E04 typed inventory
  ...
```

rather than:

```text
evidence[]
+
separate financial_decision_context citation surface
```

The structured `financial_decision_context` may remain as detailed metadata,
but its selected items must be directly represented as first-class evidence aliases.

Required design properties:

```text
one alias namespace

one evidence-ref contract

typed financial metadata retained

financial aliases remain distinguishable as typed financial evidence

no duplicate alias IDs

no price/technical/supply evidence
```

Evaluate whether this can be implemented without changing the Directional output schema.

---

# 10. Option A human-readable projection

M12G alias-map typed financial entries currently have statements such as:

```text
{"value":"300"}
```

while the model-facing structured financial block contains the full meaning.

Evaluate a deterministic human-readable evidence projection such as:

```text
label:
inventory

semantic statement:
inventory balance is higher than the prior year-end comparison

period:
POINT_IN_TIME at 2026-06-30

comparison:
prior_year_end at 2025-12-31

evidence_id:
E04
```

The exact numeric values may remain in structured metadata.

The human-readable evidence statement must be deterministic from the typed contract,
not model-generated.

Do not turn it into bullish/bearish interpretation.

Examples of forbidden deterministic statements:

```text
inventory deterioration
dangerous receivables build
strong liquidity
```

unless that meaning is itself an already-canonical direct fact.

Preferred wording remains neutral:

```text
higher / lower
current / prior
complete debt total
cash balance
financial income/cost
```

---

# 11. Architecture Option B — Explicit Evidence-Lineage Bridge

Evaluate keeping narrative and typed evidence separate,
but giving narrative evidence explicit backing lineage.

Example:

```text
E01 structural-risk narrative

backing_financial_refs:
  E03
  E04
```

or reuse current:

```text
metric_refs
```

if that field is semantically appropriate.

A narrative citation may count as financially grounded only when:

```text
the lineage was created deterministically
from actual source/financial evidence

the narrative claim scope matches the backing financial facts

the lineage is not inferred from text similarity at validation time
```

Do not use fuzzy semantic matching to invent lineage.

Required review:

```text
which current evidence producers can create deterministic lineage?

which existing narrative rows are manually/synthetically authored
without source-derived lineage?

can real production evidence support this reliably?
```

---

# 12. Option B anti-shortcut rule

Do NOT decide:

```text
narrative sentence contains "inventory"
→ automatically link every inventory fact
```

Lineage must be provenance-based.

If a narrative evidence item was not actually derived from or linked to typed financial facts:

```text
backing_financial_refs = empty
```

Citing it alone must still fail material typed grounding where typed evidence is required.

---

# 13. Architecture Option C — Structured Output Financial Grounding Field

Evaluate adding a separate structured output field such as:

```text
financial_grounding_refs
```

or:

```text
material_financial_evidence_refs
```

for the Directional candidate.

Possible semantics:

```text
refs selected by the model from supplied typed financial aliases
that materially support the candidate's financial reasoning
```

The field must NOT:

```text
require every selected financial ref

force financial evidence when immaterial

replace ordinary evidence_refs

create a score
```

Validator may require:

```text
if a material financial claim exists,
at least one relevant typed ref appears in:
  ordinary claim evidence_refs
  OR the structured financial-grounding field,
according to the frozen architecture
```

Evaluate whether this produces:

```text
better enforceability
```

without duplicating citation mechanisms unnecessarily.

---

# 14. Option C schema cost

Explicitly audit:

```text
output schema migration cost

legacy output compatibility

renderer impact

stored artifact impact

test surface

real model compliance risk

context/token overhead

whether one more field merely moves the prompt-compliance problem
```

Do not choose Option C solely because it is stricter.

---

# 15. Architecture Option D — Hybrid

Evaluate bounded hybrids such as:

```text
A + B:
first-class typed aliases
+
deterministic lineage for narrative summaries

A + C:
first-class typed aliases
+
one structured material-financial-ref field

B + C
```

Do not choose a hybrid unless each component solves a distinct proven problem.

Prefer the smallest architecture that makes grounding natural and deterministic.

---

# 16. Current alias architecture audit

Map the complete flow:

```text
canonical source ref
→ DecisionEvidenceRef
→ financial_context
→ financial_decision_context selection
→ alias map
→ evidence[] projection
→ prompt
→ output evidence_refs
→ alias resolver
→ canonical refs
→ validator
```

For each step report:

```text
owner module

input object

output object

whether typed financial evidence is present

whether human-readable semantics are present

whether lineage is preserved

whether aliases share one namespace

whether validator can resolve it
```

This is a required artifact.

---

# 17. Duplicate narrative vs typed financial audit

Across all 8 fictional cases,
classify each selected financial item:

```text
NO_NARRATIVE_DUPLICATE

NARRATIVE_SUMMARY_DUPLICATE_WITHOUT_LINEAGE

NARRATIVE_SUMMARY_WITH_VALID_LINEAGE

NARRATIVE_INTERPRETATION_NOT_DUPLICATE
```

Use actual packet/alias artifacts.

Measure:

```text
selected typed financial count

narrative duplicate count

typed-used count

narrative-only substitution count
```

Extend the audit to preserved M12 and M12R outputs where comparable.

This determines whether FIC-FIN-06 is an isolated prompt miss
or a general split-surface design risk.

---

# 18. Evidence-ref ergonomics audit

Inspect how the model sees:

```text
ordinary evidence aliases

typed financial aliases
```

Compare:

```text
location in prompt

human readability

semantic completeness

reference format

distance from task instructions

number of competing aliases describing the same concept
```

Quantify where feasible:

```text
characters/tokens between alias and relevant instruction

duplicate semantic statements per domain

typed item raw-JSON-only statement count
```

Do not treat token distance as causal proof,
but use it as architecture evidence.

---

# 19. Offline prototype requirement

Build offline-only prototypes for at least:

```text
Option A

Option B

one of:
  Option C
  Option D
```

Do not activate them in the actual runner.

For each prototype,
serialize frozen FIC-FIN-05 and FIC-FIN-06 inputs.

Produce:

```text
before representation

prototype representation

alias map

lineage map

validator-resolvable grounding map
```

No model call.

---

# 20. FIC-FIN-06 offline replay analysis

Using the preserved failed FIC-FIN-06 output,
simulate how each architecture would treat the exact same output.

Important:

This is NOT allowed to convert the historical failure into a model success.

The purpose is to answer:

```text
would this architecture make the existing cited narrative refs
provably grounded to typed financial evidence?
```

Possible results:

## Option A

If old output still does not cite E03/E04:

```text
still FAIL
```

unless alias unification changes the evidence semantics in a way that makes the cited refs typed themselves.

Do not pretend Option A retroactively changes old refs.

## Option B

Old E01 may count as grounded ONLY if a valid provenance-based lineage can be established.

If the old synthetic narrative had no true lineage:

```text
still FAIL
```

## Option C

Old output lacks the new field:

```text
legacy / NOT_APPLICABLE
```

not PASS.

This replay is architecture comparison only.

---

# 21. Corrected-output architecture comparison

Use the existing corrected FIC-FIN-06 fixture
that directly cites typed refs.

Verify all architecture options can represent it safely.

Measure:

```text
grounding clarity

duplicate refs

schema burden

validator complexity

backward compatibility
```

The corrected fixture is not a model result.

---

# 22. Real-production compatibility review

Do not design only around fictional cases.

Inspect actual production/shared evidence producers used by:

```text
Initial Analysis

monitoring onboarding

Daily monitoring evidence

Directional packet builder
```

Answer:

```text
Can selected financial facts be projected into the main evidence index generically?

Can narrative evidence carry provenance-based typed lineage generically?

Would either path create duplicate evidence rows in existing production packets?

Would existing evidence IDs remain stable?

Would M2/M3 lifecycle semantics remain unchanged?
```

---

# 23. Backward compatibility requirement

Preferred architecture should preserve:

```text
legacy DecisionEvidencePacket parsing

legacy evidence aliases where financial_context absent

historical packet hashes where no new representation is activated

output schema if possible

renderer interface if possible
```

If an output schema change is chosen,
the review must prove why a no-schema-change solution is inadequate.

---

# 24. Evidence double-counting control

A unified evidence architecture must not cause the model or validator to count:

```text
typed inventory fact
+
narrative summary of inventory fact
```

as two independent financial anchors.

Design one explicit rule for:

```text
same economic fact family
```

Possible approach:

```text
evidence_group_id / backing lineage
```

or reuse an existing canonical lineage field.

Do not implement a bullish/bearish scoring deduplicator.

The rule is about evidence identity, not weighting.

---

# 25. Narrative preservation principle

Do not remove narrative evidence simply because typed financial evidence exists.

Narrative evidence can express:

```text
why the fact matters

what remains Unknown

sector interpretation

business implications

management explanation
```

Typed financial evidence carries:

```text
what the financial fact actually is
```

The architecture should support:

```text
typed fact + narrative interpretation
```

without requiring the model to choose only one.

---

# 26. Financial-context raw-data boundary

Do not respond to M12G by dumping all raw financial facts into the main evidence list.

Only:

```text
selected financial_decision_context items
```

may become first-class aliases under Option A.

The M12 deterministic selector remains frozen.

This preserves the earlier hybrid design:

```text
machine-normalize high-risk financial semantics
→ select bounded financial context
→ AI interprets
```

---

# 27. No validator weakening

M12A must preserve the meaning:

```text
material financial reasoning
must be traceable to actual typed financial evidence
when such selected evidence is the factual basis
```

Do not redefine:

```text
any narrative paraphrase = typed grounding
```

Architecture may make grounding easier/natural,
but provenance remains required.

---

# 28. Decision criteria

Score each architecture qualitatively, not numerically, on:

```text
grounding reliability

model ergonomics

provenance integrity

double-counting risk

implementation complexity

schema migration risk

backward compatibility

validator simplicity

prompt complexity

token/context cost

real-production generality

sector compatibility

failure transparency
```

Use:

```text
STRONG
ACCEPTABLE
WEAK
BLOCKING
```

or equivalent qualitative labels.

No weighted total score.

---

# 29. Preferred architecture decision

M12A must choose ONE:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

PROVENANCE_LINEAGE_BRIDGE

STRUCTURED_OUTPUT_FINANCIAL_GROUNDING

HYBRID_<explicit components>

NO_CHANGE_PROMPT_ONLY
```

`NO_CHANGE_PROMPT_ONLY` should be selected only if evidence shows M12G failure was not architectural.

Given M12G's repeated prompt-only failure,
this outcome requires unusually strong evidence.

Do not leave the decision as a vague list of options.

---

# 30. Next implementation contract

For the chosen architecture produce a frozen implementation specification:

```text
modules to change

new/changed data fields

alias behavior

evidence index behavior

lineage behavior

output schema impact

validator behavior

legacy behavior

renderer impact

source-sufficiency impact

Daily Delta impact

migration / artifact compatibility

required tests

future model-canary topology
```

No model calls in M12A.

---

# 31. Preferred minimality principle

If Option A can make typed financial evidence first-class
using the existing alias/evidence-ref/output schema,
and Option B/C add no necessary capability,
prefer A.

If narrative producers can reliably supply explicit financial lineage
and this avoids redundant evidence surfaces,
B may be preferable.

If neither input architecture can enforce material grounding clearly enough,
consider C or a hybrid.

The decision must be evidence-based from current code,
not predetermined by this instruction.

---

# 32. Optional prototype code boundary

M12A may add:

```text
offline serializer / prototype module

architecture comparison harness

lineage audit helper

evidence-index prototype

tests
```

M12A must NOT wire a prototype into:

```text
production Directional runner

live compact AI context

production output schema

renderer

monitoring lifecycle
```

No actual model input changes in M12A.

If a prototype requires touching production/shared code,
put it behind a test/offline-only path or stop.

---

# 33. Deterministic validation requirements

Run:

```text
focused pytest
full repository pytest
ruff
git diff --check
```

Required PASS if code/prototype tooling changes.

No model tests.

No provider calls.

---

# 34. Production side-effect firewall

Required:

```text
model_calls_real = 0
model_calls_fictional = 0
model_calls_judge = 0

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

---

# 35. Required artifacts — provenance / current failure

Produce:

```text
01-repository-provenance
02-latest-result-integrity
03-m12a-scope-freeze

04-m12g-failure-summary
05-current-evidence-grounding-flow
06-current-alias-architecture-audit
07-duplicate-narrative-typed-financial-audit
08-evidence-ref-ergonomics-audit
```

---

# 36. Required architecture-option artifacts

Produce:

```text
09-option-a-first-class-evidence-design
10-option-b-lineage-bridge-design
11-option-c-structured-output-grounding-design
12-hybrid-option-analysis
13-architecture-risk-comparison
```

If one option is infeasible,
state the concrete blocker.

---

# 37. Required offline prototype artifacts

Produce:

```text
14-option-a-fic-fin-05-prototype
15-option-a-fic-fin-06-prototype

16-option-b-fic-fin-05-prototype
17-option-b-fic-fin-06-prototype

18-third-option-fic-fin-05-prototype
19-third-option-fic-fin-06-prototype

20-old-fic-fin-06-offline-replay
21-corrected-fic-fin-06-architecture-comparison
```

No model output generation.

---

# 38. Required production-compatibility artifacts

Produce:

```text
22-real-packet-producer-compatibility-audit
23-backward-compatibility-audit
24-evidence-double-counting-control
25-narrative-preservation-contract
26-output-schema-impact-decision
27-renderer-impact-decision
28-source-sufficiency-no-change-proof
29-daily-delta-no-change-proof
```

---

# 39. Required decision artifacts

Produce:

```text
30-preferred-grounding-architecture-decision
31-frozen-next-implementation-contract
32-next-model-canary-scope
33-fresh-real-proof-readiness-decision
34-production-no-change
35-schedule-pause-observation
36-master-workflow-update
37-program-completion
```

Expected:

```text
fresh_real_proof_readiness = NOT_READY
```

because M12A itself performs no repaired model canary.

---

# 40. M12A acceptance criteria

M12A is COMPLETE only if:

```text
current split evidence surface is fully traced

M12/M12R/M12G grounding behavior is audited

duplicate narrative-vs-typed evidence is measured

at least three architecture approaches are concretely evaluated

offline prototype representations exist

one preferred architecture is selected

double-counting rule is frozen

legacy/backward compatibility is explicitly decided

output-schema impact is explicitly decided

real production evidence producers are checked

next implementation scope is bounded

no production/shared Directional activation occurs

no validators are weakened

focused/full tests PASS if tooling changed

ruff PASS
git diff --check PASS

all model/provider/production side-effect counts = 0
```

M12A does NOT require:

```text
grounding problem fixed in live model output

fictional canary rerun

real proof

production readiness
```

---

# 41. Next-scope decision

The next scope must be the implementation of the architecture selected in M12A.

Examples:

## If Option A selected

```text
FIRST_CLASS_TYPED_FINANCIAL_EVIDENCE_INDEX_IMPLEMENTATION
```

## If Option B selected

```text
FINANCIAL_EVIDENCE_PROVENANCE_LINEAGE_BRIDGE_IMPLEMENTATION
```

## If Option C selected

```text
DIRECTIONAL_OUTPUT_FINANCIAL_GROUNDING_SCHEMA_IMPLEMENTATION
```

## If hybrid selected

Use one explicit bounded name,
not a generic "financial grounding repair".

After implementation:

```text
rerun full 8-subject × 3-repeat fictional canary
```

Only after that passes:

```text
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF
```

---

# 42. Production readiness

Even if architecture review completes:

```text
production_readiness = NOT_READY
fresh_real_proof_readiness = NOT_READY
```

Monitoring remains paused.

---

# 43. Program-completion fields

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

m12g_status
m12a_status

current_evidence_surface_count
typed_financial_surface_count
narrative_surface_count

selected_typed_financial_ref_count
typed_financial_ref_used_count
narrative_duplicate_count
narrative_substitution_failure_count

option_a_status
option_b_status
option_c_status
hybrid_status

preferred_grounding_architecture

output_schema_change_required
evidence_index_change_required
lineage_change_required
validator_change_required
renderer_change_required

double_counting_contract_status
backward_compatibility_status
real_packet_producer_compatibility_status

model_calls_real
model_calls_fictional
model_calls_judge
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

Anything unmeasured:

```text
NOT_MEASURED
```

---

# 44. Artifact integrity

Freeze all final reports and master workflow before final artifact index.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final ZIP SHA-256.

---

# 45. Final task principle

M12G shows that prompt wording alone is not a reliable grounding architecture.

The model understood:

```text
inventory / receivables increased
and should be monitored
```

but chose the easy first-class narrative aliases instead of the typed financial aliases
that actually carried the exact period/value/comparison provenance.

The correct next move is:

```text
inspect the evidence architecture
→ make typed financial provenance first-class or explicitly bridged
→ prevent double counting
→ freeze one grounding architecture
→ implement it in a separate bounded task
→ rerun the full fictional canary
```

Not:

```text
add another sentence to the prompt
```

Not:

```text
weaken the validator
```

Not:

```text
delete useful narrative evidence
```

Not:

```text
dump all raw accounting facts into the prompt
```

Not:

```text
change thresholds/calibration
```

Not:

```text
run a fresh real cohort
```

And not:

```text
resume production monitoring
```

Fix the evidence architecture, not the wording around it.
