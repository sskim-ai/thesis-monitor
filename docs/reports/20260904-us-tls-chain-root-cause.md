# 2026-09-04 US TLS Chain Root Cause

## Root cause

The natural primary and backup both reached the same signed-in CLI path but the nested process did not carry an explicit approved CA path, producing the compact certificate error `UnknownIssuer`. Host OpenSSL could validate the endpoint with the system bundle, and the same production-equivalent signed-in CLI succeeded once that root-owned bundle was passed through `CODEX_CA_CERTIFICATE`.

## Chain evidence

The observed endpoint chain was `chatgpt.com` through the Let's Encrypt chain to ISRG roots. A direct `openssl s_client -verify_return_error -CAfile /etc/ssl/cert.pem` check negotiated TLS 1.3 and returned `Verification: OK`. No local/corporate interception issuer was observed in the peer chain.

## Repair

The wrapper now gives the nested Codex runtime a deterministic trust source while retaining certificate verification. It logs only the trust-source enum and non-secret CA path.

| Security gate | Result |
|---|---|
| TLS root cause identified | `PASS` |
| Certificate verification enabled | `PASS` |
| `NODE_TLS_REJECT_UNAUTHORIZED=0` | `0` |
| `--insecure` / `curl -k` | `0` |
| Private certificate material committed | `0` |
