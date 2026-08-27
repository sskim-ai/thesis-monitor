# KR Rollout Validation

## Revisions

- Work instruction: `0c95ddc9be319dbacc5ce1d824802e0c3c72fed1`
- Base: `97d90815caf18a1daad1833dfbe4eb04b364f975`
- Implementation: `a7de99c2d1d1211615e0fcbf4bd3eadc06d957fb`
- GitHub Actions: run `33071858051`, Test PASS, Lint PASS

## Results

| Check | Result |
| --- | --- |
| Track A/B/C-focused regression | `162 passed` |
| Bounded non-sector-index repair | `25 passed` |
| Full pytest | `1778 passed, 1 upstream deprecation warning` |
| Ruff | PASS |
| `git diff --check` | PASS |
| Investment Knowledge v3.1 | PASS, `dc747fff856530e82477851cbd0bb16c5876770de514a9c02cfd5a26ac91c312` |
| Chart Knowledge v1 | PASS, `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b` |
| Public Action | `0.4.5` unchanged |
| Output schema | `4` unchanged |
| operationId | `20/20` unique |
| API health before promotion | PASS at `127.0.0.1:8766` |
| Run-42 immutable archive hash parity | PASS |
| User-visible runtime diff | `0` with both guards default OFF |

## Safety

Telegram test delivery, production delivery intent, manual task, pilot mutation, DB mutation,
archive rewrite, and Production Assist changes are all `0`. A dedicated test sink was not
configured, so Track C is `NOT_SENT` and Track D is `DO_NOT_ENABLE`.

`OPEN_P0 = 0`  
`OPEN_MATERIAL_P1 = 1` (`dedicated_test_sink_not_configured`)  
`KR_ROLLOUT = NOT_ENABLED`
