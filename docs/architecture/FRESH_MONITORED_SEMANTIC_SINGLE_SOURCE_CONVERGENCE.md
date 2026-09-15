# Fresh / Monitored Semantic Single-Source Convergence

## Contract

`fresh-monitored-semantic-single-source-convergence-audit-v1` maps every
proof-critical semantic family to one authoritative implementation and records
whether each execution path calls it directly, adapts only shape, duplicates
meaning, or bypasses it.

The allowed consumer classifications are:

- `CANONICAL_SHARED_SERVICE`
- `THIN_ADAPTER_TO_CANONICAL_SERVICE`
- `LEGACY_DUPLICATE_EQUIVALENT`
- `LEGACY_DUPLICATE_DIVERGENT`
- `BYPASS_OF_CANONICAL_SERVICE`
- `NOT_APPLICABLE`

Shape adaptation may translate field paths, aliases, or report formatting. It
must not independently derive temporal role, FCF identity, configured-signal
fulfillment, working-capital grounding, business-delta eligibility, expectation
independence, or financial-sector application semantics.

## M12BH Finding

The latest fresh/new-issuer execution path is rooted at
`new_issuer_final_freeze_ownership_proof.execute`, delegates model output to
`new_issuer_holdout_selection_ownership_proof.execute_run`, and applies
`core_partial_audit`. That partial audit checks evidence domains, material
anchors, and unknown treatment, but it does not call the canonical financial,
QTD/YTD, configured-signal, working-capital, business-delta, or
market-expectation validators.

The monitored monolithic and Stage-1 paths reach
`directional_financial_context_m12._audit_core_batch` through the grounding
adapter and therefore call `validate_directional_financial_semantics` and
`validate_qtd_ytd_conflict_semantics`. The M12AI wrapper additionally calls the
canonical business-delta and market-expectation validators. Working-capital
wrappers delegate to the canonical typed-binding service.

Two proof-specific hard helpers remain beside canonical validation:
`_case_semantic_errors` and `_fic_fin_05_hard_errors`. A business-delta wrapper
also retains an independently derived fallback when no canonical view is
provided, although the current M12AI path supplies the view.

## Gate

M12BH classifies this state as `CONVERGENCE_DEBT_PRESENT` and
`STOP_BEFORE_SHADOW`. No network gate or model call may run. The next bounded
scope is `BOUNDED_SEMANTIC_SINGLE_SOURCE_CONVERGENCE_REPAIR`: route the active
fresh path through the existing canonical services, reduce proof assertions to
checks over canonical audit output, seal driftable fallback logic, and rerun the
same 40-case corpus before any model call.

This architecture audit changes no prompt, schema, production runtime, database,
scheduler, delivery path, or public contract.
