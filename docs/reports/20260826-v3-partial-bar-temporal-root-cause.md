# Price Structure v3 Partial-Bar Temporal Root Cause

The prior normalizer excluded future dates but treated every provider-present bar as completed.
Pivot confirmation counted right-side array positions, so SK hynix's incomplete August monthly bar
incorrectly completed the June high's `2/2` confirmation window.

The repair binds each bar to exchange-calendar period bounds and observation time. Only complete
bars may populate `confirmation_bar_ids`; partial bars remain current context or provisional
evidence. Root cause classification: `P1_ANALYSIS_INTEGRITY`, bounded and closed retrospectively.
