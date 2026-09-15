# Directional Core Semantic Single Source

## Status

M12BI establishes `directional-core-semantic-audit-v1` as the reusable
post-model semantic orchestration contract for fresh/new-issuer and monitored
directional-core consumers.

Implementation head: `8d39557e92f5470427052e628f0c12abe4974948`.

The orchestrator does not classify financial language itself. It adapts owned
evidence into canonical views, calls the existing canonical services, records
service identity and applicability, and aggregates their hard errors.

## Canonical Flow

```text
candidate core
  + OwnedEvidencePacket
  + EvidenceAliasCatalog
  + lifecycle applicability
        |
        v
audit_owned_directional_core_semantics
        |
        +-- directional financial semantics
        +-- QTD/YTD semantics
        +-- configured-signal ownership
        +-- working-capital typed binding
        +-- business-delta evidence capability
        +-- market-expectation independence
        |
        v
DirectionalCoreSemanticAudit
        |
        +-- hard_errors
        +-- applicability matrix
        +-- semantic service provenance
        +-- deterministic service identity
```

Provider parsing, financial canonicalization, prompt construction, rendering,
and readiness policy are outside this service.

## Consumer Rules

The active fresh path calls the orchestrator from `core_partial_audit`, then
adds only fresh-specific domain, material-anchor, and Unknown-treatment checks.
`execute_run` rejects a core batch on canonical hard failure. The final-freeze
wrapper requires a complete canonical audit receipt before accepting a run.

The monitored base audit also consumes the orchestrator. Working-capital,
BusinessDelta, and MarketExpectation wrappers retain their canonical evidence
view builders where their lifecycle layer owns those views. They do not
reclassify the underlying semantics.

`_case_semantic_errors` and `_fic_fin_05_hard_errors` remain compatibility
symbols only; both return no independent hard-semantic decision. The raw
BusinessDelta fallback remains isolated as a non-proof compatibility path.
Proof-critical callers require a canonical view and fail closed with
`CANONICAL_BUSINESS_DELTA_VIEW_REQUIRED` when it is absent.

## Fresh Lifecycle

Fresh Initial Analysis has explicit applicability for every family. Empty
configured-signal or working-capital views are represented as
`APPLICABLE_WITH_EMPTY_VIEW`; they are not silently omitted.

`business_thesis_change` remains decision-active. The fresh prompt defines it
as a change assessment and requires `UNCHANGED` when no safe baseline change is
established. It is therefore validated by the canonical BusinessDelta service,
not marked lifecycle N/A.

The preserved 2026-09-07 frozen fresh proof contains 16 candidates using
`UNRESOLVED` without eligible ambiguity. All 16 had passed the old partial
audit, and all 16 are rejected by the converged canonical audit with:

```text
BUSINESS_DELTA_CAPABILITY_VALUE_VIOLATION
BUSINESS_DELTA_UNRESOLVED_WITHOUT_ELIGIBLE_AMBIGUITY
```

This is recorded as a historical acceptance regression. Candidates, prompts,
schemas, and canonical rules were not modified to conceal it. It affects proof
history only; no production state was mutated.

## Readiness

Fresh semantic readiness delegates to `evaluate_finalization_readiness` while
retaining fresh-owned transport, source, and artifact-integrity gates. A
canonical hard failure blocks candidate acceptance; diagnostic variance does
not become a hard gate.

The unchanged M12BH golden corpus passes 40/40 with zero applicable-surface
divergence. The frozen M12BD proof re-audits Stage 1, Stage 2, and final
composition at 24/24 each, with zero hard errors and zero core mutation.
Previous and current monitored hard outputs are byte-equivalent after canonical
normalization.

Therefore:

```text
semantic_single_source_convergence_status =
  SEMANTIC_SINGLE_SOURCE_CONVERGENCE_CONFIRMED

fresh_real_proof_readiness = NOT_READY

shadow_retry_readiness =
  READY_ON_CONVERGED_SEMANTIC_SINGLE_SOURCE

next_scope =
  RETRY_FULL_SHADOW_ON_CONVERGED_SEMANTIC_SINGLE_SOURCE
```

M12BI made no model call, network gate attempt, provider fetch, production
mutation or send, scheduler change, monitoring resume, remote push, main merge,
or deployment.
