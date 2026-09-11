# 2026-09-07 New Issuer Final Freeze & Ownership Proof

## Decision

The final source freeze and model-free request preflight passed, but the bounded real
proof stopped during FIRST because the selected model reported capacity exhaustion.
No retry, model substitution, timeout increase, batch split, hotfix, A/B/C continuation,
or production activation was performed.

```text
readiness = NOT_READY
ownership_proof_completion_state = INCOMPLETE_TRANSPORT_FAILURE
next_scope = BOUNDED_TRANSPORT_RUNTIME_REVIEW
```

## Repository

| Field | Value |
| --- | --- |
| Base | `8dcf12fc3d4b3bac2a6e62679feb9e05d222ea1e` |
| Work-instruction commit | `1efa69a43ce1130bc7439c03fb4f87a36b42473f` |
| Tested implementation commit | `d0433edaa0d8f929b0ebb390c478e4d64f4834d0` |
| Branch | `codex/20260907-new-issuer-final-freeze-ownership-proof-existing-data-routes` |
| Production/main merge | `0` |

## Historical Authority

The supplied selection-review ZIP was verified before use.

| Check | Result |
| --- | --- |
| ZIP SHA-256 | `b2233e37113ac84def1e974e81c413e39f9f378a84182167ca9ae4b24c75bce0` |
| ZIP members | `2545` |
| Individually indexed payloads | `2544` |
| CRC / duplicate / unsafe path failures | `0 / 0 / 0` |
| Indexed hash / size mismatches | `0 / 0` |
| Review manifest | `6bba480d63661967c80192af6d80287bb3bb9c4d9cf31084eaeeb6a45358b99c` |
| Selection policy | `c66583d78dc9155e454df172730691040778a25f5c8e4ab33da63919a172d574` |
| Exclusion registry | `f91ec0a8ea6a224a5da3375da28d83f01b46c518e8b94a8da0df23398a3f2415` |

The old review manifest remained non-executable. A new source generation and execution
precommit were created rather than mutating the review artifact.

## Final Freeze

The reviewed US4/KR12 order and four shared-context groups were preserved without
replacement. All 16 stored packets passed the current canonical builder and validator.
They were generated earlier on the same date and remained valid under existing freshness
rules, so the source recheck reused those archived packets without a network refresh.

```text
source_generation_id = 20260907-new-issuer-source-20260907T055608Z-52f069785a77
runtime_generation_id = 20260907-new-issuer-proof-20260907T055608Z-0446826566f6
source_lock = fc4ef965e06e926f0b84bebc0716915e34080b692040e92e990e2517d01a21ea
valid_archive_cache_hit_count = 16
source_network_request_count = 0
new_paid_dependency_count = 0
```

This records an existing-route/no-new-paid-dependency policy. It does not claim that all
upstream plans or entitlements were independently certified free.

The final actual-request model-free preflight passed all 32 planned contexts:

```text
actual_request_preflight_count = 32
binding_lock_count = 32
simulated_invocation_count = 32
real_model_invocation_count = 0
identity failures = 0
preservation failures = 0
```

## Real FIRST

Configuration stayed frozen at `gpt-5.6-sol`, `xhigh`, four subjects per shared context,
1,800 seconds, and one authoritative timeout owner.

| Stage | Context result | Subject coverage |
| --- | --- | --- |
| Directional Core | `4/4 PASS` | `16/16` |
| Price Timing | `2/4 PASS`, batch 3 transport failure, batch 4 not run | `8/16` complete |
| FIRST run-level gates | `NOT_MEASURED` | Run incomplete |
| A / B / C | `NOT_RUN` | Required FIRST gate was not reached |

There were seven real model invocations. The six completed contexts produced 24 raw
subject rows: 16 Directional Core rows and 8 Price Timing rows. Those completed contexts
passed output identity and per-context semantic checks. This is not a complete FIRST and
must not be reported as ownership generalization evidence.

## Failure Forensics

The failure occurred in FIRST Price Timing batch 3 for:

```text
008970, 047080, 068270, 475830
```

| Field | Measured value |
| --- | --- |
| Invocation | `20260907-new-issuer-proof-20260907T055608Z-0446826566f6:first:PRICE_TIMING:03` |
| Actual request identity preflight | `PASS` |
| Workload guard | `CONTINUE`; natural jobs `0`; other model processes `0` |
| Process exit | code `1` after `382.087626s` |
| Output | file absent; `0` bytes; parse not attempted |
| stderr | `248738` bytes |
| Provider diagnostic | `Selected model is at capacity. Please try a different model.` (2 occurrences) |
| Timeout / retry | `0 / 0` |
| Orphan model process | `0` |
| Termination initiator | `NONE` |
| Context evidence preservation | `PASS` |
| Secret scan | `PASS` |

This is a post-spawn external model-capacity transport failure, not a source, prompt,
schema, validator, renderer, ownership, timeout, or natural-workload contention failure.
Request acceptance observability remained unavailable, so the report does not infer more
than the preserved CLI diagnostic and lifecycle receipt establish.

## Exposure And Retirement

All 16 issuers received real Directional Core output, so issuer output exposure is
`FULLY_EXPOSED`. Stage completion is partial because only eight issuers completed Price
Timing. The frozen cohort is therefore `RETIRED_PARTIAL_EXPOSURE` and cannot be reused as
an unseen holdout. Semantic revelation and stability remain `NOT_MEASURED`; no completed
context exposed a semantic defect, but that observation cannot replace the missing gates.

The legacy aggregate `run_results.first` field says `NOT_RUN` because the inherited
finalizer only counts a run after full completion. The authoritative context receipts,
`27-first-execution-summary.json`, and the task-specific proof
`61-existing-data-routes-final-freeze-ownership-proof-completion.json` record FIRST as
`FAILED` after six successful contexts and one failed context.

## Validation And Isolation

| Check | Result |
| --- | --- |
| Focused tests | `52 passed` |
| Full pytest | `2665 passed`, 2 dependency deprecation warnings |
| Ruff | `PASS` |
| `git diff --check` | `PASS` |
| Production Telegram sends | `0` |
| Scheduler changes | `0` |
| DB mutations | `0` |
| Monitoring registration | `0` |
| Production activation | `0` |

## Result Bundle

```text
file = thesis-monitor-20260907-new-issuer-final-freeze-ownership-proof-existing-data-routes-report.zip
sha256 = 48f0ad3a82e332aaed61106717f8ca660a7cc297ff4353a283c5db0ca1c009fa
zip_members = 912
indexed_payloads = 911
index_self_exclusion = artifact-index.json
secret_scan_failures = 0
```

The bounded next action is transport-runtime review of the capacity failure. This result
does not authorize an automatic retry of the retired cohort or a switch to another model.
