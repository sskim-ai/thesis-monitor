# Track B — Signed-in CLI TLS Trust + Error Classification

Natural primary and backup xhigh claim-scoped CLI both emitted raw UnknownIssuer.

Find the real certificate-trust difference.
Do not disable TLS verification.

Repair:
- approved trust path
- permanent TLS error fail-fast
- UnknownIssuer => TLS_CERTIFICATE_UNKNOWN_ISSUER

Before full E2E:
one minimal same-runtime signed-in CLI preflight must return one model result with no TLS error.
