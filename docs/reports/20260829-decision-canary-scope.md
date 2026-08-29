# Cross-Market Decision Canary Scope

Date: `2026-08-29 KST`

- Contract: `cross-market-decision-bounded-canary-v1`
- Instruction commit: `c62ddff`
- Base: `f7e0829647c782ce39353086f4fcc51101b9b566`
- Implementation: `a639d326a578bb7f3a2c53b1df31723bfb2b9829`
- KR subjects: `003690`, `000660`
- US subjects: `GOOGL`, `RXRX`
- Automatic substitution: `0`
- Current BUY forced: `0`
- Global enablement: `0`
- Trading, orders, sizing, assessment mutation: `0`

Only these four stock messages may receive a decision block. Every other market and stock
message remains byte-for-byte on the pre-canary path. A decision failure suppresses only the
decision block; it never suppresses an otherwise valid stock review.

The canary enters `ENABLED_AWAITING_NATURAL_PROOF`. Two natural cycles per market remain required
before any expansion decision.
