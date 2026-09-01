# KR Natural Live Root Cause

## Classification

- Primary class: `CODE_REGRESSION`
- Scope: `MIXED` (primary systemic V2 failure; secondary subject-specific legacy validator issue)
- Earliest stage: `OTHER`
- Earliest detail: `V2_GENERATION_SCHEMA_PATH_RESOLUTION_FAILED_BEFORE_MODEL_CALL`
- Data trigger: `NOT_DATA_TRIGGERED`
- V2 natural live: `FAIL`
- User delivery safety: `PARTIAL_SAFE` via 9/9 deterministic fallback

## Root cause

The natural V2 path combined a repository-relative `--output-schema data/ai_review/claims/...schema.json` with `cwd=data/ai_review/claims`. Codex therefore looked under a duplicated directory and exited before a model call. The schema had been written correctly; path ownership at invocation was wrong.

## Why the passing test did not catch it

The prior 22/22 preflight used an absolute output directory. The shared helper therefore received an absolute schema path, which remained valid under its cwd. Unit tests either checked prompt/binary selection or replaced `_invoke_signed_in_codex`; none executed the natural relative-path plus real-subprocess combination.

## Contributing factors

- Legacy fallback validation remained cohort-wide: final errors on 005930 and 047810 rejected the corrected AI bundle.
- 047810's `needs_review` state was correctly included and was not a source/packet failure.
- Codex state-DB warnings were non-causal; the fatal line is the schema read error.

## Open severity

- P0: `0`
- Material P1: `2`
- P2: `0`

1. **Natural V2 CLI path/cwd regression:** all eight fresh V2 candidates were prevented before model invocation.
2. **047810 legacy phantom numeric validation:** product identifiers `KF-21` and `FA-50` were parsed as unbound quantities. This is secondary and subject-specific.


## Verification

- Focused V2 runtime/service tests: `25 PASS`
- Full pytest: `2033 PASS` (`1` third-party deprecation warning)
- Ruff: `PASS`
- Deterministic report replay: `26` Markdown + `4` JSON, exact-delivery errors `0`
- Production mutation, repair, manual task, and manual send: `0`

`NEXT_ACTION = BOUNDED_DECISION_PIPELINE_REPAIR`

This investigation performs no repair. The bounded next task should first normalize natural V2 subprocess paths and add a real invocation-path regression test; the 047810 identifier tokenizer can then be repaired independently.
