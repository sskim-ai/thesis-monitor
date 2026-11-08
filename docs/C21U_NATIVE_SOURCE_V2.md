# C21U: TEST_ONLY native GET Source protocol, not a live issuer

Status: PARTIAL. The versioned read/observer/result protocol and bounded transport
are implemented and tested offline. Live runtime enrollment is deliberately
unimplemented: bind_live_runtime always raises
native_signed_service_runtime_and_physical_adapter_required. This is not merely
a missing user toggle or model approval. No production runtime Root can be minted
by this change, and receipt JSON or an old direct-Kiwoom Parent cannot replace it.

## Implemented offline

- NativeReadV2 freezes the full daily-only query including investor flows, with
  registered security/issuer/venue/currency and session. V1 remains unchanged.
- Opaque runtime/Parent/result registries, expiry, process and code checks,
  signed runtime/account/caller binding, revoke, replay and cohort commit gates.
- Raw body capture plus signed query/body/page/meter proof, parser parity,
  completion and quality checks before Source result issuance.
- A protected fetch_native_daily entry requires the exact V2 observer and one
  original request attempt. It cannot fall back to unowned direct GETs.
- Existing client finalization was extracted without changing its AST body.
  Native 38 indicators, completed supply, price separation and S/R are reused.
- PhysicalBudgetTransport meters every send routed through that transport,
  including auth, data, lookup and pages. It has one finite total and sticky STOP.
  It is not installed in the original service's top-level httpx.post paths.
- Both the public context and private technical payload are bound at consumption.
  Public receipt edits cannot mutate the internal serialized rights record.

## Limits

Tests explicitly populate private TEST_ONLY runtime state with synthetic
registration leases and signing material. Those are not original registration,
operator-consent or account/Lane capabilities. TEST_ONLY roots accept only
MockTransport, never network transports. No test factory is exposed by the app.

A future reviewed host adapter must bind original current registration and exact
native GET operator consent, expiry/caller/issuer, actual loaded service code and
non-secret config identity, account concurrency/Lane and every physical HTTP send.
It must enroll a genuine runtime Root and sign response/page evidence. The current
service does not implement that adapter. Do not remove the denial or fabricate
Root registry entries to make live requests work.

W/M remain unavailable without original label authority; daily-only Source can
qualify independently in TEST_ONLY examples. Scope remains dated technical
research, NO_SEND/NO_MODEL/NO_CURRENT_PRICE_OWNER/NO_VALUATION_OWNER. No financial,
economic direction, Full Market Parent or Strict Native readiness is granted.

33 unique new checks pass across targeted attempts, including four V1 denial
reproductions. No old broad suite, provider API, model, DB, runtime/scheduler
setting, deployment or deletion was performed. Original failures are retained.
