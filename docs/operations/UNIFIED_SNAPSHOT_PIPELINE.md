# Unified Snapshot Pipeline

## Work Instruction Freeze

Task: M12DS-R6-R5F-R1. Base: `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`.
The attached work instruction is preserved under `docs/work-instructions`.
This worktree is local only. No scheduler activation, provider/model calls,
production delivery, database mutation, main merge, or deployment is part of
offline validation. Existing investment policy and sealed evidence are unchanged.

## Implementation Plan

1. Inventory app automations and launchd paths, including fallback and delivery
   retry paths. Preserve the actual before state and prepare a migration plan.
2. Implement a single-cycle, process-locked, durable snapshot state machine.
   Collection retries use original wall-clock slots and fresh whole attempts.
3. Bind collection receipts, all downstream stages, and delivery to immutable
   run/snapshot identities. Reject stale, future, incomplete, or mixed inputs.
4. Implement bounded terminal failure finalization, operational notification,
   sanitized immutable debug ZIP, and atomic local iCloud copy verification.
5. Exercise both exchanges, all collection retry slots, downstream failures,
   concurrency/crash safety, and output integrity offline.
6. Evaluate concrete production adapter parity separately from orchestration
   fixtures. Do not label fixture success as production integration proof.
7. Run full validation, publish local report ZIP/SHA to the established iCloud
   destinations, and report any unresolved promotion blocker explicitly.

## Source Contract

Accepted data is `QUERY_TIME_SNAPSHOT`; `finality_claim=NOT_CLAIMED`.
The timestamp is a collection timestamp, not certified immutable close evidence.
Source session, identity, basis, schema, hashes, and complete production role
coverage remain mandatory. Alpha Vantage and Massive are not called.

## Destination

Existing local reports use the iCloud Drive `Thesis Monitor` directory. Runtime
configuration must explicitly supply that destination; application code must
not embed a developer home path. A local hash-verified copy is not evidence of
Apple server or remote-device synchronization.

## Implemented Local Boundary

`unified_snapshot_contract.py` validates the complete configured universe and
source-role set, explicit provider/route/symbol/session/basis, OHLC integrity,
attempt-local collection timestamps, normalized JSON-pointer bindings, raw
hash receipts, and existing-owner validator receipts. A source adapter remains
responsible for actually producing those receipts from its raw responses.
Caller assertions alone are not source qualification.

`unified_market_run.py` owns one durable market/date cycle. An exclusive process
lock and pre-delivery intent prevent a second automatic normal send after a
crash. The adapter receives a fresh attempt directory with no previous attempt
inputs. The frozen collection and policy hashes are rechecked between every
Market/Core/A/B/validation/render/delivery stage. Expected output message IDs
are frozen in the production policy, not inferred from successful outputs.

Late starts use the still-open slot; missed slots are not replayed in a burst.
Each launch window is five minutes, including the final window ending at 08:25
or 16:15. This is a conservative start deadline, not a fourth collection time.
A collection already started may finish under its bounded timeout. Holiday
gates use the existing exchange calendar with no weekday fallback. US Saturday
KST can consume Friday's completed XNYS session; Sunday cannot repeat Friday.

Failure notification records `PENDING_LOCAL_COPY` before the ZIP is sealed so
the one immutable ZIP can contain the notification result. Actual copy/hash
status is a detached receipt. No notification claims successful upload before
it occurs. Failure notification send intent is durable and is not replayed
automatically after an ambiguous crash. Notification failure does not prevent
local ZIP creation/copy. Raw prompts, raw responses, environment values and
recipient identifiers are excluded from the debug export.

## Promotion Is Blocked

The current entrypoint is disabled by default and deliberately has no qualified
production adapter. Turning it on does not fall back to the old pipeline; an
eligible session terminates with `unified_production_adapter_not_qualified`.
Do not deploy or activate this intermediate implementation.

The current collection owner (`scripts/m12ds_r4_collect.py`) copies operating
state, collects both markets, consumes a pre-acquired night snapshot and writes
to a research directory layout. It does not yet expose attempt-local complete
raw receipt bindings for the new role contract. Calling it unchanged would not
prove fresh whole-attempt eligibility or zero fallback-provider calls.

The current Market/Core/A/B owner (`scripts/m12ds_r4_r4_reproof.py` and inherited
controllers) relies on research manifests, fixed 22-subject/eight-batch topology,
both-market context, a blind-pack hash, and controller-specific stage freezes.
The accepted capture path is an offline no-network capture, not live delivery.
Those owners must be adapted without bypassing their source-authority, typed
schema, numeric, or policy validators. The local orchestration fixture is not
evidence that this adaptation has occurred.

Bounded next implementation: isolate/generalize the existing collector and
existing policy controller behind `PipelinePorts`; bind the same canonical
population and message set; prove byte-equivalent request/validator/renderer
behavior with frozen existing packets and failed-attempt exclusion; then
qualify/register the adapter. Do not add substitute investment logic.

## Scheduler Cutover Plan

`unified_scheduler_plan.py` renders two inactive launchd definitions at 08:10
and 16:00. It requires a verified Asia/Seoul host and never installs them.
At authorized promotion, first boot out and durably disable old daily/KR-close,
fallback and delivery-retry agents, and retire all four Codex primary/backup
automations. Only then activate the two new definitions and verify exact
single-entry topology. Existing telemetry, publication observers, onboarding
and API service remain untouched. The old code paths remain byte-identical;
they are not alternative entrypoints for a unified cycle. Rollback must first
disable new entries before restoring any old path.

Observed before state: the four Codex jobs were PAUSED; four legacy launchd
monitoring/delivery agents were not loaded, but were not durably disabled.
Unloaded does not imply removed or disabled across login/reboot.

## Validation Scope

Offline fixtures exercise configured US14/KR8 populations and 24 combined
messages. No real provider, model, Telegram, or production DB call is made.
All seven stages use fixture adapters; real production E2E remains NOT_PROVEN.
The historical provenance checks remain unchanged. No new skip/xfail is used.
