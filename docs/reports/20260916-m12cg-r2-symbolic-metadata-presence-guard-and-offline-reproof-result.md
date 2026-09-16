# M12CG-R2 Symbolic Metadata Presence Guard and Offline Reproof

## Result

`M12CG_R2_GUARD_REPAIR_PASS_OFFLINE_CLOSURE_PENDING`

The authorized one-file runtime guard repair is complete. The canonical symbolic maturity
classifier now requires producer-owned nullable metadata keys to be present and explicitly
JSON null. Missing `source_period`, `period_label`, or `period_type` no longer qualifies as
valid symbolic provenance. Valid explicit-null financial-quality and earnings placeholders
retain their prior behavior.

The broader offline migration is not declared complete. Native accepted-v2 artifact binding
and isolated state roundtrip pass, but no authorized delivery route or intent ledger was
executed. Delivery continuity and duplicate-intent suppression therefore remain `NOT_PROVEN`,
and original fixture N17 remains partial. GOOGL and HUT also retain their pre-existing
`adjudication_introduced_unregistered_numeric` finalization failures.

## Proven Repair

- Runtime file changed: `app/services/evidence_maturity_pricing_service.py` only.
- Runtime symbol changed: `symbolic_maturity_evidence_kind` only.
- Guard implementation SHA: `50dcec1a56a81db1ebc7e23a322e69f9b028323a`.
- Explicit-null preservation: PASS.
- Missing financial-quality `source_period`: rejected by classifier and materializer.
- Missing earnings `period_label` / `period_type`: rejected by classifier/projector.
- Forged normalized symbolic projection: rejected by the independent validator.
- Invalid non-null primitive/container variants: rejected without coercion.
- Concrete peer plus invalid symbolic ref: rejected rather than ignored.

The frozen before-repair runtime reproduced the defect. The pre-patch control had 8 expected
failures and 18 passes; the repaired guard matrix passes G01-G14 across 47 variants.

## Valid-Input Neutrality

- Historical replay: 7 batches, 20 candidates, 62 rows.
- Historical original negative: 1, preserved separately.
- Historical date parity failures: 0.
- Fresh replay: 3 batches, 9 candidates, 42 rows.
- Normalized candidate hash changes: 0.
- Semantic/validation changes: 0.
- Prompt/schema/catalog byte changes: 0.
- Legacy-normalizable subjects: 8.
- New v2 finalizations: 7.
- Legacy-v2 accepted-plan/renderer comparisons: 6.
- Before-R2 versus after-R2 successful-finalization parity: 7.

The N16 negative control deletes the decisive symbolic SKHY row from the actual full normalized
candidate payload. The semantic comparator detects the loss and records both source and mutated
payload hashes. Atomic polarity mutation is independently rejected for N22.

## Owner Boundary

The accepted-v2 delivery route uses its native artifact loader and post-delivery state owner.
It does not directly use `canonical_acceptance_receipt_service`; no synthetic bridge was added.

- Artifact packet/claim/scope/hash and rendered-block tamper rejection: PASS.
- Legacy/new version dispatch: PASS.
- Isolated state roundtrip and same-version byte idempotency: PASS.
- Actual delivery route: NOT RUN.
- Operational continuity: NOT PROVEN.
- Duplicate delivery intent suppression: NOT PROVEN.

## Fixture Accounting

- Required fixtures: 35 (`P01-P13`, `N01-N22`).
- Proven: 34.
- Not proven: 1 (`N17`).
- Failed: 0.
- Unsupported group-only PASS: 0.

Focused and full JUnit evidence is deduplicated by node ID and result. Executable aggregation
controls prove that failed, skipped/not-proven, absent, or zero-denominator children cannot
produce a parent PASS.

## Validation

- Focused: 210 passed, 1 skipped.
- Full: 4120 passed, 63 skipped, 2 dependency deprecation warnings.
- Treasury: 79 passed.
- Kiwoom/local: 70 passed.
- Ruff: PASS.
- `git diff --check`: PASS.
- Source bundles: 7/7 SHA, CRC, path, duplicate-entry, manifest size/hash PASS.

## Safety

- External model calls / Full22 generations: 0 / 0.
- Model retry / fallback / judge / selective rerun: 0 / 0 / 0 / 0.
- Production send / intent / DB mutation: 0 / 0 / 0.
- Main merge / deploy / scheduler resume / remote push: 0 / 0 / 0 / 0.
- Kiwoom live read / order / modify / cancel: 0 / 0 / 0 / 0.

## Remaining Blockers

1. `M12CG_R2_NATIVE_DELIVERY_CONTINUITY_NOT_PROVEN`
2. `M12CG_R2_N17_RECEIPT_SWAP_NOT_PROVEN`
3. `M12CG_R2_GOOGL_HUT_FINALIZATION_BASELINE_FAILURE`

These do not invalidate the targeted guard repair. They prevent promotion to owner-scoped
offline migration PASS and prevent authorization of a new Full22.

## Readiness

- `offline_migration_compatibility_status=PENDING`
- `new_full22_authorized=false`
- `message_model_contract_readiness=NOT_READY_PENDING_CHAT_REVIEW_AND_NATIVE_DELIVERY_CONTINUITY_PLUS_BASELINE_FINALIZATION_SCOPE`
- `deployment_readiness=NO`

Work-instruction commit: `a141e2711beedf43b1046369b4e821b2544abbdc`.
Guard implementation commit: `50dcec1a56a81db1ebc7e23a322e69f9b028323a`.
Audit implementation commit: `4cb2cf5fe048b82b5722c8ac45d93d6baccd7263`.
The final local SHA is captured after this documentation commit in the immutable report bundle.
