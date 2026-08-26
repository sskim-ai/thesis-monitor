# Price-Only AI Anchor Packet

## Contract

`price-only-ai-anchor-packet-v1` is the only evidence object permitted to cross the variable anchor
trial boundary. The packet is public-price-only and contains no precomputed Fibonacci.

## Allowed Evidence

- Ticker, security ID, market, financial currency, cutoff, as-of date, and adjustment basis.
- Completed adjusted OHLCV bars and deterministic candle features.
- Canonical pivot and support/resistance IDs from `multi-timeframe-price-structure-evidence-v2`.
- Candidate-centered bar neighborhoods and bounded swing-segment summaries.
- Evidence hashes and public source references.

Blocked fields include user/account/portfolio identity, cost basis, private notes, thesis state,
Telegram/notification metadata, credentials, tokens, auth headers, and unrelated fundamentals.

## Windows

The compact-rich defaults are monthly 36 bars plus each candidate's +/-2 neighborhood, weekly 52
plus +/-3, and daily 90 plus +/-5. Candidate coverage takes precedence over the recent window: an
older eligible pivot brings its bounded neighborhood into the packet. `FULL_DEBUG` includes every
completed bar and is benchmark-only.

The packet reports total canonical bars, recent and included counts, eligible/included/omitted
candidates, omission reasons, neighborhoods, serialized footprint, and a deterministic hash.

## Candle Features

Features are deterministic and derived before egress: range, body, upper/lower wick, close location,
gap relation, rolling median volume and trading-value ratios, HH/LH/HL/LL relation, breakout,
reclaim, and rejection. Swing segments preserve endpoint IDs, bar count, price change, maximum
drawdown, volume relation, and supporting bar refs.

## Safety

The egress auditor recursively rejects banned field names and any Fibonacci-prefixed field. The
strict model schema rejects free numeric price fields. Runtime output can cite only IDs present in
the same packet. Packet creation and trial execution are archive-only and perform no delivery or
state mutation.
