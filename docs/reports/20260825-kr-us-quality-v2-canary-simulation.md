# KR/US Quality v2 Canary Simulation

The simulation uses the existing deterministic selector and unchanged limits: market `<=1`, stock
`<=2`, total `<=3`. There is no ticker allowlist.

| Market | Eligible | Selected | Selected keys |
| --- | ---: | ---: | --- |
| US | 14/14 | 3 | market, GOOGL, CORZ |
| KR | 8/8 | 3 | market, Hanwha Aerospace, POSCO |

The base-SHA simulation independently reproduces the prior choices: US market/CORZ/CRCL and KR
market/Hanwha/SK hynix. Quality v2 changes ranking because more entity-specific candidates qualify
for `DIRECT_ANALYST`; limits and selector policy remain unchanged.

Every newly selected message passes semantic ownership, thesis-first, generic repetition, hard
validator, runtime-quality, and material-information-loss gates. Packet-level failure is not used;
an individual failure would fall back per message.

`FREE_ANALYST_ADAPTIVE_CANARY = ENABLED_PENDING_NATURAL`

`FREE_ANALYST_ADAPTIVE_FULL = OFF`

`CANARY_LIMIT = 1/2/3`
