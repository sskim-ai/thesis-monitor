# 2026-08-26 KR Afternoon Message Quality

## P1 Findings

1. **KR local-first digest failure.** The natural digest showed local FX and then led with US S&P500/semiconductor, US macro axes, and US assumptions. It omitted the available same-session KOSPI/KOSDAQ direction, breadth, flows, and size evidence. This materially weakens the intended KR close interpretation.
2. **Structured sector numeric registry incompleteness.** All three run-40 packets had `ready_for_ai=false`: 1,961 numeric entries, 1,583 registered, and 378 unsupported sector breadth count paths. Deterministic fallback remained safe, but the natural AI path could not become eligible.

## Passed Boundaries

- Market flows were not promoted to company fundamental changes.
- KOSPI and KOSDAQ values were not conflated because neither was rendered.
- Concentration prose was suppressed after reconciliation failure.
- KRX pending data was not presented as current.
- Price Structure v3 fields did not leak into the natural message.
- Exact stock payloads were sent once and retained their existing price, supply, valuation, and evidence safety contracts.

`OPEN_P0 = 0`, `OPEN_MATERIAL_P1 = 2`.
