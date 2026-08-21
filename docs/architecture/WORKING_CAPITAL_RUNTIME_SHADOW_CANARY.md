# Working-Capital Runtime Shadow Canary

Contract: `working-capital-runtime-shadow-canary-v1`

## Problem

Phase 9.1C proved value retrospectively, but archive replay cannot prove that the same selector and
semantic boundaries survive natural terminal delivery timing without influencing production.

## Decision

Run a detached post-terminal canary for total Inventory and exact Trade AR only. Reuse Phase 9.1C
selection and validation, persist independent receipts, and keep all output archive-only.

## Why

The narrow scope preserves the seven materially improved relations while avoiding broad AR/AP and
advanced ratios that added no demonstrated prose value. A detached process proves natural runtime
behavior without putting delivery availability behind experimental reasoning.

## Rejected Alternative

A ticker allowlist, a second scheduler, direct production AI injection, broad working-capital
rendering, and canary-to-canary dependencies were rejected because they would change eligibility,
duplicate orchestration, or create a production path before natural proof.

## Safety Constraint

The canary runs only after terminal delivery, validates the immutable delivery SHA, performs no
provider fetch, and cannot mutate delivery, fallback, assessment state, warnings, Public Action,
Phase 9.0E selection, or Telegram output.

## Runtime Boundary

The AI review job invokes two independent best-effort launchers only after a production bundle is
terminally sent. The working-capital launcher verifies the immutable packet, archived
`delivery-result.json`, delivery mode, terminal counts, and whole-file SHA before it starts a
detached process. Production never waits for the process, and launcher or canary failure cannot
change delivery, fallback, assessment state, warnings, Public Action, or Telegram output.

Each logical packet has one deterministic canary ID, an append-only attempt namespace, and one
terminal completion marker. The archive lives under
`working-capital-shadow-canary/<canary-id>` beside, but independent from, the cash-flow canary.

## Eligibility

The canary reads the committed Phase 9.1B canonical report and narrows every snapshot before the
Phase 9.1C selector runs. The only allowed balance metrics are:

- total `inventory`, with exact Revenue or COGS comparison already canonicalized;
- exact `trade_accounts_receivable`, with exact Revenue comparison.

Broad AR, exact/broad AP, contract assets, accrued liabilities, inventory components, DSO,
Inventory Days, DPO, and CCC are absent from the runtime snapshot. There is no ticker allowlist.
The Phase 9.1C PIT, latest-formal freshness, industry applicability, materiality, one-insight, and
Unknown-resolution rules make the selection.

Packet financial-period context is combined with the committed snapshot date. If the packet
already knows a newer formal period, the older relation is suppressed rather than substituted as
current. A later provisional period remains context-only. Every relation input must have
`source_available_at <= packet cutoff`.

## Validation

The deterministic renderer consumes one selected canonical relation and never recalculates YoY or
percentage-point gaps. Numeric binding verifies the relation ID, exact gap, formatted claim, and all
input Fact IDs. The existing 9.1C semantic validator rejects broad-to-trade relabeling, contract
asset/accrual leakage, advanced ratios, causal overclaim, and thesis/valuation/warning mutation.
Portfolio quality rejects exact repetition and three-or-more numeric template skeletons without
changing production thresholds.

A same-date Phase 9.0 FCF period may add non-causal context. The canary only checks the existing
canonical period and filing availability; it does not derive FCF, alter Phase 9.0E selection, or
consume the cash-flow canary output.

## Receipt Lifecycle

Every attempt stores a manifest, narrowed sidecar, deterministic shadow output, numeric binding,
semantic validation, quality receipt, and terminal canary receipt. Successful or intentionally
empty observations write a completion marker; failed validation remains retryable under the same
logical canary ID. Every receipt persists `production_influence_count = 0`.

Deployment completion and natural proof are separate. Initial state is
`DEPLOYED_PENDING_NATURAL`; Inventory and exact Trade AR become `LIVE_PASS` independently only when
a natural packet selects that family and all isolation and validation gates pass.
