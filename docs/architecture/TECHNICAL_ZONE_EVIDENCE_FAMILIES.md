# Technical Zone Evidence Families

## Problem

Several correlated Fibonacci ratios from one wave can make a zone look stronger than independent
pivot, Bollinger, or timeframe evidence warrants.

## Decision

Technical zones keep source occurrences and score independent evidence families separately:

- pivot reaction groups;
- Bollinger 20 anchors;
- wave-owned Fibonacci references;
- balance-box boundaries;
- cross-timeframe contributors.

Fibonacci scoring deduplicates by evidence family, method family, and source degree. Raw source
occurrences remain auditable, but duplicate correlated methods do not repeatedly increase family
strength. `BALANCE_BOX` and `RECOVERY_BAND` are distinct concepts. MACD, RSI, volume, and trading
value are optional supporting evidence and are not required or fabricated in v3.

## Why

Family-aware scoring rewards independent confirmation and prevents ratio density from masquerading
as stronger evidence.

## Rejected Alternative

Counting every ratio as an independent vote, adding a buy/sell score, and merging box/recovery
semantics were rejected.

## Safety Constraint

The score describes evidence density only. It cannot mutate the business thesis, valuation,
assessment state, warnings, or delivery eligibility.
