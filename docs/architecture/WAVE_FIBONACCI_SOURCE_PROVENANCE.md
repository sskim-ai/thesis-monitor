# Wave Fibonacci Source Provenance

## Problem

A monthly Fibonacci level can be consumed in a weekly or daily map without becoming a weekly or
daily calculation. Losing that distinction creates false agreement and numeric ownership errors.

## Decision

`wave-fibonacci-source-provenance-v1` records for every backend-calculated reference:

- deterministic Fib ID and wave-hypothesis ID;
- source timeframe and source degree;
- confluence target timeframe;
- evidence family and method family;
- source endpoint pivot IDs;
- ratio, formula, calculated price, rounding, status, and cutoff.

Implemented families are W1 retracement, W3 retracement, primary-cycle retracement, current
rebound, and W5 projection. Projection methods remain independent evidence methods. A monthly
reference may contribute to a daily target zone while retaining `source_timeframe=monthly`.

## Why

Source identity allows validators and renderers to distinguish structural context from tactical
ownership and makes every price reproducible without AI arithmetic.

## Rejected Alternative

Copying one monthly Fib set into each timeframe with rewritten labels, returning raw ratios for AI
calculation, and merging management-style labels without method identity were rejected.

## Safety Constraint

AI packets expose hypothesis and evidence IDs but no Fibonacci or SR output prices. Monthly-to-
weekly/daily relabeling, projection-as-confirmed, and unregistered technical numerics are hard
failures.
