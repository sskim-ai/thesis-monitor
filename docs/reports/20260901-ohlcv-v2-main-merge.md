# OHLCV V2 Main Merge

## Pre-promotion gate

- origin/main before promotion: `f7c4331e7aa34eeb87e0627fb7e79ee27a1cbfa7`
- candidate code SHA: `1e0fb9cd6e4542474c623800a805026c236f2a53`
- instruction ancestry: PASS
- exact-SHA Test/Lint: PASS, Actions run `33461651863`
- run-49 replay: `14/14 PASS`
- test sink: `14/14 exact`
- open P0/material P1: `0 / 0`
- user-visible algorithm diff outside accepted technical resilience: `0`
- production replay: `0`

Promotion is authorized only as a clean linear fast-forward after the report commit also passes
Test/Lint and origin/main is re-fetched without drift. Final main, operating SHA, API health, and
post-deploy smoke are recorded in a later section after those operations actually complete.
