# Cash-Flow Runtime Shadow Canary

## Problem

Phase 9.0C proved cash-flow reasoning only against archive copies. A real natural packet must
exercise the same contract without making shadow generation or validation part of production
delivery success.

## Decision

Launch one detached, idempotent canary only after a terminal production delivery result and store
all canary evidence under a separate immutable namespace.

## Why

The exact natural packet and production outcome remain available after delivery finalization, while
the detached child cannot delay Telegram or change primary/backup, fallback, receipt, or exit state.

## Rejected Alternative

Injecting cash-flow into the production candidate, launching before fallback is final, sharing the
production completion marker, or using a manual replay as natural proof are rejected.

## Safety Constraint

Canary failure never escapes to the production decision path. User-visible cash-flow, assessment
mutation, warning lifecycle, Pilot accounting, Public Action, CCC, and ROIC remain disabled.

## Contract

Phase 9.0D implements `cash-flow-runtime-shadow-canary-v1` as a delivery-isolated consumer of
`cash-flow-shadow-consumption-v1`. It does not recalculate OCF, PPE CAPEX, or PPE-only FCF and does
not alter the production candidate. The work-instruction source is immutable commit
`a24e4f2210f944fa7c43d8dbf8be1d1a8e652164`.

## Runtime Insertion Point

The normal job completes validation, AI-assisted delivery or deterministic fallback, writes the
production `delivery-result.json`, and returns a terminal `PilotDeliveryResult`. Only a result with
`status=sent`, `pending_count=0`, and `sent_count=delivery_count` is eligible to launch a canary.
The parent process then starts `app.jobs.cash_flow_shadow_canary` in a detached child process and
immediately continues its existing print/exit path.

This ordering preserves the production lifecycle:

1. deterministic packet and held delivery rows
2. production AI claim/generation/validation
3. runtime message-quality receipt
4. AI-assisted delivery or deterministic fallback
5. production delivery result and exactly-once state
6. detached cash-flow canary launch

Validation rejection is not a launch point because deterministic fallback is not final yet.
Delivery retry launches only after it reaches the same terminal condition. A spawn, generation,
validation, quality, or archive failure is caught inside the canary boundary and cannot alter the
parent result or exit status.

## Identity And Idempotency

The logical canary ID is the SHA-256 identity of packet ID, consumption contract, and canary policy.
The manifest separately records packet SHA, production delivery-result SHA, production candidate
SHA when available, shadow candidate ID, and quality receipt ID. The canary verifies the archived
terminal delivery result before reading cash-flow evidence.

All retries live under one canary identity. A successful attempt creates the distinct
`canary-complete.json` marker. A later primary, backup, deliver, fallback, or retry invocation sees
that marker and returns `DUPLICATE_SKIPPED`; it cannot inflate natural-proof counts.

## Evidence Path

The child reads the exact natural packet, Phase 9.0B canonical facts, the Phase 9.0A formal-period
inventory, and the existing read-only preliminary-earnings snapshot. It applies the Phase 9.0C PIT,
freshness, comparable-period, industry, materiality, Unknown-resolution, numeric, and semantic
contracts. Packet thesis evidence supplies company-specific business mechanisms; ticker allowlists
do not participate in eligibility or prose selection.

The archive path is:

```text
data/ai_review/pilot/history/YYYY/MM/<packet-id>/
  cash-flow-shadow-canary/<canary-id>/
    attempts/<attempt-id>/
      canary-manifest.json
      cash-flow-sidecar.json
      shadow-input.json
      raw-shadow-output.json
      bound-shadow-output.json
      semantic-validation.json
      runtime-quality-receipt.json
      canary-receipt.json
    canary-complete.json
```

The marker is not production `archive-complete` and has no Pilot-success or delivery meaning.
Files are create-once. Production packet, candidate, fallback, receipt, delivery result, assessment,
warning state, and database rows are read-only to this module.

## Gates

- PIT: filing availability must be on or before packet assessment cutoff.
- Freshness: current formal may render; formal-lagging-provisional is context-only; stale, blocked,
  and not-applicable contexts suppress prose.
- Numeric: exact OCF, PPE CAPEX, and PPE-only FCF claims bind only to Phase 9.0B Fact IDs.
- Semantic: stale-as-current, unsupported yield/per-share/CCC/ROIC, management-FCF confusion,
  period/scope errors, resolved-Unknown contradictions, and thesis/valuation mutation are rejected.
- Quality: no threshold relaxation, repeated substantive cash-flow prose, portfolio skeletons, or
  three-number tuple dumps.
- Industry: insurance remains not applicable; KR OpenDART remains fail-closed; issuer-level foreign
  cash flow does not enable security-level arithmetic.

## Natural Proof

Runtime deployment is not natural proof. A completed artifact is initially labeled
`RUNTIME_OBSERVATION_REQUIRES_SCHEDULE_SOURCE_REVIEW`. A read-only review must verify the natural
Scheduled Task source, production delivery isolation, value add, and duplicate count before moving
runtime plumbing to `LIVE_PASS` or deciding Phase 9.0E readiness.

Until then:

- runtime plumbing: `IMPLEMENTED_PENDING_NATURAL`
- cash-flow user-visible: `NOT_ENABLED`
- `PHASE_9_0E_READY = NO`
