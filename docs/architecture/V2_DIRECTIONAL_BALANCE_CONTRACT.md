# V2 Directional Balance Contract

## Purpose

`v2-directional-balance-v1` expresses the relative force of evidence supporting BUY and SELL. It is a decision explanation contract, not a probability, expected return, odds estimate, or fixed-factor weighted score.

## Canonical Pair

The canonical object contains `buy` and `sell`. Both values must be finite, remain within 0 through 10, sum exactly to 10 under decimal arithmetic, and use integer or 0.5 increments. Invalid sums, false precision, and non-finite values fail schema validation.

The label is derived without historical state:

| Balance | Label |
| --- | --- |
| `buy >= 6` | BUY |
| `sell >= 6` | SELL |
| otherwise | HOLD |

Required anchors are `6:4 BUY`, `5:5 HOLD`, `4:6 SELL`, and `5.5:4.5 HOLD`.

## Evidence Contract

Each candidate supplies one to three evidence-bound `buy_drivers` and `sell_drivers`, plus a Korean `balance_summary`. Directional prose rejects probability and fixed-score language. Driver claims use canonical evidence references and remain subject to the existing numeric, semantic, and order-language validators.

## Ownership

The raw candidate owns only the proposed balance. A READY accepted plan owns the final balance, final drivers, summary, fingerprints, and rendered value. With no material disagreement, candidate values are copied into the accepted plan. With adjudication, the adjudication owns the accepted values; `KEEP_V2` must preserve the candidate balance and drivers exactly.

Production and shadow renderers consume only the accepted plan and emit `판단 균형: BUY x : SELL y`. Legacy persisted accepted plans may deserialize without balance metadata, but they cannot pass the new renderer or current accepted-plan validation.

## Exclusions

The contract does not alter thesis status, valuation, timing, confidence, evidence weights, or transaction behavior. It does not introduce majority voting or a universal scoring formula.
