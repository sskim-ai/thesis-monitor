# Natural Proof and Structured Autonomy Blind Program Completion

## Repository

| Item | Result |
| --- | --- |
| Base main / operating | `d18e68b1e944d7749d093b08797fcd9498412680` |
| Work-instruction commit | `2a7b7b4cfe40cf8e9c3514b083daaa36eeba5e4f` |
| Initial implementation commit | `bed88396bda3e96901e65d725f9ab492939396b8` |
| Branch | `codex/20260905-natural-proof-structured-autonomy-blind-comparison` |
| Main merge | `0` |
| Production runtime change | `0` |

The production checkout remained clean at `d18e68b1e944d7749d093b08797fcd9498412680`, equal to `origin/main`.

## Independent Gates

| Gate | Result | Reason |
| --- | --- | --- |
| KR natural explicit V2 proof | `PENDING` | The observed Saturday executions were calendar-guard safe no-ops. |
| US natural explicit V2 proof | `PENDING` | No authoritative post-deployment natural run exists yet. |
| Investment-judgment promotion | `NEEDS_MORE_SHADOW_WORK` | Run C failed schema validation and A/B were not 22/22. |
| External blind comparison | `FROZEN_REVEALED_NOT_COMPARED` | Independent judgment was frozen before the matching AI decision pack was revealed. |

Infrastructure proof and investment-judgment quality remain separate. Neither pending natural proof nor a clean fresh-first run was promoted into a broader claim.

## Source Lock

| Market | Packet | Assessment date |
| --- | --- | --- |
| US14 | `2026-09-05-us-run-57-1fbbf143dbc5` | `2026-09-05` |
| KR8 | `2026-09-04-kr-run-56-6a9ef43bb878` | `2026-09-04` |

Model equivalence is `PASS`: signed-in Codex CLI resolved `gpt-5.6-sol` with `xhigh` reasoning. Old candidate reuse, cross-run visibility, selective disagreement rerun, post-result candidate editing, and production delivery were all `0`.

## Generation Results

The preliminary generation failed its first hard gate at `20/22` on two generic validator boundaries. A bounded generic validator repair was implemented and tested; that generation remained frozen and A/B/C was never started.

The official fresh generation is:

`20260905-uskr22-blind-20260905T082245Z-e82aa2b9742a`

| Run | Result | Message quality | Material repetition |
| --- | --- | --- | --- |
| Fresh first | `22/22` | `PASS` | `0` |
| A | `20/22` | `FAIL` because candidate validation failed | `0` |
| B | `20/22` | `FAIL` because candidate validation failed | `0` |
| C | `INCOMPLETE` | Not measured | Not measured |

Run A rejected `MU` and `005490`; Run B rejected `GOOGL` and `005490`. All four rejections were the future-checkpoint metric policy. The cited evidence owned the named metric, but the prose forms were outside the validator's accepted future-checkpoint grammar. The frozen candidates were not edited and the runs were not regenerated.

Run C stopped at batch 5. Two `reevaluation_down` logical-condition expressions represented a `LEAF` with an invalid child shape, so Pydantic correctly failed closed with `logical_claim_leaf_shape_invalid`. Batch 5 was not retried and batch 6 was not called. No partial C judgment was accepted, and A/B/C stability was not calculated from an incomplete cohort.

## Runtime Call Audit

The first Generation-2 run used six planned batches. Run A used six accepted batch outputs; its fifth batch required one explicitly approved infrastructure-only resume after a completed model response could not be finalized by the outer sandbox and timed out. No failed candidate was accepted from that attempt, and the retry was not triggered by investment judgment or validator disagreement.

Run B completed its six planned batches with no retry. Run C completed four batches and produced one schema-invalid fifth batch. At the user's stop boundary, same-point retry was `0` and C6 model call was `0`.

## Blind Protocol

| Artifact | Result |
| --- | --- |
| Blind fact pack subjects | `22` |
| AI judgment leakage | `0` |
| Blind pack SHA-256 | `f415d4edb17393141dbcc3c81ebe7fc6d30ce57ac528f1af3d8d0f6733f70de0` |
| AI decision pack SHA-256 | `009aa30f35ce838f49485004c3d09c6c721033b61ce1bc1f69c631d643ce4524` |
| AI decision pack state | `REVEALED_AFTER_EXTERNAL_BLIND_FREEZE` |
| External judgment SHA-256 | `4cd6247739113cba0e18f15cf72857e11b7525961ab6102e443f38eb9bf54273` |
| Revealed AI decision ZIP SHA-256 | `9d6d4438adcfc26dc9a1967ab40182f99ceb53c8a01d17370b1e898102e78cf9` |
| Blind-review ZIP SHA-256 | `cd9bbf37a6a7199bcb5537422e7aa9072790bc6ed1f01a4d1921c987006c7764` |

The downloadable blind-review ZIP contains only the blind fact pack, comparison protocol, empty external-review template, and checksum file. It does not contain `AI_DECISION_PACK`, per-ticker AI labels, directional balances, or A/B/C decisions.

## Severity

Open P0: `0`. Unsafe candidates were rejected, no invalid result was delivered, and production was untouched.

Open P1: `2`.

1. Generalize future-checkpoint semantic ownership without allowing current or historical ROIC/CCC/DSO/DPO claims.
2. Prevent or deterministically reject-and-close malformed logical-condition leaf structures before a full run is considered complete.

P2 backlog: add finer signed-in CLI post-response finalization latency telemetry. It does not block the bounded repair.

## Validation

| Check | Result |
| --- | --- |
| Focused shadow/program tests | `188 passed` |
| Full pytest | `2421 passed`, one upstream deprecation warning |
| Ruff | `PASS` |
| `git diff --check` | `PASS` |
| Investment Knowledge v3.1 | `PASS`, `dc747fff856530e82477851cbd0bb16c5876770de514a9c02cfd5a26ac91c312` |
| Chart Knowledge v1 canonical/runtime parity | `PASS`, `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b` |
| Public Action | `0.4.5` unchanged |
| Public Action operationId | `20/20` unique |
| Required public reports | `18/18` |
| Required machine outputs | `12/12` |
| Blind ZIP AI decision entries | `0` |

## Final Gates

```text
FIRST_RUN_VALIDATED = 22
A_B_C_GATE = RUN_INCOMPLETE
RUN_A_VALIDATED = 20
RUN_B_VALIDATED = 20
RUN_C_VALIDATED = OTHER
STABILITY = NOT_MEASURED
EXTERNAL_BLIND_JUDGMENT_STATUS = FROZEN_REVEALED_NOT_COMPARED
HARD_SAFETY_REGRESSION = 5
PRODUCTION_DECISION_MUTATION = 0
PRODUCTION_RENDERER_MUTATION = 0
PRODUCTION_TELEGRAM_SEND = 0
PRODUCTION_DB_MUTATION = 0
MAIN_MERGE = 0
PROMOTION_READINESS = NEEDS_MORE_SHADOW_WORK
```

This generation remains frozen as a failed experiment. The independent judgment was
subsequently frozen and the matching fresh-first AI decision pack was revealed without
changing the A/B/C or promotion result. No external-versus-AI comparison verdict or
majority vote was produced. The next engineering step remains a generic P1 repair
followed by a completely new generation.
