# Thesis Monitor — R2B-R9-REV33
## KIS FY1 Semantic Closure
### Exact KIS Security Identity + Fiscal Boundary + Forecast Marker + EPS/PER Wire Semantics
### Reuse REV32-R1 Stage-A Raw Evidence First
### Conditional KR8 Completion Only After Positive Semantic Closure
### No Broad Full-Fresh / No Models / No 24-Message Run

**REV33 supersedes every prior unexecuted post-REV32-R1 KIS-forward-valuation instruction. Execute only REV33.**

REV32-R1 proved that the free KIS `estimate-perform` route is real, reachable and contains prospective estimate data.

It did **not** prove the final FY1 owner.

The correct terminal was:

`R2B_R9_REV32_KIS_ESTIMATE_SEMANTICS_GAP`

The live Stage-A facts are highly promising:

## 000660
- HTTP 200 / `rt_cd=0`
- output4:
  - `2023.12`
  - `2024.12`
  - `2025.12`
  - `2026.12E`
  - `2027.12E`
- output3 rows:
  `3`
- raw response SHA-256:
  `08129f80e7fc76704e65394aca693632d57fdfedbc5b73e16f0347e3fd98d5c9`

## 005930
- HTTP 200 / `rt_cd=0`
- same five period labels
- output3 rows:
  `8`
- official full-layout mapping identifies:
  - row 0 EBITDA
  - row 1 EPS
  - row 2 EPS change
  - row 3 PER
  - row 4 EV/EBITDA
  - row 5 ROE
  - row 6 debt ratio
  - row 7 interest coverage
- raw response SHA-256:
  `55394b92d4af5174e12a04d65696ac7b1e47dd9bb2e959f92b42dfc5afacc2e0`

For 005930 the unqualified raw candidate rows are:

EPS row index 1:
- 2023.12 → `21310.0`
- 2024.12 → `49500.0`
- 2025.12 → `66050.0`
- 2026.12E → `462090.0`
- 2027.12E → `672398.0`

PER row index 3:
- 2023.12 → `368.0`
- 2024.12 → `107.0`
- 2025.12 → `182.0`
- 2026.12E → `45.0`
- 2027.12E → `31.0`

These are **raw candidates only**.
REV33 must not pre-decide their human-readable scale.

The remaining blockers are narrow:

1. request `005930` vs response `A005930` exact KIS security identity;
2. exact latest-completed-FY / FY1 boundary;
3. endpoint-specific meaning of `E`;
4. output3 row/scale semantics, especially:
   - shortened 000660 output3;
   - PER's documented `0.1`-class scale text.

REV33 must close those contracts, not recollect everything.

---

# 0. Newest SoT

Adopt REV32-R1 as newest KIS-forward-source SoT.

REV32-R1 result ZIP:

`thesis-monitor-20260930-r2b-r9-rev32-r1-kis-fy1-report.zip`

SHA-256:

`86622b3f5c4d1428897bd5493ac2678c903b8d2fa53ae594aa265639a62b23a2`

Independent verification:

- sidecar:
  PASS
- ZIP CRC:
  PASS
- ZIP members:
  `72`
- internal manifest:
  `71/71`
- missing/hash/size/extra:
  `0`.

Terminal:

`R2B_R9_REV32_KIS_ESTIMATE_SEMANTICS_GAP`

Repository:

- base:
  `f5e0b96fde3f0f58e93bf82df2c09233ebcd246f`
- branch:
  `codex/r2b-r9-rev32-r1-kis-fy1-probe`
- instruction:
  `09a078b86975578c36270043cbd1fb79939809e2`
- implementation:
  `25fa55ba0e56c2f1528b6715a2be50ef70251300`
- final:
  `ee0a4f30a1df6f319f00860452efb52eedf74c67`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean:
  true.

REV32-R1 execution:

- KIS auth:
  `1`
- estimate-perform:
  `2`
- continuation:
  `0`
- transport retry:
  `0`
- semantic retry:
  `0`
- Stage B:
  `0`
- models:
  `0`
- messages:
  `0`
- Alpha Vantage:
  `0`
- FnGuide:
  `0`
- production mutations:
  `0`.

Validation:

- focused:
  `138 passed`
- full:
  `7184 passed / 63 skipped / 0 failed / 0 errors`
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

# 1. Existing credentials remain accepted

The user explicitly chose to continue using the existing locally configured KIS credential pair.

Do not:
- request credential rotation again;
- ask the user to paste credentials;
- print credentials;
- persist auth headers/tokens;
- archive auth bodies.

Continue the REV32-R1 secret policy.

If a secret is exposed again in runtime/tool output:
- stop;
- do not archive the exposed output;
- perform no further KIS request in that run;
- return:
  `R2B_R9_REV33_KIS_SECRET_EXPOSURE_GAP`.

---

# 2. Preserve REV32-R1 Stage-A raw evidence byte-identically

Before any external call:

verify and register the existing sealed Stage-A responses:

000660:
`08129f80e7fc76704e65394aca693632d57fdfedbc5b73e16f0347e3fd98d5c9`

005930:
`55394b92d4af5174e12a04d65696ac7b1e47dd9bb2e959f92b42dfc5afacc2e0`

Do not repeat `estimate-perform` for these two securities merely to get the same data.

First attempt semantic closure against:
- these exact raw bodies;
- official KIS documentation;
- existing Thesis Monitor source evidence;
- bounded identity/fiscal helper routes authorized below.

If the raw evidence is missing or hash-mismatched:

`R2B_R9_REV33_STAGE_A_RAW_IDENTITY_GAP`.

---

# 3. KIS official source inventory

Pin exact official KIS sources used for semantic closure.

At minimum:

## estimate-perform
- API:
  `국내주식 종목추정실적 [국내주식-187]`
- path:
  `/uapi/domestic-stock/v1/quotations/estimate-perform`
- TR ID:
  `HHKST668300C0`
- parameter:
  `SHT_CD`
- response:
  output1–output4.

## product/basic identity
Use the already-official KIS product-information route if needed:

`/uapi/domestic-stock/v1/quotations/search-info`

TR ID:

`CTPF1604R`

with:
- `PDNO`
- `PRDT_TYPE_CD`.

The official KIS example accepts six-digit domestic `PDNO`, including `000660`.

A second official KIS identity route such as `search-stock-info` may be used only if `search-info` is insufficient.

No unofficial security-identity service.

---

# 4. Blocker A — exact KIS security representation

REV32-R1 correctly refused to strip `A` by local convention alone.

REV33 may qualify a KIS representation normalization only from KIS-owned evidence.

Create, repository naming permitting:

`KISDomesticSecurityRepresentationBinding`

For 000660 and 005930 prove:

- request six-digit code;
- estimate-perform response `sht_cd`;
- KIS product/basic-info response identity;
- market/security/product type;
- company/security name;
- any provider product number / short code / standard code returned;
- exact normalization rule.

Allowed normalization only if official KIS evidence demonstrates that:
- the response's `A`-prefixed representation and six-digit domestic code refer to the exact same listed security;
- prefix removal/addition is provider notation, not issuer inference.

Do not rely only on:
- name equality;
- value plausibility;
- another broker's A-prefix convention.

No preferred/common sibling transfer.

---

# 5. KIS identity-call budget

First use:

`search-info`

for:
- 000660
- 005930.

Maximum initial identity calls:

`2`

If and only if `search-info` lacks enough identity fields:

one `search-stock-info` call per security is permitted.

Absolute KIS identity-call maximum:

`4`

No estimate-perform refresh for Stage-A subjects at this phase.

---

# 6. Blocker B — exact latest completed annual fiscal owner

REV32-R1 found that the currently **selected** financial owner is H1/current-prior, which is not enough to define FY1.

REV33 must first search the existing sealed/current source graph for an already-acquired official annual fiscal owner.

For each of 000660 and 005930 find, if available:

- exact latest completed annual fiscal filing;
- exact fiscal year;
- fiscal end month;
- official filing/report identity;
- annual vs interim type;
- source hash.

Do not limit this search to the selected H1 owner.

Search:
- formal-filing inventories;
- existing OpenDART acquisitions;
- existing annual financial candidate records;
- deterministic filing metadata.

If an exact annual source is already present:
use it without provider recollection.

---

# 7. Conditional bounded OpenDART annual-metadata read

Only if the existing sealed source does not contain an exact latest completed annual fiscal owner:

REV33 explicitly authorizes a **bounded read-only OpenDART metadata/acquisition check** for:

- 000660
- 005930

using the already-configured official OpenDART provider.

Maximum OpenDART calls:

`4`

Purpose only:
- identify exact latest completed annual filing/business year/fiscal period.

Do not recollect broad financial statements unless required to establish annual fiscal identity.

No other KR security yet.

No Alpha Vantage.

---

# 8. FY1 definition

After exact fiscal ownership:

`FY1` = earliest KIS **qualified forecast annual period** strictly after the latest completed annual fiscal period
for the same issuer/security fiscal calendar.

Do not:
- subtract one calendar year;
- assume every issuer is December year-end;
- use H1 as completed FY;
- infer FY1 before the forecast marker contract below closes.

Record:

- latest completed fiscal year;
- fiscal end month;
- KIS period labels;
- chosen FY1;
- chosen FY2;
- exact selection reason.

---

# 9. Blocker C — forecast-marker `E` semantics

REV32-R1 observed:

- unmarked historical period labels;
- followed by:
  - `2026.12E`
  - `2027.12E`.

The official endpoint itself is:
`종목추정실적`

and official portal text states its estimate/opinion data reflect KIS research analyst estimates.

However REV32-R1 did not locate an explicit textual definition saying "`E` means estimate."

REV33 must perform a bounded semantic closure.

## Strong path
Prefer official KIS evidence explicitly defining the suffix.

Search only:
- official KIS API portal/help;
- official KIS repository/generated examples;
- official eFriend/HTS help material reachable without credentials or financial scraping.

If found:
bind exact text/source hash.

## Controlled endpoint-semantic path
If no separate sentence defines `E`, REV33 may create:

`KIS_FORECAST_MARKER_ENDPOINT_SEMANTICS`

only when **all** are true:

1. endpoint is officially `종목추정실적`;
2. official description explicitly says it contains analyst estimate data;
3. `output4.dt` is officially documented as the period linked to data1–data5;
4. live responses show unmarked historical periods followed by literal `E`-suffixed future periods;
5. at least both Stage-A securities show the same period-marker pattern;
6. no conflicting official definition exists;
7. the inference is explicitly labelled endpoint-semantic, not a quoted KIS definition.

Under this controlled path:
- `E` may be used as the provider forecast-period marker for this endpoint;
- do not generalize the rule to unrelated KIS endpoints.

This is an explicit source-contract policy, not silent guessing.

---

# 10. Blocker D1 — full output3 semantic mapping

For an output3 array with all documented eight rows:

map only by the exact official fixed ordering:

0. EBITDA
1. EPS
2. EPS growth
3. PER
4. EV/EBITDA
5. ROE
6. debt ratio
7. interest coverage.

For 005930 with length 8:
this may qualify row identity once Sections 4, 8 and 9 pass.

No numeric reverse engineering is required.

---

# 11. EPS wire scale

For the documented EPS row:

use only the scale/unit that can be justified from official KIS documentation.

REV32-R1 recorded the official unit text as:

`EPS(원)`

If the official API representation uses an additional fixed wire scale:
it must be independently documented.

Do not infer an EPS divisor from:
- current price;
- net income;
- shares;
- PER;
- historical market knowledge.

If official documentation establishes only KRW but not an extra scale:
preserve the raw provider numeric representation until the exact wire-format contract is proven.

A raw EPS candidate is not yet a user-display EPS if its decimal scale is ambiguous.

---

# 12. PER wire scale

REV32-R1 observed official unit text equivalent to:

`PER(배, 0.1...)`

but treated the exact machine scale as ambiguous.

REV33 must not reverse-engineer the divisor from price/EPS.

Qualify provider-native FY1 PER only if official KIS source material clearly establishes the wire representation.

Acceptable evidence:
- official field definition explicitly stating the 0.1 scale;
- official HTS/API example mapping raw→display;
- official generated schema documentation with exact numeric unit semantics.

If exact scale remains ambiguous:
- FY1 EPS may still qualify independently;
- provider FY1 PER remains unavailable.

Metric independence is mandatory.

---

# 13. Blocker D2 — 000660 partial output3

000660 returns exactly 3 rows while official full layout documents 8.

Do not automatically assume the array is a prefix.

Attempt semantic closure in this order:

1. locate official KIS documentation for partial output3 behavior;
2. locate official KIS example showing shortened output3 ordering;
3. inspect whether the endpoint supplies a row-identity field omitted by the current extraction;
4. inspect raw JSON shape again byte-for-byte.

If no source-owned partial-layout rule exists:

- do **not** qualify 000660 output3 EPS/PER by position;
- retain:
  `UNAVAILABLE_PARTIAL_OUTPUT3_SEMANTICS`.

This is acceptable even if 005930 qualifies.

Do not use value plausibility or cross-metric arithmetic to force SK hynix coverage.

---

# 14. 005930 positive-control closure

005930 is the primary positive control because it has the complete documented output3 layout.

If Sections 4, 8, 9, 10 and 11 pass:

qualify:

`KIS_FY1_EPS_ESTIMATE_SNAPSHOT`

for the exact FY1 row.

If Section 12 also passes:

qualify:

`KIS_PROVIDER_FY1_PER_SNAPSHOT`.

Do not require provider PER success in order to accept exact FY1 EPS.

This is important:
EPS and PER are separate metrics.

---

# 15. Optional derived FY1 fPER remains secondary

Do not derive price/EPS merely because FY1 EPS becomes qualified.

A derived:

`completed_session_price / FY1_EPS`

requires exact compatible:
- security;
- common/preferred class;
- per-share basis;
- corporate-action/split basis;
- current-price basis.

Reuse the existing security/share-price basis owner.

If that basis is still unresolved:
derived FY1 fPER remains unavailable.

Provider-native FY1 PER may be used independently if qualified.

---

# 16. Stage-B admission

Query remaining KR6 only after at least one exact Stage-A positive path is qualified:

- FY1 EPS; or
- provider FY1 PER.

Preferred trigger:
005930 positive.

Then query:
- 003690
- 005490
- 010120
- 012450
- 047810
- 086280

through the same frozen generic owner.

No ticker-specific mapping.

No relaxed semantics for the remaining six.

---

# 17. Stage-B call budget

Estimate-perform:
- maximum one initial call per remaining security;
- continuation only if the live response explicitly requires it and current KIS endpoint policy permits it.

Maximum additional estimate-perform calls:

`12`

Preferred:

`6`

Do not repeat 000660/005930 unless a narrow transport-integrity reason requires it.
Semantic closure should use their sealed REV32 raw evidence.

No result-driven repeated calls.

---

# 18. KR8 typed result matrix

Produce exact states for every KR8:

## FY1 EPS
- QUALIFIED_KIS_FY1_EPS
- UNAVAILABLE_SECURITY_IDENTITY
- UNAVAILABLE_FISCAL_PERIOD
- UNAVAILABLE_FORECAST_MARKER
- UNAVAILABLE_PARTIAL_OUTPUT3_SEMANTICS
- UNAVAILABLE_WIRE_SCALE
- UNAVAILABLE_NO_FORECAST_ROW
- other typed reason.

## Provider FY1 PER
independent state.

## Derived FY1 fPER
independent state.

## FY2
diagnostic only; not mandatory.

No numeric coverage target.

No stock-source failure merely because forward estimate coverage is unavailable.

---

# 19. KIS estimate semantics are valuation context only

Future permissions:

Allowed:
- Valuation section;
- NewBuyer valuation context;
- Holder valuation context;
- valuation-specific caution/confidence.

Prohibited:
- Overall business direction;
- Fundamental Core;
- Pass-A directional refs;
- supporting/contradicting business evidence.

Preserve the REV31-C1 valuation authority architecture.

No model calls in REV33.

---

# 20. Current PER/PBR unchanged

Do not alter:
- Kiwoom current PER/PBR owner;
- Finnhub direct-US current PER/PBR owner;
- ADR denial;
- US fPER state.

REV33 is only Korean FY1 forecast-source closure.

Do not compare KIS forecast PER to current Kiwoom PER as a validation shortcut.

They are different metrics and may use different update times.

---

# 21. Existing credential and secret policy

Use current user-approved KIS credentials from the secure local source.

Never persist:
- App Key;
- Secret;
- access token;
- auth header.

Secret-scan every new raw artifact before persistence.

If any secret exposure occurs:
stop with:
`R2B_R9_REV33_KIS_SECRET_EXPOSURE_GAP`.

---

# 22. External transmission approval

REV33 explicitly authorizes:

## KIS
- bounded `search-info`;
- conditional `search-stock-info`;
- conditional Stage-B `estimate-perform`;
- normal one-session authentication behavior.

## OpenDART
- bounded annual-fiscal metadata acquisition only if existing source evidence is insufficient.

## Public official documentation
- KIS API portal;
- KIS official GitHub repository;
- official public help/reference material.

No:
- FnGuide paid API;
- HTML financial scraping;
- models;
- Telegram;
- broker orders;
- production DB writes;
- scheduler mutation;
- deploy;
- main merge;
- remote push;
- restart.

No additional user approval is required for this exact read-only scope.

---

# 23. No broad full-fresh

Do not run:
- US14 source refresh;
- Market source refresh;
- full KR source refresh;
- Market/Core/A/B;
- exact24.

Only bounded forward-source/identity/fiscal work is permitted.

Models:
`0`

Messages:
`0/24`

Telegram:
`0`.

---

# 24. Disk guard

REV32-R1 final free bytes:

`10,613,243,904`

REV33 is bounded.

Require before external calls:

`>= 8 GiB`

No destructive generation GC needed solely for this task.

Preserve all accepted REV31/REV31-C1 blind-review artifacts.

---

# 25. Required tests

## Security representation
- six-digit request + KIS provider binding positive;
- wrong A-prefixed security;
- sibling/preferred mismatch;
- name-only match negative.

## Fiscal owner
- completed annual positive;
- H1-only negative;
- wrong fiscal end month;
- stale annual.

## Forecast marker
- documented E positive;
- endpoint-semantic controlled positive;
- unlabeled future year negative;
- conflicting marker negative.

## Full output3
- exact 8-row mapping positive;
- reordered rows negative;
- missing row negative.

## Partial output3
- explicit source-owned partial rule positive if found;
- otherwise fail closed;
- no prefix assumption by default.

## EPS/PER scale
- exact documented scale positive;
- ambiguous scale unavailable;
- no price/EPS reverse engineering.

## Authority
- forward valuation context allowed;
- Overall direction prohibited.

## Coverage
- missing estimate typed unavailable, not source failure.

---

# 26. Validation

After implementation:

- focused REV33 tests;
- REV32 acquisition regression;
- current PER/PBR regression;
- valuation visibility/isolation tests;
- whole-source registry tests if a new mandatory owner module is registered;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No positive terminal unless full suite is green.

---

# 27. Success terminal

If at least one exact KIS FY1 metric is qualified, the generic owner is implemented and the full suite is green:

`R2B_R9_REV33_KIS_FY1_SEMANTIC_OWNER_PASS_READY_FOR_LIVE_INTEGRATION`

This does not require:
- 000660 qualification;
- all KR8 coverage;
- provider PER if only EPS semantics close;
- derived fPER.

It requires honest typed states for all queried/current KR8 subjects.

---

# 28. Honest stop terminals

- `R2B_R9_REV33_KIS_SECURITY_REPRESENTATION_GAP`
- `R2B_R9_REV33_ANNUAL_FISCAL_OWNER_GAP`
- `R2B_R9_REV33_KIS_FORECAST_MARKER_GAP`
- `R2B_R9_REV33_KIS_EPS_SCALE_GAP`
- `R2B_R9_REV33_KIS_PER_SCALE_GAP`
- `R2B_R9_REV33_KIS_PARTIAL_OUTPUT3_GAP`
- `R2B_R9_REV33_KIS_SECRET_EXPOSURE_GAP`
- `R2B_R9_REV33_VALIDATION_GAP`.

A metric-specific gap must not suppress a separately qualified metric.

---

# 29. Required result bundle

Return immutable result ZIP + `.sha256`.

At minimum:

## Integrity
- REPORT.md
- summary.json
- REV32-R1 result SHA/integrity
- repository identities
- changed files
- manifest.

## Stage-A preservation
- 000660/005930 raw SHA verification
- no unnecessary estimate refresh receipt.

## KIS security identity
- search-info raw/receipt
- optional search-stock-info raw/receipt
- exact representation-binding decision.

## Fiscal ownership
- existing-source annual inventory
- optional OpenDART bounded receipts
- annual fiscal-period owner decisions.

## Forecast semantics
- official E-marker evidence or controlled endpoint-semantic policy receipt
- output4 binding.

## Output3 semantics
- full-layout mapping
- partial-layout evidence/denial.

## Scale
- EPS unit/scale decision
- PER unit/scale decision
- exact official evidence hashes.

## KR8 forward valuation
- FY1 EPS matrix
- provider FY1 PER matrix
- derived FY1 fPER matrix
- typed denial reasons.

## Calls/safety
- KIS auth/data counters
- OpenDART counters
- Alpha 0
- FnGuide 0
- models 0
- messages 0
- Telegram 0
- production mutations 0
- secret scan.

---

# 30. Next-stage handoff

If PASS, create a recommendation for REV34 only.

REV34 should:

- integrate the qualified KIS FY1 owner into the normal KR fresh provider plan;
- retain existing current PER/PBR;
- expose:
  - current PER
  - current PBR
  - FY1 EPS
  - fPER(FY1) when provider/derived path qualifies;
- keep valuation out of Core/A;
- make it available to B/NewBuyer/Holder;
- perform archive-backed GC before broad full-fresh if disk requires it;
- seal source-only evidence before models if another blind comparison is desired.

Do not execute REV34 inside REV33.

---

# 31. Final principle

REV32-R1 did not disprove KIS forward valuation.

It proved the opposite:
the endpoint contains a real prospective estimate surface and, for 005930, the complete documented investment-indicator layout.

The remaining work is semantic ownership, not data discovery.

Close:
- KIS security representation;
- fiscal boundary;
- endpoint-specific forecast marker;
- exact EPS/PER row and wire scale.

Qualify metrics independently.

If Samsung FY1 EPS closes while SK hynix's shortened output3 remains ambiguous:
use Samsung and keep SK hynix honestly unavailable rather than inventing a positional mapping.

That is preferable to paying for a new provider or weakening provenance.
