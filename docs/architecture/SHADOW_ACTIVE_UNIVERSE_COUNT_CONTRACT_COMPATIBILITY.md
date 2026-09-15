# Shadow Active-Universe Count Contract Compatibility

## Status

M12BE implements `report-subject-identity-v1` for local shadow preflight only.
It does not change model prompts, schemas, evidence views, production delivery, or
the public action contract.

## Authoritative report contract

`market-expectation-evidence-view-v1` owns `subject_count`. A consumer must
require all of the following before using that report in a shadow preflight:

- `subject_count` is a non-negative integer.
- `rows` is a sequence of per-subject mappings.
- every row has one non-empty ticker.
- ticker identities are unique.
- `subject_count == len(rows)`.

Unknown contracts fail closed. Consumers do not guess among similarly named
count fields, and the producer does not duplicate `subject_count` into a legacy
`active_count` alias.

## Shadow identity gate

The task-start active universe is enumerated read-only. Its exact ticker set,
not a fixed cohort size, must match the frozen packet inventory and every
per-subject shadow view. The gate rejects equal counts with different tickers,
duplicates, missing tickers, extra tickers, and row-count inconsistencies.

The cross-manifest gate covers:

- frozen packet inventory;
- configured-signal view;
- configured financial-support view;
- BusinessDeltaEvidenceView;
- MarketExpectationEvidenceView;
- Stage-1 and Stage-2 working-capital binding views;
- frozen context and batching manifests.

## Proof reuse

The completed M12BD fictional proof may be reused only when its indexed bundle,
generation identity, 12 receipts and outputs, row counts, hard gates, and all
model-facing semantic hashes remain unchanged. M12BE then creates a new shadow
generation from the verified frozen packet payloads. The stopped M12BD shadow
generation is never resumed or stitched.

## Runtime firewall

M12BE is local-only. Provider fetches, production writes, Telegram sends,
monitoring mutations, main merges, deployments, and remote pushes remain zero.
Monitoring schedules remain paused and are observed read-only.

## M12BE execution outcome

The report-count boundary is repaired. `report-subject-identity-v1` consumes
`market-expectation-evidence-view-v1.subject_count`, verifies row count, and
requires exact active-universe ticker-set identity. The stopped M12BD shadow
replay and the new 22-subject, six-context preflight both passed with zero
count, ticker-set, duplicate, or packet mismatches.

The new generation
`20260911-m12ai-shadow-20260913T132402Z-c956834e1892` stopped before its first
model process was spawned. Its producer stores frozen input identities under
`frozen_contexts[].inputs.<input_name>.{path,sha256}`, while the inherited
runtime verifier still reads legacy top-level `<input_name>` and
`<input_name>_sha256` fields. The first missing lookup was `stage1_prompt`.

No model call, selective rerun, candidate edit, post-freeze hotfix, provider
fetch, production side effect, remote push, merge, deployment, or monitoring
resume occurred. The next bounded scope is to align the frozen-context input
reader with the already-frozen producer contract, add contrastive layout/hash
fixtures, and create a completely new shadow generation.
