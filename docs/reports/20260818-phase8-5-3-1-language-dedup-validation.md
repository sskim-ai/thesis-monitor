# Phase 8.5.3.1 Language and Dedup Validation

## Acceptance

| Gate | US | KR |
|---|---:|---:|
| Full validator errors | 0 | 0 |
| Runtime message quality | PASS | PASS |
| Final language | PASS | PASS |
| Unsupported specificity | 0 | 0 |
| Literal portfolio duplicates | 0 | 0 |
| Semantic skeleton duplicates | 0 | 0 |
| Generic methodology repeats | 0 | 0 |
| Watch/next meaningless overlap | 0 | 0 |
| Same numeric fact shown 3+ times | 0 | 0 |

Existing repetition thresholds and numeric, financial, identity, valuation, RR, supply, and renderer safety gates are unchanged.

## Before / After

- US particle errors: 6 -> 0.
- KR malformed actor-flow phrases: 2 -> 0.
- KR incomplete predicates: 1 -> 0.
- US watch/next overlap: 13 -> 0.
- KR exact RR fact displayed 3+ times: 6 -> 0.

## Fallback Regression

- Crossed confirmation future-trigger errors: 0.
- Dynamic structure omissions: 0.
- Available RR omissions: 0.
- Fake RR: 0.
- Automatic support promotions: 0.

## Human Preview

Representative KR scores: Samsung 18, POSCO 17, Hyundai Glovis 18, Korean Re 17, SK hynix 17; average 17.4/20.

Representative US scores: MU 18, SNDK 18, SKHY 17, TSM 18, TSLA 18, RXRX 18; average 17.8/20.

Semantic gates: Korean Grammar PASS; Intra-Message Redundancy PASS; Watch vs Next Check Separation PASS.

## Operations

- Replay Telegram sends: 0.
- Scheduled Task executions: 0.
- Pilot mutations: 0.
- Production Assist: OFF.
- AI mode: shadow.

Result: `PASS`, eligible for the separately verified conditional shadow promotion.
