# KR Market Internal AI / Fallback Parity

The adaptive renderer and deterministic daily digest consume the same canonical size and sector
claims. Both render this exact hierarchy once:

```text
📊 시장 내부

규모별
• KOSPI: ...
• KOSDAQ: ...

업종 상대 강세
• KOSPI: ...
• KOSDAQ: ...

업종 상대 약세
• KOSPI: ...
• KOSDAQ: ...
```

The run-42 replay preserved six size source refs and twelve sector source refs. All 18 percentage
tokens and the four TOP3 ranked lists match the previous production-equivalent payload. Only the
layout and scoped label presentation changed.

`AI_FALLBACK_MARKET_INTERNAL_DATA_PARITY = PASS`  
`AI_FALLBACK_MARKET_INTERNAL_LAYOUT_PARITY = PASS`  
`DATA_VALUE_DIFF = 0`  
`TOP3_RANKING_DIFF = 0`  
`EVIDENCE_SELECTION_DIFF = 0`  
`NUMERIC_PROVENANCE_DIFF = 0`

