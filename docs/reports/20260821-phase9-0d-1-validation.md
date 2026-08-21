# Phase 9.0D.1 Validation

## Repository

- Instruction commit: `20367c056e6d1da7db3edee37818210c070e1e7d`
- Implementation commit: `d473b900304e931d5acf4c4b7d17069d6b67d026`
- Implementation Actions: run `32436660207`, Test PASS, Lint PASS
- Branch: `codex/phase-9-0d-1-baseline-cash-flow-consistency-repair`

## Tests

- Contract and selected packet/fallback/canary integration: `19 passed`
- Related AI review, fallback, canary and contract suite: `254 passed`
- Full pytest: `1241 passed`, one upstream Starlette deprecation warning
- Ruff full repository: PASS
- `git diff --check`: PASS

## Replay

- Run-30 immutable packet and fallback read-only audit: PASS
- Original archive rewrites: `0`
- Active universe: `20`
- Recognized claim occurrences: `21`
- Pre-repair unsupported occurrences: `8`, one TSLA root family
- Post-repair cross-artifact errors: `0`
- Canonical numbers injected into production preview: `0`

## Safety Regression

- Phase 9.0D natural canary evidence remains `COMPLETE_PASS`
- Full FCF / OCF-only / lagging-formal / blocked controls: PASS
- Numeric binding from natural canary: automatic `10`, manual/rejected/unresolved `0`
- Natural canary PIT/lineage/arithmetic/semantic/quality errors: `0`
- Production influence: `0`
- Fallback exactly once and receipt paths: test PASS
- Run-27/run-28/run-29 and financial/valuation/night-futures regressions: full-suite PASS

## Static Contracts

- Investment Knowledge v3 SHA: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge v1 SHA: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- Public Action: `0.4.5`
- operationId: `20/20` unique
- Output schema: `4`
- CCC / standard ROIC: `DEFERRED / DEFERRED`

The final documentation SHA must pass the same GitHub Test/Lint workflow before promotion; its exact
run is resolved from GitHub at promotion time to avoid a self-referential documentation commit.
