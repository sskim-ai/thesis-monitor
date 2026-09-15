# Financial-Sector Exclusion Connective Scope

Contract: `financial-framework-claim-scope-v2`

## Purpose

Industrial-company financial frameworks must remain fail-closed for insurers. A sentence
that explicitly excludes those frameworks, however, is not an application. This contract
adds bounded Korean connective-predicate support without weakening current-claim or
financial-sector misuse controls.

## Structural Rule

For a clause shaped as:

```text
[industrial framework cluster] [exclusion connective] [sector replacement application]
```

the classifier requires all of the following:

1. The left object is one `_CLUSTER` occurrence, including coordinated `net_debt` and
   `working_capital` terms.
2. The immediately governing predicate is a supported affirmative exclusion connective.
3. The right clause names a supported financial-sector replacement framework.
4. The right clause ends in a bounded application/evaluation predicate.
5. No industrial framework occurs in the right replacement span.
6. No conditional marker governs the clause.

Supported bounded connective forms are:

```text
배제하고
제외하고
적용하지 않고
사용하지 않고
평가하지 않고
활용하지 않고
보지 않고
배제한 채
제외한 채
```

The resulting role is `CONTRASTIVE_REPLACEMENT`. Every framework term in the coordinated
left cluster receives that same role.

## Polarity And Locality

`배제하지 않고`, `제외할 수 없다`, conditional or ambiguous exclusion language are not
exemptions. A valid exclusion in one field does not immunize a current net-debt or working-
capital claim in another field. Mixed exclusion and application becomes
`CONTRADICTORY_MIXED_USE` and remains a hard failure.

## Shared Consumers

`framework_reference_is_application()` remains the single application decision used by:

- net-debt completeness validation;
- financial-sector generic-framework validation;
- working-capital framework validation.

No downstream lexical scan can override `EXPLICIT_NON_APPLICATION` or
`CONTRASTIVE_REPLACEMENT`.

## Frozen Boundaries

This change does not alter model prompts, model schemas, MarketExpectationEvidenceView,
BusinessDeltaEvidenceView, PPE-only cash-conversion semantics, Stage-2 language ownership,
price/timing ownership, or financial temporal scope. It adds no ticker-specific exception
and no production behavior.

## Shadow Manifest Safety

The M12AQ shadow harness reuses `shadow-frozen-context-manifest-v1`. Preparation validates
the six context groups and their 30 frozen prompt/schema files, writes only the canonical
`frozen_contexts` key, and includes the manifest module in the generation code hash. The
runner verifies that same canonical manifest before any of the 18 model calls. Legacy
`contexts` output is accepted only as input to the bounded preparation-time migration; it
is never accepted by the execution-time verifier.
