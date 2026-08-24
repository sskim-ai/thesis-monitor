# KR Shadow / Production Decoupling

## Before

```text
profile gate AND numeric gate
-> ready_for_ai
-> packet write allowed
-> production AI/fallback reachable
```

An unregistered audit-only number therefore removed the deterministic fallback packet.

## After

```text
production safety -> immutable packet -> packet-bound intents -> safe delivery
shadow readiness  -> ready_for_ai / claimability only
```

When shadow is false, the packet records `shadow_cohort.eligible=false`, exact suppression reasons,
errors, and `production_influence=none`. `write_ai_review_packet()` returns
`shadow_cohort_not_active` as an auditable non-blocking reason while still returning `created` or
`already_exists`.

Claim selection continues to require `ready_for_ai=true`, so unsupported numeric prose remains
fail-closed. Fallback selection requires the identity-matching packet and held packet-bound intents,
not AI claimability.

Transient profile/numeric timeout or exception is caught only at the shadow boundary. The packet ID
excludes shadow state, so retry cannot produce a second production identity. Historical packets and
receipts are not rewritten.
