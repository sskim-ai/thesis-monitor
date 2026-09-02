# Codex Natural Runtime State Contract

Contract: `codex-runtime-state-v1`

Natural signed-in Codex invocations use a private, claim-scoped runtime state root. The runtime
sets both `CODEX_HOME` and `CODEX_SQLITE_HOME`, creates every directory with owner-only mode, and
performs a real SQLite WAL write/read/rename probe before model transport.

Authentication remains owned by the existing signed-in Codex home. The isolated home contains
only a read-only symlink to an owner-only `auth.json`; copying credential contents is forbidden.
Namespace identity is a deterministic hash of the claim identity, so primary and backup work do
not share writable state and retries for one claim remain idempotent.

Preflight failure is classified as `LOCAL_CODEX_RUNTIME_STATE_NOT_READY`. It is not a model
transport failure. World-writable state, root execution, global sandbox disablement, manual
SQLite table edits, and plaintext authentication copies are forbidden.

The production invocation remains signed-in Codex CLI with `gpt-5.6-sol`, `xhigh`, and read-only
tool sandboxing. Runtime-state isolation changes local process state only; it does not change the
decision policy, packet, recipient, scheduler, or delivery contract.
