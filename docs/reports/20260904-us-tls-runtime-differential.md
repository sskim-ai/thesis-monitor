# 2026-09-04 US TLS Runtime Differential

| Surface | Observed value |
|---|---|
| Interactive shell CLI | `/Users/sskim/.local/bin/codex`, `codex-cli 0.142.5` |
| Production-equivalent signed-in CLI | `/Applications/ChatGPT.app/Contents/Resources/codex`, `codex-cli 0.148.0-alpha.15` |
| Model / effort | `gpt-5.6-sol` / `xhigh` |
| Sandbox | `read-only` |
| Auth mode | existing signed-in auth reference; no token copy |
| Explicit CA variables before normalization | `CODEX_CA_CERTIFICATE` absent; `SSL_CERT_FILE` absent |
| Other CA variables | `SSL_CERT_DIR`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE` absent |
| Proxy variables | HTTPS/HTTP/ALL proxy absent; `NO_PROXY` absent |
| Selected trust source | `ROOT_OWNED_SYSTEM_CA_BUNDLE` |
| Selected CA path | `/etc/ssl/cert.pem` |
| Bundle ownership / mode | `root:wheel`, `0644` |
| Bundle certificate count | `128` |
| Bundle SHA-256 | `9dae8d76e55cb08991f2b672d58999ea15560d910759c16b544f843bdffbb994` |

`codex_tls_environment` preserves an explicit `CODEX_CA_CERTIFICATE` first and an explicit `SSL_CERT_FILE` second. Only when both are absent does it select an approved regular CA bundle that is root-owned, non-group/world-writable, nonempty, and present on the host.

The nested CLI receives the resulting environment through the same invocation that sets the production-equivalent executable, ephemeral runtime state, read-only sandbox, model, effort, prompt, and output schema. No secret value or proxy credential is copied into reports.
