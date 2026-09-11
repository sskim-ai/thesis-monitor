# Thesis Monitor — Unknown-Field Consistency, Early Core Validation & Offline Evidence Review

**Document version:** 2026-09-08 / next-stage-v1
**Task ID:** `20260908-unknown-field-consistency-early-core-validation-offline-evidence-review`
**Companion planning document:** `20260908-thesis-monitor-master-workflow.md`
**Execution mode:** bounded repair on an isolated development branch + offline review.
**New model invocations:** **0**, including fictional probes, model-backed judges and rewritten messages.
**New provider/source requests:** **0**. No new cohort, source refresh, FIRST/A/B/C run, production promotion or message send.

## 1. Objective and authorization

The user approved moving from repeated new-issuer preparation/proof attempts to finishing the common decision path, followed by non-production integration and message-quality review.

This task has four deliverables:

1. Repair the **generic Unknown-treatment cross-field contract and its early Core validation coverage**.
2. Review the preserved Core outputs for boundary changes without relabeling an incomplete experiment as a successful proof.
3. Audit the 48 preserved complete messages for specificity and repetition without rewriting reasoning or changing the renderer.
4. Update the repository's canonical master workflow and record the existing-code integration boundaries.

This is **not** an instruction to merge into main or deploy the new decision engine. It is also not another source-universe expansion, free-API gate project, calibration retuning, or 32-call experiment.

The seven-stock independent raw-financial review is a **deferred judgment-input coverage discussion**. Record it in the master backlog. Do not silently turn that discussion into a financial-enrichment or model-input rewrite in this task.

## 2. Authority and exact inputs

### S1 — latest execution evidence

```text
thesis-monitor-20260908-authoritative-result-identity-reconciliation-us-source-expansion-proof-resume-report.zip

SHA-256:
2a58b8e8dbfcc6e3aa7cb4900bec2d16d29f149b69160e8fd0c5b0522f6a798e
```

The adjacent `.sha256` matches the actual ZIP. Independently inspected package counts:

```text
ZIP files:                2008
Indexed payload files:   2007
Excluded from index:     artifact-index.json only
Hash / size mismatches:  0 / 0
```

Verify this actual supplied file and its index. If it differs, stop dependent work and record the discrepancy; do not replace the expected hash with an unrelated historical value. `completion.json` is the packaged completion record, but detailed runtime/output evidence governs inconsistent aggregates.

### S2 — architecture/lifecycle reference

```text
thesis-monitor-new-session-system-prompt-handoff-bundle(1).zip
```

Read `00_START_HERE.md`, `01_SYSTEM_PROMPT_FULL.md`, `04_ARCHITECTURE_CONTRACTS.md`, `05_EXPERIMENT_AND_PROMOTION_PROTOCOL.md`, and `06_MONITORING_BOOTSTRAP_AND_LIVE_ROADMAP.md` when needed for the original contracts.

Its September 6 current-state/cohort/next-task declarations are historical, not current. The latest execution and subsequent user decisions supersede them. Do not re-open synthetic fixture or old cohort reuse tasks.

### S3 — normative investment knowledge

`Investment Thesis Analysis & Monitoring Knowledge Guide v3` governs Fact / Interpretation / Unknown, accounting/ADR/numeric safety and baseline-vs-delta semantics.

### Concern-specific authority

- Historical execution: S1 raw artifacts, receipts and detailed audits.
- Current code: actual repository HEAD and worktree.
- Authorized scope: this instruction and the companion master workflow.
- Production status: fresh authorized observation, never an assumed live state from an old report.

Do not change historical evidence to reconcile an inconsistency. Add a correction/interpretation record with source pointers.

## 3. Verified baseline to preserve

| Run | Core rows | Timing rows | Complete-run gates |
|---|---:|---:|---|
| FIRST | 16 | 16 | Reported ownership / renderer / hard-safety PASS |
| A | 16 | 16 | Reported PASS |
| B | 16 | 16 | Reported PASS |
| C | 16 | 4 | Partial execution; combined context check failed; full-run gates NOT_MEASURED |

```text
Model invocations / raw output documents = 29 / 29
Core rows = 64
Timing rows = 52
Total stage rows = 116
Unique issuers = 16
Complete composed states / rendered messages = 48 / 48
Context partial checks = 28 PASS, 1 FAIL
Timeout / explicit capacity / orphan = 0 / 0 / 0
Observed disconnect recovery = 1
Wrapper retry = 0
Formal current-cohort generalization = NOT_ESTABLISHED
```

S1's top-level `run_results.c = NOT_RUN` conflicts with the five actual C contexts. Its zero failed-context count describes transport, not semantic acceptance. Correct reporting in a new artifact and narrowly fix current report generation if warranted. Do not erase historical summaries.

Formal stability is `NOT_MEASURED`; zero-filled counters are not evidence of zero instability. Offline descriptive inspection found seven A/B→C direction-boundary crossings, all adjacent 0.5-point changes, with no direct BUY↔SELL reversal. This is **not** a formal stability result.

Completed-run message quality remains **ADVISORY FAIL**:
FIRST 13, A 16, B 21 repeated substantive spans. These are span counts, not issuer counts. Preserve the original advisory role.

Latest historical operational observation: all eight approved US/KR monitoring schedules paused at **2026-09-08 10:37:27 KST**; no automatic resume. This is not a new live observation.

## 4. Reproduce the exact defect before choosing a fix

Critical S1 files:

```text
experiment/fresh-real-proof/model-contexts/C/DIRECTIONAL_CORE/batch-01/output.raw.json
experiment/fresh-real-proof/model-contexts/C/DIRECTIONAL_CORE/batch-01/schema.json
experiment/fresh-real-proof/model-contexts/C/DIRECTIONAL_CORE/batch-01/partial_semantic_audit.json
experiment/fresh-real-proof/model-contexts/C/PRICE_TIMING/batch-01/prompt.txt
experiment/fresh-real-proof/model-contexts/C/PRICE_TIMING/batch-01/partial_semantic_audit.json
```

NEON's Core already contains:

```json
{
  "summary": "과거 손실은 부정 근거지만 공식 실적의 현재성이 낮아 후속 공시 확인이 필요하다.",
  "evidence_refs": ["E02", "E04"],
  "treatment": "CONFIRMATION_REQUIRED",
  "directional_negative_basis": ["E02"]
}
```

The schema allows treatment values:

```text
CONFIDENCE_LIMIT
CONFIRMATION_REQUIRED
DIRECTIONAL_NEGATIVE
```

The combined check later reports:

```text
unknown_nonnegative_has_directional_basis
```

The original raw Core conforms to its JSON schema; schema validity alone does not prove semantic consistency. The Core partial gate reported PASS, while the later combined gate detected the conflict. Timing copied the frozen Core; observed direction/balance/lean mutation flags were zero.

E02 refers to a historical official loss, not an invented fact. Its period/as-of limitation must remain visible. Preserve the distinction:

```text
confirmed historical negative fact
≠
unknown current persistence or missing follow-up evidence
```

Do not assume NEON should be BUY/HOLD/SELL from this field error. Its reported direction was unchanged at HOLD 4.5:5.5 across the four runs. This task is not a seven-stock or NEON investment reassessment.

## 5. Repository and master-document procedure

Before implementation, capture branch, HEAD, tree, worktree changes and exact test commands.

S1 reports:

```text
base_sha:               5323a73d9adde926eae5ff2b349faf954b201518
work_instruction_commit:f128a88f1599ac50116c94b9ae2b660df1bfeb17
implementation_commit:  7b7576e3e39346f61b7761b5e16f301c5a102abb
final_head_sha:          2967210296279a459f433e9624365bb26b9213ee
final_tree_sha:          731bc7ad4c5faac7dc72df49c4201cfe44605e9b
branch:
codex/20260908-us-source-universe-expansion-fresh-generalization-proof-resume
```

These are historical references, not a command to reset the repository. Explain subsequent changes; do not discard unrelated work.

Commit this instruction and the companion master-workflow update before implementation. Keep that first commit documentation-only and record it. Discover the repository's existing master document and update it in place with history; do not create competing masters. If none exists, adopt one canonical document and state its chosen path. Do not invent a path that was never inspected.

No existing `MASTER_WORKFLOW`-named file was supplied in the inspected bundles. The companion document consolidates the handoff roadmap, later results and current user decisions; reconcile it with actual repository documentation before treating it as the repository master.

At the end, update the master again with actual repair/audit results. A scheduled or planned phase is never marked complete merely because this instruction authorizes it.

## 6. Bounded mutation surface

Allowed, after root-cause confirmation:

- Stage-independent Unknown cross-field/evidence-reference validation helper.
- Early Core validation wiring using the same semantics as the final validator.
- Narrow Core prompt clarification for Unknown field placement, if the actual producer contract is ambiguous.
- Regression fixtures and no-network test orchestration.
- Error provenance and execution/validation report counters.
- Master workflow, evidence ledgers, integration boundary inventory.

Not allowed in this task:

- Directional calibration retuning, numerical threshold changes, averaging/voting or score postprocessing.
- Price-Timing policy changes, renderer prose changes or broad schema/API migration.
- Fundamental packet enrichment, new financial calculations, freshness-policy weakening or new providers.
- Silent editing of generated output to make it pass.
- Any real/fictional/model-judge call, candidate source scan or new holdout.
- Main merge, deployment, production DB writes, Telegram send, stock registration or automatic schedule resume.

If a narrow repair cannot express the existing semantics without a schema or ownership redesign, preserve the findings and report the exact blocked surface. Independent offline audits may still finish; do not widen implementation silently.

## 7. Implementation: contract alignment, not output sanitization

Trace the actual producer, alias expansion, Core validator, composer and final validation call graph. Record file/function locations and the point where the invariant is missing. The ZIP does not contain those implementation sources; inspect the repository rather than guessing function names.

Create or reuse a single canonical check for the stage-independent Unknown contract. Wire it into the actual Core result acceptance path **before the next model context could be spawned**. Keep the final validation check as defense in depth. Share implementation where feasible rather than maintaining diverging copied rule sets.

Minimum semantics to confirm against the existing validator:

- `CONFIDENCE_LIMIT` / `CONFIRMATION_REQUIRED` cannot carry a non-empty `directional_negative_basis`.
- Their ordinary `evidence_refs` need not be empty: a follow-up question may cite a real historical fact for context.
- `DIRECTIONAL_NEGATIVE` is not a loophole for missing data. Require the existing same-issuer, permitted-domain, provenance-backed negative-fact conditions.
- An actual negative fact remains representable in sell drivers / material evidence / risk fields; lack of current confirmation remains an Unknown.
- Evidence age, accounting/security basis and alias validity are not overridden by moving a field.
- Schema/identity/reference errors and cross-field semantic errors remain distinguishable.

Do **not** fix history or runtime output with rules such as:

```text
delete every directional_negative_basis
change every CONFIRMATION_REQUIRED to DIRECTIONAL_NEGATIVE
strip every negative fact when currentness is incomplete
force the final direction to HOLD
```

A narrow producer prompt clarification may explain the field allocation generically, symmetrically and without issuer examples. Preserve the calibration ladder, ownership rules and existing output schema. Do not assert that a prompt edit solves model behavior without new model evidence.

If a prompt changes, record its actual new hash and mark this prompt revision **MODEL_EMISSION_EFFECTIVENESS_NOT_MEASURED**. Historical calibration fixtures remain evidence for the historical prompt, not automatic proof for the edited prompt. Do not falsely report whole-prompt semantic drift or byte drift as zero.

## 8. Model-free regression and early-stop acceptance

Use hand-authored fictional/minimal fixtures and exact historical artifacts; no AI-generated new outputs.

Required cases:

| Case | Expected result |
|---|---|
| Exact historical NEON invalid Core | Rejected at early Core gate with the existing cause |
| Confirmation-required Unknown with contextual historical refs but no negative basis | Accepted if other contracts pass |
| Confidence-limit item with a negative basis | Rejected |
| Confirmed negative fact in its proper fact/driver fields plus separate follow-up Unknown | Accepted if currentness and other rules permit |
| Valid `DIRECTIONAL_NEGATIVE` supported under the existing contract | Accepted; do not blanket-ban negative facts |
| Missing data only promoted to negative basis | Rejected under existing evidence semantics |
| Cross-issuer, nonexistent alias or forbidden price/supply reference | Rejected |
| Same candidate before/after valid alias resolution | Same applicable semantic verdict |
| Invalid Core through actual orchestration | No subsequent context, Timing, composer acceptance or final delivery |
| Independently valid Core and valid timing pair | Existing ownership/action contracts unchanged |

The early and late applicable checks must agree on the invariant. Do not invoke a final-stage validator with fabricated Timing fields merely to simulate a Core result.

Test the real acceptance path with a strict non-network transport stub that fails if called. Record how a captured invalid Core is injected offline and where execution stops. No fabricated session ID/remote receipt may be reported as a real call.

The historical invalid output must **remain invalid after repair**. A corrected hand-authored derivative can test valid field placement but must be labeled `TEST_DERIVATIVE_NOT_MODEL_OUTPUT`; never overwrite the raw file or call it a repaired historical model success.

Run focused tests, full repository tests, lint and diff checks in offline/non-production mode using existing tools. Record unavailable tests honestly. No live service test is authorized just because it is included in a broad test suite.

A code/regression PASS means detection and contract implementation passed. It does not establish new-model emission quality, complete generalization or deployment readiness.

## 9. Offline audit of all preserved outputs

Audit all **64 Core rows**, not only NEON, and all stage-applicable checks on **52 Timing rows**. Keep an explicit inventory:

```text
raw artifact
original schema / prompt / receipt hash
run / stage / batch / issuer
original verdict
new offline verdict
new validator code/hash
error cause / field path / applicability
```

Original files are immutable. Re-run current checks into separate derived audit outputs.

Do not require every historical row to become PASS; the known invalid row is expected to remain rejected. New failures must be reported with original/current rule differences, not silently fixed.

For C, distinguish the 16 existing Core rows and 4 Timing rows from a full completed run. C's timing subset and any offline derived composition are never counted as a finished C. Any render/composer reconstruction needed for diagnosis is file-only, clearly `OFFLINE_RECONSTRUCTED`, and excluded from original-output counts.

Report denominators: raw rows, identity-valid rows, checked rows, failed rows, not-applicable and not-measured checks. A zero violation counter with zero tested rows is not PASS.

## 10. Descriptive boundary review; no calibration change

Compare all supplied Core runs at issuer level, including the C raw output, without promoting C into an accepted full run.

Deliver two views:

1. FIRST/A/B complete historical runs — descriptive comparison.
2. FIRST/A/B/C raw Core records — descriptive diagnosis with C provenance limitations.

For each issuer compare direction, balance, HOLD lean, confidence, dominant evidence, material anchors, buy/sell driver references, Unknown treatment, rationale, new-buyer/holder views and invalidation conditions.

Resolve aliases to canonical evidence identity before comparison. `E02` can mean different facts in different contexts. Preserve literal prompt hashes and report whether requests were truly identical; do not assume identity-only variation or semantic equivalence.

Classify supported causes, allowing uncertainty:

```text
ADJACENT_BUCKET_CALIBRATION_VARIANCE
MATERIAL_EVIDENCE_SELECTION_VARIANCE
CURRENTNESS_OR_UNCERTAINTY_INTERPRETATION_VARIANCE
TRUE_REASONING_DIVERGENCE
MIXED
INSUFFICIENT_EVIDENCE
```

The seven previously observed A/B→C crossings are RMD, AA, TDW, 014820, 318060, 106240 and 263750. Recompute rather than targeting that count. No direct BUY↔SELL reversal was observed in the reviewed artifacts; verify from raw rows.

Do not copy the earlier cohort's zero evidence-variance finding into this cohort. Do not compare 8/16 in the old cohort with 7/16 here as an improvement rate.

Do not compute or promote a formal new stability PASS from this partial experiment. Proposed calibration/input changes belong in the next decision memo, not this patch.

## 11. Message-quality audit of the 48 complete messages

Use FIRST/A/B's 48 preserved `composed-state.json`, `rendered-message.txt` and lineage artifacts. Preserve the original message-quality audit and its **advisory** status.

Produce a full inventory plus representative line-linked examples. Separate:

- Required/safe repeated headers and action wrappers.
- Repeated substantive model reasoning or reevaluation conditions.
- Renderer-introduced duplication.
- Generic wording inherited from sparse supplied inputs.
- Issuer-specific facts present in supplied inputs but omitted from reasoning/message.
- Facts available elsewhere in collected data but not supplied to Core — **deferred input-coverage issue**, not a reason to invent them in a message.

For each material finding, trace:

```text
source/packet if available → actual Core input → Core output
→ Timing → composed state → rendered message
```

Use `UNKNOWN_OR_NOT_AVAILABLE_IN_BUNDLE` if the trace cannot be completed. Do not assign every repetition to the renderer simply because it appears in rendered text.

Audit conclusion/explanation alignment, absolute direction vs Daily Delta, Unknown limitations, and issuer-specific next checks. This is quality diagnosis, not stylistic rewriting. No synonym substitution or name/number insertion merely to defeat a repetition detector.

Do not broaden this into independent investment analysis or enrich the packets with the seven-stock review. List the deferred input-coverage discussion as an explicit follow-up decision before any broad message rewrite.

## 12. Read-only existing-code integration inventory

Inspect, without calling production actions, the current modules for:

```text
initial analysis / read-only source preparation
explicit registration / versioned baseline
bootstrap enrichment / readiness
daily event and earnings comparison
Directional Core / Price-Timing / composer / renderer
warning / assessment persistence
scheduler / fallback / send ownership
```

For every integration boundary record:

```text
actual module/function
current caller
shared vs experiment-only implementation
input/output contract
side effects
existing tests
verified / not inspected / unresolved
minimal future adapter or test requirement
```

Do not assert that bootstrap code is absent merely because its integration proof is absent. Do not assert production completeness from an available endpoint.

Output a minimal non-production integration plan and proposed tests for:

- Baseline creation is not a Daily Delta.
- Registration requires explicit user intent; stored-but-incomplete is not monitoring-ready.
- Existing thesis versions and warnings are not overwritten by an initial absolute judgment.
- No new evidence / missing refresh is not automatically “no material change.”
- Idempotent baseline, assessment and delivery behavior at the existing contracts.
- Existing and new issuers can use the same decision/message contracts without losing lifecycle distinctions.

This phase is inventory and planning only: no production merge, registration, DB migration, new scheduler, or hidden send path.

## 13. Exposure, evidence integrity and paused operations

S1's whole cohort is **FULLY_EXPOSED / RETIRED_FOR_ARCHITECTURE_REPAIR**:

```text
RMD NEON AA TDW
066900 079370 247540 183300
014820 318060 106240 263750
170900 039980 026960 251970
```

Verify these issuer identities against the experiment exposure ledger; append missing whole-cohort exclusions idempotently in experiment artifacts only. S1 recorded 149 exclusions before appending the current cohort and `newly_excluded_current_cohort_count=0`. Do not assume the current count must be 165; deduplicate canonical issuer/share-class aliases and any later history.

No model replay, selective C continuation, fresh issuer selection or source lock creation is authorized. Local offline fixtures are not new unseen evidence.

Maintain the user's approved US/KR pause. Reuse existing observation methods for the exact eight approved objects; do not create a scheduler management project. If already paused, mutation count is zero. If one exact approved path is unexpectedly active, only the already-authorized pause may be restored with before/after evidence. Do not kill running jobs, remove stored investment logic, alter unrelated jobs or auto-resume.

Outside that narrow pause maintenance:

```text
model calls (real / fictional / judge) = 0 / 0 / 0
provider/source fetches = 0
paid data service change = 0
new free-API management gate = 0
main merge / deploy = 0 / 0
production DB / send / registration mutation = 0 / 0 / 0
live V2 / Structured Autonomy activation = 0
Night Futures change = 0
automatic monitoring resume = 0
```

No credential discovery or env-file copy is needed for the offline audits. Do not emit key/token values. Retain raw historical evidence only after the existing secret policy check; label any redacted derivative instead of calling it exact raw.

## 14. Reporting, artifacts and completion contract

Suggested result ZIP:

```text
thesis-monitor-20260908-unknown-field-consistency-early-core-validation-offline-evidence-review-report.zip
```

Keep the bundle focused: include evidence used in findings and changed-path regressions, not recursively nested copies of every old ZIP.

Required artifact groups:

| Group | Required contents |
|---|---|
| Authority | Repository provenance, S1 checksum/index verification, source manifest |
| Repair | Actual call graph, root-cause proof, contract table, bounded diff, tests, prompt/hash change ledger |
| Early stop | Exact NEON regression, positive/negative synthetic offline fixtures, actual-path no-next-call trace |
| Historical audit | 64-Core/52-Timing inventory and results, errors with original/current classifications |
| Stability review | Issuer/evidence/field comparison and descriptive-only findings |
| Message review | 48-message inventory, source-to-message trace, repetition/specificity findings |
| Integration | Actual module boundary inventory and proposed non-production tests |
| Workflow | Updated canonical master path, before/after delta, stage states and next decision |
| Integrity | Paused-state observation, side-effect counts, completion.json, artifact-index.json |

Completion must distinguish:

```text
implementation_result
offline_regression_result
historical_invalid_output_still_rejected
early_core_detection_result
model_emission_effectiveness = NOT_MEASURED
formal_current_cohort_stability = NOT_MEASURED
ownership_generalization = NOT_ESTABLISHED
message_quality_original_advisory
message_quality_review_completion
integration_inventory_completion
production_readiness = NOT_READY
```

Also record actual run accounting for the historical evidence:

```text
historical C attempted contexts = 5
historical C completed full runs = 0
transport failures = 0
context semantic failures = 1
```

New findings may change diagnostic counts; never falsify original evidence to match expected totals.

Final metadata must contain actual commits, hashes, test commands/results, scope changes, exclusions, operation counts and next_scope. Freeze completion and all payloads before indexing. Index every payload except the index itself; reopen the final ZIP and verify hashes/sizes. Emit the whole-ZIP SHA-256 after packaging and do not put a self-referential checksum inside it.

## 15. Decision and stop rules

- Untrusted/missing/corrupted source: stop affected repair/audits; do not invent history.
- Root cause cannot be confirmed in current code: no speculative patch; finish safe independent reviews.
- Repair requires broad schema/decision/source changes: stop that mutation, provide a bounded design decision.
- Focused/full offline regression fails: do not proceed to production or new model testing.
- New historical semantic problems appear: preserve and classify; no same-task broad tuning.
- Bounded repair and offline review pass: proceed **next**, under its own instruction, to non-production integration + decision/message quality review. Do not launch a real proof automatically.
- If review confirms that substantive input/reasoning changes are necessary, route the next task to that bounded decision before claiming message-only remediation is sufficient.

Task success is **CODE + OFFLINE EVIDENCE REVIEW COMPLETE**, not a financial recommendation, stable model, full generalization or monitoring-ready deployment.

## 16. Final operating principle

Fix the field contract where it is produced; reject the same contradiction immediately after Core; preserve valid negative facts and genuine Unknowns separately.

Use the existing 64 Core rows, 52 Timing rows and 48 complete messages to decide what integration and reasoning/message changes are actually needed. Do not spend another fresh cohort merely to rediscover a deterministic validation gap.

Source sufficiency, model-output consistency, repeated judgment stability, investment-information completeness, message specificity and production readiness are separate claims. The master workflow must keep them separate.
