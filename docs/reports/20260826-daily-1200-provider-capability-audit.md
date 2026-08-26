# Daily 1200 Provider Capability Audit

The public local `/ohlcv` route remains capped at 1000, but its existing official Kiwoom provider
already implements native `cont-yn` / `next-key` pagination. A direct read-only capability proof
requested 1201 KR rows (one current partial plus 1200 completed) and 1200 US rows.

```text
provider = kiwoom_official_free
calls = 20
success = 20
failure = 0
runtime_ms = 23750.894
bytes = 4439113
paid_source = 0
provider_source_commit = f19c54b8299031caf473737e044f0a2b77db5671
```

No auth header, token, account identifier, or secret is archived.
