# 2026-08-25 KR Investor Flow Natural Review

## Signal And Holding Summary

| Ticker | As of | Foreign holding | Primary signal | Basis | Quality | Actual user-visible summary |
| --- | --- | --- | --- | --- | --- | --- |
| 000660 | 2026-08-25 | 50.92% | foreign_exit_broad_absorption | 20D | mixed_absorption | 20일 기준 외국인 순매도·흡수 주체 분산 |
| 003690 | 2026-08-25 | 26.52% | material_other_participant_flow | 20D | foreign_led | 20일 기준 기타 투자주체 영향 큼 |
| 005490 | 2026-08-25 | 32.54% | material_other_participant_flow | 20D | foreign_led | 20일 기준 기타 투자주체 영향 큼 |
| 005930 | 2026-08-25 | 46.74% | foreign_exit_broad_absorption | 20D | distribution | 분산/매도 우위 · 20일 기준 외국인 순매도·흡수 주체 분산 |
| 010120 | 2026-08-25 | 18.27% | mixed_window_flow | mixed | foreign_led | 5일·20일 흐름 혼재 |
| 012450 | 2026-08-25 | 45.55% | mixed_window_flow | mixed | strong_joint | 5일·20일 흐름 혼재 |
| 086280 | 2026-08-25 | 46.48% | material_other_participant_flow | 20D | strong_joint | 20일 기준 기타 투자주체 영향 큼 |

## Full Participant Reconciliation

| Ticker | Window | Foreign | Institution | Retail | Other corp | Domestic foreign | Net | Reconciliation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 000660 | 1D | -1,235,854주 | +198,352주 | +385,536주 | +650,428주 | +1,538주 | +0주 | complete_without_provider_total |
| 000660 | 5D | -3,030,056주 | -233,338주 | +647,479주 | +2,613,675주 | +2,240주 | +0주 | complete_without_provider_total |
| 000660 | 20D | -3,518,894주 | +684,816주 | +310,090주 | +2,523,697주 | +291주 | +0주 | complete_without_provider_total |
| 003690 | 1D | +3,694주 | -3,067주 | +4,235주 | -5,037주 | +175주 | +0주 | complete_without_provider_total |
| 003690 | 5D | +10,717주 | +38,973주 | -3,228주 | -46,774주 | +312주 | +0주 | complete_without_provider_total |
| 003690 | 20D | +879,534주 | -65,809주 | -469,800주 | -342,449주 | -1,476주 | +0주 | complete_without_provider_total |
| 005490 | 1D | -150주 | +25,976주 | -25,373주 | -736주 | +283주 | +0주 | complete_without_provider_total |
| 005490 | 5D | +58,541주 | +104,178주 | -157,301주 | -5,815주 | +397주 | +0주 | complete_without_provider_total |
| 005490 | 20D | +223,813주 | -68,834주 | -131,281주 | -24,336주 | +638주 | +0주 | complete_without_provider_total |
| 005930 | 1D | -5,004,955주 | +203,484주 | +2,784,822주 | +2,015,008주 | +1,641주 | +0주 | complete_without_provider_total |
| 005930 | 5D | -10,289,389주 | -7,082,519주 | +13,294,468주 | +4,062,302주 | +15,138주 | +0주 | complete_without_provider_total |
| 005930 | 20D | -8,044,523주 | -6,098,542주 | +9,575,833주 | +4,545,071주 | +22,161주 | +0주 | complete_without_provider_total |
| 010120 | 1D | +41,890주 | -18,160주 | -21,512주 | -1,457주 | -761주 | +0주 | complete_without_provider_total |
| 010120 | 5D | -163,548주 | -261,162주 | +424,793주 | -169주 | +86주 | +0주 | complete_without_provider_total |
| 010120 | 20D | +534,392주 | -456,690주 | -48,410주 | -27,571주 | -1,721주 | +0주 | complete_without_provider_total |
| 012450 | 1D | -6,119주 | +1,517주 | +4,336주 | +266주 | +0주 | +0주 | complete_without_provider_total |
| 012450 | 5D | -52,257주 | +35,490주 | +16,160주 | +302주 | +305주 | +0주 | complete_without_provider_total |
| 012450 | 20D | +70,318주 | +8,929주 | -80,901주 | +1,438주 | +216주 | +0주 | complete_without_provider_total |
| 086280 | 1D | +48,878주 | +73,358주 | -121,455주 | -728주 | -53주 | +0주 | complete_without_provider_total |
| 086280 | 5D | +50,913주 | +61,258주 | -106,822주 | -5,192주 | -157주 | +0주 | complete_without_provider_total |
| 086280 | 20D | +191,547주 | +122,815주 | -301,387주 | -11,161주 | -1,814주 | +0주 | complete_without_provider_total |

All 21 stock/window rows reconcile to zero across the five supported participant categories. The
user-visible message intentionally labels only foreign/institution/retail as `주요 3주체`; where
omitted participant flow was material, the summary says `기타 투자주체 영향 큼` or uses a broad
absorption description instead of inventing a residual actor.

- Market-wide investor flow: `NOT_OBSERVED`
- Top-N flow concentration: `Unknown`; no compatible market-wide value input
- Residual-derived participant claims: `0`
- Unsupported absorber attribution: `0`
- Institution double count: `0`
- Mixed-window timeless attribution: `0`

`KR_INVESTOR_FLOW_NATURAL = LIVE_PASS` for stock-level quantity flow.
