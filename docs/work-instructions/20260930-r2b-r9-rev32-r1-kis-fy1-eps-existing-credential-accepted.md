# Thesis Monitor — R2B-R9-REV32-R1
## KIS Free Korean FY1 EPS / Forecast PER Capability Probe + Bounded Owner Closure
### Official Korea Investment & Securities Open API `estimate-perform`
### KR8 Only — No Broad Full-Fresh / No Models / No 24-Message Run
### No FnGuide Paid Source

**REV32-R1 supersedes REV32 and every prior unexecuted post-REV31-C1 forward-valuation instruction. Execute only REV32-R1.**

REV31-C1 is an accepted 24-message blind-comparison proof.

The current unresolved valuation gap is:

- current PER/PBR can now be qualified for some direct securities;
- fPER remains unavailable 22/22;
- for semiconductor/AI-cycle names, trailing/current PER alone is insufficient for useful entry calibration.

The user explicitly prefers a **free source** over paid FnGuide.

REV32-R1 differs from REV32 only in credential policy: the user explicitly accepts continued use of the already-configured existing KIS key pair despite the previously noted transient exposure risk. All secret-redaction and stop-on-new-exposure protections remain mandatory.

The official Korea Investment & Securities Open Trading API repository currently exposes:

- category:
  `[국내주식] 종목정보`
- API:
  `국내주식 종목추정실적[국내주식-187]`
- method:
  `estimate_perform`
- path:
  `/uapi/domestic-stock/v1/quotations/estimate-perform`
- TR ID:
  `HHKST668300C0`
- request parameter:
  `SHT_CD`
- response groups:
  `output1`, `output2`, `output3`, `output4`
- continuation:
  official example follows `tr_cont` and recursively requests additional pages when required.

REV32 must determine what the live endpoint actually returns for the current KR8 roster and whether it can own:

- exact future fiscal-year EPS;
- exact provider-native forecast PER;
- optionally FY1 EPS growth;
- optionally a source-derived FY1 fPER if all security/share/price basis requirements pass.

Do not assume response field names or period semantics before observing the official live wire response.

Do not call a fiscal-year forecast `12M Forward` or `NTM`.

---

# 0. Newest accepted SoT

Adopt REV31-C1 as newest accepted execution SoT.

REV31-C1 result ZIP:

`thesis-monitor-20260930-r2b-r9-rev31-c1-qualified-launch-report.zip`

SHA-256:

`3be0ebce7e902a820f0792f326ed5be582f0460b5baab7dc2b3ef58eb7e67520`

Independent verification:

- uploaded sidecar:
  exact match;
- ZIP CRC:
  PASS;
- internal manifest:
  `654/654`;
- missing/hash/size/extra:
  `0`.

Human-review ZIP:

`r2b-r9-rev31-c1-24-message-human-review.zip`

SHA-256:

`806cd25f13a4b554d60cc396e2e1ae258ad1e4bfaee0687e532a0f0d49cc7f39`

Independent verification:

- sidecar:
  exact match;
- ZIP CRC:
  PASS;
- internal manifest:
  `84/84`;
- missing/hash/size/extra:
  `0`.

REV31-C1 terminal:

`R2B_R9_REV31_C1_QUALIFIED_HOST_24_MESSAGE_PASS_READY_FOR_BLIND_COMPARISON`

Repository:

- branch:
  `codex/r2b-r9-rev31-c1-qualified-launch`
- base:
  `05af7519c34abd0c69ebfb93557802c24e8b8dec`
- instruction:
  `2a42663e5cb9fa57707c9762a7a1d958da96a281`
- validated implementation:
  `056700e3b3e58ec63c17d93b911ec801393c69cf`
- final:
  `f5e0b96fde3f0f58e93bf82df2c09233ebcd246f`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean:
  true.

REV31-C1 execution:

- provider refresh:
  `0`
- model calls:
  `26`
- retries:
  `0`
- Market:
  `2/2`
- Core:
  `22/22`
- A:
  `22/22`
- B:
  `22/22`
- exact messages:
  `24/24`
- Telegram:
  `0`
- production-visible side effects:
  `0`.

Validation:

- focused:
  `345 passed`
- full:
  `7158 passed / 63 skipped / 0 failed / 0 errors`
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

# 1. Preserve blind-comparison audit

Preserve byte-identically:

REV31 source-only ZIP:

`r2b-r9-rev31-source-only-review.zip`

SHA-256:

`af3b16102ec4e66d60f2d283efb2aad542ee77da84703a8b5b070cd330b66c19`

Independent source-only judgment:

`rev31-source-only-independent-judgment-freeze.md`

SHA-256:

`e935e4387f4d275466c932f9a03274dee739cfdd0dfc7411f40b755f7142b6c9`

Post-reveal comparison:

`rev31-c1-blind-human-vs-monitoring-ai-comparison.md`

Do not use the human judgment to tune valuation source acceptance.

REV32 is source-contract work only.

---

# 2. Existing valuation contract to preserve

Do not weaken:

- provider-native PER/PBR atomic snapshot contract;
- exact direct-security identity;
- no home-share→ADR valuation transfer;
- valuation not Overall-direction evidence;
- Core/A valuation exclusion;
- B-only NewBuyer/Holder valuation context;
- fPER unavailable unless exact horizon owner exists.

REV32 adds a separate Korean estimate-source family.

It does not rewrite current PER/PBR ownership.

---

# 3. KIS credential policy — user explicitly accepts continued use of the existing key pair

REV31 recorded that a Settings exception emitted sensitive KIS input text in a transient tool response.

The sensitive value was not archived.

The user has now explicitly chosen to **continue using the existing KIS App Key / Secret without rotation** for REV32-R1.

Therefore:

- do not block execution solely because the credentials were not rotated;
- do not request another rotation approval;
- use only the already-configured local secure credential source;
- never ask the user to paste the key/secret into chat;
- never print key/secret values;
- never log key/secret values;
- never include key/secret values in receipts;
- never persist Authorization/AppKey/AppSecret header values;
- never include auth request bodies containing secrets in result archives.

Create only a redacted credential-presence receipt:

- app key present:
  true/false
- secret present:
  true/false
- credential source identifier/hash if safely available;
- `user_accepted_existing_unrotated_credentials = true`;
- values:
  never recorded.

This is an explicit user risk acceptance for this KIS probe only.
It does not authorize broader credential exposure or plaintext persistence.

If the configured credentials are absent:

`R2B_R9_REV32_KIS_CREDENTIAL_GAP`

Provider calls:
`0`.

If a secret is exposed again in tool/runtime output:
- stop immediately;
- do not archive the exposed output;
- do not continue additional KIS calls in the same run;
- return:
  `R2B_R9_REV32_KIS_SECRET_EXPOSURE_GAP`.

---

# 4. Official endpoint contract

Use only the official KIS Open Trading route:

`/uapi/domestic-stock/v1/quotations/estimate-perform`

TR ID:

`HHKST668300C0`

Input:

`SHT_CD=<exact six-digit stock code>`

Official example contract returns four independent groups:

- `output1`
- `output2`
- `output3`
- `output4`

and may continue when the response `tr_cont` requires it.

Do not use:
- FnGuide paid API;
- web scraping;
- portal HTML scraping;
- undocumented KIS endpoints;
- Alpha Vantage;
- a different broker API.

---

# 5. KR8 scope

Current monitored Korean securities:

- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280.

Use exact current security identities from the existing Thesis Monitor registry.

No new Korean target.

No US forward-valuation work in REV32.

---

# 6. Two-stage bounded probe

Minimize calls.

## Stage A — semiconductor controls

Probe first:

- 000660
- 005930

Reason:
the user specifically needs forward valuation for semiconductor/AI-cycle names and these are high-value controls.

For each security:
- one initial estimate-perform request;
- preserve all four output groups;
- preserve response headers relevant to continuation;
- follow at most one continuation page initially if the official `tr_cont` contract requires it.

After both probes, perform an offline schema/semantic audit.

Do not automatically query the remaining KR6 until Stage A shows the endpoint contains an identifiable forecast-period
surface relevant to EPS/PER or another exact future-earnings metric.

## Stage B — remaining KR6

Only if Stage A is semantically useful:

query:
- 003690
- 005490
- 010120
- 012450
- 047810
- 086280.

No result-driven repeated queries.

---

# 7. Request budget

KIS authentication:
- maximum one normal auth operation required by the approved KIS client/session;
- token reuse under the official client policy is allowed.

Estimate-perform data requests:

preferred:
`8`

hard maximum:
`16`

The hard maximum allows at most one required continuation page per KR8 security.

If a security requires more than one continuation page to establish the required forecast rows:
stop that subject with a typed bounded-probe state rather than recursively walking up to the example's generic
max_depth=10.

Transport retry:
only the repository's existing bounded transport policy.
No discretionary semantic retry.

Alpha Vantage:
`0`.

---

# 8. Raw response preservation

For every KIS data request preserve, secret-scanned:

- exact SHT_CD;
- request timestamp;
- response timestamp;
- HTTP/transport status;
- KIS return code/message;
- continuation header/state;
- raw response SHA-256;
- exact field names/types for output1–output4;
- exact row ordering;
- exact raw period/year strings;
- exact raw EPS/PER fields if present;
- any estimate/actual marker if present;
- any analyst-count/consensus metadata if present;
- any source date/update date if present.

Do not normalize away:
- `E` suffixes;
- year-month strings;
- sign;
- decimal formatting;
- blank/null/sentinel values.

No credentials in raw artifacts.

---

# 9. Schema discovery — no field assumptions

Create:

`kis-estimate-perform-live-schema.json`

For output1–output4 record:

- container type;
- row count;
- every field name;
- observed types;
- representative redacted/non-secret values;
- which rows vary by period;
- which fields appear actual/forecast-related;
- which fields appear EPS/PER-related;
- which fields appear security-identity-related;
- which fields appear update/currentness-related.

Do not assign semantic names solely from intuition.

A field named `eps` is not automatically FY1 EPS until its period row is owned.

---

# 10. Exact security binding

Every accepted forecast fact must bind to the exact monitored six-digit Korean security.

Require:

- request SHT_CD exact match;
- response identity field if present exact match;
- otherwise official endpoint request-scoping plus existing KIS/Kiwoom authoritative security identity must
  deterministically bind the response to the requested security;
- no preferred/common sibling transfer;
- no local ticker-name heuristic alone.

If exact security binding cannot be established:

`UNAVAILABLE_KIS_FORECAST_SECURITY_IDENTITY`.

---

# 11. Fiscal-period owner

Create a typed fiscal-period selection contract, repository naming permitting:

`KISForecastFiscalPeriodOwner`

It must identify:

- exact source row;
- raw period/year label;
- fiscal year;
- actual vs forecast state;
- source-owned forecast marker;
- latest completed fiscal year from the existing current financial owner;
- FY1 selection reason;
- FY2 selection reason where available.

Definition:

`FY1` = the earliest explicitly forecast fiscal period after the latest completed fiscal year.

Example only:
if latest completed FY is 2025 and KIS exposes explicit `2026E`, then 2026E may be FY1.

Do not infer forecast status merely because a year is greater than the current calendar year.

Do not call an unlabeled future row a forecast.

For non-calendar fiscal issuers, use the issuer's fiscal owner rather than calendar-year assumption.

---

# 12. FY1 EPS qualification

A KIS row may own:

`FY1_EPS_ESTIMATE`

only when:

1. exact security binding PASS;
2. exact fiscal-period binding PASS;
3. row is explicitly a forecast/estimate under the live source contract;
4. EPS field semantic is identified from the source;
5. numeric parse PASS;
6. currency/share unit is compatible with the exact Korean security or source directly owns the per-share metric;
7. source row is not blank/sentinel;
8. raw and receipt hashes are preserved.

Record:
- FY1 year/period;
- EPS value;
- provider;
- retrieval time;
- provider/source update metadata if available;
- estimate count if available;
- source hashes.

Do not claim consensus-average semantics unless the source explicitly proves it.

If source exposes an estimate but not its aggregation method, label it only as:
`KIS FY1 EPS estimate snapshot`.

---

# 13. Provider-native forecast PER

If the same exact forecast-period row exposes a provider PER:

qualify:

`KIS_PROVIDER_FY1_PER_SNAPSHOT`

only when:
- exact security PASS;
- exact FY1 period PASS;
- PER field is on the same forecast row or has an exact source-owned link to that FY1 period;
- numeric parse PASS;
- no sentinel.

This is the preferred fPER path because KIS itself owns the ratio.

User-facing semantic:

`fPER(FY1)`

may be used only after the horizon is explicitly bound to FY1.

Do not call an unlabeled provider PER `fPER`.

---

# 14. Optional source-derived FY1 fPER

A Thesis Monitor-derived:

`FY1_fPER = completed_session_current_price / FY1_EPS`

is optional and secondary.

It may qualify only if all are proven:

- exact same monitored security;
- completed-session current-price owner;
- KRW price;
- FY1 EPS per-share denominator for the same security;
- split/corporate-action/share basis compatible with current price;
- no preferred/common transfer;
- denominator > 0.

If the basis cannot be proven:
do not derive.

The provider-native FY1 PER may still qualify independently.

Never reverse-engineer EPS from provider PER.

---

# 15. N/M handling

If exact qualified FY1 EPS <= 0:

do not show a normal negative fPER.

State:

`FY1_fPER = NOT_MEANINGFUL`

with user-facing:

`N/M`

only if the negative/zero EPS basis itself is qualified.

If EPS basis is not qualified:
unavailable, not N/M.

---

# 16. FY1 EPS growth

Optional:

`FY1 EPS growth`

may be computed only when a compatible actual baseline exists.

Preferred baseline:
- exact KIS actual FY EPS row from the same estimate-perform family;

or:
- an existing source-owned exact FY EPS denominator with compatible per-share/split basis.

Require:

`(FY1 EPS / latest actual FY EPS) - 1`

No quarter-to-year comparison.

No H1/YTD baseline.

No incompatible share basis.

If unavailable:
do not block FY1 EPS/fPER.

---

# 17. FY2 / estimate revisions

If the endpoint exposes FY2:
record it in diagnostic evidence.

Do not make FY2 mandatory.

If explicit estimate revision fields are present:
record exact semantics.

Do not invent:
- 1-week revision;
- 1-month revision;
- analyst count

unless the live source actually exposes those fields.

REV32's required target is FY1, not revision analytics.

---

# 18. Typed per-security states

For every KR8 security output an exact state for:

## FY1 EPS
- `QUALIFIED_KIS_FY1_EPS`
- `UNAVAILABLE_NO_FORECAST_ROW`
- `UNAVAILABLE_SECURITY_IDENTITY`
- `UNAVAILABLE_FISCAL_PERIOD`
- `UNAVAILABLE_FIELD`
- `UNAVAILABLE_SENTINEL`
- `UNAVAILABLE_SOURCE_SEMANTICS`
- other typed reason.

## FY1 provider PER
- `QUALIFIED_KIS_FY1_PER`
- typed unavailable reason.

## Derived FY1 fPER
- `QUALIFIED_DERIVED_FY1_FPER`
- `NOT_MEANINGFUL`
- typed unavailable reason.

Every KR8 subject must have a typed state even when no estimate coverage exists.

No minimum numeric coverage target.

---

# 19. Provider-source coverage is not a source failure

The KIS estimate endpoint may cover only securities with analyst estimates.

A valid "no estimate" response is not a Thesis Monitor source failure.

Do not make KR8 overall source qualification fail merely because a stock lacks KIS consensus/forecast coverage.

This is optional valuation context.

---

# 20. Model/use authority

REV32 runs no model.

Define future use permissions now.

Qualified KIS FY1 EPS/fPER may be used in:

- valuation section;
- NewBuyer valuation context;
- Holder valuation context;
- valuation-specific confidence/caution under the existing policy.

It may not independently establish:

- Overall business direction;
- Core direction;
- Pass-A business direction;
- directional supporting/contradicting refs.

Future full-pipeline integration must preserve this boundary.

---

# 21. Relationship to current Kiwoom/Finnhub valuation

Do not replace current PER/PBR.

For KR the future combined valuation view may contain:

- current PER:
  Kiwoom provider latest snapshot where qualified;
- current PBR:
  Kiwoom provider latest snapshot where qualified;
- FY1 EPS:
  KIS estimate snapshot where qualified;
- fPER(FY1):
  KIS provider FY1 PER snapshot where qualified;
- optional derived FY1 fPER:
  separately typed/audited.

Do not require KIS current PER/PBR to equal Kiwoom current PER/PBR.

They may use different provider timing/methods.

If both current and forecast metrics exist:
keep source/provider labels explicit.

---

# 22. Stage-A go/no-go

After 000660 + 005930 probe:

continue to Stage B only if at least one exact useful path is proven:

- explicit forecast-period EPS;
or
- explicit forecast-period PER;
or
- another exact future-earnings field that can support the intended FY1 contract.

If neither semiconductor control exposes a usable forecast-period surface:

do not spend six more calls automatically.

Stop with:

`R2B_R9_REV32_KIS_ESTIMATE_SEMANTICS_GAP`

unless evidence shows the endpoint's security coverage, rather than semantics, is the reason and one additional
non-semiconductor control is justified.

At most one such additional control may be probed before stop.

---

# 23. Conditional owner implementation

If Stage A proves exact semantics:

implement the KIS forecast owner generically.

Then run Stage B KR6 using the same frozen owner.

No ticker-specific extraction logic.

No hardcoded field positions based only on the first response.

Field mapping must be schema-checked.

---

# 24. Offline tests

Require:

## Security
- exact code;
- wrong code;
- preferred/common sibling mismatch;
- response identity conflict.

## Period
- latest actual FY;
- FY1 explicit forecast;
- FY2;
- past estimate row;
- unlabeled future row;
- duplicate forecast periods;
- non-calendar fiscal example.

## EPS
- positive;
- zero;
- negative;
- blank;
- malformed;
- sentinel.

## Provider FY1 PER
- same-row exact FY1;
- wrong-period PER;
- current PER accidentally mapped as FY1 negative.

## Derived fPER
- exact basis positive;
- split/share basis unresolved negative;
- denominator <=0 N/M;
- different security negative.

## Coverage
- no estimate is typed unavailable, not failure.

## Authority
- valuation context allowed;
- Overall direction prohibited.

No tests may hardcode current live numeric values.

---

# 25. Validation

After conditional implementation:

- focused KIS forecast tests;
- valuation integration tests;
- current provider-native valuation regression;
- whole-source code-owner registry tests if the new owner is registered;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No model calls.

No message generation.

---

# 26. Disk guard

REV31-C1 closeout free space was approximately:

`11.1 GB decimal / ~10.4 GiB`

class.

REV32 is bounded and requires no large full-fresh generation.

Before KIS probe require:

`free >= 8 GiB`

No destructive full-generation GC is required.

Safe cleanup of completed pytest scratch is allowed only under the existing archive/process/open-file checks.

Preserve all immutable REV31/REV31-C1 artifacts and source-only blind evidence.

---

# 27. Explicit external transmission approval

The user explicitly selected the KIS free-forward-EPS route.

REV32-R1 therefore explicitly authorizes:

- one normal KIS authentication operation using locally stored rotated credentials;
- bounded read-only calls to the official KIS `estimate-perform` route under Sections 6–7;
- secret-scanned REV32 result ZIP/SHA upload to the existing iCloud Drive / Thesis Monitor folder.

No additional approval is required for those exact reads.

Not authorized in REV32-R1:
- order/trading endpoints;
- account/order mutation;
- model runner;
- Telegram;
- production DB/warning writes;
- scheduler mutation;
- broker order;
- deploy;
- main merge;
- push;
- service restart.

---

# 28. Secret handling

Hard requirements:

- KIS credential values never printed;
- auth headers never archived;
- access token value never archived;
- request/response diagnostics redact secrets;
- subprocess command lines contain no secret literal;
- exception text is sanitized before persistence;
- raw response archive is scanned before sealing.

If a tool/runtime exception exposes a secret again:
stop, do not archive that output, and require another credential rotation before further external calls.

Terminal:

`R2B_R9_REV32_KIS_SECRET_EXPOSURE_GAP`.

---

# 29. No full-fresh / no models

REV32-R1 must not run:

- the all22 source pipeline;
- Market model;
- Core;
- Pass A;
- Pass B;
- exact24 sender messages.

Expected:

- models:
  `0`
- messages:
  `0/24`
- Telegram:
  `0`.

REV33 may integrate a successful KIS FY1 owner into the normal full-fresh pipeline.

---

# 30. Success terminal

If exact KIS forecast semantics are proven, all KR8 receive typed states, conditional owner implementation passes the
full test suite, and at least one exact FY1 EPS or FY1 PER is qualified:

`R2B_R9_REV32_KIS_FY1_FORWARD_VALUATION_OWNER_PASS_READY_FOR_LIVE_INTEGRATION`

This does not require all KR8 to have analyst estimates.

It does not require derived fPER if provider-native FY1 PER qualifies.

It does not mean 12M/NTM.

---

# 31. Honest terminal if source is not sufficient

If the official KIS endpoint does not expose enough exact horizon/estimate semantics:

`R2B_R9_REV32_KIS_ESTIMATE_SEMANTICS_GAP`

If it works only for a subset:
that is acceptable if the owner is generic and unavailable states are honest.

If no KR8 security has estimate coverage despite correct endpoint/auth:
use:

`R2B_R9_REV32_KIS_FORECAST_COVERAGE_EMPTY`

Do not fall back to paid FnGuide automatically.

---

# 32. Other honest stop terminals

- `R2B_R9_REV32_KIS_ROTATED_CREDENTIAL_GAP`
- `R2B_R9_REV32_KIS_AUTH_FAILURE`
- `R2B_R9_REV32_KIS_TRANSPORT_FAILURE`
- `R2B_R9_REV32_KIS_SECURITY_IDENTITY_GAP`
- `R2B_R9_REV32_KIS_FISCAL_PERIOD_GAP`
- `R2B_R9_REV32_KIS_FY1_PER_BINDING_GAP`
- `R2B_R9_REV32_KIS_DERIVED_FPER_BASIS_GAP`
- `R2B_R9_REV32_KIS_SECRET_EXPOSURE_GAP`
- `R2B_R9_REV32_CODE_OWNER_REGISTRY_GAP`
- `R2B_R9_REV32_VALIDATION_GAP`.

Do not solve by guessing a year or horizon.

---

# 33. Required result bundle

Return immutable result ZIP + `.sha256`.

At minimum include:

## Integrity
- REPORT.md
- summary.json
- REV31-C1 result identity/SHA
- repository identities
- changed-file inventory
- bundle manifest.

## KIS official contract
- endpoint/TR ID receipt;
- redacted credential-presence receipt;
- auth success/failure receipt;
- request counters;
- continuation counters.

## Raw/schema
- secret-scanned raw response files;
- raw hashes;
- output1–output4 schema inventory;
- row/field type inventory;
- source period strings;
- continuation headers.

## Fiscal owner
- latest completed FY per subject;
- forecast rows;
- FY1/FY2 decisions;
- selection/exclusion reasons.

## Valuation
- KR8 FY1 EPS state matrix;
- KR8 KIS provider FY1 PER state matrix;
- optional derived FY1 fPER state matrix;
- N/M receipts;
- security/share/price basis receipts;
- provider/source labels.

## Validation
- focused;
- full pytest;
- Ruff;
- diff;
- knowledge;
- secret scan.

## Safety
- KIS call count;
- Alpha 0;
- models 0;
- messages 0;
- Telegram 0;
- production mutations 0.

---

# 34. Next-stage handoff

If PASS, prepare a bounded REV33 recommendation only.

REV33 should:
- integrate the KIS FY1 owner into the normal KR fresh source plan;
- preserve current PER/PBR owners;
- expose FY1 EPS/fPER only to valuation/NewBuyer/Holder context;
- run full fresh only after archive-backed GC/headroom checks;
- render:
  - current PER
  - current PBR
  - `fPER(FY1)`
  - optional `FY1 EPS`
  - optional `FY1 EPS growth`
- keep US fPER work separate;
- keep broad detailed-message renderer restoration separate unless explicitly authorized.

Do not execute REV33 inside REV32-R1.

---

# 35. Final principle

The goal is not to force a forward multiple onto every Korean stock.

The goal is to obtain a **free, source-owned, exact-horizon Korean earnings estimate** where KIS actually provides one.

The official KIS `estimate-perform` API is a promising route because it is explicitly a stock-estimated-performance
endpoint with four structured output groups and an exact stock-code request.

But live semantics must decide what can be called FY1.

If KIS owns an explicit future fiscal-year EPS/PER row:
qualify it.

If KIS does not own the horizon clearly:
leave fPER unavailable.

Never rename FY1 as 12M/NTM without exact source evidence.
