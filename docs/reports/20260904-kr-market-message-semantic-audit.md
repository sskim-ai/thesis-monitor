# 2026-09-04 KR Market Message Semantic Audit

## Relative Weakness

`업종 상대 약세` means the bottom-ranked safe sector-index returns within each market cross-section, not necessarily an absolute negative return. The underlying KOSDAQ fields use `basis=actual_sector_breadth` and `metric_role=actual_sector_breadth`:

| Sector | Absolute return | Source ref | Interpretation |
|---|---:|---|---|
| 섬유/의류 | -0.49% | `kiwoom:ka20003:KOSDAQ:116:2026-09-04` | bottom-ranked and negative |
| 종이/목재 | +0.28% | `kiwoom:ka20003:KOSDAQ:117:2026-09-04` | bottom-ranked but positive |
| 통신 | +0.34% | `kiwoom:ka20003:KOSDAQ:128:2026-09-04` | bottom-ranked but positive |

Therefore the two positive values are not a semantic contradiction. They are relative laggards in a broadly rising market.

## Market-Wide Participant Flow

| Market | Foreign | Institution | Retail | Basis |
|---|---:|---:|---:|---|
| KOSPI | +958.5bn KRW | +1,872.5bn KRW | -4,377.8bn KRW | `KRX_NXT_INTEGRATED`, 2026-09-04 |
| KOSDAQ | +378.1bn KRW | +166.3bn KRW | -530.4bn KRW | `KRX_NXT_INTEGRATED`, 2026-09-04 |

Source refs are the six `kiwoom:ka10051:<market>:<participant>:2026-09-04` facts. `MARKET_FLOW_PROVENANCE=PASS`.
