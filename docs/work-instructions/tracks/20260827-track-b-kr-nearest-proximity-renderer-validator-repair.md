# Track B — KR Nearest / Proximity Renderer + Validator Repair

## Objective

Separate:

```text
internal nearest available structural zone
```

from:

```text
user-visible "가까운" zone
```

A `LONG_HORIZON` zone must never render as "가까운".

The supplied 000660 fixture:

```text
current 1,730,000
support ~995k-1,000k
distance 42.2%
LONG_HORIZON
```

must fail the new validator.

Audit RELEVANT-tier semantics using 005930 and 012450.

Preserve genuine near higher-timeframe zones in 003690, 005490, 010120, 086280.

## Hard gates

```text
LONG_HORIZON_RENDERED_AS_NEAR = 0
REMOTE_ZONE_PROMOTED_AS_NEAR_FILL = 0
RENDERED_NEAR_WITH_INELIGIBLE_PROXIMITY = 0
VALID_HIGHER_TF_NEAR_ZONE_DROPPED = 0
FABRICATED_SR_FILL = 0
RUN000660_OLD_RENDER_NEW_VALIDATOR = FAIL_AS_EXPECTED
```

Validator must bind rendered labels to zone provenance, not keyword-scan prose.
