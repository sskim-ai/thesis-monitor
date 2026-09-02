# Track D — Run-51 Replay / Cross-Market Regression / Merge / Live Guard

Preserve:
- V2 absolute-path repair
- canonical identifier numeric provenance
- CPNG/HUT technical recovery
- PARTIAL_SAFE semantics
- exact accepted-decision ownership
- market numeric provenance
- exactly-once delivery

Run:
1. run-51 full isolated replay
2. run-51 daily-review secondary replay
3. run-51 night-futures market replay
4. US14 production-equivalent V2
5. KR8 production-equivalent V2
6. dedicated test sink (22 if cohort unchanged)
7. full tests / Ruff / CI

Allow only a documented bounded scheduler runtime-environment diff if required.
Scheduler timing and ownership must not change.

No historical production resend.

Merge only with:
- P0/P1 0/0
- scheduler-context Codex probe PASS
- run-51 V2 model reached/candidates 14
- daily-review quality PASS
- night-futures session semantics proven
- cross-market regressions PASS

Then wait for ordinary natural US/KR live proof.
