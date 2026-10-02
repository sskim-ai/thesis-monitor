# Thesis Monitor — R2B-R9-REV36
## KIS Official Protocol-Scale Calibration
### Official KIS Historical Research Table ↔ Sealed estimate-perform Raw
### EPS/PER ×0.1 Wire Semantics → SK hynix Partial-Row Closure → Conditional KR8 Expansion
### Optional Current-Price FY1 fPER with Corporate-Action Guard
### No Broad Full-Fresh / No Models / No 24-Message Run

**REV36 supersedes every prior unexecuted post-REV35 KIS-forward-valuation instruction. Execute only REV36.**

REV35 ended with:

`R2B_R9_REV35_KIS_RESEARCH_ARTIFACT_GAP`

The official 2026 KIS StrategyDetail pages were discovered correctly but the task exhausted its artificial metadata-page
budget before acquiring the attached research tables.

This is not a KIS estimate-data failure.

REV36 no longer requires the inaccessible 2026 report attachments to define the API wire scale.

A stronger protocol-level calibration source is now pinned:

Official KIS PDF:

`https://file.truefriend.com/Storage/research/research05/20250912095428440_ko.pdf`

Document:
- 한국투자증권 반도체 산업 Note
- date:
  `2025-09-15`
- KIS analyst team includes:
  채민숙
- page 5 / `<표 3> 커버리지 valuation`.

The official KIS table contains exact display values for both Stage-A securities.

## Samsung 005930 official KIS display values
- 2023A EPS:
  `2,131`
- 2023A PER:
  `36.8`
- 2024A EPS:
  `4,950`
- 2024A PER:
  `10.7`

REV32 sealed estimate-perform raw:
- 2023 EPS:
  `21310.0`
- 2023 PER:
  `368.0`
- 2024 EPS:
  `49500.0`
- 2024 PER:
  `107.0`

## SK hynix 000660 official KIS display values
- 2023A EPS:
  `-13,244`
- 2024A EPS:
  `28,732`

REV32 sealed partial output3 candidate row 1:
- 2023:
  `-132440.0`
- 2024:
  `287320.0`

All six cross-artifact comparisons imply the exact transform:

`display = raw × 0.1`

for:
- KIS estimate-perform output3 EPS wire;
- KIS estimate-perform output3 PER wire where the PER row is independently identified.

This is not market plausibility and does not use price.

REV36 must independently fetch/verify the pinned official KIS PDF or equivalent exact official KIS PDF-content source and
then formalize this protocol-level scale contract.

---

# 0. Newest SoT

Adopt REV35 as newest KIS-forward SoT.

REV35 result ZIP:

`thesis-monitor-20261001-r2b-r9-rev35-kis-research-snapshot-report.zip`

SHA-256:

`6a3cd80983410617e6f5bb19995e0142f6f32cd7519171eaf974e59a437e5a41`

Independent verification:

- uploaded sidecar:
  exact match;
- ZIP CRC:
  PASS;
- bundle-manifest entries:
  `187`;
- missing:
  `0`;
- hash mismatch:
  `0`;
- size mismatch:
  `0`;
- unmanifested payload files:
  `0`.

REV35 terminal:

`R2B_R9_REV35_KIS_RESEARCH_ARTIFACT_GAP`

Repository:

- base:
  `7483633c633842c8d16ce8b596fbf5cdae4a310f`
- branch:
  `codex/r2b-r9-rev35-kis-research-snapshot`
- instruction:
  `8a70ce24e9f5a7466759eb247715e960affa9a67`
- implementation:
  `7d3871ed9cbed9d348c8b3bb218fa30522549d95`
- final:
  `60c79de5a56fe83145afc6d96ee7d69f30d5aca9`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean:
  true.

Validation:

- focused:
  `278 passed`
- full:
  `7324 passed / 63 skipped / 0 failed / 0 errors`
- Ruff:
  PASS
- diff:
  PASS
- Investment Knowledge:
  PASS
- Chart Knowledge:
  PASS
- secret scan:
  PASS.

REV35:
- KIS API/auth:
  `0`
- Stage-A estimate refresh:
  `0`
- Stage B:
  `0`
- models:
  `0`
- messages:
  `0`.

---

# 1. Preserve all closed REV33/REV34/REV35 contracts

Do not reopen:

## Security identity
005930:
- exact six-digit security:
  `005930`
- KIS product:
  `00000A005930`
- standard security:
  `KR7005930003`.

000660:
- exact six-digit security:
  `000660`
- KIS product:
  `00000A000660`
- standard security:
  `KR7000660001`.

## Fiscal
Both:
- latest completed FY:
  `2025.12`
- FY1:
  `2026.12E`
- FY2:
  `2027.12E`.

## Forecast marker
Preserve:

`KIS_FORECAST_MARKER_ENDPOINT_SEMANTICS`

## 005930 full output3
Preserve:
- row 1 = EPS
- row 3 = PER.

## Source-family distinction
Preserve:
- `KIS_RESEARCH_ESTIMATE_EPS`
- `KIS_REPORTED_FINANCIAL_EPS`

as different series.

Do not require research 2025 EPS to equal financial-ratio 2025 EPS.

REV34's mismatch remains historical evidence and is not deleted.

---

# 2. Exact sealed Stage-A raw evidence

Do not refresh Stage-A estimate-perform.

000660:

`08129f80e7fc76704e65394aca693632d57fdfedbc5b73e16f0347e3fd98d5c9`

005930:

`55394b92d4af5174e12a04d65696ac7b1e47dd9bb2e959f92b42dfc5afacc2e0`

Verify byte identity before doing anything else.

If either is absent/mismatched:

`R2B_R9_REV36_STAGE_A_RAW_IDENTITY_GAP`.

---

# 3. Official KIS protocol-calibration artifact

Primary official calibration source:

`https://file.truefriend.com/Storage/research/research05/20250912095428440_ko.pdf`

Expected characteristics:

- host:
  `file.truefriend.com`
- content:
  official 한국투자증권 research PDF
- document date:
  `2025.09.15`
- page:
  5
- table:
  `<표 3> 커버리지 valuation`.

Expected exact table cells to verify from the source itself:

## 005930
2023A:
- EPS 2,131
- PER 36.8

2024A:
- EPS 4,950
- PER 10.7

## 000660
2023A:
- EPS -13,244

2024A:
- EPS 28,732.

Do not accept the work instruction's copied values without independently verifying them against the official KIS source.

No third-party PDF mirror may be the authority.

---

# 4. Artifact acquisition budget

REV35's six-page budget was an instruction-local bound, not a KIS provider quota.

REV36 does not repeat that search pattern.

For the exact pinned official PDF:

maximum explicit fetch/navigation attempts:

`4`

Preferred:
`1-2`.

Permitted transports:
1. direct HTTPS fetch/download from the exact `file.truefriend.com` URL;
2. approved web/PDF parser opening the exact official URL;
3. browser navigation to the exact official PDF URL.

Do not first search for the current 2026 reports.

Do not spend attempts rediscovering report ids.

If exact official PDF bytes are unavailable but an approved web/PDF parser returns:
- the exact official PDF URL;
- content type `application/pdf`;
- page-numbered text from page 5;
- the exact required table values;

that parser output may serve as semantic source evidence for the protocol-scale contract.

Record that bytes were unavailable separately.

If neither direct bytes nor exact page-numbered official-PDF content is obtained:

`R2B_R9_REV36_OFFICIAL_SCALE_ARTIFACT_GAP`.

No Stage B.

---

# 5. Official support documentation

Also pin/review:

`https://www.truefriend.com/plus_help/0613.html`

Official screen:
`종목추정실적 [0613]`.

Use it to establish:
- this is the KIS per-security estimate-performance surface;
- KIS Research produces the estimates;
- the screen provides estimated income statement and investment indicators;
- historical actual plus future estimate periods coexist.

Preserve the existing official API documentation identity that owns:

output3 full ordering:
1. EBITDA
2. EPS
3. EPS growth
4. PER
5. EV/EBITDA
6. ROE
7. debt ratio
8. interest coverage.

and metric units:
- EPS:
  KRW/share display metric;
- EPS growth:
  0.1%-precision wire/display convention;
- PER:
  0.1x-precision wire/display convention.

Do not generalize scale to unrelated endpoints.

---

# 6. KIS output3 protocol-scale contract

Create, repository naming permitting:

`KISEstimatePerformOutput3WireScale`

The transform must be proven per metric family.

## EPS

Required calibration pairs:

005930:
- raw 21310.0 ↔ official KIS display 2,131
- raw 49500.0 ↔ official KIS display 4,950

000660:
- raw -132440.0 ↔ official KIS display -13,244
- raw 287320.0 ↔ official KIS display 28,732

All four must equal exactly:

`display = raw / 10`

No tolerance.

No rounding needed for these controls.

## PER

Required calibration pairs:

005930:
- raw 368.0 ↔ official KIS display 36.8
- raw 107.0 ↔ official KIS display 10.7

Both must equal exactly:

`display = raw / 10`

This also agrees with the documented 0.1x PER wire unit.

No price is used.

---

# 7. Why 2025 cross-series mismatch does not invalidate the protocol scale

Keep the REV34 matrix:

005930:
- estimate-series 2025 raw:
  `66050.0`
- financial-ratio reported-series 2025:
  `6564.00`.

Under the newly proven output3 scale:

estimate-series display:
`6,605`

financial-ratio series:
`6,564`.

These are different EPS series/snapshots.

Do not force equality.

Record:

`RESEARCH_VS_REPORTED_EPS_VALUE_DIFFERENCE`

This difference is allowed because:
- endpoint source families differ;
- the output3 scale is independently proven from official KIS report displays;
- no period-specific factor is introduced.

---

# 8. 005930 FY1 EPS qualification

After Section 6 passes:

raw FY1 EPS:

`462090.0`

period:

`2026.12E`

apply exact protocol transform:

`/10`

and qualify the resulting provider display value as:

`KIS_FY1_EPS_ESTIMATE_SNAPSHOT`

Required receipt:
- raw value;
- transform;
- display value;
- exact security;
- FY1 period;
- estimate date:
  `20260730`;
- Stage-A source hash;
- protocol-scale receipt hash;
- `overall_direction_use=false`.

Do not call this:
- market consensus EPS;
- NTM EPS;
- 12M EPS.

User-facing semantic:

`FY1 EPS · KIS Research snapshot 2026-07-30`.

---

# 9. 005930 provider FY1 PER qualification

After PER protocol scale closes:

raw FY1 PER:

`45.0`

period:

`2026.12E`

apply:

`/10`

and qualify:

`KIS_PROVIDER_FY1_PER_SNAPSHOT`.

Label:

`fPER(FY1) · KIS Research snapshot 2026-07-30`

This is provider/report-snapshot FY1 PER.

It is not necessarily the same as current-price-derived FY1 fPER.

Preserve both metric types separately.

---

# 10. 000660 partial row — exact EPS binding

Do not use prefix inference.

The Stage-A partial output3 rows are:

row0:
- 59434
- 360489
- 611364
- 2857128
- 4498053

row1:
- -132440
- 287320
- 620440
- 3782982
- 4499532

row2:
- -5085
- -3169
- 1159
- 5097
- 189.

## Absolute official KIS calibration

Under the frozen EPS /10 protocol:

row1 historical display:
- 2023:
  -13,244
- 2024:
  28,732

These must exactly match the official KIS PDF values from Section 3.

No other row may match those EPS controls.

This independently binds:

`row1 = EPS`

for the 000660 shortened layout.

No prefix assumption.

---

# 11. 000660 EPS-growth row structural binding

After row1 is independently EPS-bound:

test row2 as EPS growth.

For each computable transition:

`growth_pct = ((EPS_t / EPS_t-1) - 1) * 100`

Compare to:

`row2_raw / 10`

using one explicit provider precision rule:

nearest 0.1 percentage point.

Required matches:
- 2024 vs 2023;
- 2025 vs 2024;
- 2026E vs 2025;
- 2027E vs 2026E.

Do not use the first 2023 growth cell because 2022 EPS is absent from the five-period response.

Every four transition must match.

If all four match:
qualify:

`row2 = EPS_GROWTH`.

If not:
retain a typed structural gap.

This structural check confirms, but does not create, the EPS row identity.

---

# 12. 000660 FY1 EPS qualification

If Sections 10/11 pass:

raw FY1 row1:

`3782982.0`

period:

`2026.12E`

apply the global EPS protocol transform:

`/10`

and qualify:

`KIS_FY1_EPS_ESTIMATE_SNAPSHOT`.

Estimate date:

`20260729`.

No provider PER is inferred because the three-row response has no independently owned PER row.

Provider FY1 PER:

`UNAVAILABLE_NO_PER_ROW`.

---

# 13. Stage-A exact expected display values are test outputs, not target-fitting

The code must derive values from:
- raw Stage-A body;
- frozen generic protocol scale.

Tests may assert the exact sealed fixture outcome.

Production code must not contain:
- 005930-specific /10;
- 000660-specific /10;
- hardcoded FY1 EPS numeric values.

One generic transform applies to all qualified output3 EPS/PER rows.

---

# 14. Stage-B admission

Once 005930 or 000660 FY1 EPS qualifies:

Stage B is admitted.

Query remaining KR6:

- 003690
- 005490
- 010120
- 012450
- 047810
- 086280.

One fresh estimate-perform request each.

No current full-source refresh.

No US requests.

No Market requests.

---

# 15. Stage-B exact security identity

For every newly queried security:

qualify exact KIS domestic security identity using the existing generic:

`KISDomesticSecurityRepresentationBinding`.

Use already-acquired exact identity if present.

If a KIS product identity is not currently sealed:
one bounded `search-info` call is permitted for that security.

Maximum Stage-B KIS identity calls:

`6`.

Do not infer by company name alone.

---

# 16. Stage-B fiscal/FY1 owner

Use existing exact latest completed annual owner first.

If unavailable:
record:

`UNAVAILABLE_FISCAL_PERIOD`.

Do not broaden OpenDART collection in REV36.

The KIS period labels may still be retained diagnostically.

No calendar-year guess.

---

# 17. Stage-B full-layout handling

If output3 has all eight documented rows:

- row1 = EPS;
- row3 = PER;
- apply frozen /10 protocol transforms.

If exact FY1 period exists and fiscal owner passes:

qualify:
- FY1 EPS;
- provider FY1 PER.

No per-ticker scale recalibration.

---

# 18. Stage-B shortened-layout handling

Do not use prefix assumption.

For a shortened output3:

identify an EPS row only through the same generic structural method:

1. candidate EPS row;
2. candidate growth row;
3. four-period or maximum-available consecutive growth relationship;
4. row scale from frozen protocol;
5. unique match.

Minimum:
- at least two consecutive computable transitions;
- unique candidate pair.

If unique:
qualify EPS row.

PER remains unavailable unless an independent PER row semantic exists.

No row-count heuristic.

---

# 19. Missing estimates are not source failure

KIS estimates cover only a research universe.

If output is empty/no estimate:
state:

`UNAVAILABLE_NO_KIS_RESEARCH_ESTIMATE`

Do not fail the stock source.

Do not query a paid fallback.

---

# 20. KIS estimate freshness

For every qualified metric retain:

- `estdate`;
- query/retrieval time;
- age_days;
- source:
  KIS Research.

Do not relabel old `estdate` as current date.

No arbitrary freshness rejection threshold is introduced in REV36.

Future integration may show:

`KIS Research · YYYY-MM-DD`

so the user knows the estimate date.

---

# 21. Optional current-price-derived FY1 fPER

The user values forward valuation especially for semiconductor/AI names.

After FY1 EPS qualifies:

attempt:

`current_FY1_fPER = completed_session_close / KIS_FY1_EPS`

only under the existing strict price/share basis contract.

Required:

1. exact same six-digit ordinary security;
2. completed-session close owner;
3. qualified KIS FY1 EPS;
4. no share-unit-changing corporate action between estimate `estdate` and completed-session date;
5. EPS > 0;
6. no ADR/cross-security issue.

This is independent from provider FY1 PER.

---

# 22. Corporate-action guard routes

REV36 explicitly authorizes the already-configured official KIS/KSD read-only routes:

- merger/split schedule;
- reverse-split/share-unit replacement schedule;
- bonus issue schedule;
- paid-in capital increase schedule.

Only for subjects with qualified FY1 EPS and only over:

`estdate → current completed-session date`.

Do not query irrelevant historical years.

If a relevant share-unit-changing event exists:
derived current fPER remains unavailable unless an exact adjustment owner is separately proven.

No event:
may satisfy the corporate-action absence guard.

---

# 23. Current completed-session price

Reuse the existing Thesis Monitor completed-session current-price owner.

Do not use:
- intraday KIS current quote;
- report-date stock price;
- target price.

If the existing price owner is adjusted-close and the current valuation basis contract still cannot certify compatibility
even after the no-corporate-action guard:

keep derived current fPER unavailable.

Provider FY1 PER remains separately usable.

---

# 24. User-facing future valuation semantics

Future renderer target, not executed in REV36:

For qualified KR subjects:

- `PER`: current Kiwoom snapshot
- `PBR`: current Kiwoom snapshot
- `FY1 EPS`: KIS Research snapshot · exact estimate date
- `fPER(FY1)`: provider KIS Research FY1 PER where qualified
- optional `현재가 기준 FY1 PER`: separately derived current-price metric where qualified

Never collapse provider-report-date PER and current-price-derived PER into one unlabeled number.

Never label KIS house research as market consensus.

---

# 25. Direction authority

Preserve current architecture.

KIS forward metrics may eventually affect:
- NewBuyer valuation context;
- Holder valuation context;
- Valuation section;
- valuation-specific caution/confidence.

They may not establish:
- Overall business direction;
- Core;
- Pass A;
- supporting/contradicting directional refs.

No models in REV36.

---

# 26. Provider-call pacing

KIS:
- sequential only;
- no parallel calls;
- >=1.1 seconds between data calls or stricter official smart_sleep.

If `EGW00201` occurs:
- no immediate retry;
- typed rate-limit state;
- stop optional expansion if needed.

No semantic retry.

---

# 27. Call budget

New Stage-A estimate-perform:

`0`.

Official PDF:
maximum explicit fetch/parser attempts:
`4`.

Stage-B estimate-perform:
maximum:
`6`.

Stage-B search-info:
maximum:
`6`.

Corporate-action requests:
bounded to qualified subjects,
hard maximum:
`24`.

Normal KIS auth:
one session as required.

Hard KIS data-call maximum excluding auth:

`36`.

This is an instruction safety cap, not a claimed provider quota.

No Alpha Vantage.

No FnGuide.

---

# 28. Existing credential policy

The user explicitly accepts the existing KIS key pair.

Use secure local configuration only.

Never print/log/archive:
- App Key;
- Secret;
- token;
- Authorization headers.

If any secret appears:
stop:

`R2B_R9_REV36_KIS_SECRET_EXPOSURE_GAP`.

Do not archive the exposed output.

---

# 29. External transmission approval

REV36 explicitly authorizes bounded read-only access to:

- exact official KIS PDF in Section 3;
- official KIS 0613 help;
- KIS estimate-perform for conditional KR6;
- KIS search-info for exact identity where needed;
- KIS/KSD corporate-action routes for qualified EPS subjects;
- normal KIS authentication.

No:
- models;
- Telegram;
- order/trading APIs;
- production DB writes;
- scheduler mutation;
- deploy;
- main merge;
- remote push;
- restart.

No additional approval required for this exact scope.

---

# 30. No full-fresh / no models

Do not run:
- all22 source;
- Market;
- US source;
- broad existing KR source owners;
- Market/Core/A/B;
- exact24.

Models:
`0`

Messages:
`0/24`.

REV37 is the production integration task if REV36 passes.

---

# 31. Disk guard

REV35/REV36 are bounded.

Require before external calls:

`>= 8 GiB`.

No full-generation destructive GC.

Preserve:
- REV31 blind artifacts;
- accepted REV31-C1;
- REV32–REV35 immutable archives;
- sealed Stage-A raw.

---

# 32. Required tests

## Official protocol scale
- 005930 EPS 2023/2024 exact /10;
- 005930 PER 2023/2024 exact /10;
- 000660 EPS 2023/2024 exact /10;
- wrong factor negative;
- one altered official value negative;
- third-party mirror cannot qualify alone.

## 005930
- FY1 EPS conversion;
- FY1 PER conversion;
- estimate date preservation.

## 000660 partial
- row1 official absolute match;
- row2 4-transition growth equation;
- competing-row negative;
- missing transition negative;
- no prefix assumption.

## Stage B
- full 8-row;
- shortened unique EPS/growth pair;
- no estimate;
- missing fiscal owner;
- rate limit.

## Corporate action/current fPER
- no-event positive basis;
- split/reverse-split/bonus/paid-in event negative;
- non-positive EPS N/M;
- adjusted-price unresolved negative.

## Authority
- B/NewBuyer/Holder allowed;
- Overall/Core/A prohibited.

No target-fitting from current market price.

---

# 33. Validation

Require:

- focused REV36 tests;
- all REV32/33/34/35 regressions;
- current PER/PBR regression;
- valuation visibility/isolation;
- whole-source registry tests if the owner is registered;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No PASS if full suite is red.

---

# 34. Success terminal

If:
- official KIS protocol scale closes;
- Stage-A FY1 EPS qualifies;
- 005930 provider FY1 PER qualifies;
- 000660 partial EPS row is either honestly qualified or typed unavailable;
- KR8 typed matrix is complete;
- full validation is green;

use:

`R2B_R9_REV36_KIS_FY1_FORWARD_OWNER_PASS_READY_FOR_PRODUCTION_INTEGRATION`

Success does not require:
- numeric estimates for all KR8;
- 000660 provider PER;
- derived current fPER.

Derived current fPER is an additional capability.

---

# 35. Honest stop terminals

- `R2B_R9_REV36_OFFICIAL_SCALE_ARTIFACT_GAP`
- `R2B_R9_REV36_OUTPUT3_SCALE_CONTRACT_GAP`
- `R2B_R9_REV36_005930_FY1_GAP`
- `R2B_R9_REV36_000660_PARTIAL_SEMANTIC_GAP`
- `R2B_R9_REV36_STAGE_B_IDENTITY_GAP`
- `R2B_R9_REV36_KIS_RATE_LIMIT_GAP`
- `R2B_R9_REV36_CURRENT_FPER_BASIS_GAP`
- `R2B_R9_REV36_KIS_SECRET_EXPOSURE_GAP`
- `R2B_R9_REV36_VALIDATION_GAP`.

Do not solve by:
- refetching Stage-A estimates until values change;
- market-price plausibility;
- per-ticker scale factors;
- third-party report substitution;
- treating KIS house estimate as consensus.

---

# 36. Required result bundle

Return immutable result ZIP + `.sha256`.

At minimum:

## Integrity
- REPORT.md
- summary.json
- REV35 result SHA/integrity
- repository identities
- changed files
- manifest.

## Official scale source
- official PDF acquisition/parser receipt
- exact URL
- page identity
- extracted calibration cells
- source hash/content identity where available
- official help/source docs.

## Protocol scale
- EPS calibration matrix
- PER calibration matrix
- frozen generic transform receipt.

## Stage A
- 005930 FY1 EPS/PER receipts
- 000660 partial structural audit
- 000660 FY1 EPS receipt/denial.

## Stage B
- KR6 raw/receipts
- identity receipts
- period/fiscal decisions
- full/partial layout states
- KR8 final FY1 EPS/PER matrix.

## Current fPER
- corporate-action windows
- completed-session price binding
- per-security derived state.

## Safety
- KIS calls
- research fetch count
- FnGuide 0
- Alpha 0
- models 0
- messages 0
- Telegram 0
- production mutations 0
- secret scan.

---

# 37. Next handoff

If PASS, prepare REV37 recommendation only.

REV37 should:
- integrate KIS FY1 forward owner into the normal KR fresh provider plan;
- keep current Kiwoom PER/PBR;
- preserve KIS estimate date;
- expose KIS forward metrics only to Valuation + B/NewBuyer/Holder;
- run archive-backed storage GC first if required;
- then perform one fresh full-source/replay/model/message proof.

Detailed stock-message renderer restoration remains a separate task unless explicitly authorized.

Do not execute REV37 inside REV36.

---

# 38. Final principle

REV35 failed on acquisition mechanics, not forward-data semantics.

Do not keep chasing an inaccessible current PDF attachment when the protocol scale can be proven from a stable official
KIS artifact.

Use official KIS historical display values that correspond exactly to the sealed estimate-perform historical raw values:

- same provider;
- same securities;
- same metrics;
- exact historical periods;
- exact deterministic transform.

That closes the wire protocol itself.

Once the protocol is owned:
- current Stage-A FY1 raw values can be interpreted deterministically;
- SK hynix's shortened layout can be bound by absolute official EPS controls plus internal growth structure;
- the remaining KR universe can use one generic source contract.

This preserves the free KIS route without weakening provenance.
