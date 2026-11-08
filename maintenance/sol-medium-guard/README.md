# Single Medium BLIND qualification

This change is stacked on PR31 and remains disabled without a fresh immutable
backend grant. `SOL_MEDIUM_V1` is an exact profile for `gpt-6.1-sol/medium`.
Its versioned prompt uses the unchanged V3 economic output schema and validators.
The application and Rust task scope both reject ADJ for this profile.

Apply `task_guard.patch` to the C21G guard pinned by `MANIFEST.json` and replace
its sibling `sol_task_scope.rs` with the supplied module. Build the original
locked `rust-v0.155.1` source offline. The prior High binary, source, failed
ledger and seals must remain available. Do not change the installed app binary.

`maintenance/sol_medium_canary.py` permits one new BLIND context with a new
runtime, request, run ID, journal and explicit approval. Limits remain 600 seconds,
393216 input bytes, 131072 output bytes and zero retries. The original private
authentication host, typed public analysis broker, OS isolation, Source Owner,
StageController and durable parent reconsumption remain required.

The guard permits bounded tool continuations only within the same BLIND thread
and request, preserving the original 12-leg inference budget and replay denial.
One accepted BLIND does not issue a two-stage Owner or a final NO-SEND judgment.
No financial API, operating DB, service, schedule, send or order is enabled.

Failed terminal diagnostics retain bounded machine error codes and hashes;
server messages, echoed input and authentication material are not copied.

When the retained packet pins the earlier stage implementation, re-enter the
original Source Owner and bundle builder. A new derived packet must preserve
every original field except the reviewed stage implementation hash. The old
packet and failed pre-model initialization remain intact. A continuation is
allowed only when the prior result proves zero host stages, model outputs,
financial requests and journal bytes; the single model-context cap is unchanged.
