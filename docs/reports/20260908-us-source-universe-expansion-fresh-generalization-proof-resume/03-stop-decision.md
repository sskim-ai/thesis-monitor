# 03 Stop Decision

The mandatory latest-result provenance gate failed before implementation. The instruction explicitly requires:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Accordingly, this task did not:

- audit or expand the US source universe;
- change identity, routing, price, or fundamental-source adapters;
- evaluate any US or KR source candidate;
- create a fresh cohort, source generation, source lock, or proof precommit;
- invoke the model for FIRST, A, B, or C;
- alter the frozen Directional calibration, Price-Timing contract, schema, validator, renderer, or transport;
- resume or mutate scheduled monitoring;
- send a production or test Telegram message;
- mutate production data.

Resume requires one of the following explicit provenance repairs:

1. provide the authoritative result ZIP whose SHA-256 is `f0a41371e12127a891165860f3c44ce6af7d1b8dcd13d0c5b93570618a075e6a`; or
2. issue a corrected work instruction that intentionally binds the observed ZIP SHA-256 `ab330fa13a53775ecdd162f36f4f7afeda42415db03bd0c766c48bf3a2eaddac`.

No assumption was made about which identity should replace the other.
