# Scheduler-Context Network Preflight

The repaired safe probe runs the production invocation helper with a one-field strict JSON schema.
It performs DNS/TCP/TLS readiness before initializing the isolated signed-in Codex app-server.

Host proof on 2026-09-02:

- `codex-network-readiness-v1`: PASS
- DNS/TCP/TLS attempts: 1
- Codex transport attempts: 1
- app-server/model smoke: PASS
- model: `gpt-5.6-sol`
- reasoning: `xhigh`
- Telegram import/send: 0
- database mutation: 0
- accepted-decision write: 0

The corresponding restricted-network negative control ended as
`LOCAL_DNS_RESOLUTION_FAILURE:attempts=3` before subprocess launch.

`SCHEDULER_CONTEXT_NETWORK_PREFLIGHT = PASS`

