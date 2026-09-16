# M12CG-R4-R1 Independent Frozen-Core Binding Offline Closure

## Result

`M12CG_R4_R1_INDEPENDENT_BINDING_OFFLINE_CLOSURE_PASS`

R4's measured 9/9 positive result is preserved without reinterpretation. R4-R1 closes the
remaining trust-boundary condition: numeric allowance at finalization and artifact reading is
now derived only from a separately loaded and validated Fundamental Core batch. The accepted
artifact cannot grant that allowance from its own serialized Core fields.

## Frozen-Base Observation

- Required R4 base: `e15aefdf2bc8ce880482304adcee43c95d4579f0`
- Work-instruction commit: `920ae64b424c56dc73a7c1090c251bc66695e933`
- Binding implementation: `0946d663`
- Successor-owner accounting: `6c7ca2fb`
- Frozen-base reader test without an independent Core argument: 1/1 PASS

The frozen-base PASS confirms the missing reader binding: a self-contained numeric artifact
could be revalidated using the Core serialized inside that same artifact. It does not invalidate
R4's positive payloads; it shows that their reader provenance had not been independently proven.

## Binding Repair

- The finalizer continues to compare Stage-2 Core rows to the separately loaded `core_temp` batch.
- The job now forwards that same validated batch into its post-write artifact reader.
- The artifact reader compares serialized Core rows against the supplied independent batch and
  constructs numeric scope only from the independent rows.
- Without an independent batch, nonnumeric legacy artifacts retain strict validation while
  numeric Core-copy claims remain rejected.
- The delivery reader loads the existing `core_temp` path and safe-suppresses when it is missing,
  malformed, stale or inconsistent. No new authority, schema, ledger or discovery convention was
  introduced.

## Independent Replay

The replay read the original M12CE Core-stage files directly, not R4's generated
`trusted-core.json` files.

- Independent Core sources: 3/3 whole-file SHA-256 matches
- Core batch scope validation: 3/3 PASS
- Core semantic validation: 9/9 PASS
- Core equality with materialized Stage-2 output: 9/9 PASS
- Finalization: 3/3 batches, 9/9 READY
- Accepted-plan parity with R4: 9/9
- Renderer parity with R4: 9/9
- Artifact canonical-byte parity with R4: 3/3
- Reader round-trip with independent Core: 3/3
- Existing R4 seven-artifact parity: preserved
- GOOGL/HUT accepted plans: preserved

## Negative Proof

The repaired tests separately cover:

- candidate/Core numeric mutation against unchanged original Core;
- coordinated Core/candidate/plan mutation against unchanged original Core;
- missing or wrong Core batch identity;
- actual job `validate_output` with original `core_temp` retained;
- serialized artifact Core/candidate/plan/block self-consistency;
- accepted-plan tampering after materialization (the original F17 obligation);
- raw serialized trust/permission injection;
- standalone, Stage-2 and adjudication numeric strictness;
- delivery forwarding and missing-Core safe suppression;
- missing required proof-node aggregation.

All intended gates reject with their exact existing error family before receipt or delivery
acceptance. No blanket `CANDIDATE` numeric bypass was added.

## Validation

- Binding regressions: 8 passed
- Focused: 299 passed, 1 skipped
- Full: 4151 passed, 63 skipped, 2 deprecation warnings
- Treasury: 79 passed
- Kiwoom: 70 passed
- Ruff: PASS
- `git diff --check`: PASS

One focused attempt used a manually forced `/tmp` basetemp. On macOS that resolved to
`/private/tmp`, outside the session's `tempfile.gettempdir()` boundary, so 18 persistence tests
correctly failed the ephemeral-path guard. The canonical focused rerun used pytest's default
temporary root and passed; the setup-invalid attempt is retained separately and is not counted as
product evidence.

## Safety

- External model calls / Full22 generations: 0 / 0
- Production sends / intents / DB mutations: 0 / 0 / 0
- Main merge / deployment / remote push: 0 / 0 / 0
- Scheduler changes / Kiwoom live actions: 0 / 0
- Model-facing prompt/schema/catalog changes: 0

`new_full22_authorized=false`

`deployment_readiness=NO`
