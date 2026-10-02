# R2B-R5 Market Adapter and Monitoring-AI Closeout

## Decision

- Terminal: `A_MODEL_FAILURE`.
- Precise phase: local Core-to-A input composition, before any A dispatch.
- Failure: `source_input_expectation_authority_catalog_mismatch`.
- Market adapter closure: PASS for US and KR.
- Actual Market outputs: 2/2 validated and frozen.
- Actual Core outputs: 22/22 validated and frozen, comprising 21 ordinary
  evidence-based subjects and one existing SNDK `UNKNOWN_LIMIT` subject.
- A/B calls: 0/0. Rendered messages: 0/24.
- Comparison readiness: NO. Independent-assessment reveal gate remains CLOSED.
- The first failure ended execution. No hotfix, retry, selective rerun,
  fallback, judge or replacement candidate was used.

## Repository

| Role | Local identity |
| --- | --- |
| Branch | `codex/r2b-r5-market-adapter` |
| Base, R4 final | `4b216489c31c47ebc1f9efbb92da3a04b4766deb` |
| Instruction-first commit | `825aabfe963eaf8f4623bb33b89a65249b0726f1` |
| Initial implementation | `63a97972d2bf41a3479eddc154f81c1c13b9b5c3` |
| Native night numeric ownership | `8ea8cff19c462841a046501ecfcfdc37fd2a6163` |
| Exact validated dispatch commit | `bea5f6d93b638b1b8215098023994dc1697e197c` |
| Operating HEAD, unchanged | `b610e6de0a8c33d199961e821ff1b130e1fa9ad4` |

The final report-only commit is recorded in the bundle's
`repository-identities.json`; the report does not contain its own self-hash.
Full validation applies to the exact dispatch commit above. No claim of a
separate full-suite run at the final report-only commit is made.

Main merge, remote push, deploy and service restart: zero. No remote CI was
triggered because this instruction prohibits push. Operating checkout remained
clean. New audit modules are not wired into production imports.

## Immutable Source and Fairness

- REV10 ZIP: `5cd89052657b6d4d29d174415fa1ce3dd686ccf20a14ea342256feda28d9836a`.
- R4 ZIP: `fda4d4fdbe007df116b800de217ec3b85fd89e7bf61b4c08844a9daf2f9c1698`.
- Run seed: `df3b7f1102fcacd27b70e594fb58b139644a7ba1daa18620279bf1a455916bdc`.
- US source: `b2b603850e517c70d6a9a201b297952677d6542271f72db6f0eecbdebe09fdb1`.
- KR source: `d3081027ec1203a5af09adc590b13ca81dce3c049a65b988606a0d3311f74845`.
- Combined: `c4fbc25ec81abe61c3981bfaa44204cc7e15cc252f25cbe6aedc6b2a1de9b44f`.
- Authority graph: `0b69d1913e139078ed42b0fb1c0b01928b065fd2d76863e3835622b3ee0992b6`.
- Blind source ZIP: `d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3`.
- Quality supplement: `2d59748a3064a91d1ddcbbb68aefb90a961eaf4e9baa4334619c4e0db38f7edd`.
- Neutral V2 receipt: `9c9eec930400db3e7390984b6045e72961684e3db774eedd633b3f6fa1e9650d`.

All source hashes and the quality supplement were preserved. Blind fairness
remained `PASS_V2`: projected economic source objects match the facts already
present in the blind source ZIP. New economic source facts: zero. Independent
V1/V2 judgment contents were not opened. The neutral receipt alone was verified.

The source run is `rev8-live-20260927T083836Z`, with cutoff
`2026-09-27T08:41:28.502429+00:00`, completed US session 2026-09-25 and KR session
2026-09-23. This remains an ad-hoc sealed-source proof, not a natural production
run. Original publication dates were not relabeled as query time.

## Adapter Closure

`scripts/r2b_r5_market_adapter.py` implements a pure sealed-source projection
into the existing accepted Market consumer. It verifies the graph, seed,
attempt/value ownership, Class-C versions and explicit optional denials.
It delegates to native market observation, intelligence, numeric binding,
night-futures and temporal owners. It is not a second investment-policy engine.

The package includes required/optional contract inventory, leaf contract and
denials, field-by-field parity matrix, US/KR projections, current consumer
acceptance, historical shape-only parity and hashes. Historical inputs supplied
shape only, never current values or verdicts.

- US: 35 native facts; eligible 12, suppressed 23. Sealed observations did not
  contain return/prior values, so level-only rows could not imply direction.
  Existing `DATA_INSUFFICIENT` regime semantics were retained.
- KR: 82 canonical facts and 122 numeric aliases bound. Eligible 71, suppressed
  72 across the current consumer catalog. Native partial coverage remains
  partial; unavailable investor flow was not fabricated.
- Native night-futures and D/W/M numbers use their existing dedicated typed
  owner rather than being forced through the generic macro numeric registry.
- One optional scalar, `market:breakeven_inflation:T10YIE.fields.previous_level_pct`,
  has no existing generic numeric registration. Its exact source value stays
  in the explicit denial receipt and is not model-visible. Other unregistered
  generic scalars fail closed. No registry semantics were invented.
- Replay twice produced identical context/catalog/registry/coverage/session/
  prompt hashes. With network and production DB/cache entry points blocked,
  projection still matched. Provider calls and production DB/cache reads: zero.

## Stock Readiness and Freeze

Unchanged R4 stock preflight: Core/A/B 22/22 each; quality PRESENT 7,
RECONSTRUCTIBLE 14, NOT_APPLICABLE 1; quality-owner gaps 0; stored price-rule
versions 20/20; model-visible unclassified time references 0.

The unchanged R4 preflight artifact still labels its own Market check 0/2 and
`R2B_R4_PREMODEL_CONTRACT_DRIFT`. That artifact is used for stock regression
only. R5 Market acceptance is separately 2/2 in `dispatch-market/summary.json`.

Generation: `20260928-r2b-r5-20260928T012541Z`.
Whole-cohort binding: `ISSUED_WHOLE_COHORT_READY`, sealed before the first call.
It freezes exact code, source inputs, Market/Core requests, schemas, provider
wire, host qualification, decision modes and fairness identities. A/B requests
are dependent on fresh validated upstream results, with builders and policies
frozen first. A request freeze was not reached; B was never reached.

Preparation fixes were completed before first dispatch: native night-number
ownership was preserved, and an existing launch helper's historical host
contract JSON was restored byte-for-byte after clean-history migration had
omitted it. Original blob: `eaca7ae4ffa3d21ec758347bbc99cbedd66e9479` at
`f1c22493`; file SHA `9a65cc4768f86d4b05441c5a4d8db58f55b36e374314b47fa63c896683259de0`.
It records environment-policy names, not secret values. No auth semantics
changed. Earlier preparation folders are not model attempts or final evidence.

## Actual Execution

Official signed-in CLI, GPT-5.6 Sol / xhigh; per-call timeout 1200 seconds;
controller retry 0, semantic retry 0, repair 0, fallback 0, judge 0.

| Stage | Actual calls | Validated subjects | Output freeze |
| --- | ---: | ---: | --- |
| Market | 2/2 | 2/2 markets | YES |
| Core | 8/8 | 21 ordinary + 1 limit = 22/22 | YES |
| A | 0/8 | 0/22 | NO, local input failure |
| B | 0/8 | 0/22 | NOT REACHED |
| Render | 0 | 0/24 messages | NOT REACHED |

Total model calls: 10/26. All ten transport/output stages returned successfully.
There was no timeout or model rejection. Market began at
`2026-09-28T01:26:43.449016+00:00`; last Core completed at
`2026-09-28T01:45:05.042607+00:00`. Exact prompt/schema/output hashes and per-call
elapsed times are in the structural call ledger and transport receipts.

The existing CLI cannot certify hidden internal provider attempts; those remain
`UNOBSERVABLE_CLI_INTERNAL`. Controller attempts are exactly ten, with no retry.
The existing transport does not claim source-only inference certification.

## Root Cause and Test Gap

The first ordinary A subject is CORZ. The stopped stack is:

`Execution.before_a -> chain -> r2b_r2_preflight.subject_inputs ->`
`r2b_r2_contract.bound_chain -> freeze_source_use_input_expectation`.

`bound_chain` stores `catalog_sha256` using
`unified_snapshot_contract.digest`, whose JSON serializer uses
`ensure_ascii=False`. The source-use expectation validator compares that hash
against `m12da_source_use_contract.canonical_sha256`, using `ensure_ascii=True`.
New Core atomic-claim text can contain non-ASCII characters. Identical parsed
catalogs then have different serialized bytes and different SHA-256 values.

Post-stop metadata-only diagnosis, without resuming any stage:

- Empty-claim catalogs: hash agreement 21/21.
- Actual-claim catalogs: disagreement 15/21; agreement 6/21.
- Parsed ASCII-escaped and Unicode JSON objects: identical for every subject.
- First runtime mismatch: CORZ.
- Other structurally affected catalogs: CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX,
  SKHY, TSLA, WRD, WULF, 000660, 003690, 005930.
- The affected list is an offline hash diagnosis, not selective execution.
  No other subject's A stage was dispatched.

The synthetic controller probe used the ASCII text
`Offline source capability probe.`. It checked routing and schema availability
but did not exercise this Unicode identity boundary. Thus offline PASS did not
prove compatibility of all fresh Core text with the A authority hash contract.
This is an integration/test-coverage defect, not evidence that the model's
investment judgments were wrong. No candidate text was changed or disclosed in
the diagnostic output.

One P1 blocker remains: canonical catalog hash ownership across the Core-to-A
boundary. A bounded follow-up should align the derivative catalog binding with
the existing source-use canonical serializer and add ASCII/non-ASCII,
mixed-script and tamper-negative regressions. This is a recommendation only;
no such repair or continuation was performed in this frozen generation.

## Validation and Safety

At exact dispatch SHA `bea5f6d93b638b1b8215098023994dc1697e197c`:

- Focused tests: 541 PASS.
- Full pytest: 6176 PASS / 63 unchanged skips; existing warnings 3.
- Ruff, diff, Investment Knowledge, Chart Knowledge: PASS.
- Exact clean SHA and unchanged skip/xfail identities: PASS.
- These tests did not cover the fresh Unicode catalog mismatch above.

After the stop, frozen code/input/request/host identities were rechecked and
passed before adding this report. Operating HEAD/cleanliness, configuration,
production DB-file hashes and scheduler snapshot were unchanged over the
captured post-implementation-to-closeout interval.

Source/provider refresh, Telegram, recipient intent, production DB write,
warning/notification/scheduler mutation, broker action, main merge, remote push,
deploy and restart: zero. No observed P0 safety violation. P1 blocker: one.
Later A/B/render safety is NOT TESTED, not retrospectively marked PASS.

## Delivery and Gate

Package one report ZIP plus SHA-256 sidecar, with internal manifest, secret scan,
source/input bindings, current code, validation logs, Market/Core frozen outputs
and failure diagnostics. Do not claim 24-message completion or emit a
comparison-ready receipt. Partial-result sealing keeps comparison closed.

The iCloud delivery receipt is external to the immutable ZIP. It records
destination hash/size checks and per-file `isUploaded=1`, `isUploading=0`,
`isExcludedFromSync=0` for the root and existing `Thesis Monitor` folder.
Upload completion is asserted only after those checks, not merely file copy.

`R2B_R5_MONITORING_AI_24_MESSAGE_PASS_READY_FOR_BLIND_COMPARISON = NO`.
