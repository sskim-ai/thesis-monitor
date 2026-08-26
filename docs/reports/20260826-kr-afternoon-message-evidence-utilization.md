# 2026-08-26 KR Afternoon Message Evidence Utilization

| Evidence available in active packet | Sent market digest use | Result |
|---|---|---|
| KOSPI/KOSDAQ close and return | 0 | omitted |
| KOSPI/KOSDAQ breadth | 0 | omitted |
| Foreign/institution/retail aggregate flow | 0 | omitted |
| KOSPI size context | 0 | omitted |
| Same-session sector context | 0 | omitted |
| KR close FX | 3 pairs | used |
| Prior US macro/price context | multiple paragraphs | used as primary body |

The packet acquisition path was complete, but the deterministic digest renderer consumed only KR close FX before reusing the US morning macro body. The omission is therefore downstream evidence-utilization loss, not provider absence.

`MATERIAL_INFORMATION_LOSS > 0` and `KR_MARKET_DIGEST_LOCAL_FIRST = FAIL`.
