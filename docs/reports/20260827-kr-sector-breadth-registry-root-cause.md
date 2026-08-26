# KR Sector Breadth Registry Root Cause

Run-40 had 1,961 numeric entries, 1,583 registered entries, and 378 unsupported entries. All 378
were six count paths across 63 `market_cross_section_sector` occurrences. Return and ratio paths
were already typed; component/listed counts were not.

A second provenance issue was found during classification: 20 same-name KOSPI/KOSDAQ sector pairs
shared a legacy fact ID. This affected 120 count occurrences. The repair adds six exact rules and
changes sector fact identity to include market scope and sector code. No wildcard or tolerance
change was used.

