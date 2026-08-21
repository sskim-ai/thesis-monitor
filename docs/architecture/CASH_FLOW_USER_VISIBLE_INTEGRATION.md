# Cash-Flow User-Visible Integration

## Problem

Canonical FCF may be safe without being current, material, or suitable for a user-visible daily
message. Production needs one fail-closed selector shared by AI and fallback, with exact provenance,
delta-first suppression, and an immediate OFF switch.

## Decision

Use one `cash-flow-user-visible-v1` context, default OFF, and expose at most one current-formal
PPE-only FCF number for dynamically selected US/foreign SEC subjects.

## Why

The context preserves Phase 9.0B lineage and Phase 9.0C timing/materiality while giving AI and
fallback the same auditable selection identity. One number controls density and ownership.

## Rejected Alternative

Rejected designs include a ticker allowlist, broad all-subject blocks, OCF/CAPEX/FCF tuple dumps,
stale or lagging-formal substitution, management-FCF conflation, and independent AI/fallback
calculations.

## Safety Constraint

Unknown mode, missing metadata, incompatible lineage, unsupported industry, renderer failure, or
cross-path mismatch fails closed. OFF produces no user-visible cash-flow Fact or prose.

## Contract

`cash-flow-user-visible-v1` is the single selected cash-flow context shared by the production AI
packet and deterministic fallback. It consumes `cash-flow-capital-efficiency-v1` Facts through the
Phase 9.0C point-in-time, freshness, comparison, industry, and materiality contracts. It does not
recalculate OCF, PPE CAPEX, or FCF.

The initial rollout mode is configured by `CASH_FLOW_USER_VISIBLE_MODE`:

- `OFF`: no cash-flow Fact, number, or prose is available to either renderer.
- `SELECTIVE_CURRENT_FORMAL_FULL_FCF`: current-formal, PIT-safe, full-FCF contexts may be selected.
- Any unknown value resolves to `OFF`.

The default is `OFF`. Mode resolution happens on every packet/fallback build, so disabling the
feature cannot reuse a previously selected in-process object.

## Selection

A selected context must satisfy every gate:

1. The subject is in the canonical active-universe report.
2. Initial market/source scope is US or US-foreign official SEC evidence.
3. Industry applicability is not `NOT_APPLICABLE`.
4. Usage mode is full FCF, not OCF-only or CAPEX-only.
5. Freshness is `CURRENT_FORMAL`; lagging-provisional, stale, blocked, and missing contexts fail
   closed.
6. OCF, PPE CAPEX, and PPE-only FCF Facts are eligible and untainted.
7. Period, issuer, entity scope, statement basis, currency, and unit are compatible.
8. FCF input lineage contains the exact OCF and PPE CAPEX Fact IDs, and arithmetic reproduces.
9. Existing thesis/Unknown/materiality evidence makes cash flow decision-relevant.
10. Baseline cash-flow consistency has no unresolved conflict.

There is no ticker allowlist and no magnitude threshold. The initial exclusions are KR/OpenDART,
insurance/reinsurance generic enterprise FCF, OCF-only, stale or formal-lagging-provisional facts,
management-defined FCF, security-level FCF valuation, CCC, DSO/DPO, inventory days, and ROIC.

## Delta First

The selected context records an evidence signature derived from the three canonical Fact IDs and
their deterministic comparable-period relations. The latest prior sent delivery payload is read
only. Identical evidence is suppressed as `SUPPRESSED_NO_DELTA`; a newly safe period, first safe
exposure, or resolved cash-flow Unknown may render once. Suppression of an unchanged number does
not restore a resolved false Unknown.

## User-Facing Ownership

The exact number belongs to `business_earnings`. The initial renderer exposes one number: PPE-only
FCF, labeled as `PPE 투자 후 잉여현금흐름` and prefixed by issuer fiscal-period identity.
OCF and PPE CAPEX remain lineage inputs and are not dumped as a three-number tuple.

The semantic validator requires:

- one exact primary FCF claim bound to the canonical FCF Fact ID;
- `business_earnings.text` ownership;
- explicit PPE scope and fiscal/YTD/FY/QTD label;
- no use in core, price, supply, or valuation owners;
- no management-FCF mislabel, FCF yield/share/EV multiple, CCC/ROIC, runway inference, or resolved
  missing-data contradiction.

When the feature is suppressed or OFF, cash-flow Fact IDs are absent from the prose-eligible packet.
The new unsupported-metric checks therefore do not reclassify unrelated legacy prose outside a
selected cash-flow context.

## Industry Interpretation

The deterministic fallback renders one compact industry-specific consequence:

- cloud/platform: AI/Cloud investment conversion with Cloud growth and margin;
- software/services: Software/Consulting conversion and acquisition funding;
- memory: ASP, mix, inventory cycle, and investment timing;
- HPC/data center: build-out, energization/billing, and funding;
- biotech: cash-burn evidence without unsupported runway months;
- automotive: margin and growth-investment conversion;
- stablecoin/platform: reserve income and non-interest platform conversion.

Positive or negative FCF is a Fact, not an automatic thesis verdict. No thesis state, warning
lifecycle, or valuation context is mutated.

## AI/Fallback Parity

Both paths construct the context independently from the same inputs and must match on context ID,
selection state/reason, display reason, evidence signature, primary Fact, period, currency,
freshness, baseline suppression IDs, and visibility. A mismatch raises before delivery and existing
deterministic fallback safety remains in force.

Delivery metadata records mode, selected subjects, context IDs, Fact IDs, and baseline suppressions.
The detached runtime canary writes an observational production-parity audit after terminal delivery;
it has zero delivery influence.

## Failure Isolation

Per-ticker canonical-report, selector, or renderer failure produces an audited suppression and does
not prevent unrelated messages. Missing metadata never becomes verified metadata, and missing
CAPEX never becomes zero. The fallback contract and exactly-once delivery ownership are unchanged.

Public Action remains `0.4.5`, output schema remains `4`, and no public snapshot field is added.
