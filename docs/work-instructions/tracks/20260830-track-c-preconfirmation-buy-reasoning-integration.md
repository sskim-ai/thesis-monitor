# Track C — Pre-Confirmation BUY Reasoning Integration

Allow BUY before full proof when the current price/expectations compensate for uncertainty.

Add PRE_CONFIRMATION_BUY flag when:
decision = BUY
and decisive evidence is EARLY/PARTIAL.

Also explicitly support:
CONFIRMED thesis + expensive pricing → HOLD/SELL.

Audit old HOLD change-conditions that effectively say:
"wait for confirmation, then BUY."

Do not bypass factual safety gates.
