# Live Orchestration Artifact Index

## Source and implementation

- Work instruction: `docs/work-instructions/20260903-kr-live-v2-delivery-orchestration-repair-and-live-path-e2e.md`
- Work-instruction SHA: `20d052d35d80c4eddf50562763199a43bb55df6f`
- Implementation SHA: `d00741abbe227bd199c8383de0cad9bbd740ceeb`
- Root-cause machine proof: `docs/reports/20260903-run54-root-cause.json`
- State transition proof: `docs/reports/20260903-delivery-state-transition-proof.json`
- E2E proof: `docs/reports/20260903-live-path-e2e-proof.json`
- Final gates: `docs/reports/20260903-live-orchestration-repair-proof.json`
- Redacted command manifest: `docs/reports/20260903-live-path-e2e-command-manifest.json`
- Redacted TEST receipt: `docs/reports/20260903-run54-test-sink-delivery-receipt.json`
- Implementation Actions: run `33742703384`, Test/Lint PASS

## Report set

The sibling `20260903-*` reports cover first failure, identity, pending/retry, V2 selector,
eligibility authority, state machine, reuse, retry/fallback, late packet, E2E contract/full run,
process boundary, backup/dedupe, controlled fallback, test taxonomy, and verdict.

The completion ZIP includes these files, the exact instruction and track files, implementation
diff, test output, git checks, and secret scan. It excludes DB files, recipient values, tokens,
credentials, and hidden reasoning.
