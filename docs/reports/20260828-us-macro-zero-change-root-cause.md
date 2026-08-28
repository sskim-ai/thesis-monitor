# US Macro Zero-Change Root Cause

Run-43 selected `market:relative:SOXX:SPY` for `MACRO_CONTEXT`. The Fact type was
`market_sector_relative`, while the legacy exclusion checked only `market_relative`. The selected
Fact had no macro change field, so the plan converted the missing value to the display status
`변화 없음` and mechanically appended `했습니다.`. The final renderer trusted stored
`claim_text`, exposing `변화 없음했습니다.`.

The repair uses a positive macro Fact registry, omits generic zero/missing changes, renders
specific semantics from the canonical Fact, and revalidates stored plans at the final renderer.

`MACRO_ZERO_CHANGE_ROOT_CAUSE = PASS`
