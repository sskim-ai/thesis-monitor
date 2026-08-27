# KR Pre-Enable Artifact Index

Instruction commit: `f161bc1c724cfd431efaaa458af61e02a378daeb`
Base: `de352342f15a75069289f35f00b4bd24ddcdd19f`
Implementation: `7d2823c236c458cf76c77faae043c6288e46e65e`

This report set is intentionally fail-closed: the candidate and all data gates pass, but no exact
test-delivery or received-message proof exists because a dedicated sink is not configured.

Required reports: 16/16. Machine-readable reports: 3/3.

## Validation

| Check | Result |
| --- | --- |
| Focused | 55 passed |
| Full pytest | 1765 passed, 1 upstream warning |
| Ruff | PASS |
| git diff --check | PASS |
| Investment / Chart Knowledge | PASS / PASS |
| Public Action / operationId | 0.4.5 / 20 of 20 unique |
| API health | PASS |
| Implementation CI | [PASS](https://github.com/sskim-ai/thesis-monitor/actions/runs/33065959938) |

Completion bundle: `20260827-kr-market-preenable-test-send-and-bounded-enablement-bundle.zip`.
