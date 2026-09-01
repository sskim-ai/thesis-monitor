# KR Natural Live Artifact Index

## Scope

| Type | Path |
| --- | --- |
| instruction | docs/work-instructions/20260901-kr-natural-live-failure-deep-readonly-root-cause-investigation.md |
| instruction | docs/work-instructions/tracks/20260901-track-a-kr-run-packet-data-lineage-and-freshness.md |
| instruction | docs/work-instructions/tracks/20260901-track-b-kr-v2-candidate-accepted-validator-root-cause.md |
| instruction | docs/work-instructions/tracks/20260901-track-c-kr-renderer-fallback-delivery-exact-payload.md |
| instruction | docs/work-instructions/tracks/20260901-track-d-data-trigger-delta-isolation-and-next-repair-classification.md |
| report | docs/reports/20260901-kr-natural-live-run-identity.md |
| report | docs/reports/20260901-kr-runtime-lineage.md |
| report | docs/reports/20260901-kr-scheduler-ownership.md |
| report | docs/reports/20260901-kr-frozen-cohort.md |
| report | docs/reports/20260901-kr-source-monitor-data-readiness.md |
| report | docs/reports/20260901-kr-market-data-session-proof.md |
| report | docs/reports/20260901-kr-price-supply-proof.md |
| report | docs/reports/20260901-kr-technical-context-live-proof.md |
| report | docs/reports/20260901-kr-evidence-packet-audit.md |
| report | docs/reports/20260901-kr-today-vs-last-pass-data-delta.md |
| report | docs/reports/20260901-kr-v2-candidate-generation.md |
| report | docs/reports/20260901-kr-ai-runtime-model-forensics.md |
| report | docs/reports/20260901-kr-candidate-validation.md |
| report | docs/reports/20260901-kr-adjudication-accepted.md |
| report | docs/reports/20260901-kr-renderer-route.md |
| report | docs/reports/20260901-kr-final-validator.md |
| report | docs/reports/20260901-kr-market-message-proof.md |
| report | docs/reports/20260901-kr-fallback-proof.md |
| report | docs/reports/20260901-kr-live-delivery-exactly-once.md |
| report | docs/reports/20260901-kr-live-exact-payload.md |
| report | docs/reports/20260901-kr-047810-deep-trace.md |
| report | docs/reports/20260901-kr-eight-stock-forensic-table.md |
| report | docs/reports/20260901-kr-test-vs-live-environment-parity.md |
| report | docs/reports/20260901-kr-failure-trigger-proof.md |
| report | docs/reports/20260901-kr-natural-live-root-cause.md |
| json | docs/reports/20260901-kr-live-stage-matrix.json |
| json | docs/reports/20260901-kr-data-delta.json |
| json | docs/reports/20260901-kr-failure-trigger.json |
| json | docs/reports/20260901-kr-natural-live-proof.json |

## Immutable evidence sources

- Natural packets: `2026-09-01-kr-run-50-a601ddc0620a`, `2026-09-01-kr-run-50-a90e46db30c9`, `2026-09-01-kr-run-50-44156fe0fa76`
- Primary/backup claim and V2 CLI logs
- Legacy rejected candidate/validation archives
- Deterministic/fallback/delivery history for `2026-09-01-kr-run-50-44156fe0fa76`
- SQLite monitor run and Telegram delivery ledger, opened read-only
- Passing preflight context/artifact under `/private/tmp/cpng-hut-technical-recovery-preflight-final-v2/kr`

The bundle excludes recipient IDs, tokens, auth headers, account identifiers, and hidden reasoning. Exact user-visible payload text is included without recipient metadata.

Validation: focused pytest `25 PASS`; full pytest `2033 PASS`; Ruff `PASS`; deterministic report replay `PASS`.
