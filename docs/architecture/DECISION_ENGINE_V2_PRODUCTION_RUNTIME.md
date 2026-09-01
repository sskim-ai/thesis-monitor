# Decision Engine V2 Production Runtime

Contract: `v2-accepted-production-runtime-v2`

```text
immutable review packet
  -> packet-owned technical context
  -> canonical decision evidence
  -> signed-in Codex CLI (`gpt-5.6-sol`, `xhigh`)
  -> candidate and adjudication
  -> accepted decision plan
  -> accepted-only renderer
```

The V2 runtime does not fetch local OHLCV. It consumes safe packet-owned feature facts bound to a
`technical_context_id`, timeframe, completed bar, key, and value. Low-level duplicated technical
facts may be omitted from prose prompts while their status/quality remains visible.

`PARTIAL_SAFE`, `UNAVAILABLE`, and `INVALID` contexts are explicit limitations. They do not map to a
fixed decision and do not kill a cohort. The renderer still consumes only accepted decisions; raw
or unresolved candidates remain invisible.

Price Structure, valuation, Public Action 0.4.5/schema 4, Telegram routes, deterministic fallback,
accepted-decision ownership, and scheduler configuration are unchanged.
