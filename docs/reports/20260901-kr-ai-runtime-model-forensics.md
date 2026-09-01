# KR AI Runtime Model Forensics

## Configured runtime

- Signed-in Codex CLI model: `gpt-5.6-sol`
- Reasoning effort: `xhigh`
- Sandbox: `read-only`
- Batch size: `3`

## Observed natural failure

```text
Failed to read output schema file data/ai_review/claims/2026-09-01-kr-run-50-44156fe0fa76--daily-review-v3.10--dc747fff8565--65f0c307-72aa-4f45-9154-25981f5a3eaf.decision-v2-schema.json: No such file or directory (os error 2)
```

Warnings about the read-only Codex state DB were non-terminal (`proceeding`). The terminal failure was the missing schema at the duplicated effective path. There was no model transport, timeout, rate-limit, or model-schema response failure because the model call never started.

## Passing control

The same signed-in CLI helper succeeded in the 22/22 preflight with workdir `/private/tmp/cpng-hut-technical-recovery-preflight-final-v2/kr`, model `gpt-5.6-sol`, and reasoning `xhigh`. Its output schema argument was absolute.
