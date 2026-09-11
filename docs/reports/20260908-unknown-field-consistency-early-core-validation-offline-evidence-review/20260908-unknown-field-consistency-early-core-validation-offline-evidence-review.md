# Unknown-Field Consistency, Early Core Validation & Offline Evidence Review

## Final Result

`CODE_AND_OFFLINE_EVIDENCE_REVIEW_COMPLETE`

The deterministic Unknown-field defect is repaired at the Core acceptance boundary and remains checked by the final validator. The preserved S1 archive was audited without model calls, provider calls, candidate rewrites, production integration, or monitoring resume.

This result does not establish model emission quality, current-cohort stability, ownership generalization, or production readiness.

| Decision | Result |
|---|---|
| implementation_result | `PASS` |
| offline_regression_result | `PASS` |
| historical_invalid_output_still_rejected | `true` |
| early_core_detection_result | `PASS` |
| model_emission_effectiveness | `NOT_MEASURED` |
| formal_current_cohort_stability | `NOT_MEASURED` |
| ownership_generalization | `NOT_ESTABLISHED` |
| message_quality_original_advisory | `RECORDED` |
| message_quality_review_completion | `COMPLETE` |
| integration_inventory_completion | `COMPLETE` |
| production_readiness | `NOT_READY` |

## Authority

Source S1:

`thesis-monitor-20260908-authoritative-result-identity-reconciliation-us-source-expansion-proof-resume-report.zip`

Expected and actual SHA-256:

`2a58b8e8dbfcc6e3aa7cb4900bec2d16d29f149b69160e8fd0c5b0522f6a798e`

Independent checks:

| Check | Result |
|---|---:|
| ZIP members | 2,008 |
| Indexed payloads | 2,007 |
| Unsafe / duplicate members | 0 / 0 |
| Missing / unexpected index rows | 0 / 0 |
| Hash / size mismatches | 0 / 0 |
| Independent secret-scan failures | 0 |
| CRC | PASS |

Repository provenance at canonical evidence generation:

| Item | SHA / name |
|---|---|
| origin/main base | `d18e68b1e944d7749d093b08797fcd9498412680` |
| work-instruction commit | `3858f6a6b32f6e14a7337e135a4ddf7d5572a823` |
| preserved S1 merge | `d6679691a8771ad1449e46fa610136a5b291dd0d` |
| implementation commit | `df8ffb7858a9a1b5f30b77d72ca440121f142c15` |
| branch | `codex/20260908-unknown-field-consistency-early-core-validation-offline-review` |

Detailed authority receipt: `01-authority-integrity.json`.

## Root Cause

The exact historical C/NEON Core output contained a `CONFIRMATION_REQUIRED` Unknown with a non-empty `directional_negative_basis`. Its schema and old Core partial audit passed. The final combined validator later rejected it as `unknown_nonnegative_has_directional_basis`.

Actual call path:

```text
Directional Core prompt
→ alias expansion
→ Core partial audit
→ Price-Timing context
→ composer
→ final structured validator
```

The missing invariant was between alias expansion and acceptance of Core. Timing copied the frozen Core; it did not create the contradiction.

Exact failure provenance:

| Field | Value |
|---|---|
| run / stage / ticker | `C / DIRECTIONAL_CORE / NEON` |
| error | `unknown_nonnegative_has_directional_basis` |
| path | `unknown_treatments[0].directional_negative_basis` |
| normalized output SHA | `d48ded29b55da5a06ac5c4cbc90603c7e9e8c400ce34c1564dcf53a5eac08df5` |
| candidate mutation | 0 |

The historical negative fact remains evidence. The repair separates a confirmed negative fact from uncertainty about its current persistence; it does not sanitize the historical candidate or change NEON's investment direction.

## Contract Repair

One shared `unknown_treatment_consistency_issues` helper now owns the stage-independent invariant:

| Treatment | `directional_negative_basis` | Result |
|---|---|---|
| `CONFIDENCE_LIMIT` | empty | allowed |
| `CONFIRMATION_REQUIRED` | empty | allowed |
| either non-negative treatment | non-empty | reject |
| `DIRECTIONAL_NEGATIVE` | empty | reject |
| `DIRECTIONAL_NEGATIVE` | only missing/Unknown evidence | reject |
| `DIRECTIONAL_NEGATIVE` | provenance-backed non-Unknown evidence | allowed, subject to existing gates |

The Core partial audit applies the helper before any Price-Timing context can be spawned. The final validator reuses the same helper as defense in depth. Existing alias, issuer, domain, source, ownership, and hard-safety checks remain in force.

The Core prompt gained one generic field-placement sentence. No issuer example, directional threshold change, calibration retuning, ticker exception, renderer rewrite, or schema change was added.

Because prompt bytes changed, all four current prompt hashes differ from S1. Therefore:

```text
MODEL_EMISSION_EFFECTIVENESS = NOT_MEASURED
historical calibration transfer to edited prompt = false
```

See `02-call-graph-root-cause.json` and `03-prompt-hash-ledger.json`.

## Early-Stop Proof

The model-free regression matrix passed 10/10 cases:

1. Exact historical NEON invalid Core rejected at Core.
2. Confirmation-required context with empty negative basis accepted.
3. Confidence-limit item with a negative basis rejected.
4. Confirmed negative plus a separate follow-up Unknown accepted.
5. Missing-only evidence promoted to negative rejected.
6. Forbidden price reference in Core rejected.
7. Valid alias resolution preserved the same semantic verdict.
8. Nonexistent alias rejected.
9. Cross-issuer alias catalog rejected.
10. Independently valid Core/Timing ownership remained valid.

The orchestration test injects a captured invalid Core through the actual `execute_run` acceptance path with a strict non-network adapter. It observes one Core context, zero Timing contexts, zero renderer contexts, and an immediate `SemanticStop`. No remote receipt or session is fabricated.

See `04-offline-regression-matrix.json` and `evidence/exact-neon-invalid-core.json`.

## Historical Output Audit

| Stage | Raw rows | Identity valid | Checked | Failed | Alias parity | Not applicable / measured |
|---|---:|---:|---:|---:|---:|---:|
| Directional Core | 64 | 64 | 64 | 1 | 64 | 0 / 0 |
| Price-Timing | 52 | 52 | 52 | 1 | 52 | 0 / 0 |

Both failures are the same C/NEON contradiction propagated from frozen Core. The Core row changed from historical partial `PASS` to current early `FAIL`; the Timing row was already a final `FAIL`. No additional historical semantic failure appeared.

Historical run accounting remains:

```text
C attempted contexts = 5
C completed full runs = 0
transport failures = 0
context semantic failures = 1
```

The detailed 64- and 52-row inventories retain raw/prompt/schema/receipt/source hashes, original and current verdicts, validator hashes, error codes, and field paths.

See `05-historical-core-timing-audit.json`, `inventory/historical-core-64.jsonl`, and `inventory/historical-timing-52.jsonl`.

## Descriptive Boundary Review

FIRST/A/B are the three complete historical runs. C is a raw Core diagnostic only.

| Observation | Count |
|---|---:|
| Issuers compared | 16 |
| B→C absolute-direction crossings | 7 |
| B→C lean/balance-only changes | 1 |
| Direct BUY↔SELL reversals | 0 |

Absolute crossings: `RMD`, `AA`, `TDW`, `014820`, `318060`, `106240`, `263750`.

Lean/balance-only change: `247540`.

All eight reviewed changes are conservatively classified `MIXED` because the preserved fields can include both adjacent-bucket movement and evidence/Unknown selection changes. No formal stability PASS, improvement rate, majority vote, or calibration change is inferred.

See `06-boundary-review.json`.

## Message Quality

All 48 complete FIRST/A/B messages have a complete source → Core → Timing → composed state → rendered message trace. Candidate and renderer rewrites were both 0.

| Run | Original repeated substantive spans |
|---|---:|
| FIRST | 13 |
| A | 16 |
| B | 21 |

The original advisory status is preserved. Conclusion-alignment failures are 0/48, and no message labels an absolute cold-start judgment as Daily Delta. Repetition findings distinguish safe headers, model-owned substantive wording, and model content wrapped by the renderer. Facts collected elsewhere but absent from actual Core input remain a deferred input-coverage decision; they were not injected during review.

See `07-message-quality-review.json` and `inventory/complete-messages-48.jsonl`.

## Integration Inventory

Ten existing boundaries were inspected and verified without invoking them:

1. Explicit registration and versioned thesis continuation.
2. Initial read-only evidence preparation.
3. Versioned initial absolute baseline.
4. Bootstrap readiness and activation.
5. Daily event/earnings comparison and persistence.
6. Accepted V2 context preparation, validation, and generation boundary.
7. Directional Core / Price-Timing ownership and composition.
8. Structured validator and renderer.
9. Assessment and warning persistence.
10. Fallback, queue, and Telegram send ownership.

The minimal next design is a non-production adapter from lifecycle-qualified evidence to the shared decision packet, with explicit tests for baseline-vs-delta distinction, user-intent registration, version/warning preservation, missing-refresh semantics, and idempotent baseline/assessment/delivery behavior.

See `08-integration-inventory.json`.

## Exposure Retirement

S1 explicitly records all 16 issuers as `FULLY_EXPOSED / RETIRED_FOR_ARCHITECTURE_REPAIR`, but its source merged registry still had 149 rows and recorded `newly_excluded_current_cohort_count=0`.

The original S1 registry was not rewritten. A report-local reconciliation mapped the 16 packet issuer IDs to canonical SEC/OpenDART keys and appended all 16 missing issuers:

| Check | Result |
|---|---:|
| Source registry | 149 |
| Missing canonical issuers before | 16 |
| Appended | 16 |
| Reconciled registry | 165 |
| Missing after | 0 |
| Second-pass additions | 0 |
| Second-pass registry rows equivalent | true |

This cohort cannot be reused as unseen evidence or selectively continued.

See `09-exposure-retirement-review.json` and `09a-updated-exposure-registry.json`.

## Validation

| Check | Result |
|---|---|
| Focused tests | `329 passed` |
| Full repository pytest | `2746 passed, 1 third-party deprecation warning` |
| Ruff | PASS |
| `git diff --check` | PASS |
| Canonical offline audit | PASS |

The warning is Starlette's third-party `httpx` deprecation notice and is unrelated to this repair. No live-service test was run.

See `12-validation.json`.

## Operating Safety

Fresh read-only observation found all four approved Codex automations paused and all four LaunchAgents disabled/unloaded. Active natural jobs and running model processes were both 0. Scheduler mutations were 0.

```text
model calls (real / fictional / judge) = 0 / 0 / 0
provider/source fetches = 0
candidate rewrites = 0
production DB / send / registration mutations = 0 / 0 / 0
main merge / deploy = 0 / 0
live V2 activation = 0
Night Futures change = 0
automatic monitoring resume = 0
```

See `10-operating-safety.json` and `11-completion.json`.

## Decision

M1 is complete at the code and offline evidence level. The next bounded scope is:

`NONPRODUCTION_INTEGRATION_AND_DECISION_MESSAGE_QUALITY_REVIEW`

That next task must decide and freeze any input/reasoning/message change before spending another real cohort. It must not automatically run a new proof, register a subject, mutate production state, send a message, merge to main, deploy, or resume monitoring.
