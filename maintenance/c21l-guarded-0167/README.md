# C21L: OFFLINE-ONLY 0.167 guard port candidate

Stacked on PR33 commit `be0736574cb814a5c6950b8882c47a80e1cc5ef3`.
This is an unqualified patch, **not** a production host or a live model launcher.
No existing Python adapter, profile, Source Owner or economic contract is changed.
The installed CLI and both older guarded hosts remain untouched. Default OFF,
NO-SEND and Strict READY 0/22 remain in force.

## Exact upstream and outcome

- Official repository: https://github.com/openai/codex.git
- Tag: `rust-v0.167.0`
- Commit: `086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a`
- Cargo.toml Git blob: `01075846114cf4579cab2219d5a367be90dc7d1e`
- Cargo.lock Git blob: `2eae72dab578ac844d15ae8585f47ef2d1019607`
- Exact tag was acquired in one fresh shallow/partial clone.
- One `cargo fetch --locked --target aarch64-apple-darwin` exited 101:
  `cannot update the lock file ... because --locked was passed to prevent this`.
- One network-denied, offline/locked metadata diagnostic reproduced this resolver
  failure. The reason a new resolution wants a lock change is not proven.
- Cargo.lock SHA remains
  `9e71c74824a7ea114d0a3a4c94e93d81a1ddd13ca8fa6f698cbd1284c2e9ff2f`.
- Upstream pins Rust 1.95.0; available Homebrew rustc is 1.96.0. This difference is
  recorded, **not** asserted to be the cause or accepted as equivalent release reproduction.
- Build attempts 0. Real-binary predispatch matrix, stdio RPC and adapter acceptance
  are **NOT RUN**, because locked dependencies were not established.
- C21K success was not rerun. Model/authentication/financial HTTP, DB access,
  scheduler/service changes and sends are all 0.

Removing `--locked`, changing the lock, resolving new versions or retrying the
network fetch is not a permitted fix in this task. Do not call this host PASS.

## Patch and preserved boundaries

`guard-0167.patch` contains the exact task-local port including the reused old
guard, scope parser and compiled calculation-tool catalog. It hooks the new
`TransportClient::execute_without_request_logging` before reqwest. Typed HTTP/SSE,
direct and routed requests share this path; TLS replay returns through it.
Internal reqwest redirects are disabled; opaque raw clients and custom-CA fallback
fail closed instead of silently replacing TLS/provider configuration. Responses
WebSocket is disabled in core and the shared WebSocket connector denies before
dialing, including loopback. The 384KiB/128KiB, 600-second, High-only, pinned
schema/catalog/prompt/thread/source and ledger contracts are retained. Account
header equality is added, not relaxed. C21L-only task binding rejects older scopes.

The application adapter and C21I error collector remain unchanged and must be
qualified separately against the new binary. A synthetic transport seam is not
StageController acceptance, original financial Owner approval or inference 200.
Full actual thread-generated tool exposure is not verified by this patch alone.

## Reproduction, only after the locked-dependency blocker is resolved

Use a new task scratch root; never modify an installed executable or old scope.
Verify commit and both upstream Git blobs first, then:

```bash
git -C "$UPSTREAM" apply --unidiff-zero --check "$PACKAGE/guard-0167.patch"
git -C "$UPSTREAM" apply --unidiff-zero "$PACKAGE/guard-0167.patch"
```

Do not rerun the consumed C21L dependency fetch without a new task authorization.
A future approved build must use `--offline --locked`, a task-specific
`CARGO_TARGET_DIR`, no inherited secrets, OS-denied network and a 2GiB reserve.
Only build `codex-app-server` (dev-small profile). Do not run workspace-wide tests.
After a real binary exists, the prepared scripts take an explicit receipt directory
and runtime root (`source/`, `target/dev-small/codex-app-server` beneath it):

```bash
python "$PACKAGE/offline_probe.py" "$RECEIPTS" "$RUNTIME_ROOT"
python "$PACKAGE/smoke.py" "$RECEIPTS" "$RUNTIME_ROOT"
```

The matrix has 15 prepared cases, **not 15 passing tests**. It uses only synthetic
scope/policy/input, real RequestBuilder/transport/guard, an empty native auth home
and OS network denial. Positive exit77 is before transport, negative exit78 is
denied; exit79 is failure. Smoke sends only stdio initialize, never turn/start.
Both scripts create fresh exact `/private/tmp/c21l-*` paths and refuse overwrite.

Next required input is a reproducible official pinned dependency/toolchain
environment for this exact upstream commit and unchanged Cargo.lock. Whether the
upstream Rust 1.95.0 toolchain resolves this failure is UNVERIFIED.
