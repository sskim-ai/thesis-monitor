# KR/US Bounded Quality Canary Simulation

Date: 2026-08-26 KST
Mode: archive-only replay; no delivery

## KR

- market selected: 1
- stocks selected: 2
- total selected: 3
- selected keys:
  - `market:2026-08-25-kr-run-38-6cd8c5d5091b`
  - `stock:012450`
  - `stock:005490`
- all candidates eligible: 8/8
- hard safety: PASS
- runtime quality: PASS
- semantic ownership: PASS
- specificity: PASS

`KR_CANARY_SIMULATION = PASS`

## US

- market selected: 1
- stocks selected: 2
- total selected: 3
- selected keys:
  - `market:2026-08-25-us-run-37-7e04812311c2`
  - `stock:CORZ`
  - `stock:CRCL`
- all candidates eligible: 14/14
- hard safety: PASS
- runtime quality: PASS
- semantic ownership: PASS
- batch specificity: PASS

`US_CANARY_SIMULATION = PASS`

The simulation retains the existing 1/2/3 ceiling. Per-message fallback remains available; a
batch specificity failure rejects only affected stock candidates and does not block the packet.
No Telegram, Scheduled Task, Pilot, database, or archive mutation occurred.
