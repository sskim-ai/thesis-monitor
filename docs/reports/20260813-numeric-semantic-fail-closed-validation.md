# Numeric Semantic Fail-Closed Validation

## Scope

- Analysis policy: `daily-review-v3.2`
- Output schema: `2` (unchanged)
- Knowledge: `3.0`, SHA-256
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18` (unchanged)
- Production Assist: disabled
- GitHub Actions: pending at report creation

## Registry

Packet generation and validation now share one explicit numeric-semantic registry. Each semantic
defines allowed units, labels, formatter, rounding policy, scope, and whether prose use is allowed.

| Registry measure | Count |
| --- | ---: |
| Semantic specifications | 43 |
| Prose allowed | 39 |
| Prose denied | 4 |

The denied specifications are audit counts, audit ratios, audit years, and share denominators. An
unmatched fact field remains visible to packet audit as `registered=false` and
`prose_allowed=false`; it cannot use a generic prose fallback.

## Production Packet Coverage

The latest reconstructable US production packet covered 10 stock assessments and all 20 active
company profiles.

| Measure | Result |
| --- | ---: |
| Numeric entries | 236 |
| Explicitly registered | 236 |
| Prose allowed | 159 |
| Prose denied | 77 |
| Unsupported | 0 |
| Gate | ready |

The denied entries include repeated event relevance scores and audit-only valuation/capital fields.
The latest KR run predates two newly active KR names, so its historical run count cannot reconstruct a
complete current-universe packet. KR coverage remains covered by the full fixture suite and will be
verified again on the next normal KR close packet.

## Fail-Closed Fixtures

| Scenario | Expected | Result |
| --- | --- | --- |
| operating margin -> 영업이익률 | pass | pass |
| operating margin -> 매출 성장률 | reject | reject |
| foreign flow -> institution label | reject | reject |
| share price -> revenue growth | reject | reject |
| futures close -> futures return | reject | reject |
| PER -> PBR | reject | reject |
| unknown `mystery_ratio` semantic | reject | reject |
| `prose_allowed=false` share denominator | reject | reject |
| signed foreign net selling `-100` | pass | pass |
| sign-flipped absolute `100` | reject | reject |
| compact KRW `318,964,597,910` -> `3,190억원` | pass | pass |
| `0.1095%` -> approximately `0.11%` | pass | pass |
| `0.1095%` -> approximately `0.2%` | reject | reject |

Night-futures close, point change, and return are separately registered as `points`, `points`, and
`pct`. FX rate, FX point change, and FX return are likewise separate semantics. PER/PBR, modeled versus
consensus wording, historical comparability, and exact prose `text_ref` checks remain additive
guardrails.

## Generic Fallback Removal

The prior fallback accepted an unknown semantic when the usage had a sufficiently long text label.
That branch is removed. A prose numeric claim now passes only if:

1. `fact_id` and `field_path` exist.
2. The semantic is explicitly registered and prose-enabled.
3. Value and unit match the backend registry.
4. The usage contains an approved label for that exact semantic.
5. The displayed value is an approved deterministic variant.
6. The usage occurs at the exact `text_ref` and covers that numeric occurrence.
