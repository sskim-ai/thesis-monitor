# Price Structure v3 Fib Confluence Render Audit

- Instruction commit: `2ac7eaaede9cb8d9047173bbec5f2bd99c665573`
- Implementation: `4246efb4f8afa3516402d1df7864967c177ac6e7`
- Test run: `v3-renderer-run:2a7a4203cf52ba05d8f8`
- Dataset: `v3-current-dataset:252d923f98173a1f2638`
- Render: `v3-renderer-render:4fe27a16d89fa24af40e`
- Source current-data run: `v3-current-run:ff97be1d62a9810dc315`
- Target sessions: KR `2026-08-26`, US `2026-08-25`.

| Ticker | Policy | Rendered range | Result |
| --- | --- | --- | --- |
| 000660 | MATERIAL_RANGE_EXTENSION | 약 186.9만~191.6만원 | PASS |
| 003690 | MATERIAL_RANGE_EXTENSION | 약 1.42만~1.45만원 | PASS |
| 005490 | DISTINCT_RANGE | 약 38.6만~39.6만원 | PASS |
| 005930 | IDENTICAL_DISPLAY_RANGE | numeric repeat suppressed | PASS |
| 012450 | DISTINCT_RANGE | 약 104.7만~105.8만원 | PASS |
| 086280 | MATERIAL_RANGE_EXTENSION | 약 20만~20.6만원 | PASS |
| GOOGL | MATERIAL_RANGE_EXTENSION | 약 $346.04~$351.64 | PASS |
| HUT | MATERIAL_RANGE_EXTENSION | 약 $65.9~$67.49 | PASS |
| IBM | IDENTICAL_DISPLAY_RANGE | numeric repeat suppressed | PASS |
| WULF | DISTINCT_RANGE | 약 $18.73~$19.1 | PASS |
