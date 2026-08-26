# Adaptive Renderer Production

## Contract

The selector contract is `adaptive-renderer-selector-v1`. It is deterministic and does not make an LLM call.

Renderer families:

```text
DIRECT_ANALYST
CONCISE_HYBRID
MINIMAL_VNEXT
```

## Selection

DIRECT is required when a shorter form would drop a material alternative interpretation, uncertainty boundary, expectation threshold, causal boundary, temporal qualification, or material next check.

CONCISE_HYBRID is selected for a clear primary conclusion when every material boundary remains represented.

MINIMAL_VNEXT is selected only for a low-information source shape and only when its information audit reports zero material loss. A low-information label alone never overrides the information-loss audit.

No selector rule contains a ticker, market-cap threshold, industry hard-code, or model preference.

## Information Audit

Each renderer is audited for retention of:

- primary conclusion
- thesis linkage
- alternative interpretation
- uncertainty boundary
- expectation and valuation context
- positioning synthesis
- next check
- material warning

The selected renderer must have `material_information_loss = 0`.

## Fail-Closed Behavior

If Free Analyst validation, selection, rendering, or safety validation fails, the production result is `DETERMINISTIC_FALLBACK`. Production does not pass the failed result through a second unvalidated prose fixer.

Negative OCF/FCF, market ambiguity, and competing interpretations are facts or boundaries, not automatic thesis-status changes. The renderer cannot mutate assessments, warnings, valuation context, or monitoring versions.

## Broad Repetition

The immutable full-cohort replay exposes two repeated generic Free Analyst synthesis sentences. Existing repetition thresholds remain unchanged, so full mode is not enabled. The limited canary contains at most two stock messages, passes its scoped receipt, and is the only production mode eligible for a later explicit enablement decision.

## Price Structure v3 Ownership Boundary

Future selective v3 rendering must keep current completed-session SR/Fib under
`CURRENT_PRICE_STRUCTURE` and existing confirmation, warning, invalidation, and registered support
under `STORED_MONITORING_PRICE_RULE`. A material Fib confluence extension must preserve its full
registered range. Stale legacy technical prose cannot appear as a second current technical system.
This policy statement does not enable v3 in production.
