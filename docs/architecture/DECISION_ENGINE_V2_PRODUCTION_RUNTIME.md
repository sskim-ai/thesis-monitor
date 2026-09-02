# Decision Engine V2 Production Runtime

Contract: `v2-accepted-production-runtime-v2`

```text
immutable review packet
  -> packet-owned technical context
  -> canonical decision evidence
  -> signed-in Codex CLI (`gpt-5.6-sol`, `xhigh`)
  -> candidate and adjudication
  -> accepted decision plan
  -> accepted-only renderer
```

The V2 runtime does not fetch local OHLCV. It consumes safe packet-owned feature facts bound to a
`technical_context_id`, timeframe, completed bar, key, and value. Low-level duplicated technical
facts may be omitted from prose prompts while their status/quality remains visible.

`PARTIAL_SAFE`, `UNAVAILABLE`, and `INVALID` contexts are explicit limitations. They do not map to a
fixed decision and do not kill a cohort. The renderer still consumes only accepted decisions; raw
or unresolved candidates remain invisible.

Price Structure, valuation, Public Action 0.4.5/schema 4, Telegram routes, deterministic fallback,
accepted-decision ownership, and scheduler configuration are unchanged.

## Claim-scoped Codex runtime state

Natural primary, backup, schema-repair, candidate-repair, and onboarding invocations use
`codex-runtime-state-v1`. Before transport, the helper creates owner-only claim-scoped
`CODEX_HOME` and `CODEX_SQLITE_HOME` directories, references the existing signed-in auth through
an owner-safe symlink, and verifies SQLite WAL write/read/rename behavior. Local state failure is
reported as `LOCAL_CODEX_RUNTIME_STATE_NOT_READY`, separately from model transport.

The runtime state namespace is derived from the claim ID. This prevents primary/backup writable
state collisions without changing packet identity, model (`gpt-5.6-sol`), reasoning effort
(`xhigh`), read-only sandboxing, accepted-decision validation, or delivery ownership.

## CLI filesystem boundary

Natural claims may store repository-relative artifact paths, but the runtime resolves them against
the module-owned repository root. Prompt, output, log, schema, and subprocess cwd are absolute and
prechecked before Codex starts. A local path defect fails as a deterministic precondition error;
primary, backup, schema repair, and candidate repair all use the same invocation helper.

## Bounded generation convergence

Structured generation keeps the validator strict. A batch that fails Pydantic schema or
cross-field validation may be regenerated once for exactly the same subjects and canonical
evidence. A subject that then fails the semantic validator may be regenerated once with only the
exact validator errors and original rejected candidate. The repair prompt may clarify an existing
contract, including evidence dates not later than the assessment cutoff and the relationship
between confirmed maturity and post-confirmation HOLD flags. A second failure suppresses the run
safely; no JSON mutation, threshold relaxation, or decision-specific exception is allowed.
