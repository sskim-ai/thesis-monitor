# KR Failure Trigger Proof

## Exact trigger

1. Claim stored `final_output_path` as repository-relative.
2. `accepted_v2_production_paths()` returned a repository-relative schema path.
3. `_invoke_signed_in_codex()` passed that full relative path to `--output-schema`.
4. The same call set `cwd` to `data/ai_review/claims`.
5. Codex resolved `/Users/sskim/Codex/thesis-monitor/data/ai_review/claims/data/ai_review/claims/2026-09-01-kr-run-50-44156fe0fa76--daily-review-v3.10--dc747fff8565--65f0c307-72aa-4f45-9154-25981f5a3eaf.decision-v2-schema.json`, which does not exist.
6. The real schema `/Users/sskim/Codex/thesis-monitor/data/ai_review/claims/2026-09-01-kr-run-50-44156fe0fa76--daily-review-v3.10--dc747fff8565--65f0c307-72aa-4f45-9154-25981f5a3eaf.decision-v2-schema.json` exists.
7. CLI stopped before prompt/model/candidate work.

Observed primary and backup error:

```text
Failed to read output schema file data/ai_review/claims/2026-09-01-kr-run-50-44156fe0fa76--daily-review-v3.10--dc747fff8565--65f0c307-72aa-4f45-9154-25981f5a3eaf.decision-v2-schema.json: No such file or directory (os error 2)
```

Read-only path-resolution negative control: root-relative schema exists; cwd-prefixed duplicate does not. Passing preflight used an absolute schema and produced 8/8 candidates.

No ticker, fact, field, or value triggered this error.

`KR_FAILURE_TRIGGER = NOT_DATA_TRIGGERED`
