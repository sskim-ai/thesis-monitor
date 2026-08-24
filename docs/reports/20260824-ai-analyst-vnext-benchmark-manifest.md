# AI Analyst vNext Benchmark Manifest

- Contract: `ai-analyst-vnext-shadow-v1`
- Instruction: `docs/work-instructions/20260824-ai-analyst-quality-vnext-shadow-benchmark.md`
- KR rehearsal: `2026-08-24-kr-live-rehearsal-193419`
- Benchmark messages: `12` (`KR 8`, `US 4`)
- Immutable packets: `4`
- Provider recollection: `0`
- Production mutation: `0`

## Benchmark Items

| ID | Market | Packet | Ticker | Evidence shape |
|---|---|---|---|---|
| kr-193419-01-__DAILY_DIGEST_KR__ | KR | 2026-08-24-kr-run-36-e4ac1c029c06 | __DAILY_DIGEST_KR__ | macro_temporal_digest |
| kr-193419-02-000660 | KR | 2026-08-24-kr-run-36-e4ac1c029c06 | 000660 | kr_dynamic_industry_and_supply |
| kr-193419-03-003690 | KR | 2026-08-24-kr-run-36-e4ac1c029c06 | 003690 | kr_dynamic_industry_and_supply |
| kr-193419-04-005490 | KR | 2026-08-24-kr-run-36-e4ac1c029c06 | 005490 | kr_dynamic_industry_and_supply |
| kr-193419-05-005930 | KR | 2026-08-24-kr-run-36-e4ac1c029c06 | 005930 | kr_dynamic_industry_and_supply |
| kr-193419-06-010120 | KR | 2026-08-24-kr-run-36-e4ac1c029c06 | 010120 | kr_dynamic_industry_and_supply |
| kr-193419-07-012450 | KR | 2026-08-24-kr-run-36-e4ac1c029c06 | 012450 | kr_dynamic_industry_and_supply |
| kr-193419-08-086280 | KR | 2026-08-24-kr-run-36-e4ac1c029c06 | 086280 | kr_dynamic_industry_and_supply |
| us-run26-wulf-rr-sensitive | US | 2026-08-19-us-run-26-cd80a8e4d373 | WULF | current_price_rr_sensitive_hpc |
| us-run28-crcl-expectation-valuation | US | 2026-08-20-us-run-28-9024def294e6 | CRCL | speculative_expectation_valuation |
| us-run32-googl | US | 2026-08-22-us-run-32-dde10ec6c9eb | GOOGL | fcf_heavy_cloud_platform |
| us-run32-mu | US | 2026-08-22-us-run-32-dde10ec6c9eb | MU | inventory_eligible_fcf_priority_memory |

## Source Locks

| Artifact | SHA-256 |
|---|---|
| /Users/sskim/Codex/thesis-monitor/data/ai_review/pilot/history/2026/08/2026-08-19-us-run-26-cd80a8e4d373/packet.json | 8d5f8fb627a3354a122aeffb2398b4007003d34aaa384827ee5a8ac826c20067 |
| /Users/sskim/Codex/thesis-monitor/data/ai_review/pilot/history/2026/08/2026-08-20-us-run-28-9024def294e6/fallback-messages.json | efc2b629e0f860ba9b09e971e71fddd0c565eb58d926f78232f088170e9fad45 |
| /Users/sskim/Codex/thesis-monitor/data/ai_review/pilot/history/2026/08/2026-08-20-us-run-28-9024def294e6/packet.json | 03bed9b77e58e390dcb2de2790b61f3d8d86815ffd00b550420e5b1e072a9c5f |
| /Users/sskim/Codex/thesis-monitor/data/ai_review/pilot/history/2026/08/2026-08-22-us-run-32-dde10ec6c9eb/deterministic-messages.json | a5025d04bd73986433691f34bf4c5091d3039443c94853fe9a616b23d3f3dcc4 |
| /Users/sskim/Codex/thesis-monitor/data/ai_review/pilot/history/2026/08/2026-08-22-us-run-32-dde10ec6c9eb/fallback-messages.json | c40b7b2f11432e224f33dc862742ae409aa76456b9a019bd84d3271f31ce52cf |
| /Users/sskim/Codex/thesis-monitor/data/ai_review/pilot/history/2026/08/2026-08-22-us-run-32-dde10ec6c9eb/packet.json | 36237ff3991bcc8a9feccc286199b70f55e26d068aaba379b0d41a3fffed6a99 |
| docs/reports/20260819-run26-ai-validation-repair.md | 91a5d3f534b16be34a3da461ea4ce01d2dde3f299a09060824071a128e64d114 |
| docs/reports/20260819-run26-targeted-repair-preview.md | 3f45e3055790cf8d41c09b3f85105689326c1662f31fe78db4bc391dbe03fec4 |
| docs/reports/20260820-run28-repaired-ai-output.json | 7599f43c98c283dbdce7d76fbbb4e99f37814118e4a24f3ea92dacf63fd321f3 |
| docs/reports/20260820-run28-runtime-quality-receipt.json | 7964a41e92271f76606706f545b37e90f792ff51351c44088f664a2e397cb374 |
| docs/reports/20260822-us-run32-replay-artifacts/run32-repaired-candidate.json | ac9c4b6b865707ef6224448551b642607c865480a9d30a121c37ec5f1394b281 |
| docs/reports/20260822-us-run32-replay-artifacts/run32-replay-result.json | 04de674c91efdcc9ad032459707be53b7098fa7959ba6f97a347c7562a73342e |
| docs/reports/20260824-rehearsal-193419-ai-fallback-parity.md | 86e39330668a0543d4dbb19197c78d5108131f4f0985d073cfe642b9a3455f34 |
| docs/reports/20260824-rehearsal-193419-post-repair-message-bundle.md | d3457241d53aac3267b63116546586aa72d1bf529c1328ea24a90764dd9509f4 |
