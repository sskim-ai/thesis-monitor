# Track A — Natural Codex DNS / Network Transport Stability

Goal:
make KR/US natural scheduler execution reliably reach the signed-in Codex model path.

Investigate:
- natural vs test resolver/network environment
- launch/service environment
- DNS resolution
- TLS reachability
- Codex WebSocket + HTTPS fallback
- primary/backup behavior
- exact first failure boundary

Do not:
- hardcode public DNS
- edit hosts
- disable TLS
- run as root
- globally disable security

Implement:
- bounded scheduler-context network readiness probe
- exact failure taxonomy
- bounded retry/backoff for transient DNS/network errors
- primary/backup identical network contract

Track acceptance:
scheduler-context DNS/TLS/app-server/model smoke PASS,
no production send,
no unbounded retry.
