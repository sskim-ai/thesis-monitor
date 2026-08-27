# KR Market Internal Layout Contract

`📊 시장 내부` has one blank line before its first subsection. `규모별`, `업종 상대 강세`, and
`업종 상대 약세` are standalone headings. Each available market scope owns one `• KOSPI:` or
`• KOSDAQ:` row, and subsections are separated by exactly one blank line.

The canonical plan remains partial-safe:

- an unavailable market scope creates no empty row;
- incomplete size tuples are omitted rather than fabricated;
- fewer than three safe sectors render only the safe rows;
- no empty subsection heading, nested bullet, or escaped bullet is produced;
- user-facing `leader` and `laggard` terms remain absent.

`MARKET_INTERNAL_FORMATTING_POLICY = PASS`  
`MARKET_INTERNAL_SECTION_LINEBREAKS = PASS`  
`SIZE_SECTION_READABILITY = PASS`  
`STRONG_SECTOR_SECTION_READABILITY = PASS`  
`WEAK_SECTOR_SECTION_READABILITY = PASS`

