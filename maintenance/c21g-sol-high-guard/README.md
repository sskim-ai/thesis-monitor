# Task-local Sol guarded host

This branch is stacked directly on PR29, not main. It does not activate a service.

`task_guard.patch` applies to the original, attested `rust-v0.155.1` task guard.
Copy the new `sol_task_scope.rs` alongside that guard, then use the exact locked
offline build command in `MANIFEST.json`. Keep the original source, binary,
failed test and old task ledgers. This patch is not an upstream Codex policy.

The application keeps its existing `SOL_HIGH_V1` and
`UNIFIED_AI_V3_SOL_HIGH` contracts. `maintenance/guarded_sol_host.py` accepts a
trusted local `Binding`, not a public JSON grant. Its configuration must pin:

- Private binary and real installed-model catalog projection, with SHA-256.
- Original broker/task/helper source closure, with relative paths and SHA-256.
- A fresh canonical runtime root and an immutable task/account/subject/source
  scope file. The exact ledger is `<runtime>/inference-ledger.json`.
- `SOL_61_HIGH_EXECUTION_V1`, 600 seconds, 393216 input bytes, 131072 output
  bytes and zero retries. No Astra or medium substitution in the Sol task.

Supply this transport only through the original `StageController.run_stage`,
live source loader, fresh explicit approval and account lease. An ADJ request
requires the original accepted BLIND; two different real sessions are required
by the original `StageReviewOwner`. Transport receipts alone do not issue an
economic, source, Stage or Native right.

Authentication belongs only to the trusted host. The original typed analysis
executor retains its separate no-network, no-credential, public-input-only OS
profile. CodeMode remains disabled; the original typed Python exec-server was
tested without a CodeMode companion. This is not a claim about CodeMode support.

No binary, full guard source, model prompt, private model-cache identity,
credential, DB or personal thesis is included here. No financial endpoint or
previous successful financial suite is invoked. The local launch manifest and
private outputs are intentionally not published.
