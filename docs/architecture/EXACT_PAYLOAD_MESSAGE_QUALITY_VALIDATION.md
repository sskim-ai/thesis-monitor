# Exact-Payload Message Quality Validation

Contract: `us-morning-exact-payload-quality-v1`

User-facing quality is evaluated against the exact text returned in the Telegram response. The
delivery receipt records the rendered, outbound, and received payload hashes, invokes the bounded
validator on `result.text`, and stores the validator result beside the received hash.

```text
rendered payload
-> outbound payload
-> Telegram response text
-> exact-payload validator
-> hash-bound quality report
```

The validator rejects malformed zero-change predicate constructions, a visible generic
no-change macro section, generic macro subjects without specific semantics, and invalid required
section order. It is intentionally a bounded product-language check, not a general Korean grammar
engine.

A report may claim PASS only when `quality.payload_sha256 == received_sha256` and the validator
status is `PASS`. A changed candidate paired with a stale quality result fails hash parity. The
historical run-43 payload remains immutable and is retained only as a negative-control fixture.
