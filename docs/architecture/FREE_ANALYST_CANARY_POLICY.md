# Free Analyst Canary Policy

## Entity-Specific Eligibility

In addition to hard validation, semantic ownership, and runtime message quality, stock candidates
must pass `entity-specific-synthesis-v1`. Batch selection applies
`cross-message-synthesis-specificity-v1` before ranking candidates. Cross-industry generic leakage
falls back per message; it does not fail the whole packet. A legitimate Minimal candidate remains
eligible when no specific supported synthesis is available.

The fixed limits remain market `<= 1`, stock `<= 2`, total `<= 3`. This quality gate does not expand
the canary or enable full mode.

## State

Current state:

```text
PRODUCTION_ASSIST_CONTROL_PLANE=B
COMMON_AI_CORE_V1=INTEGRATED
FREE_ANALYST_ADAPTIVE_CANARY=ARMED_LIMITED
```

Production Assist remains off as a governance state. The existing Pilot gate is already enabled and
can select current validated AI output, so it does not prohibit this bounded canary. This repair does
not change that Pilot setting. Full Free Analyst mode remains off; only the bounded `1/2/3` canary is armed.

## Eligibility

A message is eligible only when:

- natural-packet adaptation passes
- Free Analyst structured analysis validates
- every support reference resolves
- semantic owner identity matches the current entity, ticker, market, and packet
- industry concepts, thesis drivers, relations, and expectation level resolve to current-message refs
- Adaptive selection and rendering pass
- material information loss is zero
- numeric, semantic, temporal, language, relation, and causality checks pass
- Trade AR is absent
- no Open Research dependency exists
- packet and receipt ownership are unambiguous

Semantic ownership is a hard eligibility gate shared by canary and any future full mode. A non-zero ownership mismatch rejects only that message and selects its deterministic fallback.

## Limits

The configuration validator enforces:

```text
market messages <= 1
stock messages <= 2
total messages <= 3
```

Selection is deterministic. It prioritizes validated material candidates and renderer diversity, then uses stable message identity. It does not use ticker or market-cap hard-codes.

## Runtime Quality

The scoped receipt contains the exact selected stock ticker set. Completeness is evaluated against that explicit set, while all existing quality thresholds and checks remain unchanged. Receipt verification rejects scope tampering.

Non-selected messages stay on the existing production path. A failed new candidate falls back per message. If no canary subset passes, the existing packet fallback remains authoritative.

## Rollback

Set:

```text
FREE_ANALYST_ADAPTIVE_ENABLED=false
FREE_ANALYST_ADAPTIVE_MODE=current
```

This disables the Common AI Core selection path without disabling ordinary deterministic production. It does not change schema, stored investment logic, Inventory, FCF, schedules, or delivery history.

Any wrong fact, unsupported causality, temporal violation, Trade AR leak, duplicate delivery, orphan, or receipt mismatch requires immediate disablement and incident review. One natural PASS never authorizes cohort expansion.
