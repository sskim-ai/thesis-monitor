# US Macro Message Rendering

Contract: `us-market-digest-plan-v1`

The US morning macro slot consumes only canonical macro Fact families verified by the shared
market context: nominal and real yields, breakeven inflation, credit spreads, FX, oil, volatility,
and the dollar index. Equity index, style, sector, and sector-relative Facts cannot own this slot.

## Neutral Policy

A generic zero-change or missing-change Fact is not decision-material and produces
`OMITTED_SAFE_NOT_MATERIAL`. It does not produce an empty or vacuous `🌐 보조 시장환경` section.
A specific neutral Fact may be rendered only when an upstream stored plan selected that exact Fact
with matching observation date and temporal role. Its sentence is produced from the canonical
series label by a semantic template such as `전 세션과 큰 변화가 없었습니다.` Status labels are
never concatenated with Korean verb endings.

## Final Gate

The final renderer requires exactly one supported evidence ref, a valid observation date, an
allowed temporal role, current-signal eligibility for current observations, and a renderable
specific label. It ignores stored macro prose and rebuilds the claim from the Fact. Prior-session
and reference-lagging Facts receive an explicit official-observation date prefix. Any mismatch
omits the section safely.

This contract does not change index, RSP, sector, night-futures, Price Structure, valuation, or
business-thesis ownership.
