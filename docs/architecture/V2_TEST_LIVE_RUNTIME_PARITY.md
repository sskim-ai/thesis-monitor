# V2 Test/Live Runtime Parity

Contract: `v2-test-live-runtime-parity-v1`

The previous absolute temporary-directory preflight did not reproduce natural production. Natural
claims stored repository-relative paths and launched Codex with `cwd=data/ai_review/claims`, causing
the relative schema prefix to be applied twice.

Parity now requires tests to exercise production `_paths()` and the production subprocess boundary.
The path matrix covers absolute and relative schema/cwd combinations, relative prompt/output/log,
and a missing-schema negative control. The run-50 fixture starts from the original relative
`final_output_path` and verifies one canonical claims directory.

Passing a separate preflight helper is supporting evidence only. KR and US production-equivalent
proofs must use the natural path contract before test-sink or live-readiness credit is granted.

