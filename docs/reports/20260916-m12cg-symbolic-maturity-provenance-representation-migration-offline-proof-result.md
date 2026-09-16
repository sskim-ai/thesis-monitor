# M12CG Symbolic Maturity Provenance Migration Offline Proof

## Result

```text
M12CG_RESULT = M12CG_REQUIRED_SOURCE_COVERAGE_FAILURE
IMPLEMENTATION = R2_IMPLEMENTED_AND_FRESH_REPLAY_PASS
MESSAGE_MODEL_CONTRACT_READINESS = NOT_READY_REQUIRED_OFFLINE_EVIDENCE_REPAIR
DEPLOYMENT_READINESS = NO
```

The bounded R2 representation is implemented on the local integration branch. It keeps the raw
model contract unchanged, adds explicit normalized v2 dispatch, derives nullable maturity
provenance from ticker-local same-row evidence, and independently validates the derived date/status
pair. No model call, Full22 generation, production send, DB mutation, scheduler change, merge,
deploy, or remote push occurred.

## Repository

```text
branch = codex/20260916-m12cg-symbolic-maturity-provenance-offline-migration
required base = 912b1ce6c46f0caf801b2c620b42d904b489c4e7
work-instruction commit = ef5a0ad12bac733ec5ab5220db258a86e912665b
implementation commit = b7e541b6a3c54567018f937f32d6f92be09a7e4e
work-instruction SHA-256 = 327175d2657e7b85c0f23b6e0ba9999ecdadcee3a185942cb2aca5c1a6a04486
origin/main observed by M12CF = 9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479
```

## Contract

```text
raw model output = v2-accepted-stage2-model-output-v2 (unchanged)
legacy normalization = stage2-maturity-as-of-deterministic-v1
R2 normalization = stage2-maturity-as-of-deterministic-v2
legacy normalized output = v2-accepted-production-output-v1
R2 normalized output = v2-accepted-production-output-v2
legacy artifact = v2-accepted-production-artifact-v1
R2 artifact = v2-accepted-production-artifact-v2
```

The R2 states are `CONCRETE_ONLY`, `CONCRETE_WITH_SYMBOLIC_REFS`, and
`SYMBOLIC_ONLY_NO_CONCRETE_DATE`. Raw model-authored `as_of` or `provenance_status` is rejected
before materialization. Legacy readers retain strict v1 behavior and unsupported versions fail
closed.

## Fresh Replay

The three completed immutable M12CE Stage-2 batches were replayed offline:

```text
subjects = 9
maturity rows = 42
CONCRETE_ONLY = 41
SYMBOLIC_ONLY_NO_CONCRETE_DATE = 1
Stage-2 validation = 9/9
raw semantic field changes = 0
driver row loss = 0
atomic claim/polarity changes = 0
```

SKHY retains all five maturity rows. Its decisive financial-quality limitation is represented by
`as_of = null` and `SYMBOLIC_ONLY_NO_CONCRETE_DATE`. The immutable v1 replay still rejects that row
for having no concrete owned date, as expected.

Eight candidates have a v1-normalized comparison and all eight receive the expected candidate hash
change. Six candidates complete both old and new accepted-plan paths; their investment semantics and
renderer text are unchanged while identity hashes change. SKHY has no v1 normalized baseline.
GOOGL and HUT retain pre-existing historical adjudication numeric-validation failures and therefore
are not counted as accepted-plan comparisons.

## Blocking Evidence

The required M12CD report ZIP with SHA-256
`89d51179aca722ce38b282c51d3fedb34ea6446df8c6c6ea71bb8e5cf74951ff` is not available locally.
M12CF contains only two verified mixed-row excerpts from the expected 62-row historical inventory.
The other 60 rows cannot be reconstructed or declared compatible by inference.

The accepted-v2 artifact/state path proves version dispatch, strict cross-version parsing, isolated
state roundtrip, and same-version idempotency. The supplied evidence does not expose an executable
bridge from that artifact to `canonical_acceptance_receipt_service`, so cross-version receipt
authentication and delivery-intent neutrality remain `NOT_PROVEN`.

These are formal M12CG PASS requirements. The implementation remains local, but the result cannot be
promoted to `M12CG_SYMBOLIC_MATURITY_PROVENANCE_REPRESENTATION_MIGRATION_OFFLINE_PASS`.

## Validation

```text
focused = 214 passed, 1 skipped
full = 4080 passed, 63 skipped, 2 existing warnings
Treasury = 69 passed
Kiwoom local = 32 passed
Ruff = PASS
git diff --check = PASS
```

## Next Scope

Recover the exact M12CD bundle, verify its manifest, and replay all 62 rows. Then exercise the
canonical receipt/delivery-dedupe boundary through an existing approved extension point. No new
model call or Full22 generation is authorized by this result.

