# Primary Monthly Wave Hypothesis

## Problem

Fibonacci anchors need a defensible structural degree. Selecting endpoints from proximity or ratio
fit alone can produce attractive but unsupported wave labels.

## Decision

`primary-monthly-wave-hypothesis-v1` builds bullish W0-W5 candidates from monthly pivots. Daily
pivots use `3/3`; weekly and monthly use `2/2`. Confirmed pivots have the required right bars;
eligible edge pivots remain `PROVISIONAL` and are never relabeled as confirmed.

Candidate generation enforces the quoted hard-rule family before scoring: ordered alternating
endpoints, W1 above W0, W2 between W0/W1, W3 above W1 and not the shortest impulse, W4 above W1
and below W3, and W5 above W3 or explicitly unconfirmed. Weekly pivots may confirm monthly
endpoints within bounded date and price tolerances. Fibonacci fit, magnitude, recency, endpoint
confirmation, and weekly confirmation are supporting score components only.

States are `VALID_CONFIRMED`, `VALID_PROVISIONAL`, `AMBIGUOUS`, or `NONE`. Multiple close
candidates remain ambiguous unless the ID-only variable-AI consensus is stable. The bounded
repair assigns explicit degree metadata and ranks grand-cycle, primary-current-cycle, and
intermediate candidates independently; raw magnitude no longer decides the shared top-N set.

## Why

This preserves a reproducible primary degree while allowing incomplete current structures to be
represented honestly.

## Rejected Alternative

Ticker-specific endpoint tables, Fib-first anchor discovery, arbitrary wave labels, and treating
W5 absence as an error were rejected.

## Safety Constraint

The implementation does not claim bearish impulses, ABC corrections, or a complete nested
Elliott ontology. An unsupported structure produces abstention and no Fibonacci prices.
