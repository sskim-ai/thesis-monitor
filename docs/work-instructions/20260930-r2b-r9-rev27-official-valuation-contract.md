# Thesis Monitor — R2B-R9-REV27
## Official Valuation Source Contract Expansion
### Kiwoom ka10001 KR Native PER/PBR + Finnhub Identity/Metric/Estimate Capability
### No Full-Fresh / No Models / No 24-Message Run in REV27

**REV27 supersedes every prior unexecuted post-REV26 valuation instruction. Execute only REV27.**

REV26 reached an honest capability result:

`R2B_R9_REV26_NO_CONFIGURED_VALUATION_AUTHORITY_ROUTE`

That terminal means:

> no valuation-authority route existed inside the **currently configured Thesis Monitor route inventory**.

It does **not** mean the already-used vendors lack valuation endpoints.

External documentation review identifies official candidate endpoints under already-used providers:

## Kiwoom official REST
- `ka10001`
- API name:
  `주식기본정보요청`
- URL:
  `/api/dostk/stkinfo`
- official example/guide fields include:
  - `stk_cd`
  - `stk_nm`
  - `per`
  - `eps`
  - `pbr`
  - `bps`
  - `cur_prc`
  - other security/basic-info fields.

## Finnhub official API
- `/stock/profile2`
  - ticker
  - exchange
  - currency
  - shareOutstanding
  - company identity
- `/stock/metric?symbol=...&metric=all`
  - provider-native Basic Financials including P/E/P/B-related metrics;
  - `symbol`
- `/stock/eps-estimate?symbol=...&freq=annual`
  - explicit estimate period/year;
  - `epsAvg`
  - analyst count;
  - symbol;
  - premium entitlement may be required.

REV27 is authorized to determine whether these **official endpoints under already-used providers**
can be added as exact source contracts without weakening the valuation-authority requirements.

Do not:
- invent a metric basis;
- accept a value solely because the field is named PER/PBR;
- treat retrieval time as metric as-of unless the endpoint contract explicitly supports snapshot semantics;
- transfer home-share metrics to ADR automatically;
- add a new provider;
- run a full-fresh all22 generation;
- call models;
- generate 24 messages.

---

# 0. Newest SoT

Adopt REV26 as newest valuation capability SoT.

REV26 result ZIP:

`thesis-monitor-20260930-r2b-r9-rev26-valuation-authority-capability-report.zip`

SHA-256:

`e851b33aabe967bb20af3f0abe8712752b2baac69a4031d7a394700a3635c9ca`

Independent verification:

- sidecar:
  PASS
- ZIP CRC:
  PASS
- members:
  `102`
- internal manifest:
  `101/101`
- missing:
  `0`
- hash mismatch:
  `0`
- size mismatch:
  `0`
- extra:
  `0`

Terminal:

`R2B_R9_REV26_NO_CONFIGURED_VALUATION_AUTHORITY_ROUTE`

Repository:

- base:
  `8ee40e39b205ff0d207afc956d80120b549965f8`
- branch:
  `codex/r2b-r9-rev26-valuation-authority-probe`
- instruction:
  `a22cd17ba51224fae26e12550d05afe8b8537d69`
- final:
  `14054c465bac0110da60bf78453c539e149910ca`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- production code/config changes:
  `0`

REV26 bounded probe:

- provider requests:
  `9`
- HTTP:
  all PASS
- retries:
  `0`
- models:
  `0`
- messages:
  `0/24`
- full-fresh:
  `0`
- GC:
  `0`
- qualified valuation routes:
  `0`
- capability decisions:
  `68`
- selected denominators:
  `0`

REV26 final free bytes:

`11,916,488,704`

This is above the bounded-probe 10 GiB floor but below the standing full-fresh 12 GiB binary admission threshold.

REV27 is not a full-fresh task.

---

# 1. Preserve REV26 negative findings

Do not erase or reinterpret REV26 evidence.

Preserve:

## Finnhub `/stock/metric`
Observed for direct IBM:
- native `peTTM`, `pbQuarterly`, `pbAnnual`, `epsTTM`, `forwardPE` fields exist;
- exact symbol echo exists;
- current configured route does not independently own:
  - share class;
  - metric currentness/as-of;
  - split/denominator basis;
  - currency/method basis.

Observed for TSM:
- requested ADR ticker did not establish an exact ADR valuation contract;
- no ADR conversion owner.

## Kiwoom chart route
- raw/adjusted request controls exist;
- raw and adjusted bytes being equal does not prove valuation basis compatibility;
- chart endpoint itself does not own PER/PBR.

## OpenDART
- EPS/equity/share candidate rows exist;
- current H1 is not a valid TTM/FY PER denominator by itself;
- exact common-equity allocation / security-class / split bridge remains unresolved.

These denials remain valid for those exact routes.

REV27 adds separate official valuation endpoints/contracts rather than weakening the old routes.

---

# 2. Preserve REV24 blind-review audit

Byte-preserve:

`rev24-source-only-independent-judgment-freeze.md`

SHA-256:

`55e46586c529685cb6c5d71296e3e3bd6db3b0829a69e75c5b7e59613337fed7`

and:

`rev24-blind-human-vs-monitoring-ai-comparison.md`

SHA-256:

`b1cfd24097ec88afb873eca2c03e4a1c084d966bd898a5f5fa71a97c8bf5898d`

No decision calibration work is authorized in REV27.

---

# 3. REV27 goal

Answer, with source receipts:

1. Can official Kiwoom `ka10001` become a provider-native current PER/PBR owner for direct KR securities?
2. Can Finnhub `profile2 + stock/metric` become a provider-native PER/PBR owner for direct US securities?
3. Can Finnhub annual EPS estimates become an exact `fPER(FY1)` owner if account entitlement and identity/currentness requirements pass?
4. Which security classes remain explicitly unsupported, especially ADRs?
5. If one or more source families qualify, implement only those families offline and close the tests.
6. Do not full-fresh until this is answered.

---

# 4. External transmission approval

The user explicitly approves the following bounded external reads in REV27.

Approved providers:

- Kiwoom official REST API
- Finnhub official API

Approved purpose:

- valuation source-contract qualification only.

Approved endpoints are limited to the exact sealed REV27 plan.

No new provider.

No model transmission in REV27.

No Telegram.

No production DB write.

No scheduler mutation.

No broker/trading action.

No deploy/main merge/remote push/restart.

Do not request redundant external-read approval if the run stays within this instruction.

---

# 5. Probe budget

Maximum provider requests excluding one Kiwoom auth request:

`14`

Preferred:

`<= 10`

No Alpha Vantage:

`0`

No automatic pagination unless the exact endpoint contract requires one bounded continuation and it is declared in the sealed plan.

No repeated requests to obtain a more favorable metric value.

No semantic retry.

Transport retry only under existing frozen transport policy; report exact count.

---

# 6. Phase A — Official Kiwoom `ka10001` source contract

Add a diagnostic-only configured endpoint candidate:

- provider:
  Kiwoom
- API ID:
  `ka10001`
- method:
  POST
- route:
  `/api/dostk/stkinfo`
- body:
  exact `stk_cd`.

Do not make it production/current-source eligible before the contract below passes.

---

# 7. Kiwoom representative probes

Minimum:

## 005930
Direct KRX common security positive candidate.

Optionally one second KR direct-common security only if needed to prove generic behavior:
- 003690
or
- 012450.

Negative class/control:
- if repository identity includes a preferred-share sibling example, use only a local/offline identity negative;
- do not add another external request solely to create a preferred-share negative unless necessary.

For every raw response preserve:

- request body;
- request/response timestamp;
- exact raw bytes;
- SHA;
- `return_code`;
- `stk_cd`;
- `stk_nm`;
- `per`;
- `eps`;
- `pbr`;
- `bps`;
- `cur_prc` if present;
- any exchange/security/class fields actually present;
- all relevant endpoint metadata.

No invented fields.

---

# 8. Kiwoom NativeValuationSnapshot contract

A `ka10001` PER/PBR may qualify only if all are proven:

1. response `stk_cd` matches exact monitored provider security code;
2. authoritative repository security identity maps that code to the monitored listing/class;
3. endpoint is documented as the stock-basic-info snapshot for that security;
4. metric field semantics are exact:
   - `per` = provider-native PER
   - `pbr` = provider-native PBR
   - supporting `eps`/`bps` retained but not required for arithmetic if the provider-native metric itself is used;
5. query/current snapshot ownership is explicit in the provider contract;
6. retrieval receipt is current generation;
7. value parses exactly;
8. zero/blank/sentinel handling is explicit;
9. no cross-security or preferred/common transfer;
10. `overall_direction_use = false`.

Provider-native PER/PBR are atomic provider metrics.

If this provider-native snapshot contract qualifies, do **not** re-derive the same PER/PBR from current price / EPS/BPS merely to match it.

The provider metric is the owner.

---

# 9. Kiwoom currentness requirement

Do not silently equate HTTP response time with financial-metric period.

The contract may use retrieval time as the **snapshot retrieval timestamp** only if the official endpoint semantics support a current stock-information snapshot.

Keep separate:

- retrieval time;
- provider metric snapshot role;
- underlying financial denominator period, if not provided.

User-facing renderer may display provider-native current valuation without pretending EPS/BPS are from the same day.

If official/raw evidence does not support current snapshot semantics:
route remains unqualified.

---

# 10. Kiwoom zero/sentinel semantics

Probe and tests must distinguish:

- actual numeric zero;
- blank;
- null/missing;
- provider sentinel for unavailable;
- negative/invalid metric.

Do not treat `0` as cheap valuation automatically.

If exact provider documentation/current examples show unavailable PER/PBR as zero/blank:
map to typed unavailable.

No N/M from a provider zero unless an exact negative-earnings basis is separately proven.

---

# 11. Phase B — Finnhub exact security identity expansion

Use the existing provider.

Add diagnostic-only candidate route:

`/stock/profile2?symbol=<ticker>`

Representative direct-US subjects:

- IBM
- MU

Do not use only GOOGL because issuer multi-class identity is a harder special case.

Negative ADR control:

- TSM.

For each profile preserve:

- ticker;
- exchange;
- currency;
- shareOutstanding;
- name;
- raw response SHA;
- retrieval receipt.

---

# 12. Finnhub profile + metric identity binding

For a direct-US provider-native metric candidate require:

1. profile2 ticker equals requested monitored ticker;
2. profile exchange/listing is compatible with authoritative local security identity;
3. profile currency matches expected security currency;
4. metric response symbol equals the same provider ticker;
5. both responses belong to the same bounded diagnostic generation;
6. no symbol remapping occurred.

This may close:
- ticker;
- exchange;
- currency;
- direct-security identity.

It does not automatically close:
- per-metric as-of;
- metric methodology;
- split basis.

Those remain separately required.

---

# 13. Finnhub native PER/PBR currentness/method requirement

The official Basic Financials route exposes native metrics such as:

- `peTTM`
- `pbQuarterly`
- `pbAnnual`.

Do not qualify them merely because these fields exist.

A positive contract requires official route semantics or raw response metadata sufficient to establish:

- metric is a provider-native current/basic-financial snapshot;
- exact semantic basis:
  - TTM P/E for `peTTM`;
  - P/B basis for the selected P/B field;
- no incompatible stale-period ambiguity;
- exact monitored direct security identity from Section 12.

If the official API does not expose enough per-metric timing/methodology to satisfy the strict current valuation contract:

Finnhub native PER/PBR remain unqualified.

Do not lower the contract.

---

# 14. Finnhub ADR control

For TSM:

- inspect profile2 response;
- inspect stock/metric response.

If provider resolves the request to a different home-market security, exchange, ticker or currency:
explicitly deny:

`UNQUALIFIED_ADR_CONVERSION`.

Do not use home-market PER/PBR for TSM ADR.

Same principle applies to SKHY without needing another external probe if the structural negative is already demonstrated.

---

# 15. Phase C — Finnhub annual EPS estimate / fPER(FY1)

Diagnostic-only candidate:

`/stock/eps-estimate?symbol=<ticker>&freq=annual`

Probe only one direct-US security first:

- IBM
or
- MU.

If entitlement denies the route:
record typed unavailable and stop this subtrack.

Do not retry with another symbol just to obtain data unless the failure is symbol-specific rather than entitlement-specific.

---

# 16. Exact FY1 horizon contract

Do not use generic "forwardPE" without horizon.

If annual EPS-estimate response qualifies, define:

`FY1_FORWARD_PER`

only when all are proven:

- exact direct monitored security ticker;
- profile2 identity binding;
- estimate `period`;
- estimate `year`;
- `epsAvg`;
- number of analysts;
- current retrieval receipt;
- estimate currency/share basis compatible with monitored security;
- first exact annual estimate period after the latest completed fiscal year under the existing fiscal-owner mapping;
- current completed-session price owner compatible with the security.

Compute:

`FY1_FORWARD_PER = completed_session_current_price / exact FY1 epsAvg`

only after all basis checks PASS.

Renderer must label the horizon explicitly, e.g.:

`fPER(FY1)`

Do not silently call it generic fPER if horizon is not visible in the contract.

Negative/zero estimate:
typed N/M or unavailable according to exact method; do not show a normal negative multiple.

---

# 17. No premium entitlement assumption

Finnhub EPS-estimate may require premium entitlement.

If current configured key returns an entitlement/access denial:

- no key rotation;
- no alternate account;
- no new provider;
- no fallback estimate source.

Record:

`UNAVAILABLE_ESTIMATE_ROUTE_ENTITLEMENT`

and preserve fPER unavailable.

This is an acceptable outcome.

---

# 18. Phase D — source-derived denominator path stays secondary

Do not expand SEC/OpenDART denominator taxonomy scope in REV27 unless needed to support an already-qualified provider-native contract.

Provider-native metrics are preferable where the provider directly owns PER/PBR for the exact security.

REV27 is not authorized to resume a broad 3,359-occurrence denominator search.

Keep source-derived PER/PBR denial owner intact.

---

# 19. Typed source contracts

Implement only if supported by probe evidence.

Potential contracts:

- `KiwoomNativeValuationSnapshot`
- `FinnhubDirectSecurityIdentityBinding`
- `FinnhubNativeValuationSnapshot`
- `FinnhubFY1EstimateSnapshot`

Each receipt must include:

- provider;
- route;
- request security;
- response security;
- listing/exchange;
- currency;
- metric;
- metric semantic/basis;
- value;
- snapshot retrieval timestamp;
- metric as-of if provider owns it;
- source hashes;
- identity hashes;
- display eligibility;
- NewBuyer/Holder valuation-context eligibility;
- `overall_direction_use = false`.

---

# 20. Metric states

Per security/metric use only:

- `QUALIFIED_PROVIDER_NATIVE`
- `QUALIFIED_SOURCE_DERIVED`
- `NOT_MEANINGFUL`
- `UNAVAILABLE_PROVIDER_SENTINEL`
- `UNAVAILABLE_SECURITY_IDENTITY`
- `UNAVAILABLE_CURRENTNESS`
- `UNAVAILABLE_METHOD_BASIS`
- `UNAVAILABLE_ADR_CONVERSION`
- `UNAVAILABLE_ESTIMATE_HORIZON`
- `UNAVAILABLE_ESTIMATE_ROUTE_ENTITLEMENT`
- other explicit typed reason.

No target coverage count.

---

# 21. Offline implementation gate

If any positive source family qualifies, implement it and run:

## Kiwoom
- exact 005930 positive;
- wrong code negative;
- common/preferred identity mismatch;
- zero/blank sentinel;
- stale/unowned snapshot negative;
- malformed numeric negative.

## Finnhub direct
- IBM/MU identity positive if evidence permits;
- wrong ticker;
- exchange mismatch;
- currency mismatch;
- metric response symbol mismatch;
- missing currentness/methodology negative.

## ADR
- TSM home-share mismatch negative;
- no conversion owner.

## FY1
- exact future annual period positive if entitled;
- stale/past period negative;
- wrong security;
- no analyst/estimate missing;
- entitlement denial;
- zero/negative estimate handling.

## Cross-cutting
- no Overall direction use;
- valuation metric independence;
- no provider metric reverse engineering;
- no source-derived fallback.

Then run:
- focused valuation tests;
- affected integration tests;
- canonical code-owner registry tests;
- full pytest;
- Ruff;
- diff;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

Full suite must be green before REV27 can end in positive-owner PASS.

---

# 22. Baseline failure from REV26

REV26 exact baseline still had one pre-existing integration failure:

`test_all22_common_generation_whole_source_replay_and_stages`
→ `matrix_native_qualified_source_required`

Do not hide this.

If REV27 implements a valid native valuation source family and the test is intended to require exactly that capability,
the test may naturally close.

If it remains unrelated:
preserve it and explain.

No threshold weakening.

---

# 23. No full-fresh / no models

REV27 must not run:

- all22 full-fresh;
- Market model;
- Core;
- A;
- B;
- exact24.

Expected:

- model calls:
  `0`
- messages:
  `0/24`.

REV28 will perform archive-backed GC + full-fresh only if REV27 establishes at least one positive valuation source family
and the full suite is green.

---

# 24. Storage policy

REV27 is bounded and should not perform destructive full-fresh GC solely for headroom.

Pre-probe disk floor:

`10 GiB`

Current REV26 free:

~`11.1 GiB`.

Seal probe artifacts into REV27 result archive.

Do not delete REV24 blind audit or REV24/REV25/REV26 immutable archives.

If temporary probe/raw files can be safely removed after sealing, record cleanup separately.

Full archive-backed generation GC remains deferred to REV28.

---

# 25. External transmission

Explicitly approved:

- bounded Kiwoom/Finnhub read-only API requests;
- result ZIP/SHA upload to existing iCloud Drive / Thesis Monitor folder.

Not used:

- model runner.

Still prohibited:

- Telegram;
- production DB/warnings;
- scheduler mutation;
- broker;
- deploy;
- main merge;
- remote push;
- restart.

---

# 26. Renderer backlog remains separate

Do not address in REV27:

- static `증거 성숙도: 판단 자료 부족` renderer behavior;
- missing detailed stock-message sections;
- English business-performance sentence issue.

Those are queued renderer-only work after valuation source ownership.

Do not mix them into source-contract work.

---

# 27. Success terminals

If at least one source family becomes a qualified positive owner and full validation is green:

`R2B_R9_REV27_OFFICIAL_VALUATION_SOURCE_CONTRACT_PASS_READY_FOR_FULL_FRESH`

This may be:
- KR-only;
- US-direct-only;
- both.

It does not require ADR qualification.
It does not require fPER qualification.

If all official candidate endpoints remain insufficient under the strict authority contract:

`R2B_R9_REV27_NO_QUALIFIED_OFFICIAL_VALUATION_SOURCE_CONTRACT`

This is an acceptable honest result.

If Kiwoom qualifies but Finnhub does not:

still use the positive PASS terminal with per-family matrix clearly showing US unavailable.

---

# 28. Honest stop terminals

- `R2B_R9_REV27_KIWOOM_NATIVE_VALUATION_CONTRACT_GAP`
- `R2B_R9_REV27_FINNHUB_IDENTITY_CONTRACT_GAP`
- `R2B_R9_REV27_FINNHUB_METRIC_CURRENTNESS_GAP`
- `R2B_R9_REV27_FY1_ESTIMATE_CONTRACT_GAP`
- `R2B_R9_REV27_PROVIDER_ENTITLEMENT_GAP`
- `R2B_R9_REV27_BASELINE_INTEGRATION_GAP`
- `R2B_R9_REV27_POSITIVE_OWNER_INTEGRATION_GAP`
- `R2B_R9_REV27_CODE_OWNER_REGISTRY_GAP`
- `R2B_R9_REV27_BOUNDED_PROBE_DISK_GUARD`.

Do not weaken source requirements to avoid these terminals.

---

# 29. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum include:

## Integrity
- REPORT.md
- summary.json
- REV26 archive identity/SHA
- repository identities
- changed-file inventory
- validation

## Official route contracts
- Kiwoom ka10001 official contract receipt
- Finnhub profile2 contract receipt
- Finnhub stock/metric contract receipt
- Finnhub EPS-estimate contract/entitlement receipt
- raw provider response hashes
- exact probe plan/counters

## Valuation authority
- provider/security identity matrix
- per-metric method/currentness matrix
- PER/PBR/fPER capability decisions
- ADR negative controls
- sentinel/N-M decisions
- source-family qualification matrix

## Conditional implementation
If positive:
- owner schemas
- positive/negative tests
- offline metric state matrix for representative securities
- code-owner registry parity

## Preservation/safety
- REV24 blind artifact preservation receipt
- model calls 0
- messages 0/24
- Alpha Vantage 0
- Telegram 0
- production side effects 0
- secret scan
- bundle manifest

---

# 30. Final principle

REV26 proved only that the **existing configured route set** did not own valuation authority.

It did not prove Kiwoom or Finnhub lack useful official valuation endpoints.

REV27 may add official endpoints under already-used providers, but only with exact source contracts.

For KR, `ka10001` is a strong candidate because the provider itself returns security-specific PER/EPS/PBR/BPS.

For US, Finnhub profile/metric/estimate endpoints may close some identity and horizon gaps, but must still satisfy the strict
currentness/method/security requirements.

Qualify only what the provider can prove.

Leave ADRs, fPER or any unsupported family honestly unavailable.

Do not spend another full-fresh/model budget until this source-contract layer is closed offline.
