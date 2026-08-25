# KR/US Structured Data + Quality v2 Readiness

Instruction commit: `e04403c76abfd8d2f74ca91d438fccc54b479bad`.

Implementation commit: `1a6d2f411e7fa9ef414197a3fa5711b336a0d3e7`.

## Gates

```text
STRUCTURED_SOURCE_CAPABILITY_AUDIT = PASS
KR_STRUCTURED_ACQUISITION = PARTIAL
US_STRUCTURED_ACQUISITION = PARTIAL
KR_STRUCTURED_CONTEXT_VALUE_ADD = NO_MATERIAL_VALUE
US_STRUCTURED_CONTEXT_VALUE_ADD = PASS
KR_MESSAGE_QUALITY_V2 = PASS
US_MESSAGE_QUALITY_V2 = PASS
COMMON_MESSAGE_QUALITY_V2 = PASS
GENERIC_SYNTHESIS_REPETITION = PASS
THESIS_FIRST_PRIORITIZATION = PASS
MARKET_DIGEST_EVIDENCE_UTILIZATION = PASS
KR_US_REASONING_SCHEMA_COMMON = PASS
```

## Replay and Validation

- KR enriched replay: `8/8`.
- US enriched replay: `14/14`.
- Automatic numeric binding: `245`; rejected/unresolved: `0`.
- Generic synthesis lines: `36 -> 0`.
- Duplicate substantive messages: `18 -> 0`.
- Focused tests: `310 passed`.
- Full pytest: `1561 passed, 1 existing deprecation warning`.
- Ruff: PASS.
- `git diff --check`: PASS.
- Investment Knowledge / Chart Knowledge checksum parity: PASS / PASS.
- Public Action / operationId / schema: `0.4.5` / `20/20 unique` / `4`.
- Implementation SHA Actions: run `32851930739`, Test/Lint PASS.
- Final report SHA Actions: mandatory PASS before promotion and bundle publication.
- User-visible mutation from replay: `0`.

Open P0: `0`. Open material P1: `0`.

P2: KRX same-day publication timing pending, KR market-wide flow unsupported, US exchange breadth
unsupported, US participant flow unsupported, Open Research connector unavailable.

Safe partial sources do not block promotion. The implementation SHA is green, and promotion is
conditioned on the final report SHA receiving the same exact-SHA Test/Lint PASS.

`STRUCTURED_DATA_QUALITY_V2_PRODUCTION_READY = YES`

Next action: `WAIT_FOR_US_STRUCTURED_QUALITY_V2_NATURAL_CANARY`, followed by KR when complete KRX
publication evidence exists. No manual task or Telegram proof is authorized.
