# Thesis Monitor — R2B-R9-REV28
## Provider-Native Valuation Snapshot Contract + Exact Security Identity Closure
### Kiwoom ka10099 + ka10001 for KR
### SEC-Authoritative Identity + Finnhub Basic Financials for Direct US Common Securities
### ADRs and fPER Remain Fail-Closed
### No Full-Fresh / No Models / No 24-Message Run in REV28

**REV28 supersedes every prior unexecuted post-REV27 valuation instruction. Execute only REV28.**

REV27 returned an honest result:

`R2B_R9_REV27_NO_QUALIFIED_OFFICIAL_VALUATION_SOURCE_CONTRACT`

However, REV27 also proved that provider-native valuation numbers exist in live official responses.

Examples from the sealed REV27 diagnostic evidence:

## Kiwoom 005930
- PER:
  `41.33`
- PBR:
  `4.24`
- EPS:
  `6564`
- BPS:
  `63997`
- provider current-price field:
  `-271250`
  (provider sign convention retained; do not reinterpret in REV28 unless the official field contract is separately owned)

## Finnhub direct-US examples
IBM:
- peTTM:
  `19.5016`
- pbQuarterly:
  `7.6717`

MU:
- peTTM:
  `23.8625`
- pbQuarterly:
  `10.34`

## ADR negative control
TSM request:
- profile/metric resolve to:
  `2330.TW`
- exchange/currency:
  Taiwan / TWD
- observed metric values are home-security metrics, not TSM ADR metrics.

REV27 denied all positive routes because the previous valuation contract demanded exact metric as-of/currentness and
share-class/basis evidence beyond what an atomic provider-native ratio endpoint actually owns.

REV28 must distinguish two fundamentally different valuation methods:

1. **source-derived valuation**
   - price / EPS/BPS arithmetic;
   - requires exact denominator/share/split basis.

2. **provider-native atomic valuation snapshot**
   - provider itself reports PER/PBR as a security-level basic-information metric;
   - does **not** require Thesis Monitor to reconstruct the provider's denominator;
   - requires exact security identity, exact provider metric semantics and a truthful snapshot/currentness label;
   - must never be presented as same-session recomputation when the provider does not own such a claim.

REV28 closes this distinction.

Do not:
- reverse-engineer provider-native metrics;
- pretend provider retrieval time is denominator-period time;
- claim same-session PER/PBR when only provider latest snapshot is owned;
- transfer home-share metrics to ADR;
- invent fPER;
- run a full-fresh all22 proof before the snapshot contract is closed offline.

---

# 0. Newest SoT

Adopt REV27 as newest valuation-source SoT.

REV27 result ZIP:

`thesis-monitor-20260930-r2b-r9-rev27-official-valuation-contract-report.zip`

SHA-256:

`78a7be7ce9038a4cc9ceba27d80e180a2c8ae92f492c56553fd9add0f101c0a0`

Independent verification:

- sidecar:
  PASS
- ZIP CRC:
  PASS
- members:
  `91`
- internal manifest:
  `90/90`
- missing:
  `0`
- hash mismatch:
  `0`
- size mismatch:
  `0`
- extra:
  `0`

Terminal:

`R2B_R9_REV27_NO_QUALIFIED_OFFICIAL_VALUATION_SOURCE_CONTRACT`

Repository:

- base:
  `14054c465bac0110da60bf78453c539e149910ca`
- branch:
  `codex/r2b-r9-rev27-official-valuation-contract`
- instruction:
  `33ce267221df344bf4bead81663ba7c905cba67e`
- final:
  `9dfbbd04e95b962629ed4f6b0036dca66346735b`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- production code/config changed:
  false

REV27:
- data requests:
  `8`
- Kiwoom auth:
  `1`
- public documentation downloads:
  `4`
- models:
  `0`
- messages:
  `0/24`
- full-fresh:
  `0`
- retries:
  `0`
- positive valuation families:
  `0`.

---

# 1. Preserve REV27 denials that remain valid

Do not erase these:

## TSM ADR
Finnhub resolves TSM request to home security `2330.TW`.

State remains:

`UNAVAILABLE_ADR_CONVERSION`

unless a separate exact ADR conversion/valuation owner is proven.

REV28 does not attempt to close ADR valuation.

## fPER
Finnhub EPS-estimate returned HTTP 403 entitlement denial.

State remains:

`UNAVAILABLE_ESTIMATE_ROUTE_ENTITLEMENT`

No alternate account/key/provider.

Generic `forwardPE` without a horizon remains insufficient.

## Source-derived valuation
REV25/REV26 exact denominator/split/current-price basis denials remain valid.

REV28 does not resume source-derived PER/PBR arithmetic.

---

# 2. Correct semantic distinction — atomic provider metric

For an **atomic provider-native PER/PBR**, the provider owns the ratio as one reported security-level field.

Thesis Monitor does not need to prove:
- provider's hidden EPS denominator;
- provider's hidden book-value denominator;
- internal split arithmetic;

unless the system tries to recompute or validate the metric mathematically.

Instead, the required contract is:

- exact security identity;
- exact provider route;
- exact metric semantic;
- provider snapshot role;
- retrieval provenance;
- provider update/currentness semantics;
- no cross-security transfer.

This is a source contract, not a denominator contract.

Do not apply `CURRENT_PROJECTION_OMITS_SECURITY_OWNED_DENOMINATORS` to a qualified atomic provider-native metric.

That denial remains valid for source-derived valuation only.

---

# 3. Typed ProviderNativeValuationSnapshot

Create one typed contract, repository naming permitting:

`ProviderNativeValuationSnapshot`

Required fields:

- provider;
- route/API ID;
- requested provider security ID;
- returned provider security ID;
- canonical monitored security ID;
- security identity receipt;
- market/exchange;
- currency when source owns it;
- metric:
  - PER
  - PBR;
- provider field:
  - e.g. `per`, `pbr`, `peTTM`, `pbQuarterly`;
- provider metric semantic;
- qualified numeric value;
- retrieval timestamp;
- provider snapshot role;
- provider update policy if documented;
- metric_asof:
  explicit date if provider owns it, otherwise null;
- underlying_denominator_period:
  explicit if provider owns it, otherwise null;
- source raw SHA;
- receipt SHA;
- display eligibility;
- NewBuyer valuation-context eligibility;
- Holder valuation-context eligibility;
- `overall_direction_use=false`;
- caveat/reason codes.

The contract must clearly distinguish:

`retrieval_timestamp`

from:

`metric_asof`.

---

# 4. Provider latest snapshot semantics

A provider-native valuation metric may be displayed as:

`PROVIDER_LATEST_SNAPSHOT`

when:

1. the API is an official security/basic-financials endpoint;
2. the exact security identity is qualified;
3. the field semantic is officially documented;
4. the fresh current generation requested the endpoint;
5. the response contains a valid metric;
6. provider documentation identifies the endpoint as current/basic stock/company information or otherwise a latest provider metric surface;
7. no conflicting metric timestamp is present;
8. no stale cached response is reused.

This does **not** mean:
- denominator is from retrieval day;
- ratio was recomputed at completed-session close;
- same-day fundamentals exist.

Renderer/audit must preserve:

`provider snapshot retrieved at <time>`

and the provider update caveat where known.

---

# 5. User-facing valuation wording

Provider-native snapshot metrics may render in the normal Valuation section, but the source receipt must distinguish them.

Preferred compact user-facing shape:

- `PER 41.33배 · Kiwoom snapshot`
- `PBR 4.24배 · Kiwoom snapshot`

or equivalent existing Korean renderer wording.

For Finnhub:

- `PER 19.50배 · Finnhub TTM snapshot`
- `PBR 7.67배 · Finnhub quarterly snapshot`

if and only if exact direct-security identity qualifies.

Do not label these:
- same-session PER;
- exact 2026-09-29 fundamental ratio;
- source-derived PER/PBR.

If renderer currently cannot expose the snapshot qualifier, retain it in audit metadata and add only the smallest
renderer change needed to avoid a false same-session implication.

Do not mix broader renderer-format restoration into REV28.

---

# 6. KR exact security identity — Kiwoom ka10099

Add/qualify the official Kiwoom stock-list route:

- API ID:
  `ka10099`
- route:
  `/api/dostk/stkinfo`
- request:
  exact market type.

Official fields include:
- `code`
- `name`
- `listCount`
- `regDay`
- `lastPrice`
- `state`
- `marketCode`
- `marketName`
- industry/company-size fields.

Use this route only for exact provider security identity.

---

# 7. KiwoomExactSecurityCodeIdentity

A monitored KR security may receive:

`KiwoomExactSecurityCodeIdentity`

when all are true:

1. ka10099 current provider list contains exact `code`;
2. code matches the monitored security provider code exactly;
3. `marketName/marketCode` match the expected listed market under current security-master contract;
4. ka10001 request/response `stk_cd` matches the exact same code;
5. names are compatible under normalized issuer/security naming;
6. no conflicting sibling code is substituted;
7. response/generation hashes are bound.

For Korean listed shares, the six-digit exchange security code itself identifies the traded instrument.

Do not require a separate textual "common share" label when the authoritative provider code is exact and the
provider list/security-master mapping proves the same instrument.

Preferred shares remain different security codes and cannot inherit metrics from the ordinary code.

Negative:
- 005930 metric cannot apply to 005935;
- wrong market;
- missing code;
- conflicting code/name;
- list route from another generation without current binding.

This closes exact security identity without a local inferred common/preferred guess.

---

# 8. Kiwoom ka10001 provider-native snapshot

For exact KR security identity from Section 7:

`ka10001` may own atomic:

- PER from `per`;
- PBR from `pbr`.

Official endpoint/documentation already establishes:
- stock basic-information role;
- security-code request;
- PER/PBR fields.

REV27 documentation notes:
- PER supplied by external vendor with weekly or earnings-season update cadence;
- PBR update policy not explicitly stated;
- response contains no metric date.

Therefore:

## PER
state may be:

`QUALIFIED_PROVIDER_LATEST_SNAPSHOT`

with caveat:

`PROVIDER_UPDATE_CADENCE_WEEKLY_OR_EARNINGS_SEASON`

It must not be claimed same-session.

## PBR
may qualify as:

`QUALIFIED_PROVIDER_LATEST_SNAPSHOT`

only if official stock-basic-info endpoint semantics plus fresh request are accepted as provider latest snapshot
and there is no contradictory stale/as-of metadata.

Caveat:

`PROVIDER_METRIC_ASOF_NOT_EXPLICIT`

Do not invent a PBR date.

If the project policy requires an explicit as-of date even for atomic provider snapshot display, keep PBR unavailable
and report that as a separate metric-level result.

PER qualification must not depend on PBR.

---

# 9. Kiwoom sentinel/value semantics

Preserve REV27:

- blank/null/missing:
  unavailable;
- numeric zero:
  not automatically cheap;
- negative native multiple:
  not automatically N/M;
- malformed/nonfinite:
  unavailable.

For ka10001 positive numeric `per`/`pbr`, no price/EPS/BPS arithmetic is required.

Do not "repair" provider signed current price to validate the multiple.

The atomic metric stands or fails on its own provider contract.

---

# 10. KR representative positive proof

Use a bounded fresh diagnostic probe:

- ka10099 KOSPI list sufficient to bind 005930;
- ka10001 exact 005930.

Maximum:
- auth 1 if needed;
- ka10099 pages only as required to locate 005930 under the exact documented continuation protocol;
- ka10001 one call.

Do not enumerate other KR securities externally unless necessary for one negative identity control.

Expected candidate:

- 005930 PER 41.33 / PBR 4.24 from REV27 may differ in REV28;
- use only the new fresh response values.

No target fitting to prior numbers.

---

# 11. US direct-security identity

For Finnhub, provider-native atomic ratios may qualify only for direct securities whose repository already has an
authoritative exact security identity.

Use:

- SEC official ticker;
- SEC official exchange/listing;
- SEC official security type/title where available;
- Finnhub profile2 ticker/exchange/currency;
- metric response symbol.

The existing IBM authoritative identity is a positive control.

MU may qualify only after an existing configured SEC official-identity owner proves its exact direct listing/security.

Do not lower identity requirements for MU just because the metric number exists.

---

# 12. Finnhub Basic Financials snapshot semantics

Official Finnhub documentation describes `/stock/metric` as:

`Get company basic financials such as margin, P/E ratio, 52-week high/low etc.`

Response:
- `metric`: key-value ratios/metrics;
- `series`: time-series ratios;
- `symbol`.

For a direct security with authoritative identity:

## peTTM
May qualify as:

`QUALIFIED_PROVIDER_LATEST_SNAPSHOT`

only as:

`Finnhub provider-reported TTM P/E from fresh Basic Financials response`

not as same-session recomputation.

Metric semantic comes from field name:
`peTTM`.

## pbQuarterly
May qualify as:

`QUALIFIED_PROVIDER_LATEST_SNAPSHOT`

only as:

`Finnhub provider-reported quarterly P/B from fresh Basic Financials response`

with:
`metric_asof = null`
unless provider response owns a date.

Caveat:

`PROVIDER_METRIC_ASOF_NOT_EXPLICIT`

If current product policy refuses all metrics with null as-of even when explicitly provider-native Basic Financials,
record that as a **product policy blocker**, not a source-identity blocker.

Do not silently reclassify retrieval timestamp as metric date.

---

# 13. Product policy decision must be explicit

REV27 applied a standard appropriate for source-derived valuation:

exact per-metric currentness/as-of.

REV28 must explicitly distinguish whether the product permits:

`provider latest snapshot with unknown underlying metric date`

as user valuation context.

Implement a named policy:

`PROVIDER_NATIVE_VALUATION_SNAPSHOT_ALLOWED_FOR_DISPLAY_CONTEXT`

Set it only through this explicit work instruction.

Authorized value for REV28:

`true`

under these constraints:

- exact direct security identity;
- fresh provider request;
- official provider-native valuation field;
- no contradictory staleness evidence;
- snapshot source/provider disclosed in audit;
- no Overall business direction use;
- no claim of same-session metric date.

This is a deliberate product policy choice, not a hidden validator weakening.

---

# 14. Finnhub IBM positive control

Using a new fresh bounded probe or sealed REV27 raw response only for offline implementation test:

IBM has:
- SEC authoritative ticker/exchange/common-stock identity;
- Finnhub profile ticker/exchange/USD alignment;
- Finnhub metric symbol alignment.

With Section 13 policy:
- `peTTM` may qualify provider-native PER;
- `pbQuarterly` may qualify provider-native PBR;
- exact new response values only.

No source-derived denominator arithmetic.

Run current-generation live probe only after offline contract tests pass.

---

# 15. Finnhub MU conditional control

If repository/SEC official identity can be resolved through the existing configured identity owner without adding a
new provider:

qualify direct identity then apply the same snapshot contract.

If authoritative identity remains missing:

MU remains unavailable.

Do not infer from ticker alone.

---

# 16. ADRs remain excluded

TSM and SKHY:

provider/home-security metric cannot be used unless exact ADR valuation conversion source exists.

REV28 does not add one.

States:

`UNAVAILABLE_ADR_CONVERSION`

Preserve.

Do not use the new snapshot policy to bypass ADR identity.

---

# 17. fPER remains unavailable

Finnhub EPS-estimate entitlement:
HTTP 403.

No new entitlement.

No generic `forwardPE` substitution because horizon remains unowned.

fPER remains:

`UNAVAILABLE_ESTIMATE_ROUTE_ENTITLEMENT`
or existing exact typed equivalent.

REV28 does not implement fPER.

---

# 18. Offline contract tests

Before any live probe:

## KR identity
- exact ka10099 code + market + ka10001 code → positive;
- common/preferred different code negative;
- wrong market;
- conflicting name/code;
- missing list identity.

## KR valuation
- positive numeric PER;
- positive numeric PBR;
- blank/null;
- zero;
- negative;
- malformed;
- PER update-cadence caveat retained;
- PBR null as-of caveat retained;
- no denominator arithmetic.

## US identity
- IBM SEC/Finnhub exact positive;
- wrong ticker;
- wrong exchange;
- wrong currency;
- metric/profile mismatch.

## US valuation
- peTTM positive snapshot;
- pbQuarterly positive snapshot;
- missing field;
- malformed/nonfinite;
- metric_asof remains null unless source provides it;
- retrieval time not relabelled metric date.

## ADR
- TSM remains denied.

## fPER
- entitlement-denied remains denied.

## Policy
- provider-native snapshot may affect:
  - Valuation display;
  - NewBuyer valuation context;
  - Holder valuation context;
- cannot independently create Overall direction.

---

# 19. Bounded external probe authorization

The user has explicitly approved bounded provider/API transmission for current Thesis Monitor source work.

REV28 authorizes:

- Kiwoom ka10099;
- Kiwoom ka10001;
- Finnhub profile2;
- Finnhub stock/metric;
- existing SEC official identity route only if needed for one direct-US identity closure.

No new provider.

Maximum external data/API calls excluding Kiwoom auth:

`12`

Preferred:

`<= 8`

Alpha Vantage:

`0`

No models.

No Telegram.

No production writes.

---

# 20. Positive owner implementation

If offline tests and bounded live evidence pass:

implement provider-native valuation snapshot owner for supported families.

Expected possible result:

## KR direct listed securities
- PER:
  provider-native Kiwoom snapshot
- PBR:
  provider-native Kiwoom snapshot if Section 8 PBR policy passes
- fPER:
  unavailable

## US direct securities with authoritative identity
- PER:
  Finnhub peTTM snapshot
- PBR:
  Finnhub pbQuarterly snapshot
- fPER:
  unavailable

## ADRs
- unavailable.

Do not force all22 coverage.

---

# 21. Valuation state schema

Use exact per-metric states such as:

- `QUALIFIED_PROVIDER_LATEST_SNAPSHOT`
- `NOT_MEANINGFUL`
- `UNAVAILABLE_PROVIDER_SENTINEL`
- `UNAVAILABLE_SECURITY_IDENTITY`
- `UNAVAILABLE_ADR_CONVERSION`
- `UNAVAILABLE_PROVIDER_FIELD`
- `UNAVAILABLE_ESTIMATE_ROUTE_ENTITLEMENT`
- other typed reason.

For qualified snapshot include:

- value;
- provider;
- provider field;
- retrieval time;
- metric_asof nullable;
- provider update caveat;
- exact security receipt;
- source hashes;
- use permissions.

---

# 22. Existing REV27 known integration failure

Baseline known failure:

`matrix_native_qualified_source_required`

REV28 positive native snapshot owner is intended to close the missing native-qualified source condition if that test's
semantic expectation matches the new contract.

Do not alter the test to accept a fake source.

After implementation run the actual production/common-cohort path.

If the new exact native owner exists but the integration fixture cannot represent it:
update the fixture through the production owner, not a synthetic bypass.

Full suite must become green before positive terminal.

---

# 23. Validation

After implementation:

- focused valuation snapshot tests;
- Kiwoom identity tests;
- Finnhub identity tests;
- ADR negatives;
- fPER entitlement negative;
- common-cohort integration;
- canonical code-owner registry;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No positive PASS if full suite remains red.

---

# 24. No full-fresh in REV28

REV28 remains an offline/bounded contract task.

Do not:
- run all22 full-fresh;
- run Market/Core/A/B;
- generate exact24.

If positive owner closes and full suite is green:

REV29 will:
- execute archive-backed GC;
- start new full-fresh;
- collect valuation snapshots for eligible securities;
- replay twice;
- run models/messages.

---

# 25. Storage

REV28 bounded probe floor:

`10 GiB`

No destructive full-generation GC solely for this bounded task.

Preserve:
- REV24 blind audit;
- REV24 accepted result/human-review;
- REV25/26/27 immutable archives;
- registered fixtures.

Seal REV28 probe/raw evidence in the result ZIP.

REV29 performs the next standing full-fresh GC.

---

# 26. Renderer backlog remains separate

Do not mix:
- detailed-section restoration;
- English business-performance line fix;
- evidence-maturity renderer mapping

into REV28.

REV28 may only make the smallest valuation-line qualifier change needed to distinguish provider snapshot semantics.

Full detailed renderer restoration remains a separate task after valuation is proven live.

---

# 27. Success terminal

If at least one provider-native valuation family qualifies and full validation is green:

`R2B_R9_REV28_PROVIDER_NATIVE_VALUATION_SNAPSHOT_PASS_READY_FOR_FULL_FRESH`

This does not require:
- all22 numeric valuation;
- ADR valuation;
- fPER.

Report qualified coverage by source/security family.

If the explicit provider-snapshot product policy still cannot be safely satisfied:

`R2B_R9_REV28_PROVIDER_NATIVE_SNAPSHOT_POLICY_GAP`

No full-fresh.

---

# 28. Honest stop terminals

- `R2B_R9_REV28_KIWOOM_SECURITY_IDENTITY_GAP`
- `R2B_R9_REV28_KIWOOM_NATIVE_SNAPSHOT_GAP`
- `R2B_R9_REV28_FINNHUB_DIRECT_IDENTITY_GAP`
- `R2B_R9_REV28_FINNHUB_NATIVE_SNAPSHOT_GAP`
- `R2B_R9_REV28_COMMON_COHORT_INTEGRATION_GAP`
- `R2B_R9_REV28_CODE_OWNER_REGISTRY_GAP`
- `R2B_R9_REV28_BOUNDED_PROBE_DISK_GUARD`.

Do not lower security identity to avoid these.

---

# 29. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

## Integrity
- REPORT.md
- summary.json
- REV27 archive identity
- repository identities
- changed-file inventory
- validation

## KR
- ka10099 raw/receipt/hash
- ka10001 raw/receipt/hash
- exact security-code identity receipt
- PER/PBR snapshot receipts
- sentinel/caveat decisions

## US
- SEC authoritative identity receipt used
- Finnhub profile2/metric raw hashes
- direct-security identity binding
- peTTM/pbQuarterly snapshot receipts
- metric-asof null/caveat proof

## Negatives
- ADR denial
- fPER entitlement denial
- wrong code/class/exchange/currency
- stale/cache reuse negative

## Policy
- explicit provider-native snapshot policy receipt
- stage visibility/use receipt
- no Overall direction use.

## Safety
- data call counters
- models 0
- messages 0/24
- Alpha 0
- Telegram 0
- production side effects 0
- secret scan
- bundle manifest.

---

# 30. Final principle

Provider-native valuation and source-derived valuation are different contracts.

A provider-native atomic PER/PBR should not be forced through Thesis Monitor's EPS/BPS denominator reconstruction
rules when the provider itself owns the ratio for the exact traded security.

The correct requirement is:

- exact security;
- official provider-native metric;
- fresh provider response;
- truthful snapshot semantics;
- no false same-session/as-of claim;
- no cross-security/ADR transfer.

For KR, Kiwoom ka10099 + ka10001 can potentially provide the exact security-code identity and the provider-native ratio.

For direct US securities, authoritative SEC identity + Finnhub profile/metric can potentially provide a provider-native
Basic Financials snapshot.

This recovers useful PER/PBR without pretending Thesis Monitor knows the provider's hidden denominator date or
reconstructing arithmetic it cannot own.

ADRs and fPER remain honestly unavailable until their separate source authority exists.

