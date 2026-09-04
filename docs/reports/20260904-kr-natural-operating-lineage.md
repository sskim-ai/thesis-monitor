# 2026-09-04 KR Natural Operating Lineage

## Result

- `MAIN_SHA=906b092749511dc42d5799ed335165819efee2ea`
- `OPERATING_SHA=906b092749511dc42d5799ed335165819efee2ea`
- `OPERATING_REPAIR_STATE=KR_US_INTEGRATED`
- KR repair final `90cc52231c7343056c853c355ea90dfea10de25b`: operating ancestor
- US repair final `deb4dc511aafa6e435b0af00436d690e2e498c0b`: operating ancestor
- Integration lineage: `d365c31` -> `3b413cf` -> `e43d3c` -> `f23e973` -> `906b092`

## Runtime Revisions

| Layer | Revision / contract |
|---|---|
| Producer entrypoint | `app/jobs/monitor_daily.py`; last relevant commit `d00741a` |
| Regular review | `daily-review-v3.10`, output schema `4` |
| Explicit V2 runtime | `v2-accepted-production-runtime-v1` |
| Explicit V2 output | `v2-accepted-production-output-v1` |
| V2 model | signed-in Codex CLI `0.148.0-alpha.15`, `gpt-5.6-sol`, `xhigh` |
| Pilot | `ai-assisted-pilot-v3` |
| Renderer | `ai-assisted-pilot-renderer-v3` |
| Delivery lifecycle | `ai-delivery-lifecycle-v1` |
| Delivery eligibility | `ai-delivery-eligibility-v1` |

The operating checkout was clean and exactly matched `origin/main`. No missing-repair explanation applies.
