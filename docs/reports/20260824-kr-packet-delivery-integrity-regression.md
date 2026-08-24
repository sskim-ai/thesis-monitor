# KR Packet / Delivery Integrity Regression

## Invariants

- Packet persistence precedes intent creation.
- Failed persistence creates zero deliverable intent.
- Packet-bound intent is provisional until hold.
- Held fallback selection accepts an identity-matching production-safe packet even when
  `ready_for_ai=false`.
- AI claim selection still skips that packet.
- Missing packet cannot make an orphan row deliverable.
- Retry reuses one packet and eight unique intent rows.

## Replay Result

Run-36 after repair produced one packet, eight packet-bound rows, eight `held` states, eight fallback
eligibilities, and zero sends. A second processing pass returned `already_exists`, the same packet
ID, eight existing rows, and zero duplicate packet or intent.

Weekend, Sunday, XKRX holiday, and normal-session producer-role fixtures retain the shared calendar
guard. The 2026-08-22 orphan reconciliation history is unchanged. Macro temporal and investor-flow
payloads survive packet construction without changes to their selection or semantics.

Relevant regression suite: 385 passed. Full repository suite: 1,428 passed with one pre-existing
Starlette deprecation warning.
