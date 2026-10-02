# Thesis Monitor — R2B-R9-REV34
## KIS EPS Wire Cross-Endpoint Calibration + Partial-Row Semantic Binding
### Same-Provider Annual EPS Calibration via KIS Financial-Ratio
### Then Conditional KR8 FY1 EPS Expansion
### Provider FY1 PER / Derived fPER Remain Independent
### No Broad Full-Fresh / No Models / No 24-Message Run

**REV34 supersedes every prior unexecuted post-REV33 KIS-forward-valuation instruction. Execute only REV34.**

REV33 closed most of the KIS FY1 semantic problem.

Closed:

- exact KIS security representation:
  `2/2`;
- exact latest completed annual fiscal owner:
  `2/2`;
- endpoint-specific forecast marker:
  `2/2`;
- FY1 candidate:
  `2026.12E`;
- FY2 diagnostic:
  `2027.12E`;
- 005930 exact full output3 row layout:
  EPS = row 1,
  PER = row 3.

Remaining primary blocker:

`R2B_R9_REV33_KIS_EPS_SCALE_GAP`

The problem is now narrowly:

> What deterministic conversion, if any, maps the `estimate-perform` EPS wire value to a display EPS in KRW?

REV33 correctly refused to infer a divisor from:
- stock price;
- PER;
- market plausibility;
- historical knowledge.

REV34 introduces a stronger independent calibration path:

**same provider + same security + same metric + same fiscal period**

using the official KIS annual financial-ratio endpoint.

Official KIS repository route:

- API:
  `국내주식 재무비율 [v1_국내주식-080]`
- path:
  `/uapi/domestic-stock/v1/finance/financial-ratio`
- TR ID:
  `FHKST66430300`
- annual selector:
  `FID_DIV_CLS_CODE=0`
- market:
  `fid_cond_mrkt_div_code=J`
- security:
  `fid_input_iscd=<six-digit code>`
- output includes:
  - `stac_yymm`
  - `eps`
  - other financial-ratio fields.

This allows estimate-perform historical EPS wire rows to be calibrated against an **independent official KIS EPS series**
without using price or PER.

REV34 must use that source relationship narrowly.

---

# 0. Newest SoT

Adopt REV33 as newest KIS semantic SoT.

REV33 result ZIP:

`thesis-monitor-20261001-r2b-r9-rev33-kis-fy1-semantic-closure-report.zip`

SHA-256:

`fd8b2c582603a6d7e87d5a130355f3ace63d5591ed316aa33225cbf79a868f04`

Independent verification:

- sidecar:
  exact match;
- ZIP CRC:
  PASS;
- ZIP members:
  `86`;
- internal manifest:
  `85/85`;
- missing:
  `0`;
- hash mismatch:
  `0`;
- size mismatch:
  `0`;
- extra:
  `0`.

REV33 terminal:

`R2B_R9_REV33_KIS_EPS_SCALE_GAP`

Repository:

- base:
  `ee0a4f30a1df6f319f00860452efb52eedf74c67`
- branch:
  `codex/r2b-r9-rev33-kis-semantic-closure`
- instruction:
  `6ea5b84ffa15f40bb8e7d18548f1a4ac04c70298`
- frozen acquisition probe:
  `e6fdba14f700e87a7d467f1fe885d3ca08f3cc8e`
- implementation:
  `886d248a0413bab3197da961f23bb1afba69c3cc`
- final:
  `07bc7f722828d798d6c463749532a4a885abc1d4`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean:
  true.

Validation:

- focused:
  `193 passed`
- full:
  `7239 passed / 63 skipped / 0 failed / 0 errors`
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

REV33 final free bytes:

`10,329,563,136`

REV34 is bounded, not a broad generation.

---

# 1. Preserve all REV33 closed contracts

Do not reopen:

## Security identity
000660:
- six-digit code:
  `000660`
- KIS product number:
  `00000A000660`
- standard security:
  `KR7000660001`

005930:
- six-digit code:
  `005930`
- KIS product number:
  `00000A005930`
- standard security:
  `KR7005930003`

The A-prefix relationship is owned by the exact KIS product tuple.
No standalone prefix stripping.

## Fiscal owner
Both:
- latest completed annual FY:
  `2025.12`

No H1 substitution.

## Forecast-period owner
For both Stage-A controls:

- FY1:
  `2026.12E`
- FY2 diagnostic:
  `2027.12E`

Method:

`KIS_FORECAST_MARKER_ENDPOINT_SEMANTICS`

This remains a controlled endpoint-specific semantic policy, not a universal KIS "E" definition.

## Full-layout row mapping
For 005930 full eight-row output3:

- row 1:
  EPS
- row 3:
  PER.

No numeric plausibility inference.

---

# 2. Preserve sealed Stage-A estimate responses

Do not repeat estimate-perform for Stage-A controls.

000660 raw SHA-256:

`08129f80e7fc76704e65394aca693632d57fdfedbc5b73e16f0347e3fd98d5c9`

005930 raw SHA-256:

`55394b92d4af5174e12a04d65696ac7b1e47dd9bb2e959f92b42dfc5afacc2e0`

Verify both before calibration.

If missing/mismatch:

`R2B_R9_REV34_STAGE_A_RAW_IDENTITY_GAP`

No automatic refresh.

---

# 3. Exact Stage-A historical EPS candidates

For 005930, full-layout row 1 raw historical candidates:

- 2023.12:
  `21310.0`
- 2024.12:
  `49500.0`
- 2025.12:
  `66050.0`
- 2026.12E:
  `462090.0`
- 2027.12E:
  `672398.0`.

These remain wire values until calibration.

For 000660, no partial-row semantic is assumed yet.

---

# 4. Official KIS annual EPS calibration route

Add a bounded diagnostic route under the existing KIS provider:

`/uapi/domestic-stock/v1/finance/financial-ratio`

TR ID:

`FHKST66430300`

Parameters:

- `FID_DIV_CLS_CODE=0`
- `fid_cond_mrkt_div_code=J`
- `fid_input_iscd=<exact six-digit security>`.

Use only for:
- same-provider annual EPS calibration;
- partial-row EPS semantic binding.

Do not add this route to production source collection in REV34.

---

# 5. Stage-A financial-ratio calls

Query:

- 005930
- 000660.

Maximum:

`2`

initial financial-ratio data calls.

Continuation:
follow at most one page per subject only if the official response header explicitly requires it and the needed
2023/2024/2025 annual rows are not already present.

Absolute financial-ratio maximum:

`4`

No semantic retry.

Use KIS published/client rate pacing rather than REV33's 0.2-second loop.
Preferred minimum spacing for these bounded calls:

`>= 1.0 second`

unless the official KIS client `smart_sleep()` contract enforces a safer delay.

No result-driven rapid follow-up.

---

# 6. Annual financial-ratio EPS owner

For each calibration response create:

`KISAnnualEPSReference`

Required:

- exact security binding;
- `stac_yymm`;
- `eps`;
- annual selector proof;
- raw response SHA;
- retrieval timestamp;
- KIS route/TR ID;
- exact unit/field semantic from official documentation where available.

Do not assume this endpoint's wire representation is human-display EPS until its own official field contract is reviewed.

If its `eps` representation is itself ambiguous:
do not use it as calibration authority.

---

# 7. Optional OpenDART same-period corroboration

Existing sealed OpenDART annual filings may be used as a corroborating source for exact annual EPS facts if such facts
already exist in the sealed source graph.

Do not recollect broad OpenDART data by default.

If an exact annual EPS fact is not already available and one bounded official OpenDART read is needed to disambiguate
the KIS financial-ratio EPS representation:

REV34 authorizes at most:

`2`

bounded OpenDART reads total,
one per Stage-A subject.

OpenDART is corroboration.
The KIS cross-endpoint relationship remains the wire-calibration owner.

Do not use price/PER to calibrate EPS.

---

# 8. Same-provider same-metric calibration policy

Create:

`KISEstimatePerformEPSWireCalibration`

This is explicitly allowed in REV34.

It is not "market plausibility inference."

Calibration requires:

1. estimate-perform and financial-ratio are both official KIS endpoints;
2. exact same six-digit security;
3. exact same annual fiscal period;
4. estimate-perform full-layout EPS row identity is already independently owned for the calibration control;
5. financial-ratio `eps` field semantic is independently owned;
6. at least two historical actual annual periods overlap;
7. every overlapping non-null pair implies the exact same deterministic conversion;
8. no period is selectively dropped merely because it disagrees;
9. no price or PER is used;
10. conversion is simple and exact, not a fitted regression.

Preferred control:

005930.

Use:
- 2023.12
- 2024.12
- 2025.12

when present in both endpoints.

A valid conversion may be:
- identity;
- one exact fixed decimal factor;
- another deterministic source-owned representation transform.

Do not pre-assume:
`0.1`.

Let the data/source contract determine it.

---

# 9. Calibration acceptance threshold

For 005930 require:

- minimum matched periods:
  `2`
- preferred:
  `3`
- exact same conversion for all available matches.

If three periods exist and one conflicts:
do not drop the conflicting period.

State:

`UNAVAILABLE_CROSS_ENDPOINT_SCALE_CONFLICT`

No FY1 EPS qualification.

If the conversion closes:
apply it to 005930 FY1 raw EPS:

`462090.0`

only through the exact frozen conversion receipt.

Record:
- raw value;
- conversion;
- display EPS;
- FY1 period;
- both endpoint source hashes;
- calibration hash.

---

# 10. Cross-provider corroboration cannot be the scale owner

OpenDART/current Kiwoom values may be used only to detect a serious contradiction.

They may not be the sole basis for choosing among multiple KIS conversion factors.

No:
- "this value looks realistic";
- "this matches market consensus";
- "this makes PER plausible."

The scale must close from KIS same-metric evidence.

---

# 11. 000660 partial-row EPS semantic binding

REV33 correctly refused to assume the three-row output3 is the prefix of the eight-row layout.

REV34 introduces a separate narrow semantic path:

`KISPartialOutput3EPSCrossEndpointBinding`

After the 005930 EPS wire calibration is frozen:

for every 000660 output3 row:
- align historical data1/data2/data3 with:
  - 2023.12
  - 2024.12
  - 2025.12;
- apply the already-frozen estimate EPS wire conversion;
- compare against official KIS financial-ratio annual EPS for the same three periods.

A row may be bound as EPS only if:

1. exact security;
2. all available overlapping historical periods match the independent KIS EPS series exactly under the frozen conversion;
3. exactly one output3 row satisfies the full match;
4. no competing row satisfies it;
5. no period is selectively ignored;
6. no price/PER/market plausibility is used.

This is a cross-endpoint semantic identity proof.

It is not a prefix assumption.

If row 1 uniquely matches:
qualify row 1 as EPS for this shortened response layout.

If no row or multiple rows match:
retain:

`UNAVAILABLE_PARTIAL_OUTPUT3_SEMANTICS`.

Do not qualify 000660 provider PER in this path.

---

# 12. FY1 EPS qualification

Once:

- security identity;
- annual fiscal owner;
- FY1 forecast owner;
- EPS row identity;
- EPS wire calibration

all PASS,

create:

`KIS_FY1_EPS_ESTIMATE_SNAPSHOT`

with:

- exact security;
- `FY1 = 2026.12E` for Stage-A controls under current source;
- raw estimate value;
- display EPS value;
- currency:
  KRW;
- provider:
  KIS;
- endpoint:
  estimate-perform;
- retrieval snapshot timestamp;
- underlying provider estimate date only if independently owned;
- source hashes;
- calibration receipt hash;
- `overall_direction_use=false`.

Do not call it:
- NTM EPS;
- 12M EPS;
- consensus average

unless separately proven.

Preferred user label:

`FY1 EPS (KIS estimate snapshot)`.

---

# 13. Provider FY1 PER remains metric-independent

REV33's PER blocker remains:

`UNAVAILABLE_WIRE_SCALE`

Do not use EPS calibration to automatically scale PER.

Do not reverse-engineer provider PER from:
- price;
- calibrated EPS;
- output row relationships.

REV34 may review newly encountered official KIS source material for exact PER wire semantics.

If an independent official PER conversion rule is found:
qualify it separately.

Otherwise provider FY1 PER remains unavailable.

FY1 EPS success is still a REV34 success.

---

# 14. Optional derived FY1 fPER — narrow conditional path

The user ultimately needs forward valuation.

A Thesis Monitor derived:

`FY1_fPER = completed_session_price / qualified_FY1_EPS`

may be attempted only **after FY1 EPS is qualified**.

Do not weaken the existing price/share/split basis contract.

First audit whether the current KR completed-session price owner plus exact six-digit KIS security identity can already
satisfy the existing `SecurityValuationBasisReceipt`.

If it still cannot:

derived FY1 fPER remains:

`UNAVAILABLE_PRICE_SHARE_SPLIT_BASIS`.

REV34 does not need to solve this to pass.

---

# 15. Optional same-KIS current-price basis experiment

Only if the existing completed-session basis remains the sole blocker after FY1 EPS closes:

REV34 authorizes a diagnostic KIS current-price read for the two Stage-A controls through the already-official route:

`/uapi/domestic-stock/v1/quotations/inquire-price`

TR ID:

`FHKST01010100`

Maximum:

`2`

calls.

Purpose:
determine whether KIS can source-own an exact current direct-security price basis compatible with the same KIS security
identity.

Do not use the current quote to infer EPS scale.

Do not calculate a production fPER unless the per-share/corporate-action basis contract independently passes.

This experiment is optional and must not block FY1 EPS qualification.

---

# 16. Stage-B admission

Stage B is admitted if at least one Stage-A FY1 EPS is qualified.

It does not require provider PER qualification.

Preferred positive control:

005930.

Then query remaining KR6:

- 003690
- 005490
- 010120
- 012450
- 047810
- 086280.

One estimate-perform call per subject.

No broad source refresh.

---

# 17. Stage-B endpoint pacing

REV33 observed:

`EGW00201`
per-second rate-limit failure

after 0.2-second pacing on the fourth identity call.

REV34 must use safer sequential pacing.

For KIS data calls:
- no parallel calls;
- preferred >=1.0 second spacing;
- obey official client sleep/backoff;
- no immediate retry after EGW00201.

A rate-limit response is a transport/source event, not "no estimate coverage."

If encountered:
record typed source transport state and stop further optional calls if needed.

No retry unless existing frozen KIS transport policy explicitly permits it.

---

# 18. Stage-B row handling

For each remaining KR security:

## Full 8-row output3
- use official full layout;
- row 1 = EPS;
- apply frozen EPS wire calibration.

## Partial output3
Do not assume prefix.
Use the same `KISPartialOutput3EPSCrossEndpointBinding`.

A financial-ratio call is permitted only for a partial-layout security.

Maximum additional financial-ratio calls for Stage B:

`6`

Only when needed to identify EPS in a shortened output3.

No extra call for full-layout subjects.

---

# 19. Stage-B fiscal owner

Use existing exact annual fiscal ownership first.

If a subject lacks latest completed annual owner in the sealed/current source:

do not guess FY1.

Record:

`UNAVAILABLE_FISCAL_PERIOD`

in REV34.

Do not broaden into a full OpenDART recollection for all six.

A later live integration task may acquire missing annual identity under its normal source plan.

---

# 20. KR8 typed states

Produce for all KR8:

## FY1 EPS
- QUALIFIED_KIS_FY1_EPS
- UNAVAILABLE_NO_ESTIMATE
- UNAVAILABLE_SECURITY_IDENTITY
- UNAVAILABLE_FISCAL_PERIOD
- UNAVAILABLE_FORECAST_MARKER
- UNAVAILABLE_WIRE_SCALE
- UNAVAILABLE_PARTIAL_OUTPUT3_SEMANTICS
- UNAVAILABLE_RATE_LIMIT
- other typed reason.

## Provider FY1 PER
independent typed state.

## Derived FY1 fPER
independent typed state.

No numeric coverage target.

Missing KIS estimates do not fail stock-source qualification.

---

# 21. No model-direction authority

Preserve current policy.

KIS FY1 EPS/fPER may eventually affect:
- Valuation section;
- NewBuyer valuation context;
- Holder valuation context;
- valuation-specific confidence/caution.

It may not establish:
- Overall business direction;
- Core;
- A;
- directional supporting/contradicting refs.

No model calls in REV34.

---

# 22. No production integration yet unless owner is proven

REV34 implements the bounded generic owner offline.

Do not add mandatory production source slots yet.

Do not run all22 full-fresh.

Do not modify final messages.

REV35 is the integration phase if REV34 succeeds.

---

# 23. Existing current PER/PBR unchanged

Do not alter:
- Kiwoom current PER;
- Kiwoom current PBR;
- Finnhub direct-US PER/PBR;
- ADR denials;
- US fPER.

KIS FY1 estimate data is a separate metric family.

---

# 24. Credential policy

The user has explicitly accepted continued use of the existing KIS credentials.

Use only the existing secure local credential source.

Never:
- print;
- log;
- archive;
- put credentials in subprocess command lines;
- persist access token/auth headers.

If a secret appears in runtime/tool output:
stop immediately with:

`R2B_R9_REV34_KIS_SECRET_EXPOSURE_GAP`.

Do not archive the exposed output.

---

# 25. External transmission approval

REV34 explicitly authorizes bounded read-only access to:

## KIS
- finance/financial-ratio;
- conditional remaining-KR6 estimate-perform;
- optional Stage-A inquire-price diagnostic;
- normal authentication.

## OpenDART
- maximum two narrow Stage-A annual EPS reads only if needed for contradiction review.

## Official public documentation
- KIS official API portal;
- KIS official GitHub repository.

No:
- FnGuide paid API;
- web financial scraping;
- Alpha Vantage;
- model runner;
- Telegram;
- broker orders;
- production DB writes;
- scheduler mutation;
- deploy/main merge/push/restart.

---

# 26. Call budget

Preferred maximum new provider data calls:

- KIS financial-ratio Stage A:
  `2`
- optional KIS current price Stage A:
  `2`
- Stage B estimate-perform:
  `6`
- Stage B partial-only financial-ratio:
  up to `6`
- optional OpenDART:
  `2`.

Hard total KIS data-call maximum:

`16`

excluding one normal authentication operation.

No repeated Stage-A estimate-perform calls.

No call may be repeated merely to obtain a more favorable value.

---

# 27. Disk guard

REV33 final free bytes:

`10,329,563,136`

REV34 is bounded.

Before external calls require:

`>= 8 GiB`.

No destructive full-generation GC.

Temporary pytest/report scratch cleanup is allowed under the existing protection rules.

Preserve:
- REV31 blind artifacts;
- REV31-C1 accepted proof;
- REV32/REV33 immutable archives;
- Stage-A raw fixtures.

---

# 28. Tests

## Calibration
- exact same-provider same-period same-EPS positive;
- one inconsistent period → fail;
- period mismatch → fail;
- security mismatch → fail;
- scale inferred from price/PER → prohibited;
- multiple candidate transforms → fail.

## 005930
- full row identity;
- historical calibration;
- FY1 raw→display conversion;
- source hash mismatch negative.

## 000660 partial
- unique cross-endpoint EPS row match positive;
- no match;
- duplicate/multiple row match;
- one-period-only insufficient;
- no prefix assumption.

## Stage B
- full-layout;
- partial-layout;
- no estimate;
- rate-limit;
- missing annual owner.

## Derived fPER
- only after EPS qualification;
- price/share/split basis positive fixture;
- unresolved basis remains unavailable.

## Authority
- valuation context only;
- Overall-direction use prohibited.

No live numeric value hardcoded as expected output beyond sealed fixture/hash tests.

---

# 29. Validation

Require:

- focused REV34 tests;
- all REV32/REV33 KIS tests;
- current valuation regression;
- valuation visibility/isolation;
- whole-source registry tests if owner registration changes;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No model calls.

No messages.

---

# 30. Success terminal

If:

- EPS wire calibration closes;
- at least one Stage-A FY1 EPS qualifies;
- generic owner/tests pass;
- KR8 typed state matrix is complete;
- full suite is green;

use:

`R2B_R9_REV34_KIS_FY1_EPS_OWNER_PASS_READY_FOR_LIVE_INTEGRATION`

This terminal does not require:
- provider FY1 PER;
- derived FY1 fPER;
- SK hynix qualification;
- all KR8 estimate coverage.

If derived FY1 fPER also closes:
record it as an additional capability.

---

# 31. Honest stop terminals

- `R2B_R9_REV34_STAGE_A_RAW_IDENTITY_GAP`
- `R2B_R9_REV34_KIS_FINANCIAL_RATIO_EPS_GAP`
- `R2B_R9_REV34_KIS_EPS_CROSS_ENDPOINT_SCALE_GAP`
- `R2B_R9_REV34_KIS_EPS_SCALE_CONFLICT`
- `R2B_R9_REV34_KIS_PARTIAL_OUTPUT3_EPS_GAP`
- `R2B_R9_REV34_KIS_RATE_LIMIT_GAP`
- `R2B_R9_REV34_KIS_SECRET_EXPOSURE_GAP`
- `R2B_R9_REV34_VALIDATION_GAP`.

Provider PER ambiguity must not block a separately qualified FY1 EPS.

---

# 32. Required result bundle

Return immutable result ZIP + `.sha256`.

At minimum:

## Integrity
- REPORT.md
- summary.json
- REV33 identity/SHA
- repository identities
- changed files
- bundle manifest.

## Stage-A preserved source
- estimate raw/hash verification.

## KIS annual EPS reference
- financial-ratio raw/receipts
- annual rows
- EPS semantics
- source hashes.

## Calibration
- matched-period matrix
- exact conversion decision
- conflict analysis
- calibration receipt.

## Partial layout
- 000660 candidate-row comparison matrix
- unique-match/denial receipt.

## FY1
- Stage-A FY1 EPS receipts
- optional provider PER state
- optional derived fPER state.

## Stage B
- remaining KR6 raw/receipts if admitted
- row-layout states
- partial calibration receipts where needed
- KR8 final typed state matrix.

## Safety
- KIS counters
- OpenDART counters
- Alpha 0
- FnGuide 0
- models 0
- messages 0
- Telegram 0
- production mutations 0
- secret scan.

---

# 33. Next handoff

If PASS, prepare REV35 recommendation only.

REV35 should:
- integrate the qualified KIS FY1 EPS owner into the normal KR provider plan;
- decide whether provider FY1 PER or derived FY1 fPER is available per security;
- keep current PER/PBR;
- expose valuation only to NewBuyer/Holder/B;
- run archive-backed GC if required;
- then perform one fresh all-source proof and messages only after the forward owner is stable.

Do not execute REV35 inside REV34.

---

# 34. Final principle

REV33 solved identity, fiscal period and forecast horizon.

The remaining EPS issue is a wire representation problem.

Do not use market plausibility to solve it.

Use a stronger independent source contract:

**KIS estimate EPS vs KIS annual financial-ratio EPS, same security, same fiscal period, same metric.**

If a single exact conversion holds across the historical controls, that is a defensible provider-owned wire calibration.

Then use the same frozen calibration to interpret FY1 EPS.

For shortened output arrays, identify EPS by independent same-provider historical EPS matching rather than assuming the
array is a prefix.

This keeps the forward-valuation path free, deterministic and provenance-safe.
