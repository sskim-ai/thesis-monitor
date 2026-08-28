# Dynamic Bollinger Layer Policy

## Decision

`주요 구조 지지/저항` remains price-anchored. Bollinger-only evidence is visible only as
`볼린저 지지/저항(<timeframe>)` or as a secondary `볼린저 중첩` annotation.

The canonical summary preserves one support and one resistance candidate. The renderer uses
existing `NEAR/RELEVANT` relevance, monthly/weekly/daily timeframe importance, and distance to
select one material dynamic reference per subject. This yielded 6
standalone lines and 12 confluence annotations across 20 subjects.

## Safety

- Completed indicator bars only; partial weekly/monthly bars are excluded before calculation.
- Current role is determined from the whole zone relative to current price.
- Same display or overlapping raw ranges become confluence, not duplicate lines.
- Security, currency, adjustment basis, source refs, observation date, and bar state remain bound.
- AI calculation/promotion: `0`; target/stop generation: `0`.
