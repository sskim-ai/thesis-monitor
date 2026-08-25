# KR Run Valuation Post-Repair Replay

- Packet: `2026-08-25-kr-run-38-6cd8c5d5091b`
- Replay source: immutable operating archive
- Provider recollection: `0`
- Candidate: rejected natural candidate SHA `43a6ef4a7ce8fca137d8c0483e08a6557d0ea23b512d03cfc4dab3ee4f563330`
- Implementation: `b39c2ea38a8d5d3466889a9da394df05ad95701a`

## Result

| Gate | Before | After |
| --- | ---: | ---: |
| valuation ref errors | 2 | 0 |
| numeric binding rejected | 2 | 0 |
| bound numeric claims | 121 | 123 |
| full candidate hard errors | 2 | 0 |

The replay used the archived packet and candidate without rewriting either.
The post-repair binder resolved both PBR references, and
`validate_ai_review_output` against the current read-only operating state
returned a validated output with `errors=[]`.

Reachability after the repaired hard gate:

- Free Analyst candidate validation: `REACHABLE`
- Adaptive Renderer: `REACHABLE`
- bounded canary selector: `REACHABLE`
- delivery performed: `0`

## Validation

- focused: `18 passed`
- full pytest: `1513 passed`
- Ruff: `PASS`
- `git diff --check`: `PASS`
- GitHub Actions implementation SHA: `PASS` ([run 32830227835](https://github.com/sskim-ai/thesis-monitor/actions/runs/32830227835))
- Public Action: `0.4.5` unchanged
- schema: `4` unchanged

Status: `KR_VALUATION_REPLAY = PASS`.
