# Major S/R Reality-Gate Root Cause

## Result

`MAJOR_SR_ROOT_CAUSE = PASS`

The shared producer assigned the latest indicator observation date to the legacy
`interaction_date` field for Bollinger sources. The merge layer treated every such date as a
meaningful price interaction. Major-zone ranking then had no price-anchor eligibility gate, and
the renderer accepted the selected zone. A monthly Bollinger projection could therefore appear as
`주요 구조 지지/저항` with a recent-looking interaction date even when `reaction_count = 0`.

## Repair

- Split `indicator_observation_date` from `last_price_interaction_date`.
- Admit confirmed `PIVOT`, `BOX`, or verified equivalent `PRIOR_HIGH_LOW` evidence as anchors.
- Require anchor provenance before major ranking and again before rendering.
- Keep Bollinger/Fibonacci as confluence-only evidence for major labels.
- Preserve near-S/R selection unchanged.

The same-raw old base exposed `18`
dynamic-only visible majors. The repaired replay exposes `0`. No ticker exception,
forced fill, threshold relaxation, wave-policy change, or Fib-family-policy change was introduced.
