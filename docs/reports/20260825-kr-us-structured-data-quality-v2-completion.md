# KR/US Structured Data Acquisition First And Message Quality v2 Completion

## Repository

- Instruction commit: `e04403c76abfd8d2f74ca91d438fccc54b479bad`
- Branch: `codex/kr-us-structured-data-first-quality-v2`
- Operating base: `b7dc15117b9295ab272eafb71c2e280b468a9307`
- Implementation commit: `1a6d2f411e7fa9ef414197a3fa5711b336a0d3e7`
- Report/final main/operating: resolve from Git after the clean fast-forward
- Superseded instruction: `20260825-kr-us-message-quality-market-specific-bounded-repair.md`
- Implementation Actions: run `32851930739`, Test/Lint PASS
- Final Actions: exact report SHA must PASS before promotion

## Acquisition

```text
STRUCTURED_SOURCE_CAPABILITY_AUDIT = PASS
KR_STRUCTURED_ACQUISITION = PARTIAL
US_STRUCTURED_ACQUISITION = PARTIAL
KR_STRUCTURED_CONTEXT_VALUE_ADD = NO_MATERIAL_VALUE
US_STRUCTURED_CONTEXT_VALUE_ADD = PASS
```

KR implemented KOSPI/KOSDAQ broad-index identity, separate and aggregate stock breadth, and official
activity volume/value with exact session/publication provenance. The exact 2026-08-25 publication
returned no rows, so all current numbers remained absent. Market-wide participant flow remains
unsupported.

US added RSP equal-weight context, an RSP-versus-SPY typed relation, and all 11 sector SPDRs. The
safe session-complete style/sector subset is current; exchange breadth and participant flow remain
Unknown. No new paid provider or API was added.

Provider audit calls: KRX `8/8` successful HTTP responses and local OHLCV `24/24`; Massive and
Kiwoom calls `0`. Four KRX exact-slot calls proved provider-pending, while four prior-session calls
were capability-only and were not substituted into current context.

## Quality v2

```text
KR_MESSAGE_QUALITY_V2 = PASS
US_MESSAGE_QUALITY_V2 = PASS
COMMON_MESSAGE_QUALITY_V2 = PASS
GENERIC_SYNTHESIS_REPETITION = PASS
THESIS_FIRST_PRIORITIZATION = PASS
MARKET_DIGEST_EVIDENCE_UTILIZATION = PASS
KR_US_REASONING_SCHEMA_COMMON = PASS

GENERIC_SYNTHESIS_LINES_BEFORE = 36
GENERIC_SYNTHESIS_LINES_AFTER = 0
DUPLICATE_SECTION_CLAIMS_BEFORE = 18
DUPLICATE_SECTION_CLAIMS_AFTER = 0

KR_ENRICHED_REPLAY = 8/8
US_ENRICHED_REPLAY = 14/14
KR_CANARY_SIMULATED_SELECTED = 3
US_CANARY_SIMULATED_SELECTED = 3
```

Quality v2 keeps thesis-first ownership, permits deterministic supporting facts only under the same
entity/owner boundary, rejects generic synthesis when specific linkage exists, and preserves one
canonical supply owner. KR pending-publication prose stays local and fail-closed; US market prose
uses the available style/sector evidence without inventing breadth.

## Safety

All hard counts are zero: Fact mismatch, unsupported numeric/causality, temporal violations, Trade
AR leak, hidden arithmetic, external unsourced facts, semantic ownership errors, material
information loss, market-context unit conflicts, and missing-to-zero defaults. Numeric binding is
`245/245` automatic with manual/rejected/unresolved all zero.

The limited Free Analyst Adaptive canary remains enabled pending natural proof at market/stock/total
limits `1/2/3`. Full mode is OFF. Open Research production integration is `0`; the production
research connector remains `NOT_AVAILABLE`. Production Assist is OFF. Replay caused no Telegram,
task, Pilot, DB, archive, or delivery mutation.

## Validation And Decision

- Focused structured/quality suite: `310 passed`
- Final documentation/structured focused rerun: `25 passed`
- Full pytest: `1561 passed, 1 existing deprecation warning`
- Ruff / diff: PASS / PASS
- Investment Knowledge / Chart Knowledge: PASS / PASS
- Public Action / operationId / schema: `0.4.5` / `20/20 unique` / `4`
- Open P0 / material P1: `0 / 0`
- P2: KRX same-day publication timing, KR market-wide flow, US exchange breadth, US participant
  flow, optional KR sector/size context, and unavailable production research connector

```text
STRUCTURED_DATA_QUALITY_V2_PRODUCTION_READY = YES
NEXT_ACTION = WAIT_FOR_US_STRUCTURED_QUALITY_V2_NATURAL_CANARY
PRODUCTION_MUTATION_FROM_REPLAY = 0
MANUAL_TELEGRAM_SEND = 0
MANUAL_PRODUCTION_TASK = 0
```
