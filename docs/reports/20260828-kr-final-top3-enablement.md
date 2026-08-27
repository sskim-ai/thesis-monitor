# KR Final TOP3 Enablement

`KR_MARKET_TOP3_ENABLED = true`

TOP3 was enabled first while KR Price Structure remained OFF. API health passed; market rank limit
was 3; KOSPI/KOSDAQ strong/weak terminology was present; Price Structure leak was zero.

Rollback: set `KR_MARKET_SECTOR_TOP3_ENABLED=false` in the canonical environment and restart the
service. No database cleanup is required.
