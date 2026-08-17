# Master Workflow v2 Validation

## Scope

[`docs/MASTER_WORKFLOW.md`](../MASTER_WORKFLOW.md) is the portable human/AI handoff for the project as
of 2026-08-17. It has all 28 required chapters and resolves the final repository commit with
`git rev-parse HEAD` rather than embedding a stale self-referential SHA.

## Repository And Runtime Parity

| Item | Verified state |
|---|---|
| Experimental branch | `codex/phase-8-4-1-1-valuation-context-finalization` |
| Exact base | `3ee719e9bc7db1ffea441f1de4b2a3ca8e8f26de` |
| Production main / operating checkout | `aeb87a9d2aee0d4b840c0a8717319e01b375f5f5`, clean |
| Pilot | KR 3/5, US 3/5 |
| Latest natural packet | KR run-23 rejected pre-send; Pilot unchanged |
| AI mode | shadow |
| Production Assist | OFF |
| Scheduled Tasks | 4 ACTIVE, 08:15/08:30/16:15/16:55, operating checkout |
| DB migration | none |

## Contract Parity

The workflow was checked against code constants and structured state:

- policy `daily-review-v3.10`, output schema 4;
- `ohlcv-structure-v2`, `monitoring-state-v1`;
- `security-identity-v2`, `financial-quality-taint-v2`;
- `financial-statement-basis-v1`, `financial-amount-period-v1`, `financial-lineage-v2`;
- `typed-valuation-interpretation-v2`;
- `market-cross-section-v1`, `market-breadth-v1`;
- `delta-first-rendering-v1`, `decision-material-delta-v1`;
- `semantic-scope-and-decision-hierarchy-v1`, `valuation-context-wording-v1`;
- `runtime-message-quality-v1`, `runtime-message-quality-receipt-v2`;
- Pilot v3 and renderer v3.

Public Action is 0.4.5 with 20 operationIds and 20 unique values.

## Knowledge Parity

Investment Knowledge v3 canonical, upload, and runtime mirror:
`559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`.

Chart Knowledge v1 canonical and runtime mirror:
`beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`.

## State And Roadmap Consistency

`MASTER_WORKFLOW.md`, `PROJECT_HANDOFF.md`, `NEXT_SESSION_PROMPT.md`, and `project-state.json` agree:

- Phase 8.4.x message-intelligence foundation is complete;
- main is unmerged and operating deployment is unchanged;
- Human-approved Production Assist evidence is insufficient;
- next default phase is Phase 8.5 Industry-Specific Investment Reasoning;
- Phase 8.2A becomes the alternative priority only if KRX approval is confirmed;
- Production Assist stays OFF.

## Persistent Gaps

Industry-specific reasoning PARTIAL; peer/sector valuation OPEN/PARTIAL; KR breadth PARTIAL; KR
market-wide flow OPEN; Massive 08:05 readiness OPEN; OCF PARTIAL; CAPEX/FCF OPEN; natural-live
validation OPEN; human-approved production evidence INSUFFICIENT.

## Result

Master Workflow v2 is internally consistent with repository contracts and the read-only runtime
reconciliation. Exact final-commit GitHub Actions Test/Lint is verified after the documentation
commit is pushed and is reported in the completion response.
