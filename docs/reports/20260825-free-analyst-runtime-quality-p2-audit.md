# Free Analyst Runtime-Quality P2 Audit

- Instruction commit: `3df40de53cf35ff5c47d662e0a14fbf9e30be3f7`
- Implementation base: `f7d2552185ff2ff6d932337e7555ce02f87fa613`
- US packet: `2026-08-25-us-run-37-7e04812311c2`
- KR packet: `2026-08-24-kr-run-36-e4ac1c029c06`
- Provider recollection: `0`
- Manual Telegram / Task / DB mutation: `0 / 0 / 0`

| Check | Existing current AI | Full Free Analyst + Adaptive replay |
| --- | ---: | ---: |
| Price particle errors | 12 | 0 |
| Repeated price sentences | 5 | 0 |
| Broad rendered repetition | N/A | 5 |
| Full-cohort legacy receipt | FAILED | FAILED |
| Limited-canary scoped receipt | N/A | PASSED |

The known price P2 is `NOT_REPRODUCED_IN_NEW_PATH`. Two broad Free Analyst synthesis sentences repeat across the full 13-stock cohort, so full rollout remains out of scope and the limited two-stock canary stays below the unchanged duplicate threshold. No threshold was changed.
