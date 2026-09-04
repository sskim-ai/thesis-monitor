# 2026-09-04 KR Natural TLS, Claim, and Lease State

## TLS

- `KR_TLS_STATUS=NO_TLS_ERROR_OBSERVED`
- `codex_tls_environment()` accepts only explicit CA settings or an approved root-owned, non-group/world-writable system bundle.
- `/etc/ssl/cert.pem` was present with uid 0, mode 0644, nonzero size. No certificate bytes are recorded here.
- Primary reached the model and emitted content. Logs contain no runtime `UnknownIssuer`, `TLS_CERTIFICATE_UNKNOWN_ISSUER`, certificate-verification, SSL/x509, or DNS failure marker.

## Claim / Lease

- Owner: `codex-kr-primary`
- Claim acquired: 16:16:05.738 KST
- Lease expiry at acquisition: 16:46:05.738 KST
- Fencing token matched the claim identity.
- Configured lease / heartbeat: 30 minutes / 60 seconds.
- Persisted primary V2 terminal receipt: absent because the caller-interrupted wrapper exited through traceback.
- Exact primary heartbeat renewal count and last heartbeat: `UNKNOWN`; no terminal receipt exists, so they are not inferred.
- Backup reclaim while primary healthy: 0 observed.
- `KR_PRIMARY_OWNERSHIP=HEALTHY_RETAINED`

Backup later acquired a different packet and claim. Its receipt records 28 lease renewals and preserved fencing. It did not overwrite or resend the authoritative delivery.
