# Run-51 Market Night Renderer Replay

The repaired renderer inserts exactly one canonical section before the existing next-check block:

```text
한국 야간선물 · 09/01 새벽 종료 · 08/31 주간장 대비
• KOSPI200 최근월물 1,064.50 · -3.35pt (-0.31%)
• KOSDAQ150 최근월물 1,432.80 · -7.30pt (-0.51%)
```

The downloadable machine replay preserves the production glyph in the actual section. Both
canonical Fact IDs are packet-owned and rendered. Removing only this section recovers the frozen
baseline byte-for-byte. No Telegram send or production delivery intent was created.
