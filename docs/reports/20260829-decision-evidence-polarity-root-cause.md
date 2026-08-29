# Decision Evidence Polarity Root Cause

- Date: `2026-08-29 KST`
- Instruction commit: `0bba7c9`
- Base: `483888edcd4afb64d108c667b47d7e9f6b5ba423`
- Implementation: `86b9fc44006c45431ccc1822131df3b4a74eb1ca`

`supporting_evidence` and `opposing_evidence` are relative to the final BUY/HOLD/SELL
classification. The old canary renderer treated their first entries as directional BUY/SELL
evidence. That assumption inverted SELL evidence ownership and could force neutral data-quality
facts into a directional section.

Exact negative controls:

- GOOGL HOLD: favorable trailing valuation and intact chart structure appeared under SELL.
- RXRX SELL: verified statement/security/book basis appeared under SELL.

The repair preserves decision-relative fields and adds independent structured directional
ownership. No sentence sentiment, ticker exception, decision recalibration, valuation policy, or
Price Structure rule is used to infer polarity.

`CANARY_SAFETY_DURING_REPAIR = TEMPORARILY_SUPPRESSED` until implementation CI and operating
promotion passed.
