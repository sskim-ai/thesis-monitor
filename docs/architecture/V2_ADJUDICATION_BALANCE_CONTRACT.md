# V2 Adjudication Balance Contract

## Trigger

Directional adjudication is required when any of these conditions is true:

- the candidate label differs from the prior accepted label;
- the current label crosses the BUY, HOLD, or SELL band;
- identical evidence moves BUY balance by at least 1.5;
- a machine-detected major configured thesis condition conflicts with the current decision.

A same-label movement of 0.5 does not require adjudication. Changed evidence with an unclassified material delta is retained for audit and does not create a fixed numeric score.

## KEEP_V1

When prior balance metadata exists, `KEEP_V1` preserves prior label and balance. It also preserves prior directional drivers and summary when available. A mismatch fails accepted-plan resolution. This supports migration baselines that predate balance metadata without inventing historical ratios.

## KEEP_V2

`KEEP_V2` accepts the candidate label, balance, buy drivers, sell drivers, and summary exactly. A partial copy or rewritten ratio fails resolution.

## Same-Evidence Rule

Adjudication may expose a candidate boundary crossing, but it may not authorize a materially unexplained accepted drift under identical evidence. Keeping the prior accepted outcome can stabilize a boundary case. Accepting a material same-evidence jump remains fail-closed.

## Ownership and Thesis Isolation

Accepted balance and drivers contribute to accepted fingerprints and renderer output. A balance change does not mutate the business thesis, earnings estimate, valuation context, warning lifecycle, or transaction state.
