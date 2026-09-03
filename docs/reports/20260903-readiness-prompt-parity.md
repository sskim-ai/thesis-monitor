# Readiness and Prompt Parity

`build_decision_evidence_packet` now applies the same `STOCK_V2` projection used by numeric
readiness. Frozen run-53 produced 14 evidence packets with:

- included numeric occurrence without a prompt-owned canonical fact: 0
- legacy prompt canonical fact-set difference: 0
- standalone market surface sent directly to `STOCK_V2`: 0
- `market:night_futures` references in production-equivalent V2 context: 0

Market facts enter a stock prompt only after the existing transmission selector copies them into
that stock catalog and adds explicit `STOCK_V2` ownership.

The same projection audit on frozen KR run-52 produced eight evidence packets, zero included
numeric/prompt mismatch, and zero legacy prompt fact-set difference.
