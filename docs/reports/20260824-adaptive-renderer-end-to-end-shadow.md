# Adaptive Renderer End-to-End Shadow

`immutable packet -> Free Analyst -> structured analysis -> synthesis validator -> selector -> selected renderer -> safety validators -> shadow would-send`

| Benchmark | Synthesis | Selector | Renderer | Safety | Final Mode |
|---|---|---|---|---|---|
| kr-193419-01-__DAILY_DIGEST_KR__ | PASS | PASS | MINIMAL_VNEXT | PASS | ADAPTIVE_SHADOW_WOULD_SEND |
| kr-193419-02-000660 | PASS | PASS | DIRECT_ANALYST | PASS | ADAPTIVE_SHADOW_WOULD_SEND |
| kr-193419-03-003690 | PASS | PASS | CONCISE_HYBRID | PASS | ADAPTIVE_SHADOW_WOULD_SEND |
| kr-193419-04-005490 | PASS | PASS | DIRECT_ANALYST | PASS | ADAPTIVE_SHADOW_WOULD_SEND |
| kr-193419-05-005930 | PASS | PASS | DIRECT_ANALYST | PASS | ADAPTIVE_SHADOW_WOULD_SEND |
| kr-193419-06-010120 | PASS | PASS | CONCISE_HYBRID | PASS | ADAPTIVE_SHADOW_WOULD_SEND |
| kr-193419-07-012450 | PASS | PASS | CONCISE_HYBRID | PASS | ADAPTIVE_SHADOW_WOULD_SEND |
| kr-193419-08-086280 | PASS | PASS | CONCISE_HYBRID | PASS | ADAPTIVE_SHADOW_WOULD_SEND |
| us-run26-wulf-rr-sensitive | PASS | PASS | CONCISE_HYBRID | PASS | ADAPTIVE_SHADOW_WOULD_SEND |
| us-run28-crcl-expectation-valuation | PASS | PASS | CONCISE_HYBRID | PASS | ADAPTIVE_SHADOW_WOULD_SEND |
| us-run32-googl | PASS | PASS | CONCISE_HYBRID | PASS | ADAPTIVE_SHADOW_WOULD_SEND |
| us-run32-mu | PASS | PASS | CONCISE_HYBRID | PASS | ADAPTIVE_SHADOW_WOULD_SEND |

Fallback simulation is covered by focused tests: invalid Free Analyst output produces no Free Analyst message; selector or selected-renderer failure selects the existing safe vNext shadow path; a failed safe path would use deterministic shadow fallback. No delivery call is present.
