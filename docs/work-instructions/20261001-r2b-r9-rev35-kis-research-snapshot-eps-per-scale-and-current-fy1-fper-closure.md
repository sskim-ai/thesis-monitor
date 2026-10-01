# Thesis Monitor — R2B-R9-REV35
## KIS Research-Snapshot EPS/PER Scale Closure
### Official KIS Research Report ↔ estimate-perform Binding
### Partial output3 EPS Identity by Internal Growth Equation
### Optional Current-Price FY1 fPER with Corporate-Action Guard
### Conditional KR8 Expansion
### No Broad Full-Fresh / No Models / No 24-Message Run

**REV35 supersedes every prior unexecuted post-REV34 KIS-forward-valuation instruction. Execute only REV35.**

REV34 ended honestly:

`R2B_R9_REV34_KIS_EPS_SCALE_CONFLICT`

The observed conflict was:

005930 estimate-perform EPS raw vs KIS financial-ratio EPS raw:

- 2023.12:
  `21310.0` vs `2131.00`
- 2024.12:
  `49500.0` vs `4950.00`
- 2025.12:
  `66050.0` vs `6564.00`

REV34 correctly refused to:

- drop 2025;
- add tolerance;
- fit per-period factors;
- use price/PER to force a scale.

However, the cross-endpoint assumption must now be corrected.

`estimate-perform` is not the same source family as statutory/current financial-ratio EPS.

Official KIS documentation/help states that the `[0613] 종목추정실적` surface contains estimates published by the
KIS research department and reflects analyst estimate/opinion information.

Therefore:

> historical rows inside the KIS research estimate table are not required to equal KIS financial-ratio reported EPS
> byte-for-byte.

The 2025 difference is evidence of a **definition/update-series difference**, not proof that the estimate-perform wire
scale itself changes by year.

REV35 must close the estimate wire semantics against the **official KIS research artifact that generated the same
analyst/date estimate snapshot**, not against an unrelated reported-EPS series.

---

# 0. Newest SoT

Adopt REV34 as newest KIS calibration SoT.

REV34 result ZIP:

`thesis-monitor-20261001-r2b-r9-rev34-kis-eps-calibration-report.zip`

SHA-256:

`0446464d221218dc9cf635e3e490889c46ce1f1a740c1bc31bb6852b0dbfdde3`

Independent verification:

- sidecar:
  exact match;
- ZIP CRC:
  PASS;
- internal manifest:
  `190/190`;
- missing:
  `0`;
- hash mismatch:
  `0`;
- size mismatch:
  `0`;
- extra:
  `0`.

Terminal:

`R2B_R9_REV34_KIS_EPS_SCALE_CONFLICT`

Repository:

- base:
  `07bc7f722828d798d6c463749532a4a885abc1d4`
- branch:
  `codex/r2b-r9-rev34-kis-eps-calibration`
- instruction:
  `a44d9c75624e54adb4a0ccea8de3c13ed8fab42e`
- frozen acquisition probe:
  `ff31b2830a59e4e1bf6d6127245729853487d5e3`
- offline implementation:
  `7e8dd357ad5f60bb677ddf775e6444347f4ff32f`
- final:
  `7483633c633842c8d16ce8b596fbf5cdae4a310f`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean:
  true.

REV34 validation:

- focused:
  `237 passed / 0 failed`
- full:
  `7283 passed / 63 skipped / 0 failed / 0 errors`
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

---

# 1. Preserve REV34 raw evidence exactly

Do not refresh Stage-A estimate-perform.

000660 raw SHA-256:

`08129f80e7fc76704e65394aca693632d57fdfedbc5b73e16f0347e3fd98d5c9`

005930 raw SHA-256:

`55394b92d4af5174e12a04d65696ac7b1e47dd9bb2e959f92b42dfc5afacc2e0`

Preserve KIS financial-ratio evidence as a separate reported-EPS/reference series:

000660 ratio SHA-256:

`c2f723ae070a9257d3bfec2209c718a74c8e28d54a5c3907710c3892dd81b52f`

005930 ratio SHA-256:

`5667f3d022675b1f760e2f26626fb2aa239949d3f2f8a6f7c0ca3c3040835e46`

Do not delete the mismatch.
Reclassify its semantic meaning only if the official research-source contract below closes.

---

# 2. Preserve all already-closed identity/fiscal/forecast contracts

Do not reopen:

## 005930
- exact KIS security:
  `005930`
- standard security:
  `KR7005930003`
- security:
  삼성전자보통주.

## 000660
- exact KIS security:
  `000660`
- standard security:
  `KR7000660001`
- security:
  에스케이하이닉스보통주.

Both:
- latest completed FY:
  `2025.12`
- FY1 candidate:
  `2026.12E`
- FY2 diagnostic:
  `2027.12E`
- forecast-marker contract:
  `KIS_FORECAST_MARKER_ENDPOINT_SEMANTICS`.

005930 full output3:
- row 1:
  EPS
- row 3:
  PER.

No value-based remapping.

---

# 3. Important source distinction

Create a formal distinction:

## KIS_REPORTED_FINANCIAL_EPS
Source:
`finance/financial-ratio`

Meaning:
KIS financial-ratio/reporting series.

## KIS_RESEARCH_ESTIMATE_EPS
Source:
`estimate-perform`

Meaning:
KIS Research monthly estimate-series snapshot for the covered security.

These are not required to be numerically identical for a historical/year column.

The following is now prohibited:

> using KIS_REPORTED_FINANCIAL_EPS equality as a mandatory scale oracle for KIS_RESEARCH_ESTIMATE_EPS.

REV34's mismatch remains preserved as a cross-series difference.

It no longer automatically means:
`wire_scale_conflict`.

Only the official KIS research binding below may replace that terminal.

---

# 4. Official KIS research snapshot identity

Stage-A estimate output1 owns:

## 005930
- security:
  005930
- analyst:
  `채민숙`
- estimate date:
  `20260730`
- recommendation:
  `매수`

## 000660
- security:
  000660
- analyst:
  `채민숙`
- estimate date:
  `20260729`
- recommendation:
  `매수`.

Official KIS public research pages exist for:

- 삼성전자 005930, 채민숙, 2026-07-30
- SK하이닉스 000660, 채민숙, 2026-07-29.

REV35 must create:

`KISResearchEstimateSnapshotBinding`

Require exact match on:
- security;
- analyst;
- research date;
- official KIS host/source;
- report type/title identity;
- no third-party report substitution.

The report does not need to prove that estimate-perform is generated from exactly one PDF unless official evidence
supports that stronger claim.

It is sufficient to prove that the report and estimate API represent the exact same KIS Research security/analyst/date
snapshot family.

---

# 5. Official KIS research sources only

Approved semantic sources:

- `securities.koreainvestment.com`
- `truefriend.com`
- official KIS Open API portal;
- official KIS GitHub repository.

May follow:
- official report "원문보기";
- official attached PDF/document;
- official downloadable research artifact.

Do not use as authority:
- Newsis;
- NewsPim;
- Telegram;
- blogs;
- aggregators;
- IRGO;
- portal copies.

Those may not define EPS/PER scale.

If the official report attachment cannot be retrieved:
record the failure honestly.
Do not substitute a third-party copy.

---

# 6. Research report financial-table extraction

For each Stage-A control, inspect the official KIS research artifact.

Extract only the report's own displayed financial table fields relevant to:

- fiscal year labels;
- EPS;
- PER;
- possibly net income/shares if present;
- forecast/actual markers.

Required provenance:
- official report URL/id;
- report title;
- analyst;
- report date;
- attachment SHA;
- table page/section identity;
- extracted values;
- extraction method.

Prefer parsed text/table.
Use page/image inspection only if the official PDF's table text is not reliably parsed.

No OCR unless unavoidable.

No value transcription without preserving the original official page/table evidence.

---

# 7. 005930 research-table calibration

Primary positive control:

005930.

API raw:

EPS row:
- 2023:
  `21310.0`
- 2024:
  `49500.0`
- 2025:
  `66050.0`
- 2026E:
  `462090.0`
- 2027E:
  `672398.0`

PER row:
- 2023:
  `368.0`
- 2024:
  `107.0`
- 2025:
  `182.0`
- 2026E:
  `45.0`
- 2027E:
  `31.0`.

Create independent candidate conversion decisions for:

- EPS wire → report-display EPS;
- PER wire → report-display PER.

A conversion qualifies only if:
- exact same security/report snapshot;
- exact same fiscal period;
- exact same metric;
- at least two available periods agree;
- all available report periods for that metric agree;
- no disagreeing report period is dropped;
- conversion is one exact fixed factor/format transform;
- no price is used;
- no market plausibility is used.

If the official report displays only FY1/FY2:
two forecast periods are sufficient.

---

# 8. Research-table semantic win condition

If official KIS report shows, for example, FY1/FY2 display EPS/PER and they map exactly to API raw values under one
fixed transform:

create:

`KISEstimatePerformResearchWireSemantics`

with per-metric transforms.

This source contract supersedes the failed REV34 financial-ratio calibration for the estimate-series wire.

It does not alter the financial-ratio endpoint.

Record:

- raw;
- display;
- factor/format;
- periods;
- report/source hash;
- estimate body hash;
- exact equality receipts.

Do not use approximate matching.

---

# 9. If research table uses different FY values

If the exact same KIS research security/analyst/date report has FY1/FY2 EPS values that do not map to the API raw table
under one deterministic transform:

stop that metric:

`UNAVAILABLE_RESEARCH_SNAPSHOT_MISMATCH`.

Do not:
- assume a newer intraday version;
- choose a different report date;
- average values;
- use another broker.

This would mean API and public report are not a sufficiently identical snapshot family for that metric.

---

# 10. Provider-native FY1 PER is independent

PER does not depend on EPS scale.

If the exact KIS research report closes the FY1 PER wire transform:

qualify:

`KIS_PROVIDER_FY1_PER_RESEARCH_SNAPSHOT`

even if EPS remains unavailable.

Required:
- exact FY1 period:
  `2026.12E`;
- exact provider PER value;
- report/API snapshot identity;
- research date;
- source hashes;
- `overall_direction_use=false`.

User-facing semantics:

`fPER(FY1) · KIS research snapshot YYYY-MM-DD`

Do not call it:
- current-session fPER;
- market consensus fPER;
- NTM fPER.

---

# 11. KIS is a house-research estimate, not market consensus

This is mandatory.

The KIS source is:

`KIS Research analyst estimate snapshot`.

It is not proven to be:
- all-broker consensus;
- consensus average;
- consensus median.

Record:
- analyst name when supplied;
- research/estimate date;
- latest query time separately.

Future renderer must label the source accordingly.

No generic word:
`consensus`
unless a separate consensus source is added.

---

# 12. Estimate freshness state

Create:

`KISResearchEstimateFreshness`

Fields:
- query/retrieval time;
- `estdate`;
- age_days;
- exact provider snapshot state;
- whether a newer KIS estimate-perform snapshot was returned by the fresh query;
- source latest-available evidence.

Possible states:
- `LATEST_KIS_RESEARCH_SNAPSHOT_VERIFIED`
- `KIS_RESEARCH_SNAPSHOT_STALE_BY_POLICY`
- `UNAVAILABLE_ESTDATE`
- other typed reason.

Do not replace estdate with query date.

Do not claim same-day/current consensus.

REV35 should report that the existing Stage-A:
- 005930 estdate = 2026-07-30;
- 000660 estdate = 2026-07-29.

No arbitrary freshness threshold is introduced in REV35.

Future integration may display latest-available snapshot with date and a caveat.

---

# 13. 000660 partial output3 — internal structural identity

Do not use prefix assumption.

Use the official full-layout semantics plus internal mathematical relationship.

000660 output3:
- row 0
- row 1
- row 2

with five period columns.

A partial row may qualify as EPS only if:

1. one candidate row has values for the five period columns;
2. another candidate row equals the period-over-period change of that candidate to the official EPS-growth wire
   precision for every computable transition;
3. the relationship holds exactly under one documented rounding rule;
4. the pair is unique among the three rows;
5. no market price or external EPS is needed.

For standard growth:

`growth_t = (eps_t / eps_t-1 - 1) * 100`

Use the signed denominator as mathematically written.
Do not replace with absolute value.

Negative→positive periods must be checked exactly against provider behavior.

If row1/row2 uniquely satisfy:
bind:
- row1 = EPS
- row2 = EPS growth.

This is structural endpoint proof, not prefix inference.

If not unique:
remain unavailable.

---

# 14. 000660 research-table scale

After partial EPS row identity is closed:

use the official 000660 KIS Research report dated 2026-07-29 to calibrate the EPS wire scale exactly as Section 7.

If the report also owns FY1 PER and no API PER row exists:
do not inject report-only PER into the estimate API owner.

The report is a semantic/calibration source.

Production provider value must still originate from an authorized machine-readable route unless a separate official
research-report source owner is explicitly added in a later task.

Therefore for 000660:
- FY1 EPS may qualify if API EPS row + report scale close;
- provider FY1 PER remains unavailable if estimate-perform provides no PER row.

---

# 15. Optional current FY1 fPER

Once FY1 EPS qualifies:

`current_FY1_fPER = completed_session_current_price / KIS_FY1_EPS`

may qualify only if exact basis closes.

Required:
- exact same six-digit ordinary security;
- KIS research EPS is KRW per share for that security;
- completed-session price is the same traded security;
- no relevant split/reverse split/merger/share-unit change between research estdate and completed-session date;
- exact corporate-action source;
- denominator > 0.

Do not use provider report-date PER as current FY1 fPER.

They are different:
- provider report-date fPER snapshot;
- current-price / frozen FY1 EPS.

---

# 16. Corporate-action guard

Use already configured official KIS/KSD corporate-action routes only as needed.

Allowed:
- reverse split;
- merger/split;
- other exact share-unit-changing event route already present in repository.

Scope:
- Stage-A securities first.

Window:
- from KIS research `estdate`
through
- current completed-session price date.

If an action exists:
do not derive current FY1 fPER unless adjustment compatibility is explicitly solved.

If no action exists and exact security identity is unchanged:
the basis may qualify under the new KIS research EPS per-share contract.

No broad corporate-action scan outside queried subjects.

---

# 17. Current-price basis

Reuse the existing completed-session current-price owner.

Do not call intraday current price for the final derived metric.

Current FY1 fPER numerator must be the same deterministic completed-session close used by Thesis Monitor.

Do not use:
- retrieval-time price;
- report-date price;
- target price.

---

# 18. Stage-B admission

Stage B is admitted if at least one of these closes on Stage A:

- FY1 EPS research snapshot;
- provider-native FY1 PER research snapshot.

Then query remaining KR6 through estimate-perform:

- 003690
- 005490
- 010120
- 012450
- 047810
- 086280.

No target numeric coverage.

No requery of 000660/005930 estimate-perform.

---

# 19. Stage-B generic semantics

For each remaining KR6:

- exact security binding;
- exact annual FY owner;
- exact FY1 forecast period;
- full or partial output3 semantic binding;
- global/frozen EPS and PER wire transforms established from Stage-A official KIS research evidence.

Do not recalibrate a different scale per ticker.

If a security's raw shape contradicts the frozen transform:
typed unavailable / contract conflict.

Do not create ticker-specific conversion factors.

---

# 20. KIS research report calls/download budget

Official KIS public research metadata/pages:

maximum:
`6`

Official report/attachment downloads:

maximum:
`2`

one for:
- 005930
- 000660.

KIS data API calls:

Stage-A estimate:
`0`

Stage-B estimate:
maximum `6`

Corporate-action calls:
bounded only to subjects with qualified FY1 EPS and current-fPER attempt.

Hard total new KIS API data calls:
`16`

excluding one normal auth operation.

No FnGuide.

No Alpha Vantage.

---

# 21. Rate pacing

No parallel KIS calls.

Minimum spacing:
`>= 1.1 seconds`

or the official client `smart_sleep()` if stricter.

If:
`EGW00201`

occurs:
- no immediate retry;
- record typed rate-limit state;
- stop optional expansion if necessary.

Do not classify it as no-estimate coverage.

---

# 22. External transmission approval

REV35 explicitly authorizes bounded read-only access to:

- official KIS public research website;
- official KIS report attachments;
- KIS estimate-perform for conditional KR6 Stage B;
- KIS/KSD corporate-action routes for qualified EPS subjects;
- normal KIS authentication;
- official KIS API portal/GitHub documentation.

No:
- paid FnGuide;
- non-KIS report scraping as source authority;
- model runner;
- Telegram;
- trading/order routes;
- production DB writes;
- scheduler mutation;
- deploy;
- merge;
- push;
- restart.

No additional user approval is required for this exact bounded scope.

---

# 23. Credential policy

The user explicitly accepted current KIS credentials.

Continue using only secure local configuration.

Never persist:
- App Key;
- Secret;
- token;
- auth header.

If exposed:
stop:

`R2B_R9_REV35_KIS_SECRET_EXPOSURE_GAP`

Do not archive exposed output.

---

# 24. No broad full-fresh / no models

REV35 must not run:

- US source collection;
- Market source collection;
- broad KR source collection;
- Market/Core/A/B;
- exact24.

Models:
`0`

Messages:
`0/24`

Telegram:
`0`.

---

# 25. Typed KR8 matrix

For every KR8 produce:

## KIS FY1 EPS
- QUALIFIED_KIS_RESEARCH_FY1_EPS
- UNAVAILABLE_RESEARCH_REPORT_BINDING
- UNAVAILABLE_RESEARCH_SNAPSHOT_MISMATCH
- UNAVAILABLE_PARTIAL_ROW_SEMANTICS
- UNAVAILABLE_FISCAL_PERIOD
- UNAVAILABLE_NO_ESTIMATE
- other typed reason.

## KIS provider FY1 PER
- QUALIFIED_KIS_RESEARCH_FY1_PER
- UNAVAILABLE_NO_PER_ROW
- UNAVAILABLE_RESEARCH_SNAPSHOT_MISMATCH
- other typed reason.

## Current derived FY1 fPER
- QUALIFIED_CURRENT_PRICE_FY1_FPER
- UNAVAILABLE_EPS
- UNAVAILABLE_CORPORATE_ACTION_BASIS
- NOT_MEANINGFUL
- other typed reason.

Every state independently owned.

No metric suppresses another.

---

# 26. Validation

Required:

- research-snapshot binding tests;
- same-security/date/analyst mismatch negatives;
- EPS/report scale tests;
- PER/report scale tests;
- 000660 growth-equation partial-row tests;
- uniqueness negative;
- corporate-action guard tests;
- current completed-session numerator tests;
- Stage-B generic transform tests;
- no ticker-specific factor;
- valuation authority isolation;
- REV32/33/34 regressions;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No positive owner PASS if full suite is red.

---

# 27. Success terminal

If at least one Stage-A forward valuation metric closes from the exact KIS research snapshot and full validation passes:

`R2B_R9_REV35_KIS_RESEARCH_FORWARD_VALUATION_PASS_READY_FOR_LIVE_INTEGRATION`

Acceptable success examples:

- FY1 EPS only;
- provider FY1 PER only;
- both;
- current derived FY1 fPER as additional capability.

It does not require:
- all KR8 coverage;
- consensus semantics;
- 000660 provider PER.

---

# 28. Honest stop terminals

- `R2B_R9_REV35_KIS_RESEARCH_ARTIFACT_GAP`
- `R2B_R9_REV35_KIS_RESEARCH_SNAPSHOT_BINDING_GAP`
- `R2B_R9_REV35_KIS_RESEARCH_WIRE_SCALE_GAP`
- `R2B_R9_REV35_KIS_RESEARCH_SNAPSHOT_MISMATCH`
- `R2B_R9_REV35_KIS_PARTIAL_ROW_SEMANTIC_GAP`
- `R2B_R9_REV35_CURRENT_FPER_BASIS_GAP`
- `R2B_R9_REV35_KIS_RATE_LIMIT_GAP`
- `R2B_R9_REV35_KIS_SECRET_EXPOSURE_GAP`
- `R2B_R9_REV35_VALIDATION_GAP`.

Do not solve by:
- dropping 2025;
- comparing to market plausibility;
- using third-party report tables;
- fitting a scale;
- treating KIS house estimate as consensus.

---

# 29. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

## Integrity
- REPORT.md
- summary.json
- REV34 result identity/SHA
- repository identities
- changed files
- manifest.

## Source-definition review
- research-vs-reported EPS semantic distinction receipt;
- preserved REV34 mismatch matrix.

## Official KIS research
- official report metadata;
- official page/attachment hashes;
- exact analyst/date/security binding;
- extracted report table/page evidence.

## Wire semantics
- 005930 EPS transform receipt;
- 005930 PER transform receipt;
- mismatch negatives.

## Partial
- 000660 EPS/growth structural-equation audit;
- unique row binding or denial;
- 000660 report scale receipt.

## Freshness
- estdate ages;
- latest KIS research snapshot state;
- no query-date relabel.

## Current fPER
- completed-session price identity;
- corporate-action guard;
- derived current FY1 fPER receipt or typed denial.

## KR8
- conditional Stage-B raw/receipts;
- final per-metric state matrix.

## Safety
- KIS call counters;
- research downloads;
- FnGuide 0;
- Alpha 0;
- models 0;
- messages 0;
- Telegram 0;
- production mutations 0;
- secret scan.

---

# 30. Next handoff

If PASS, prepare REV36 recommendation only.

REV36 should:

- integrate the qualified KIS research FY1 source into the normal KR fresh plan;
- preserve the KIS estimate date explicitly;
- render:
  - current PER
  - current PBR
  - FY1 EPS (KIS research)
  - provider/report-date fPER(FY1) if qualified
  - current-price FY1 fPER if separately qualified;
- label KIS house estimate, not consensus;
- expose forward valuation only to B/NewBuyer/Holder;
- perform archive-backed GC if needed;
- run one fresh full-source proof before model/messages.

Keep detailed renderer restoration as a separate task unless explicitly authorized.

---

# 31. Final principle

REV34's exact-equality failure was useful because it exposed a false premise:

the KIS research estimate series and KIS reported financial-ratio series are not necessarily the same EPS definition or
update snapshot.

Do not force them to match.

The strongest free source-definition authority is the KIS research artifact tied to the same:
- security;
- analyst;
- estimate date.

Use that artifact to calibrate the machine-readable estimate-perform EPS/PER representation.

Then preserve the estimate date and source identity honestly.

If a current-price FY1 fPER is derived, guard the per-share basis and corporate actions explicitly.

The result is a free KIS **house-research** forward valuation source, not market consensus.
