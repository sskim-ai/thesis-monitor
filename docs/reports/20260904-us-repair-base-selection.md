# 2026-09-04 US Repair Base Selection

## Result

| Item | Evidence |
|---|---|
| Natural operating revision | `5d5f3363d3a762b62698943b1feb4fa121d0d0f9` |
| Selected base | `5d5f3363d3a762b62698943b1feb4fa121d0d0f9` |
| Repair branch | `codex/20260904-us-natural-tls-lease-validator-repair` |
| Work-instruction commit | `c6e2f94` |
| Core implementation commit | `1a50853` |
| Bounded quality repair commit | `21296c0` |
| Base contains natural revision | `PASS` |
| Shadow-only decision contract imported | `0` |
| Main merge | `0` |

The repair starts directly from the natural operating revision. The preceding Structured Autonomy A/B/C work remains on its isolated worktree at `8a1edfdd42f503f715c644688b890dcadf193abc`; no commit from that branch was merged or cherry-picked.

The work-instruction files were committed and pushed before implementation. The operating checkout and `origin/main` both remained at the natural revision throughout this repair.
