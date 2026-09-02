# Codex Runtime State Contract

Implemented contract: `codex-runtime-state-v1`.

Each claim receives deterministic hashed state directories with mode `0700`. The preflight checks
ownership and privacy, creates an owner-only auth symlink, and executes a real SQLite WAL
round-trip plus rename cleanup. A failed preflight raises
`LOCAL_CODEX_RUNTIME_STATE_NOT_READY` before model transport.

The contract is used by accepted-decision V2 generation and onboarding generation. It preserves
signed-in credentials, read-only tool sandboxing, packet identity, and accepted-decision policy.

- World-writable state: `0`
- Root execution: `0`
- Plaintext auth copy: `0`
- Manual state-table edit: `0`
- Global sandbox disablement: `0`
