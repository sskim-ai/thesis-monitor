# M12V Runtime Architecture And Full Fictional Proof

## Status
**M12V_RUNTIME_PROOF_FAIL.** The first fictional context hit the frozen 2,400-second
watchdog without final output. The generation is closed; no additional model call is authorized.
Fresh real proof and production remain **NOT_READY**.

## Frozen Repository
- Base: `b3bd63ac734047d624d94e08f558d47ce6b679f7`
- Work instruction: `f1da357ff8553b0b3d8503b532433d508255af8f`
- Architecture decision: `2e50558`
- Implementation: `46ec85c62f37ff3a81aed356d3b1265d74ee5511`
- Branch: `codex/20260910-astra-runtime-architecture-m12v`
- Origin main unchanged: `d18e68b1e944d7749d093b08797fcd9498412680`
- New runtime adapter and audit consumer only; no existing application/runtime file changed.
- Existing M12U financial semantics, source fixtures, prompt, schemas, calibration thresholds, Daily Delta, Price-Timing and renderer remain frozen.

## Architecture Decision
Selected exactly one: **INCREASED_FINITE_ABSOLUTE_WATCHDOG**.

The experimental cap is **2,400 seconds**, increased from 1,800. Wrapper retry is **0**.
Four subjects remain coupled per context. A context failure stops the generation.
There is no per-name retry, context split, model/effort fallback or indefinite activity reset.

Measured evidence:
| Generation | Context 1 | Context 2 |
|---|---:|---:|
| M12E | 371.47s, complete | 329.53s, complete |
| M12F | 1133.48s, complete with CLI retry | 1800.01s, timeout with CLI retry |
| M12T | 321.70s, complete | 331.91s, complete |
| M12U | 1800.07s, timeout, no final output | NOT_RUN |

These are 5 returns and 2 censored timeouts, not a reliability estimate.
The 2,400-second choice budgets two observed 1,133.48-second recovered-tail windows,
rounded up to a 600-second boundary. This is a finite experimental tolerance hypothesis,
not proof that either timed-out request would have recovered with more time.
If it fails again, the hypothesis of sufficient finite tail tolerance is not validated.

The adapter reuses `codex-transport-lifecycle-v1`: separate stdout/stderr readers,
first/last local-byte timing, monotonic hard deadline, process-group cleanup and an
immutable lifecycle receipt. Original streams remain separate. The legacy
`transport.log` is explicitly stderr-then-stdout, **not chronological**.

## Supported Interfaces And Limits
Installed CLI 0.153.4 help confirms `--json`, `--output-schema` and
`--output-last-message`. Official documentation describes JSONL lifecycle events,
but does not establish a recurring backend-sampling heartbeat. Local CLI bytes,
startup events and process liveness therefore do not extend the watchdog.
[Official non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode)

No supported direct same-account Astra/xhigh route is established. The repository's
API-key narrative HTTP client is a different authentication/effort/output contract,
so it is not used. No new API, secret, credential copy or CLI upgrade is introduced.
The existing saved-auth/runtime-isolation route is retained.

The root cause of intermittent no-final-output remains unresolved. Same-size,
same-topology contexts both succeeded and failed. Current resource snapshots do not
establish historical CPU/memory contention. CLI model headers are local advertised
configuration, not backend model attestation.

## Deterministic Validation
- Focused: **243 PASS**.
- Full local: **3,238 PASS**, two existing deprecation warnings.
- Ruff and diff check: **PASS**.
- Implementation CI: **3,233 PASS / 5 FAIL**, new M12V failures **0**.
- Hosted failures are the unchanged historical Git-object/local-ZIP portability backlog.
  Lint was skipped after hosted test failure; local Ruff passed.
- [Exact implementation CI](https://github.com/sskim-ai/thesis-monitor/actions/runs/34421150460)

## New Generation
`20260910-m12v-fictional-20260910T002912Z-cb6d03277dc8`

Source lock:
`98b38c1b63b147269b25953a1770cd97c4eb8eb354fa3102ddc797d81b433577`

Planned: 8 fictional subjects, 2 contexts, 3 repetitions, 6 calls / 24 outputs.
Both prompt/schema pairs are byte-identical to M12U after generation-ID normalization.
All source contexts are identical.

Actual execution: **1 attempt, 0 successful contexts, 0/24 output rows**, five later
contexts **NOT_RUN**. There is no schema/semantic sample to validate.
FIC-FIN-01/02/04/05 target uniqueness, financial exclusion, expectation/leverage,
grounding, formal/core stability, new-buyer/holder stance and Daily Delta variance
are **NOT_MEASURED**, not zero-error PASS.

| Observation | Result |
|---|---|
| First context | run-1/context-01, FIC-FIN-01 through 04 |
| Start | 2026-09-10 09:29:20.373 KST |
| Completion receipt | 2026-09-10 10:09:24.796 KST |
| Monotonic watchdog to child exit | 2,400.062226 seconds |
| Adapter wall-clock elapsed | 2,404.422353 seconds, including setup/receipt overhead |
| First stderr byte | 0.687993 seconds; local CLI prelude/prompt only |
| stdout / final output | 0 bytes / absent |
| stderr | 29,652 bytes; no later stream activity observed |
| Recorded CLI internal / wrapper retries | 0 / 0 |
| Termination | SIGTERM, exit -15, process group terminated |
| Orphans / duplicate timeout receipts | 0 / 0 |
| Remote request acceptance / response ID / progress | NOT_MEASURED |

The CLI advertised gpt-6-astra/xhigh; backend model attestation is NOT_MEASURED.
Read-only post-exit PID inspection found neither the runner nor its CLI child.
All **679 frozen code/contract file hashes** still match after the call.
The generic historical `M12B_RUNTIME_FAILURE` stop tag is retained unchanged in the
original receipt; the authoritative M12V classification is MODEL_TIMEOUT.

## Interpretation And Next Scope
The selected finite-tail-tolerance architecture did **not** complete the observed request.
This is not evidence of a financial semantic failure: there was no candidate to review.
Nor does it establish server saturation, continued reasoning, a websocket defect, or
an incorrect backend model. Startup TLS readiness and CLI process liveness do not
establish request acceptance or remote sampling progress.

Next scope: **ASTRA_FINITE_2400_TAIL_TOLERANCE_ASSUMPTION_REVIEW**.
Review the failed sufficiency assumption and what supported transport evidence could
distinguish acceptance, remote work and connection loss. Do not automatically increase
the cap again or reuse this exposed generation. Further calls require a new authorized scope.

Open P0: **0 observed**. Open P1: **2**, runtime proof failure and the pre-existing hosted-CI
portability backlog. Runtime uncertainty blocks fresh real proof; the CI backlog is not
new to M12V and was not repaired in this task. Minor receipt/presentation polish is P2.

## Export Provenance
The final report commit and exact final CI observation are late-bound in the exported
`86-program-completion.json`, after the documentation commit exists and before the
artifact index is frozen. The committed snapshot cannot contain its own future SHA;
the export adds an explicit final-provenance receipt without rewriting raw model artifacts.
ZIP payload hashes, sizes and secret scan are independently verified during export.

## Safety
Eight approved schedules observed PAUSED. No resume.
Real-issuer calls, judge calls, financial-provider fetches, Telegram sends,
DB/assessment/warning/queue writes, main merge and deployment: 0.
Production readiness remains **NOT_READY**. No schedule or production runtime was changed.
