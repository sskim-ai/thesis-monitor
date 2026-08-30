# Track A — Decision-Aware Change-Condition Wording

Fix impossible self-transition wording in BUY/HOLD/SELL decision messages.

Mandatory control:
003690 is currently accepted HOLD and must not say "보유 판단으로 낮춘다".

Generalize by current accepted decision:
- BUY downside → HOLD/SELL reassessment or BUY-confidence reduction
- HOLD upside → BUY reassessment
- HOLD downside → SELL/negative reassessment or HOLD-confidence reduction
- SELL upside → HOLD/BUY reassessment
- SELL further downside → stronger SELL conviction, not "SELL로 낮춤"

No decision retuning.
No automatic trade triggers.
