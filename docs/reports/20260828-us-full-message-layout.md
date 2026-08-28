# US Full Message Layout

Contract: `us-morning-full-message-v1`

Section order: `HEADER -> INDEX_BLOCK -> MARKET_INTERNAL -> MACRO_CONTEXT -> NEXT_CHECK`

The index block and selected sector numbers are deterministic. Adaptive rendering may retain only
a bounded next check. The optional night-futures and macro sections are omitted when their gates do
not pass.
