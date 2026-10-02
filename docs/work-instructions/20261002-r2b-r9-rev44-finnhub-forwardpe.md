# Thesis Monitor — R2B-R9-REV44
## Finnhub Provider-Native `forwardPE` Semantic Qualification + US Forward-Valuation Owner Integration
### Stop free-EPS-provider hunting
### Use Finnhub atomic forward multiple directly; do NOT reconstruct an EPS owner
### Horizon must remain explicit/unknown unless Finnhub itself owns it
### No model calls / no user messages / no Telegram / no production writes

---

# 0. Task decision

The free exact-FY1 provider hunt is closed for now.

REV41:
- Yahoo provided useful FY1 semantics but automated-use authority was not acceptable for the recurring pipeline.

REV42:
- Business Quant free account returned AAPL preview for unrelated requested tickers.

REV43:
- FMP free access qualified GOOGL FY1 only;
- MU returned entitlement denial;
- TSM returned annual estimates but the listed-ADS denominator basis remained unresolved.

Do not continue another broad free-provider search in REV44.

Instead, qualify and integrate the Finnhub Basic Financials `forwardPE` field as a **provider-native atomic valuation snapshot**, using the same architectural distinction already accepted for Finnhub `peTTM` and `pbQuarterly`.

Key rule:

> `forwardPE` is used directly as Finnhub's provider-reported forward multiple.

Do **not** calculate an EPS from `price / forwardPE` and then pretend that derived value is FY1 EPS.

---

# 1. REV43 newest SoT

Verify the uploaded REV43 result before work.

Expected ZIP:

`thesis-monitor-20261001-r2b-r9-rev43-fmp-us14-fy1-eps-qualification-report.zip`

Expected SHA-256:

`ab0bdc6e6454036fde82e69a50387673085680f5eb4587d6b93dbf2a666b79b5`

Expected integrity:

- sidecar exact;
- ZIP CRC PASS;
- members: `60`;
- internal manifest payload files: `59`;
- manifest self-hash excluded;
- missing: `0`;
- hash mismatch: `0`;
- size mismatch: `0`;
- extra: `0`.

Expected terminal:

`R2B_R9_REV43_FMP_FREE_ENTITLEMENT_GAP`

Expected REV43 counts:

- GOOGL exact FY1 qualified: `1`;
- TSM ADS basis blocked: `1`;
- MU observed entitlement failure: `1`;
- remaining US11 not requested after smoke-gate failure;
- FMP data calls: `3`;
- Business Quant: `0`;
- Alpha Vantage: `0`;
- models/messages/production writes: `0`;
- replay: PASS;
- validation: PASS.

REV43 final repository SHA:

`0a0d68b9f9b1b62c61839ba3b7f91fba808a38b8`

Tested implementation SHA:

`6f39bb28ba7b4444422d17b8a3168c975890c0a8`

Operating main remains:

`b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

---

# 2. Preserve REV43 remotely first

Before REV44 implementation:

1. secret-scan REV43 outgoing commit range;
2. push REV43 final history to a non-force archival GitHub ref;
3. fetch it back;
4. prove exact remote SHA equals:

`0a0d68b9f9b1b62c61839ba3b7f91fba808a38b8`

Suggested archival ref:

`archive/worktree-cleanup/20261002/codex-r2b-r9-rev43-fmp-us-forward-eps`

Then create REV44 from that exact remote-preserved SHA.

Suggested branch:

`codex/r2b-r9-rev44-finnhub-forwardpe-owner`

No main merge.
No force push.
No remote deletion.

---

# 3. Existing accepted Finnhub architecture

Preserve the already accepted provider-native valuation distinction.

Existing direct-US Finnhub owner uses:

- `/stock/profile2`
- `/stock/metric?metric=all`

Accepted atomic fields:

- `peTTM`
  → provider-native TTM P/E snapshot
- `pbQuarterly`
  → provider-native quarterly P/B snapshot

These metrics are not Thesis Monitor's price/EPS or price/BPS recomputations.

The accepted provider-native snapshot policy already allows:

- deterministic valuation display;
- NewBuyer valuation context;
- Holder valuation context.

And forbids:

`overall_direction_use = true`

Preserve that exact architecture.

REV44 extends this same provider-native family to:

`forwardPE`

only if the source/identity/policy qualification below passes.

---

# 4. First question REV44 must answer

Determine exactly what Finnhub itself owns for the `forwardPE` field.

Inspect only authoritative/current sources first:

1. Finnhub official Company Basic Financials documentation;
2. Finnhub official Swagger/OpenAPI schema if available;
3. Finnhub official estimates/pricing documentation where relevant;
4. the actual `/stock/metric` response shape and any metric metadata.

Record:

```text
field = forwardPE
provider = Finnhub
route = /stock/metric
metric family = Basic Financials
exact published definition
exact horizon definition
price-date definition
earnings-denominator definition
accounting basis
estimate consensus basis
metric as-of / update policy
security/listing basis
```

Do not fill undocumented fields by inference.

---

# 5. Horizon states

The public Finnhub documentation currently proves that Basic Financials exists and that the separate estimates product provides explicit future estimates, but the public documentation reviewed before REV44 does not yet establish an exact FY1/NTM definition for `forwardPE`.

REV44 must therefore use one of these states.

## Exact horizon proved by Finnhub itself

Only if authoritative Finnhub material explicitly defines it:

```text
PROVIDER_FORWARD_HORIZON_FY1
```

or:

```text
PROVIDER_FORWARD_HORIZON_NTM
```

or another exact provider-owned horizon.

## Exact horizon not proved

Use:

```text
PROVIDER_FORWARD_HORIZON_UNSPECIFIED
```

This is an acceptable positive provider-native valuation state.

Do not fail the whole field solely because the internal horizon is unspecified if the product policy explicitly accepts an atomic provider forward-multiple snapshot.

But never relabel it:

- `fPER(FY1)`
- `NTM P/E`
- `next-year P/E`

without provider-owned proof.

---

# 6. Explicit product-policy authorization

REV44 authorizes:

`PROVIDER_NATIVE_FORWARD_PE_SNAPSHOT_ALLOWED_FOR_VALUATION_CONTEXT = true`

under all of these conditions:

- exact monitored direct security identity;
- fresh or immutable sealed Finnhub response;
- provider field exactly `forwardPE`;
- finite positive numeric value;
- no contradictory security remapping;
- no known ADR/home-share mismatch;
- provider/source disclosed;
- horizon state stored explicitly;
- metric_asof remains null unless provider owns it;
- no claim of same-session recomputation;
- no Thesis Monitor reconstruction of the hidden EPS denominator;
- no Overall/Core/A direction use.

This is an explicit product policy choice, not a hidden relaxation.

---

# 7. Atomic metric contract

Implement a typed owner such as:

`ProviderNativeForwardValuationSnapshot`

or extend the existing provider-native snapshot type without weakening old semantics.

Required fields:

```text
provider
route
requested_security_id
returned_security_id
canonical_security_id
security_identity_receipt
market_exchange
currency_if_owned
metric = FORWARD_PE
provider_field = forwardPE
value
retrieval_timestamp
metric_asof
provider_snapshot_role
forward_horizon_state
provider_definition
underlying_denominator_period
source_raw_sha256
receipt_sha256
display_eligible
new_buyer_valuation_context_eligible
holder_valuation_context_eligible
overall_direction_use = false
caveats[]
```

Default when the provider does not own dates:

```text
metric_asof = null
underlying_denominator_period = null
```

Do not invent them.

---

# 8. Do not derive an EPS owner

Forbidden production transformation:

```text
implied_forward_eps = current_price / forwardPE
```

followed by:

```text
new_price / implied_forward_eps
```

That would convert an opaque provider-native ratio into a falsely precise EPS denominator.

If REV44 performs:

`price / forwardPE`

at all, it may exist only in:

`diagnostic-calibration.json`

and must be marked:

```text
NOT_AN_EPS_OWNER
NOT_USER_VISIBLE
NOT_PRODUCTION_CONSUMABLE
```

No implied EPS may enter:

- source registry;
- financial facts;
- FY1 owner;
- model context;
- renderer.

---

# 9. Diagnostic calibration — allowed but never authoritative

Use known exact/sealed values only as controls.

## GOOGL

REV43 FMP exact FY1 diagnostic:

- fiscal year: `2026`
- period end: `2026-12-31`
- EPS avg: `20.61329`
- analysts: `41`
- state: `QUALIFIED_FY1_EPS_POSITIVE`
- production consumption: false.

Compare a Finnhub `forwardPE` observation with an appropriate price snapshot only to answer:

> Is the provider forward multiple numerically more consistent with the separately observed FY1 consensus than with obviously different horizons?

This is diagnostic evidence only.

Even a close match must **not** promote the Finnhub horizon to FY1 unless Finnhub documentation itself owns that semantic.

## REV41 Yahoo

The sealed Yahoo semantic snapshot may also be compared where periods overlap.

Again:

- no averaging;
- no source substitution;
- no horizon promotion from numerical similarity.

---

# 10. Security identity

For direct US securities, retain the existing exact Finnhub binding:

1. authoritative monitored-security identity;
2. `profile2` ticker exact match;
3. exchange/listing compatibility;
4. currency compatibility where owned;
5. `/stock/metric` symbol exact match;
6. same canonical security;
7. no provider symbol remap.

A ticker string alone is not sufficient when existing exact identity evidence conflicts.

---

# 11. ADR / ADS boundary remains fail-closed

Preserve strict handling for depositary securities, including:

```text
TSM
SKHY
WRD
```

Known prior problem:

- Finnhub TSM may resolve to home-market `2330.TW` / TWD rather than the monitored US ADS.

Do not use home-share `forwardPE` for the US ADS.

Do not transform using depositary ratios merely to make the number usable.

If the exact Finnhub metric belongs to a different home security:

```text
UNAVAILABLE_ADR_FORWARD_VALUATION_CONVERSION
```

If exact listed ADS metric identity is not owned:

```text
UNAVAILABLE_ADR_FORWARD_VALUATION_IDENTITY
```

The same rule applies to any other security where a direct/depositary mismatch is observed.

---

# 12. US14 subject matrix

Exactly these subjects:

```text
CORZ
CPNG
CRCL
GOOGL
HUT
IBM
MU
RXRX
SKHY
SNDK
TSLA
TSM
WRD
WULF
```

Create:

`us14-finnhub-forwardpe-qualification-matrix.json`

Each row:

```text
ticker
security_kind
profile_identity_state
metric_identity_state
forward_pe
forward_horizon_state
metric_asof
retrieval_timestamp
provider_definition_state
qualification_state
display_label
new_buyer_use
holder_use
overall_direction_use
source_raw_sha256
reason_codes[]
```

Do not require 14/14 numeric coverage.

---

# 13. Qualification states

Use exact states such as:

```text
QUALIFIED_PROVIDER_FORWARD_PE_SNAPSHOT_EXACT_HORIZON
QUALIFIED_PROVIDER_FORWARD_PE_SNAPSHOT_UNSPECIFIED_HORIZON
UNAVAILABLE_FORWARD_PE
INVALID_FORWARD_PE
IDENTITY_MISMATCH
UNAVAILABLE_ADR_FORWARD_VALUATION_IDENTITY
UNAVAILABLE_ADR_FORWARD_VALUATION_CONVERSION
SOURCE_RESPONSE_INVALID
```

If `forwardPE` is null/blank/zero/nonfinite:

typed unavailable/invalid according to provider semantics.

Do not convert zero into "cheap".

---

# 14. Data acquisition strategy

Prefer **zero new Finnhub calls for qualification mechanics**.

First use:

- sealed REV27/REV28 evidence;
- sealed REV29/current-generation Finnhub raw responses;
- existing source archives that already contain `/stock/profile2` and `/stock/metric`.

These are sufficient to build and replay the owner contract if the required field is present.

Only if the existing sealed corpus is missing an essential response needed to prove mechanics may REV44 make bounded Finnhub calls.

Maximum new Finnhub API calls:

`6`

Preferred:

`0–3`

Suggested positive controls if needed:

```text
IBM
MU
GOOGL
```

Do not probe ADRs again merely to repeat a previously proven structural mismatch.

No Finnhub EPS-estimate call.

The premium EPS route is not REV44 scope.

---

# 15. Zero calls to abandoned estimate-provider tracks

Hard zero in REV44:

```text
FMP_CALLS = 0
BUSINESS_QUANT_CALLS = 0
YAHOO_NEW_COLLECTION = 0
NASDAQ_ZACKS_CALLS = 0
ALPHA_VANTAGE_CALLS = 0
```

Do not restart the free exact-EPS hunt.

---

# 16. Existing normal Finnhub acquisition route

The normal US valuation source plan already acquires Finnhub Basic Financials for eligible securities.

REV44 should not add a second side-channel request merely for `forwardPE`.

Instead:

> consume `forwardPE` from the same sealed `/stock/metric` response already used for `peTTM` and `pbQuarterly`.

One response, multiple independent atomic valuation fields.

No post-freeze valuation refresh.

No per-field duplicate provider calls.

---

# 17. Currentness semantics

Treat `forwardPE` like the accepted Finnhub provider-native snapshot family.

Owned:

```text
retrieval_timestamp
provider route
provider response
provider field/value
```

Not automatically owned:

```text
metric_asof
hidden price timestamp
hidden estimate timestamp
hidden denominator period
```

Renderer/audit must say provider snapshot, not same-session recomputation.

If Finnhub official documentation proves update cadence/as-of later, preserve it explicitly.

---

# 18. Display semantics

If exact horizon remains unknown, user-facing label must make that visible.

Preferred:

```text
Finnhub Forward P/E: 12.3배 · provider forward 기준
```

or existing Korean renderer style equivalent.

Do **not** display:

```text
fPER(FY1): 12.3배
```

or:

```text
NTM PER: 12.3배
```

unless exact Finnhub horizon is formally qualified.

If exact horizon is later proven:

use the exact provider-owned horizon label.

---

# 19. Relationship to current PER/PBR

US Valuation section may contain independently:

```text
PER: <peTTM> · Finnhub snapshot
PBR: <pbQuarterly> · Finnhub snapshot
Finnhub Forward P/E: <forwardPE> · provider forward basis
```

These are separate metrics.

Do not imply that:

`forwardPE`

is mathematically derived from the same current price used by Thesis Monitor.

Do not compare arithmetic equality as an acceptance gate.

---

# 20. Model authority

Finnhub forwardPE may influence only:

- Valuation display;
- NewBuyer valuation context;
- Holder valuation context.

It may **not** independently influence:

- Market direction;
- Core business direction;
- Pass A business classification;
- Overall direction;
- business thesis polarity.

Required:

```text
overall_direction_use = false
core_visibility = false
pass_a_visibility = false
pass_b_new_buyer_visibility = true
pass_b_holder_visibility = true
```

Use the same leakage guards already proven for KR forward valuation.

---

# 21. Cheap/expensive valuation interpretation

Do not create a universal threshold such as:

```text
forwardPE < 10 => BUY
```

Forward valuation is context, not a direction generator.

Pass B may reason that a high provider forward multiple weakens entry attractiveness or a lower multiple improves valuation context, but only under the existing NewBuyer/Holder policy and with business evidence kept separate.

No Overall BUY/SELL creation from the multiple alone.

---

# 22. Offline tests

Before any new live call, add tests for:

- positive finite forwardPE;
- null;
- zero;
- negative;
- malformed string;
- infinity/NaN;
- exact ticker;
- wrong metric symbol;
- profile/metric mismatch;
- direct common stock;
- ADR home-security mismatch;
- metric_asof null;
- horizon unspecified;
- exact horizon only from authoritative provider definition;
- no derived implied-EPS owner;
- no FY1/NTM relabel from numerical calibration;
- Core exclusion;
- Pass A exclusion;
- Pass B NewBuyer inclusion;
- Pass B Holder inclusion;
- Overall direction exclusion;
- renderer label for unspecified horizon;
- no duplicate Finnhub request.

---

# 23. Historical/replay proof

Run the new owner over sealed historical Finnhub responses first.

Prove:

- deterministic parse;
- deterministic security binding;
- deterministic forwardPE state;
- same raw SHA → same canonical result;
- no network required;
- old accepted peTTM/pbQuarterly outputs unchanged.

If a historical response lacks `forwardPE`:
that historical row may be typed unavailable.

Do not alter the fixture to force coverage.

---

# 24. No model/message execution in REV44

Hard zero:

```text
MODEL_CALLS = 0
MARKET = 0
CORE = 0
PASS_A = 0
PASS_B = 0
RENDERED_USER_MESSAGES = 0
TELEGRAM = 0
```

REV44 qualifies and wires the source owner only.

The next task will perform a fresh US proof after review.

---

# 25. No production mutation

Hard zero:

- production DB/WAL writes;
- scheduler mutation;
- notification mutation;
- broker action;
- deploy;
- restart;
- main merge.

Repository branch/local report writes are allowed.

---

# 26. Full validation

Require:

- focused provider-native forward valuation tests;
- existing Finnhub peTTM/pbQuarterly regression;
- KR forward valuation regression;
- source materializer regression;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No live network in pytest.

---

# 27. Success definition

REV44 passes if:

1. REV43 integrity PASS;
2. REV43 final SHA remotely preserved;
3. REV44 exact base verified;
4. authoritative Finnhub docs/raw semantics audited;
5. exact `forwardPE` field identity proven;
6. provider-native atomic policy explicit;
7. horizon exact if documented, otherwise typed `UNSPECIFIED`;
8. no inferred FY1/NTM label;
9. no implied EPS promoted to an owner;
10. direct-security identity guard PASS;
11. ADR/home-share guard PASS;
12. US14 typed matrix produced from sealed evidence and/or bounded probe;
13. same existing `/stock/metric` route reused;
14. no FMP/BQ/Yahoo/Alpha/Zacks collection;
15. model/message calls 0;
16. full regression PASS;
17. secret scan PASS;
18. production isolation PASS.

Success terminal:

`R2B_R9_REV44_FINNHUB_PROVIDER_NATIVE_FORWARDPE_OWNER_PASS_READY_FOR_FRESH_US_INTEGRATION`

Report exact coverage:

```text
qualified exact-horizon forwardPE: X/14
qualified unspecified-horizon forwardPE: Y/14
ADR/identity blocked: Z/14
missing/invalid forwardPE: N/14
new Finnhub calls used: C
```

---

# 28. Honest stop states

Use:

```text
R2B_R9_REV44_FINNHUB_FORWARDPE_FIELD_SEMANTIC_GAP
R2B_R9_REV44_FINNHUB_FORWARDPE_IDENTITY_GAP
R2B_R9_REV44_FINNHUB_FORWARDPE_ONLY_ADR_HOME_SECURITY
R2B_R9_REV44_FINNHUB_FORWARDPE_POLICY_VALIDATION_GAP
R2B_R9_REV44_VALIDATION_GAP
R2B_R9_REV44_STORAGE_HEADROOM_GAP
```

Do not restart another provider hunt automatically.

---

# 29. Result bundle

Create:

`thesis-monitor-20261002-r2b-r9-rev44-finnhub-provider-native-forwardpe-owner-report.zip`

+ `.sha256`

Include at minimum:

```text
REPORT.md
summary.json
REV43-integrity.json
repository-identities.json
remote-preservation-receipt.json
finnhub-forwardpe-documentation-ledger.json
finnhub-forwardpe-semantic-contract.json
provider-native-forwardpe-policy.json
us14-finnhub-forwardpe-qualification-matrix.json
security-identity-ledger.json
adr-forward-valuation-ledger.json
diagnostic-calibration.json
historical-replay-1.json
historical-replay-2.json
request-ledger.json
validation.json
secret-scan.json
production-isolation.json
bundle-manifest.json
```

No API keys.

---

# 30. Next task after PASS

Stop after REV44.

If accepted, next task:

> REV45 — fresh US14 source integration proof using the normal Finnhub profile2 + stock/metric acquisition, with `peTTM`, `pbQuarterly`, and provider-native `forwardPE` flowing into Valuation / Pass-B NewBuyer / Holder, followed by exact US14 messages and blind comparison if the source-only seal passes.

Do not run REV45 automatically.

---

# 31. Final principle

We no longer require Finnhub to reveal a hidden EPS denominator in order to use a ratio that Finnhub itself publishes as an atomic provider metric.

But we also do not claim more than Finnhub proves.

Therefore:

```text
provider says forwardPE
→ store/display as provider-native Forward P/E

provider does not define exact horizon
→ horizon stays UNSPECIFIED

no exact FY1 semantics
→ never call it fPER(FY1)

no exact ADS identity
→ do not transfer home-share forwardPE to ADR

forward valuation
→ Valuation/NewBuyer/Holder only
```

That is the intended REV44 contract.
