# M12CG-R1 Source Recovery and Offline Proof Reconciliation

## Result

`M12CG_R1_RUNTIME_REPAIR_REQUIRED`

M12CG remains `NO_GO`. This task made no runtime behavior change and did not call a model,
run Full22, touch production storage, resume a scheduler, send a message, or contact Kiwoom.

## Proven closed

- M12CB through M12CG source ZIPs: 6/6 SHA, CRC, path, duplicate-entry, and manifest PASS.
- Historical source map: 62/62 rows bound to immutable M12CB output bytes.
- Historical replay: 62/62 rows materialized and validated under the frozen M12CG runtime.
- M12CD deterministic date parity: 62/62.
- Historical provenance population: 60 `CONCRETE_ONLY`, 2 `CONCRETE_WITH_SYMBOLIC_REFS`.
- Original `010120` wrong-date row remains invalid; its model-free R2 copy derives `2026-08-12`.
- Fresh M12CE replay: 42/42 rows, 9/9 candidates, zero semantic field changes.
- The original 42 false row-preservation flags were a harness comparator scope error: the
  candidate-only stripping helper was applied to a row, so runtime-owned `as_of` and
  `provenance_status` were not removed before comparison.
- Raw `as_of` (including JSON null) and raw `provenance_status` are rejected at ingress.
  The prior failed assertion expected a nonexistent diagnostic token; runtime rejection was correct.
- Legacy and R2 parser roundtrips have equal model dumps, canonical bytes, and canonical hashes.
  Pydantic object equality was false only because defaulted fields changed `model_fields_set`.
- GOOGL/HUT finalization errors reproduce identically on exact pre-M12CG and current runtimes,
  so they are baseline-parity numeric rejections rather than an R2 regression.
- Identical frozen-input prompt, schema, and ref-catalog bytes are unchanged across runtimes.

## Runtime blocker

`M12CG_R1_SYMBOLIC_MISSING_METADATA_BOUNDARY_GAP`

The typed context and full materializer still accept `canonical:financial_quality:latest`
after `source_period` is deleted from the structured statement. The classifier uses
`statement.get("source_period") is None`, which treats a missing key as equivalent to an
intentional explicit null. The same helper-level issue exists for missing earnings
`period_label` and `period_type`.

The bounded repair is to require presence plus explicit null for those producer-owned keys,
then rerun this complete offline proof. No producer allowlist, ticker branch, inferred date,
or blanket symbolic rejection is warranted.

## Architecture decision

`DIFFERENT_RECEIPT_OWNER_OR_REQUIREMENT_NOT_APPLICABLE`

Accepted-v2 uses `AcceptedDecisionPlan`, an orchestration receipt
`v2-accepted-production-receipt-v1`, and state advancement after completed delivery.
`canonical_acceptance_receipt_service` instead accepts a trusted `DirectionalCoreCandidate`
from `canonical_two_stage_finalizer_v1` and owns a different persistence architecture.
There is no supported bridge in the frozen runtime. Canonical receipt isolation is therefore
`NOT_APPLICABLE_PENDING_CHAT_DECISION`; duplicate delivery intent remains `NOT_PROVEN` because
the real delivery path was intentionally not executed.

## Denominators

- R2 normalized subjects: 9
- V1-normalizable subjects: 8
- New-only finalized: 7
- Paired finalized/renderer comparisons: 6
- SKHY old baseline: `NOT_AVAILABLE_OLD_NORMALIZER_REJECTED`
- Corrected renderer label: `PARTIAL_PASS_6_PAIRED_OF_9_SUBJECTS`

## Validation

- Focused: 178 passed, 1 skipped
- Full: 4084 passed, 63 skipped, 2 deprecation warnings
- Treasury: 79 passed
- Kiwoom/local: 70 passed
- Ruff: PASS
- `git diff --check`: PASS

## Safety and readiness

- Runtime source changes from required base: 0
- External model calls / Full22 generations: 0 / 0
- Production send / intent / DB mutation: 0 / 0 / 0
- Main merge / deploy / scheduler resume / remote push: 0 / 0 / 0 / 0
- Kiwoom read / order / modify / cancel: 0 / 0 / 0 / 0
- `source_coverage_ready=true`
- `offline_compatibility_ready=false`
- `new_full22_authorized=false`
- `message_model_contract_readiness=NOT_READY_PENDING_BOUNDED_RUNTIME_REPAIR_AND_CHAT_RECEIPT_DECISION`
- `deployment_readiness=NO`

Work-instruction commit: `28d640856f0bd3c6d1655d260f6f043562325eaf`.
Audit implementation commit: `473499ebc82bffcdcd167f4249a2d5a52996640a`.
The final local SHA is captured after this documentation commit in the immutable report bundle.
