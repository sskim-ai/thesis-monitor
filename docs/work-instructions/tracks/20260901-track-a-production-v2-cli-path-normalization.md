# Track A — Production V2 CLI Path Normalization

Fix the generic signed-in Codex invocation boundary.

Required:
- resolve cwd/prompt/output/log/schema against canonical operating repository root
- pass unambiguous absolute paths
- precheck schema/prompt existence
- natural relative claim path fixture
- primary/backup identical path logic
- production `_paths()` covered directly in tests
- no KR-only patch
- no persisted claim-path migration required

Mandatory control:
run-50 relative schema + cwd must no longer duplicate `data/ai_review/claims`.
