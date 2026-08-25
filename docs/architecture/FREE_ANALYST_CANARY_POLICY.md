# Free Analyst Canary Policy

## State

Current state:

```text
PRODUCTION_ASSIST_CONTROL_PLANE=A
COMMON_AI_CORE_V1=INTEGRATED_READY_NOT_ARMED
FREE_ANALYST_ADAPTIVE_CANARY=READY_NOT_ARMED
```

Production Assist remains off. This task does not flip either the authoritative pilot gate or the independent Free Analyst kill switch.

## Eligibility

A message is eligible only when:

- natural-packet adaptation passes
- Free Analyst structured analysis validates
- every support reference resolves
- Adaptive selection and rendering pass
- material information loss is zero
- numeric, semantic, temporal, language, relation, and causality checks pass
- Trade AR is absent
- no Open Research dependency exists
- packet and receipt ownership are unambiguous

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
