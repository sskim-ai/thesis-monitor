# Track A — BUY:SELL Directional Balance

Implement:
- candidate buy/sell balance summing to 10
- accepted balance in accepted_decision_plan
- BUY/HOLD/SELL label derivation
- HOLD = current neutral band, not prior-decision carry-forward
- user-facing `판단 균형: BUY x : SELL y`

Anchors:
6:4 BUY
5:5 HOLD
4:6 SELL
5.5:4.5 HOLD

No probability language.
No fixed universal factor weights.
No raw candidate authority.

Focused tests must include prior BUY/SELL transitioning to 5:5 HOLD.
