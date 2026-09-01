# V2 CLI Path Root Cause

Run-50 persisted a repository-relative schema path while invoking Codex with the claims directory as cwd. The child therefore resolved `data/ai_review/claims` twice and failed before model generation. The test-only preflight used absolute temp paths and missed the production shape.

`OLD_EFFECTIVE_SCHEMA_PATH = <repo>/data/ai_review/claims/data/ai_review/claims/<schema>`

`KR_PRIMARY_FAILURE_CLASS = CODE_REGRESSION`
