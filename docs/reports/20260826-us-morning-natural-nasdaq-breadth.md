# 2026-08-26 US Morning Nasdaq Breadth Audit

## Verdict

```text
NASDAQ_BREADTH_NATURAL = SAFE_PUBLICATION_PENDING
NYSE_BREADTH_NATURAL = UNAVAILABLE
NASDAQ_BREADTH_MESSAGE_VALUE_ADD = NOT_OBSERVED
STALE_BREADTH_INJECTED = 0
BREADTH_SCOPE_MISLABEL = 0
```

## Exact-Session Check

| Item | Value |
|---|---|
| Packet session | `2026-08-25` |
| Provider | `NASDAQ_TRADER_YTD` |
| Retrieval | `2026-08-26 08:07:07.128972 KST` |
| Source latest row | `2026-08-21` |
| Publication state | `PUBLICATION_PENDING` |
| Contract | `structured-market-context-v1` |
| Raw payload SHA-256 | `6297c8d983ad63b7beed1e8e42edc5465558b6535f12d6a03d2682e31e0cdb81` |

The source did not contain the packet session. The envelope correctly emitted `nasdaq_breadth:exact_session_not_published`; `cross_section` remained null. No `2026-08-21` advances/declines row was injected into the `2026-08-25` packet.

NYSE breadth remained explicitly unavailable and was not inferred from Nasdaq. The delivered digest made no breadth claim, so there was no scope generalization. Natural breadth value-add was not observed because exact-session data had not been published.
