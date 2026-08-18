# Phase 8.2A KRX Validation

Date: 2026-08-18
Branch: `codex/phase-8-2a-krx-market-breadth`
Status: DEVELOPMENT / ARCHIVE ONLY

## Contracts

- Market cross section: `market-cross-section-v1`
- Breadth calculation: `market-breadth-v1`
- Universe: `krx-kospi-kosdaq-common-share-v1`
- Provider role: primary candidate, not registered in operating runtime
- Session: exact historical XKRX session `2026-08-14`
- Current 2026-08-18 empty response: fail-closed, not current canonical

## Provider Validation

| Endpoint | HTTP | Rows | Latency ms | Date |
|---|---:|---:|---:|---|
| `sto/stk_bydd_trd` | 200 | 942 | 1510.1 | 2026-08-14 |
| `sto/ksq_bydd_trd` | 200 | 1,821 | 2041.5 | 2026-08-14 |
| `sto/stk_isu_base_info` | 200 | 942 | 451.8 | 2026-08-14 |
| `sto/ksq_isu_base_info` | 200 | 1,821 | 778.2 | 2026-08-14 |
| `idx/kospi_dd_trd` | 200 | 51 | 270.2 | 2026-08-14 |
| `idx/kosdaq_dd_trd` | 200 | 40 | 139.8 | 2026-08-14 |

- Duplicate identities: 0
- Wrong-date rows: 0
- Empty canonical endpoints: 0 for archive session; fail-closed for current empty probe
- Pagination: none
- Rate-limit headers: absent
- Credential exposure in cache/report/log: 0

## Universe And Breadth

- Raw daily rows: 2,763
- Eligible common shares: 2,532
- Excluded rows: 231
- Exclusion reasons: `{"ineligible_certificate_type": 113, "ineligible_security_group": 47, "spac": 71}`
- KOSPI: eligible 804, advance 575, decline 180, unchanged 49; advance ratio 71.5%; median 1.06%, equal weight 1.30%
- KOSDAQ: eligible 1,728, advance 866, decline 718, unchanged 144; advance ratio 50.1%; median 0.07%, equal weight 0.53%

`advance + decline + unchanged == eligible` passes for aggregate and both segments.

## Numeric Provenance

- Canonical market Facts: 29
- Numeric registry entries: 76
- Registered: 76
- Prose allowed: 76
- Unsupported: 0
- Ready: `true`
- Market/stock flow collision: 0; market actor flow Facts emitted: 0

## Safety

- Main merge: 0
- Operating checkout update: 0
- API production restart: 0
- Scheduled Task changes/executions: 0
- Telegram sends: 0
- Pilot mutations: 0
- Production Assist: OFF

## Regression

- Focused KRX/cross-section/intelligence/documentation tests: 43 passed
- Full pytest: 1,054 passed, 1 existing dependency deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- Investment Knowledge SHA-256: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge SHA-256: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- Public Action: 0.4.5; operationId 20/20 unique
- Implementation commit: `0bf8921981bd3bd226e65291e785a831832055bd`
- GitHub Actions run `32129314573`: Test/Lint PASS

The archive-only result does not replace the pending Phase 8.5.x natural AI-assisted delivery proof.
