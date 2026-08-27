# Track A — US Shared Market Digest Plan Repair

## Objective

Repair the common evidence-selection ownership used by both AI and deterministic fallback.

Do not touch packet claim, numeric registry, macro temporal classification, exactly-once delivery, or
Price Structure v3.

## Required plan hierarchy

```text
CURRENT_MARKET
→ PARTICIPATION_STYLE
→ SECTOR_DISPERSION
→ BREADTH_STATE
→ MACRO_CONTEXT
```

Use repository-native names/types.

## Run-41 controls

```text
SPY  +0.0222%
QQQ  +0.0915%
IWM  -0.1003%
SOXX +0.2607%
RSP  +0.1533%

XLI  +1.0874%
XLV  -0.9983%
```

Do not hard-code these into production logic.

## Hard gates

```text
CURRENT_SESSION_CORE_MARKET_EVIDENCE_USED = PASS
CORE_ETF_ALL_DROPPED = 0
RSP_MATERIAL_EVIDENCE_DROPPED = 0
MATERIAL_SECTOR_EXTREMES_ALL_DROPPED = 0
MACRO_ONLY_DIGEST_WHEN_CURRENT_MARKET_AVAILABLE = 0
AI_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS
FALLBACK_CURRENT_SESSION_EVIDENCE_UTILIZATION = PASS
AI_FALLBACK_MARKET_PLAN_DIVERGENCE = 0
```

## Critical requirement

Near-flat market returns are not permission to discard the entire current-session cross-section.

Do not dump every ETF number. Produce bounded semantic coverage with provenance refs.

## Deliverables

Root cause, shared plan contract, run-41 plan artifact, AI/fallback integration tests, implementation SHA.
