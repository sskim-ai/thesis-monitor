# OHLCV Long-History Contract

## Problem

Long-cycle structure cannot be compared consistently when daily, weekly, and monthly analysis use
short or implicitly resampled histories. Provider limits and short listings must not be hidden by
padding or calendar assumptions.

## Decision

`ohlcv-long-history-contract-v1` requests independent adjusted histories:

| Timeframe | Canonical bars | Current provider maximum |
|---|---:|---:|
| Daily | 1200 | 1000 |
| Weekly | 600 | 1000 |
| Monthly | 300 | 1000 |

Only completed bars at or before the cutoff are eligible. Each timeframe preserves requested,
returned, and used counts; start/end dates; adjustment basis; provider-limit status; and
short-listing status. No timeframe is created by resampling another timeframe in this contract.

Coverage is `PASS` only when the canonical count is available, `PARTIAL` for genuine provider or
listing limits with enough safe data to analyze, and `FAIL` when the minimum safe structure cannot
be formed. Missing history is never padded.

## Why

Explicit coverage makes long-history improvements measurable while preventing a partial dataset
from being presented as the canonical budget.

## Rejected Alternative

Reducing the requested daily count to 1000, repeating old bars, silently resampling daily bars,
or treating all short listings as errors were rejected.

## Safety Constraint

The current local `/ohlcv` interface caps `count` at 1000. Therefore `DAILY_1200 = PARTIAL` for
all 20 subjects and the overall contract is `PARTIAL`; no production readiness claim is allowed.
