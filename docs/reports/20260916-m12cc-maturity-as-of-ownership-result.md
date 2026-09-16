# M12CC Stage-2 Maturity `as_of` Ownership Result

## Result

```text
top_level_result = MATURITY_AS_OF_MODEL_OWNERSHIP_DESIGN_GAP
ownership = DETERMINISTIC_PROVENANCE_FIELD
full22_generation = NOT_STARTED_BY_DESIGN
model_calls = 0
message_model_contract_readiness = NOT_EVALUATED_BY_DESIGN
next_scope = BOUNDED_MATURITY_AS_OF_OWNERSHIP_MIGRATION_DESIGN
```

This is the required Track 0B fail-closed completion, not a Full22 proof failure. The mandatory
semantic-ownership and Git-history audit found no downstream investment decision, renderer,
accepted-plan, or persisted-state consumer that treats `driver_maturity.as_of` as a meaningful
model choice. The field is model-authored historically, but its only live functions are typed
validation, same-row evidence-date validation, candidate hashing, and raw artifact retention.

## Repository

```text
branch = codex/20260916-m12cc-stage2-maturity-as-of-ownership
base = 978eced97e80d3f1f5f896f53dd317088f4f4a41
origin/main observed = 9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479
work-instruction commit = 7766b29
implementation SHA = NOT_APPLICABLE_OWNERSHIP_BRANCH_STOP
main merge = 0
deploy = 0
remote push = 0
```

The exact work-instruction Markdown SHA-256 is
`a8ce3155203809e46e8627559ab8c40914a6eb1b4d14bc0e06a0f8a78d514309`; the supplied instruction
ZIP SHA-256 is `3d5dca07d609f9f91e0dbd008ad7be4b4d5ab99af60bb25ec1759af5793f1dd1`.

## M12CB Integrity

The authoritative M12CB bundle passed independent verification:

```text
SHA-256 = 86d9a40debc253b1a2a155fe260962f701274bc7a75d17bf3c744ab3871bcddb
manifest artifacts = 262
ZIP entries = 263
missing / extra = 0 / 0
hash / size mismatch = 0 / 0
secret scan failures = 0
```

M12CB target-scope convergence remains frozen as PASS. Its SNDK, TSLA, and TSM frozen-core
claim-language repair was not reopened.

## Ownership Audit

The canonical date ownership chain already exists:

```text
concrete_evidence_date
  -> evidence-local resolved_as_of_date
  -> accepted_v2_stage2_ref_catalog_manifest maturity_ref_dates
  -> same-row cited-ref ownership validation
```

Git history shows:

- `5aed685` introduced `as_of` as a model field.
- `209e1eb` integrated it into the candidate.
- `eb24f37` added the typed evidence-local date owner and same-row deterministic gate.
- No commit establishes investment semantics for selecting among multiple same-row owned dates.
- No production renderer or accepted decision plan consumes the selected value.

Accordingly, adding stronger prompt wording or a larger schema would preserve duplicate model
authorship instead of repairing the actual ownership boundary. Removing that duplication requires
an explicit output-contract compatibility and migration design, which M12CC did not authorize.

## Failure Forensic

The immutable M12CB `010120` row remains invalid without modification:

```text
generation = 20260916-uskr22-m12cb-20260916T041207Z-dcaac603f11e
cited ref = decision-evidence:e3e0e73c7b80428e5459
same-row owned date = 2026-08-12
emitted as_of = 2026-09-15
classification = CONCRETE_BUT_UNOWNED_DATE
validator = FAIL maturity_evidence_date_not_owned
source output SHA-256 = 946eff418eeb984da56b618a377f86ca9981c573ab39d9635a1cc4e1f6548bf9
source bytes modified = false
```

This confirms that the existing validator is correct. The defect is the redundant model-owned
output field, not a need to loosen the same-row ownership gate.

## Deterministic Proof

The fixture matrix covers:

- one ref / one owned date: PASS;
- multiple refs / same owned date: PASS;
- globally valid but same-row-unowned date: rejected as `CONCRETE_BUT_UNOWNED_DATE`;
- another ticker's owned date: rejected;
- global-catalog-only date: rejected;
- noncanonical or symbolic date: rejected;
- future date: rejected;
- unresolved owner: rejected;
- unknown ref: rejected;
- ref/date pair swap: rejected;
- historical M12CB bad output: still rejected.

The multiple-ref / different-owned-date fixture is explicitly
`NOT_RUN_BY_OWNERSHIP_BRANCH`: history did not prove meaningful model selection, so M12CC did not
invent that policy.

## Model And Schema Boundary

Baseline model-facing measurements were recorded before stopping:

```text
max schema bytes = 60,934
max prompt bytes = 174,291
max combined bytes = 235,225
max ref/date pairs = 166
oneOf / anyOf / total branches = 0 / 5 / 10
```

Candidate schema growth and runtime feature support are
`NOT_MEASURED_OWNERSHIP_BRANCH_STOP`. Prompt changes, schema changes, semantic policy changes,
ticker/date exceptions, assessment-date defaults, and latest-date defaults are all zero.

## Validation

```text
focused pytest = 115 passed
full pytest = 4055 passed, 63 skipped, 2 existing warnings
Ruff = PASS
git diff --check = PASS
historical bad output reinterpreted = 0
```

GOOGL pre-confirmation, SNDK/TSLA/TSM Stage-2 ownership, maturity polarity/atomic identity,
exact-ref, typed contract, Treasury, and local Kiwoom regressions remain frozen PASS. The Kiwoom
gateway remains unconfigured; live read/order/modify/cancel counts are `0/0/0/0`.

## Operating Safety

```text
new generation ID = null
planned / started / completed / usable model calls = 0 / 0 / 0 / 0
retry / fallback / judge / repair / selective rerun = 0 / 0 / 0 / 0 / 0
production DB mutations = 0
production sends = 0
scheduler mutations / resumes = 0 / 0
main merges / deployments / remote pushes = 0 / 0 / 0
```

## Final Gate

```text
MESSAGE_MODEL_CONTRACT_READINESS = NOT_EVALUATED_BY_DESIGN
MARKET_CONTEXT_READINESS = LOCAL_PASS_LIVE_KIWOOM_UNAVAILABLE
DEPLOYMENT_READINESS = NO_BY_PHASE_BOUNDARY
M12CC_RESULT = MATURITY_AS_OF_MODEL_OWNERSHIP_DESIGN_GAP
NEXT_SCOPE = BOUNDED_MATURITY_AS_OF_OWNERSHIP_MIGRATION_DESIGN
```

The next task should design a compatibility-safe migration in which `as_of` is derived from the
canonical same-row evidence owner instead of authored independently by the model. It must decide
how multi-date rows are represented, how hashes and stored artifacts migrate, and how old outputs
remain replayable before any new Full22 proof is authorized.
