# Night-Futures Attempt Archive Validation

## Contract Coverage

Tests prove deterministic attempt/group IDs, atomic files, idempotent replay, and preservation of:

- expected NIGHT and preceding XKRX DAY dates;
- every returned business date and distinct NIGHT `BAS_DD`;
- HTTP status, raw/parsed row counts, sanitized raw refs and aggregate SHA;
- independent product, contract, maturity, matched DAY, readiness, and rejection reason;
- parser, canonicalization, and provider-change cross-check status.

Classification fixtures cover `PROVIDER_EMPTY`, stale prior session, expected session with no
matching DAY, provider conflict, partial readiness, and complete readiness. Existing probe fixtures
also retain holiday-aware DAY traversal, contract identity, source SHA, and provider-change checks.

## Idempotency And Failure

The same group/role/start timestamp produces one attempt file. A second write returns
`IDEMPOTENT_REPLAY`; logical duplicates are zero. Forced atomic-write failure returns
`TELEMETRY_WRITE_FAILED` and `production_effect=0` rather than raising into production.

No credential-bearing header or API key is stored. Raw evidence is represented only by endpoint,
query date, status, row count, and payload SHA.
