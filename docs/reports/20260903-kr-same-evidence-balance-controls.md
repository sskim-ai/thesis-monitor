# 2026-09-03 KR Same-Evidence Balance Controls

## Frozen Identity

- Packet: `2026-09-02-kr-run-52-d077cd42b44c`
- Controls: `000660`, `003690`, `005930`, `047810`
- Fresh signed-in Codex CLI executions per control: `3`
- Reasoning effort: `xhigh`
- Candidate input and per-ticker evidence fingerprints: identical across runs

## Results

| Ticker | fresh-1 | fresh-2 | fresh-3 | Accepted max distance |
| --- | --- | --- | --- | --- |
| 000660 | HOLD, 4.5:5.5 | HOLD, 4.5:5.5 | HOLD, 4.5:5.5 | 0.0 |
| 003690 | HOLD, 5:5 | HOLD, 5:5 | HOLD, 5:5 | 0.0 |
| 005930 | SELL, 4:6 | SELL, 4:6 | SELL, 4:6 | 0.0 |
| 047810 | HOLD, 4.5:5.5 | HOLD, 4.5:5.5 | HOLD, 4.5:5.5 | 0.0 |

For all four controls:

- candidate label boundary crossings: `0`
- accepted label boundary crossings: `0`
- unexplained same-evidence accepted drift: `0`
- identity mismatch: `0`
- majority voting: `0`

`TRACK_B_VARIANCE_ADJUDICATION = PASS`

The result is diagnostic evidence, not a production consensus mechanism. Every
fresh run was accepted independently under the same frozen evidence contract.
