# Codex Test / Live Network Parity

Both test probes and natural V2 generation call `_invoke_signed_in_codex` and therefore share:

- the `codex-network-readiness-v1` DNS/TCP/TLS gate;
- the same signed-in Codex binary selection;
- `gpt-5.6-sol` with `xhigh` reasoning;
- claim/probe-scoped writable runtime state and read-only auth reference;
- read-only Codex sandboxing;
- one bounded transport retry under the original timeout budget.

Primary and backup scheduled tasks both enter `app.jobs.stock_decision`, so neither has a private
resolver rule or a separate model transport implementation. Scheduler timing and ownership are
outside this contract and remain unchanged.

Parity means the code and safety contract are identical. It does not claim that every execution
observes identical external network availability. Each invocation records readiness and terminal
failure class so an intermittent scheduler resolver outage remains distinguishable from model,
runtime-state, or validator failures.

