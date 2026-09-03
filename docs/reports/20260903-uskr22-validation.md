# USKR22 Structured Autonomy Validation

## Code validation

- Focused structured-autonomy suite: `16 passed`
- Full pytest: `2177 passed, 1 warning`
- Ruff: `PASS`
- `git diff --check`: `PASS`
- Implementation SHA: `2b348d9d1b6091b4a04a9d3952e3dd69babbe30f`

The warning is the existing Starlette `httpx` deprecation notice from `fastapi.testclient`; it did not fail the suite.

## Frozen-source validation

- Required KR repair base contained: `PASS`
- US source packet: `2026-09-03-us-run-53-055ae8ea01f6`
- KR source packet: `2026-09-03-kr-run-54-f19bb379daa7`
- Later KR reuse packet used as evidence: `false`
- Canonical evidence fingerprints: `22/22`
- Price-map fingerprints: `22/22`
- Fresh fact collection: `0`
- Cross-market fact leakage: `0`
- Cross-generation fact leakage: `0`

## First blind run

- Signed-in Codex CLI: `PASS`
- Model: `gpt-5.6-sol`
- Reasoning effort: `xhigh`
- Candidates generated: `22/22`
- Candidate/message structural validation: `21/22`
- Unsupported price numeric: `0`
- Top-label/entry ambiguity: `0`
- AVOID actionable-entry leakage: `0`
- KR accounting/valuation safety: `PASS`
- ADR/security-basis safety: `PASS`
- Substantive repeated spans: `1`

`086280` cited `decision-evidence:5979d204f48a93a7626`, which does not exist in its frozen canonical evidence. WRD and WULF repeated the same substantive confirmation sentence. Neither candidate output nor sentence was repaired, overridden, or regenerated.

## Stability phase

Runs A/B/C: `NOT_RUN_FIRST_GATE_FAILED`.

The work instruction allows A/B/C only after a structurally valid first run. Stopping at that boundary preserved `POST_RESULT_TUNING = 0` and prevented an invalid first result from being silently normalized away.

## Verdict

`PROMOTION_READINESS = NOT_READY`

Production decision mutation, production renderer integration, recipient send, and main merge all remained `0`.
