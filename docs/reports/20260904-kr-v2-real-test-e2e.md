# 2026-09-04 KR Explicit V2 Real TEST E2E

The exact implementation ran the production entrypoint against an isolated
copy of the production database and the dedicated TEST Telegram sink. Recipient
identifiers are redacted and were never written to the repository.

| Gate | Result |
|---|---|
| Packet | `2026-09-04-kr-run-56-ea785fbd2c9e` |
| Signed-in model / reasoning | `gpt-5.6-sol / xhigh` |
| Child start | `2026-09-04T13:09:30.487155Z` |
| Accepted | `2026-09-04T13:27:43.478741Z` |
| Outer lifetime | `1092.99 sec` |
| Lease renewals / fencing | `19 / PASS` |
| AI market sent | `1` |
| Explicit V2 accepted / sent | `8 / 8` |
| KR Pilot sent | `0` |
| Deterministic fallback / duplicate | `0 / 0` |
| TLS UnknownIssuer | `0` |
| Healthy-primary backup reclaim | `0` |
| Natural-proof test gate | `PASS` |

The archive completed at `2026-09-04T22:27:53.122323+09:00`, about ten
seconds after V2 acceptance. Production recipient sends, production database
mutations, and scheduler changes were all `0`.

This is controlled TEST evidence, not a natural production proof.
