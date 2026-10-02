# Thesis Monitor — R2B-R9-REV43
## FMP Free Basic — US14 Exact FY1 EPS Source Qualification
### Bounded credential/entitlement smoke → one-pass US14 only if smoke passes
### No Business Quant retry / no Yahoo production feed / no Alpha Vantage
### No current fPER yet / no model calls / no messages / no production writes

---

# 0. Why REV43

REV42 closed Business Quant honestly.

Accepted REV42 terminal:

`R2B_R9_REV42_BUSINESSQUANT_FREE_ENTITLEMENT_GAP`

Observed Business Quant behavior:

- 3 data calls only;
- requested:
  - GOOGL
  - MU
  - TSM
- all three returned HTTP 200;
- all three returned the same AAPL preview payload:
  - ticker `AAPL`
  - CIK `320193`
  - provider note: free preview is AAPL only;
- no requested security was accepted;
- Stage C was correctly suppressed;
- duplicate calls 0;
- retries 0;
- Alpha Vantage 0;
- model/messages 0.

Business Quant is therefore closed for the free path.

Do not call it again in REV43.

REV41 Yahoo remains semantic secondary evidence only and is not a production automated source.

The next documented API candidate is Financial Modeling Prep (FMP).

Current official FMP documentation exposes:

`GET /stable/analyst-estimates`

with:
- exact `symbol`;
- `period=annual`;
- explicit estimate period `date`;
- `epsAvg`;
- `epsHigh`;
- `epsLow`;
- `numAnalystsEps`.

Current official pricing advertises a Basic free plan with 250 calls/day, but the analyst-estimates endpoint is marked limited access.

Therefore REV43 must test the **actual account entitlement**, not infer it from marketing/pricing pages.

---

# 1. REV42 integrity / newest execution SoT

Verify:

`thesis-monitor-20261001-r2b-r9-rev42-businessquant-us14-fy1-eps-qualification-report.zip`

Expected SHA-256:

`1146eeb10f6e394a15e81621a298f701dbc6acc651d3741a26003db8eca58c27`

Expected integrity:

- sidecar exact;
- CRC PASS;
- ZIP members `65`;
- internal manifest payload files `64`;
- manifest self excluded;
- missing `0`;
- hash mismatch `0`;
- size mismatch `0`;
- extra `0`.

Expected REV42 facts:

- terminal:
  `R2B_R9_REV42_BUSINESSQUANT_FREE_ENTITLEMENT_GAP`
- Business Quant calls:
  `3`
- requested-security usable:
  `0`
- typed universe:
  `14`
- entitlement blocked:
  `14`
- replay:
  `PASS_TWO_IDENTICAL`
- full pytest:
  `7830 passed / 63 skipped`
- model:
  `0`
- messages:
  `0`
- production writes:
  `0`
- Alpha Vantage:
  `0`.

Do not reinterpret the 11 unrequested rows as 11 observed Business Quant failures.
They are account-gate suppressions.

---

# 2. Repository base

REV42 final SHA:

`638cec8ed12bd88b0dd864ef3747eccc5c21687a`

REV42 tested implementation SHA:

`f93048692581fc187fd4ace6062960c4366b2a90`

Branch:

`codex/r2b-r9-rev42-businessquant-us-forward-eps`

Before REV43:

1. secret-scan outgoing REV42 commit history;
2. preserve REV42 exact final SHA on GitHub using a non-force archival ref;
3. fetch and verify exact remote SHA;
4. create REV43 from that exact remote-preserved commit.

Suggested preservation ref:

`archive/worktree-cleanup/20261001/codex-r2b-r9-rev42-businessquant-us-forward-eps`

Suggested REV43 branch:

`codex/r2b-r9-rev43-fmp-us-forward-eps`

No main merge.
No force push.
No remote branch deletion.

---

# 3. FMP access / licensing gate

Use only the documented FMP API.

Before any data call, revalidate current official:

- Financial Estimates API documentation;
- Basic/free pricing;
- Terms of Service / acceptable-use requirements.

The intended Thesis Monitor use for this task is:

- single-user;
- private;
- personal investment research;
- not public;
- not client-facing;
- not employer/business analytics;
- no third-party API/data access;
- no public display or redistribution.

If actual intended use does not fit the applicable personal-use/API license:

stop:

`R2B_R9_REV43_FMP_LICENSE_SCOPE_GAP`

Do not assume a technical API key grants display/redistribution rights.

Raw FMP data must never be pushed to a public GitHub repository.

---

# 4. Credential gate

Check the repository's accepted secret/config mechanism for an existing FMP key.

Recognize only local secret aliases already used or explicitly documented, for example:

```text
FMP_API_KEY
FINANCIAL_MODELING_PREP_API_KEY
```

Do not print the value.

Do not commit it.

Do not add it to result archives.

If no FMP credential exists:

stop **before any FMP request**:

`R2B_R9_REV43_FMP_CREDENTIAL_REQUIRED`

Report that a free FMP account/API key is required for the bounded smoke test.

Do not create an account on the user's behalf.
Do not substitute another provider automatically.

---

# 5. API call budget

Although the advertised Basic limit is much larger than Business Quant, development still uses frozen evidence.

REV43 target:

```text
smoke calls       = 3
portfolio calls   = 11
target total      = 14
normal hard cap   = 16
absolute cap      = 18
```

Retries:

`0` by default.

A single retry is allowed only for:
- no valid response body;
- clear transport error or provider 5xx.

Maximum transport retry calls:

`2`.

Never retry:
- 400;
- 401;
- 402;
- 403;
- 404;
- 422;
- valid empty result;
- entitlement error;
- ticker unsupported;
- parser bug;
- semantic/basis rejection.

Alpha Vantage remains:

`0`.

Business Quant remains:

`0`.

---

# 6. No live calls in tests

Before first FMP call:

implement offline:

- response schema;
- canonical owner;
- FY1 selector;
- typed failure states;
- API-key redaction;
- request ledger;
- replay parser;
- quota guard.

Use synthetic fixtures first.

No FMP call may be made by:

- pytest;
- parser debugging;
- renderer tests;
- replay;
- validation;
- documentation checks.

After a raw response exists for a ticker, code changes must replay that response rather than recall FMP.

---

# 7. Documented endpoint

Use only:

`GET https://financialmodelingprep.com/stable/analyst-estimates`

Parameters:

```text
symbol=<exact monitored ticker>
period=annual
page=0
limit=10
apikey=<secret>
```

If current official documentation has changed the credential parameter name, use the documented form and record the contract change.

Do not use undocumented endpoints.

Do not scrape FMP website pages for portfolio numbers.

---

# 8. Expected response owner

Bind only documented response fields relevant to forward EPS, including:

```text
symbol
date
epsAvg
epsHigh
epsLow
numAnalystsEps
```

Other estimate fields may be retained for raw evidence but are not required for this owner.

Official documentation currently states currency is:

`as reported in financials`

Preserve that semantic.

Do not relabel the EPS currency as USD merely because the monitored quote trades in USD.

---

# 9. FY1 selection

FMP analyst-estimates rows are forecast-period rows.

For each ticker:

1. require returned `symbol` exact match;
2. resolve latest completed fiscal annual period from the accepted Thesis Monitor/issuer/SEC owner;
3. consider annual estimate rows only;
4. normalize the provider's explicit `date` as forecast fiscal-period end;
5. choose the earliest estimate period strictly after the latest completed fiscal period;
6. label that row FY1.

Do not use:

`MAX(date)`.

Do not choose a calendar year merely from retrieval year.

Examples of expected fiscal logic:

- calendar issuers with completed FY2025:
  FY1 normally 2026;
- MU with completed FY2026:
  FY1 normally FY2027;
- SNDK with completed FY2026:
  FY1 normally FY2027.

Actual source rows control.

---

# 10. Estimate snapshot date

Do not confuse forecast period `date` with estimate-as-of.

Unless FMP response/documentation owns a separate consensus update timestamp:

```text
estimate_asof = null
estimate_date_state =
  ESTIMATE_DATE_UNAVAILABLE_ACCEPTED_LATEST_PROVIDER_SNAPSHOT
```

`retrieved_at` remains separate.

---

# 11. Accounting basis

Do not assume:

- GAAP;
- normalized;
- non-GAAP;

from `epsAvg` unless FMP explicitly owns that definition.

Default:

`PROVIDER_CONSENSUS_ACCOUNTING_BASIS_UNSPECIFIED`

This is nonfatal for denominator qualification if:
- exact security;
- exact FY1 period;
- currency;
- listed-share basis

are otherwise proven.

Do not compare/merge FMP and Yahoo values to manufacture an accounting label.

---

# 12. US14 universe

Exactly:

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

Exactly one primary typed state per ticker.

---

# 13. Stage A — documentation and offline implementation

No data calls.

Require:

- endpoint contract captured;
- pricing/free contract captured;
- terms/access contract captured;
- request redaction tested;
- synthetic parser tests PASS;
- latest-completed-FY owner available;
- security identity ledger available;
- ADR ratio evidence from REV41 retained but not automatically applied.

Only then proceed.

---

# 14. Stage B — three-call smoke

Call exactly once each:

```text
GOOGL
MU
TSM
```

Purpose:

## GOOGL
- ordinary US common listing;
- calendar FY;
- exact symbol;
- common-share/currency owner.

## MU
- non-calendar fiscal year;
- verify first-future-period FY1 selection.

## TSM
- ADR/ADS behavior;
- inspect provider currency and share basis;
- fail closed if FMP EPS is ordinary-share or reporting-currency basis incompatible with US ADS price.

Seal each raw response immediately.

No second call because parser code changed.

---

# 15. Stage B account/entitlement gate

To continue to the remaining US11:

GOOGL and MU must both return:

- successful authorized response;
- exact requested symbol;
- at least one usable annual estimate row;
- deterministic FY1 period.

If either response clearly states/returns a plan entitlement error:
stop before US11.

Use:

`R2B_R9_REV43_FMP_FREE_ENTITLEMENT_GAP`

If response is valid but analyst estimates are absent for one issuer:
that ticker may be typed unavailable; do not automatically close the whole provider unless the failure is account-wide.

TSM may remain basis-blocked without failing Stage B.

---

# 16. Stage B freeze

After the three raw responses:

network off.

Using only the frozen responses:

- finish parser support;
- replay twice;
- verify FY1 selection;
- verify no secret leakage;
- verify currency/share basis logic;
- add real-response regression fixtures only in a license-compliant/redacted form.

Do not commit raw FMP portfolio data unless current FMP terms explicitly allow it.

Prefer hashes + minimal schema-safe synthetic regression fixtures in Git.

Commit/freeze the implementation before Stage C.

---

# 17. Stage C — remaining US11 once each

Only if Stage B common-share gate passes.

Call once:

```text
CORZ
CPNG
CRCL
HUT
IBM
RXRX
SKHY
SNDK
TSLA
WRD
WULF
```

One data request per ticker.

No profile calls by default.

No per-ticker retry except allowed transport rule.

Target cumulative FMP calls:

`14`.

---

# 18. Security identity

For each response require exact monitored symbol.

Use existing accepted issuer/SEC identity data for CIK/legal issuer/listing when available.

If FMP returns only ticker and not a strong issuer identifier:

do not invent CIK.

Bind the exact ticker/listing through the existing security identity owner.

If exact security cannot be proven:

`IDENTITY_MISMATCH_OR_UNRESOLVED`.

---

# 19. Currency / common-share basis

FMP documentation states estimate currency follows reported financials.

Therefore exact quote compatibility must be checked.

For common-share US listings:

```text
CORZ
CPNG
CRCL
GOOGL
HUT
IBM
MU
RXRX
SNDK
TSLA
WULF
```

prove:

- monitored security is the listed common share;
- issuer financial reporting currency for EPS estimate is compatible with future price denominator;
- per-share basis maps directly to the monitored listed share.

If not:

`CURRENCY_OR_SHARE_BASIS_UNRESOLVED`.

Do not assume all Nasdaq/NYSE tickers report EPS in USD.

---

# 20. ADR / ADS hard boundary

For:

```text
TSM
SKHY
WRD
```

existing depositary ratios may be used only as evidence:

- TSM: 5 ordinary shares / ADS
- SKHY: 0.1 ordinary share / ADS
- WRD: 3 ordinary shares / ADS

But FMP documentation's "currency as reported in financials" makes automatic US-ADS fPER conversion unsafe unless the returned EPS basis is proven.

Determine whether FMP row represents:

- ordinary-share EPS in issuer reporting currency;
- ADS EPS;
- another transformed basis.

Do not multiply/divide/FX-convert merely from the ratio.

If exact listed ADS denominator cannot be proven:

`ADR_BASIS_UNRESOLVED`.

A numeric response may still be retained as non-consumable source evidence.

---

# 21. Negative/zero EPS

Negative or zero FY1 EPS is valid forecast data.

Use:

```text
QUALIFIED_FY1_EPS_POSITIVE
QUALIFIED_FY1_EPS_NONPOSITIVE
```

Only positive values can later produce numeric fPER.

Do not map negative EPS to unavailable.

---

# 22. Typed states

Each US14 subject ends in one:

```text
QUALIFIED_FY1_EPS_POSITIVE
QUALIFIED_FY1_EPS_NONPOSITIVE
UNAVAILABLE_ESTIMATE
SOURCE_UNSUPPORTED_SECURITY
SOURCE_ENTITLEMENT_GAP
SOURCE_RATE_LIMIT
IDENTITY_MISMATCH_OR_UNRESOLVED
PERIOD_IDENTITY_UNRESOLVED
CURRENCY_OR_SHARE_BASIS_UNRESOLVED
ADR_BASIS_UNRESOLVED
SOURCE_RESPONSE_INVALID
```

Additional nonfatal metadata:

```text
ACCOUNTING_BASIS_UNSPECIFIED
ESTIMATE_DATE_UNAVAILABLE_ACCEPTED_LATEST_PROVIDER_SNAPSHOT
```

---

# 23. Comparison with REV41 Yahoo

Use the sealed REV41 Yahoo values only as diagnostic secondary evidence.

For overlapping qualified rows record:

```text
ticker
FMP FY1 period
FMP epsAvg
Yahoo FY1 period
Yahoo EPS
difference
FMP basis state
Yahoo basis label
```

No equality requirement.

Do not average.

Do not choose the lower or more convenient value.

Yahoo remains non-production.

---

# 24. Do not pursue Nasdaq Zacks in REV43

Current Nasdaq Data Link Zacks Earnings Estimates (`ZACKS/EE`) is explicitly a **Premium** database.

Its free sample ticker set includes IBM but does not provide a useful free US14-wide path.

Therefore:

- no Nasdaq Zacks data calls in REV43;
- no attempt to build a mixed one-ticker IBM owner merely because IBM appears in sample data.

Record it as:

`PREMIUM_WITH_LIMITED_SAMPLE_NOT_US14_SOLUTION`.

---

# 25. Do not use Business Quant again

Hard zero:

`BUSINESS_QUANT_CALLS = 0`

The free-account behavior is already proven by three exact smoke responses.

Do not repeat it tomorrow.

---

# 26. No Alpha Vantage

Hard zero:

`ALPHA_VANTAGE_CALLS = 0`

Preserve the user's 25/day Alpha Vantage budget.

---

# 27. No current fPER yet

REV43 closes the forward EPS denominator only.

Hard zero:

```text
NEW_US_PRICE_CALLS = 0
CURRENT_FPER_CALCULATIONS = 0
```

Do not derive user-facing fPER in this task.

The later integration task will combine:

`latest completed-session close / qualified FY1 EPS`

only for eligible securities.

---

# 28. No model/message work

Hard zero:

```text
MODEL_CALLS = 0
MARKET_MODEL = 0
CORE = 0
PASS_A = 0
PASS_B = 0
USER_MESSAGES = 0
TELEGRAM = 0
```

No KR provider calls.

---

# 29. Raw evidence policy

For every live FMP response used in qualification save privately:

- ticker;
- redacted route;
- retrieval timestamp;
- HTTP status;
- quota/rate headers if exposed;
- raw response SHA;
- local raw response.

Never save:
- API key;
- authenticated full URL;
- cookies/session secrets.

Do not push raw FMP data to public GitHub.

Result ZIP handling must follow the current FMP license/access contract.
If archival redistribution/storage rights are ambiguous, include:
- response hashes;
- canonical typed projection;
- minimal permitted evidence;
and keep raw response local only.

Do not weaken reproducibility silently; record the limitation.

---

# 30. Replay

After live acquisition:

network off.

Replay all captured FMP responses twice.

Require identical canonical semantic hashes.

Any parser repair after acquisition uses frozen responses.

Do not recollect.

---

# 31. Exact matrix

Create:

`us14-fmp-fy1-eps-qualification-matrix.json`

Exactly 14 rows with:

```text
ticker
provider = FMP
provider_symbol
latest_completed_fy
fy1_period_end
fy1_eps_avg
fy1_eps_high
fy1_eps_low
num_analysts_eps
estimate_asof
estimate_date_state
accounting_basis_state
currency_state
share_basis_state
security_kind
adr_ratio_state
qualification_state
additional_states[]
raw_sha256
```

---

# 32. Call ledger

Create:

`fmp-call-ledger.json`

Record:

```text
advertised_basic_daily_limit
calls_before_task_if_known
calls_used_by_task
ticker_call_counts
duplicates
transport_retries
profile_calls
remaining_estimated_headroom
```

Do not claim account-level remaining calls if FMP does not expose them.

---

# 33. Validation

Before any live call:
synthetic focused tests must PASS.

After acquisition:

- real-response offline replay tests;
- GOOGL calendar FY;
- MU non-calendar FY;
- exact first-future-period selection;
- negative EPS preservation;
- symbol mismatch;
- empty response;
- entitlement response;
- estimate-asof null;
- accounting basis unspecified;
- reporting-currency mismatch;
- ADR fail-closed;
- API key redaction;
- call guard;
- no Business Quant;
- no Alpha Vantage;
- no models/messages.

Then:

- focused pytest;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

Tests must be network-blocked.

---

# 34. Storage guard

Record current APFS free bytes.

Hard floor before any provider call:

`>= 12 GiB`

Preferred:

`>= 16 GiB`.

Do not perform broad second-stage worktree cleanup inside REV43.

If below 12 GiB:

`R2B_R9_REV43_STORAGE_HEADROOM_GAP`

and stop.

---

# 35. Success definition

Success does not require 14 numeric EPS values.

REV43 passes when:

1. REV42 integrity PASS;
2. REV42 final history preserved remotely;
3. REV43 exact base verified;
4. FMP license/access scope acceptable for current private personal workflow;
5. FMP credential available without secret exposure;
6. Stage B GOOGL/MU account entitlement PASS;
7. FMP calls bounded and nonduplicative;
8. all US14 get deterministic typed states;
9. exact FY1 period selection;
10. currency/share basis proven or failed closed;
11. ADRs failed closed unless exact listed basis is proven;
12. no Business Quant calls;
13. no Alpha Vantage calls;
14. no price/fPER calls;
15. no models/messages;
16. replay twice PASS;
17. full validation PASS;
18. secret scan PASS;
19. production isolation PASS.

Success terminal:

`R2B_R9_REV43_FMP_US14_EXACT_FY1_EPS_QUALIFICATION_PASS_READY_FOR_CURRENT_FPER_INTEGRATION`

Report:

```text
qualified positive FY1: X/14
qualified nonpositive FY1: Y/14
currency/share/ADR blocked: Z/14
unavailable/provider blocked: N/14
FMP calls used: C
```

---

# 36. Honest stop terminals

```text
R2B_R9_REV43_FMP_CREDENTIAL_REQUIRED
R2B_R9_REV43_FMP_LICENSE_SCOPE_GAP
R2B_R9_REV43_FMP_FREE_ENTITLEMENT_GAP
R2B_R9_REV43_FMP_SCHEMA_GAP
R2B_R9_REV43_FMP_COMMON_SHARE_BASIS_GAP
R2B_R9_REV43_FMP_ADR_BASIS_GAP
R2B_R9_REV43_FMP_RATE_LIMIT_GAP
R2B_R9_REV43_STORAGE_HEADROOM_GAP
R2B_R9_REV43_VALIDATION_GAP
```

Do not fall back automatically to:
- Yahoo;
- StockAnalysis scraping;
- Nasdaq Zacks premium;
- Business Quant;
- Alpha Vantage.

---

# 37. Result bundle

Create:

`thesis-monitor-20261001-r2b-r9-rev43-fmp-us14-fy1-eps-qualification-report.zip`

+ `.sha256`.

Include at minimum:

```text
REPORT.md
summary.json
REV42-integrity.json
repository-identities.json
remote-preservation-receipt.json
storage-preflight.json
fmp-documentation-ledger.json
fmp-access-contract.json
credential-capability.json
fmp-call-ledger.json
request-ledger.json
security-identity-ledger.json
ADR-basis-ledger.json
us14-fmp-fy1-eps-qualification-matrix.json
rev41-yahoo-comparison.json
raw-evidence-manifest.json
replay-1.json
replay-2.json
validation.json
secret-scan.json
production-isolation.json
bundle-manifest.json
```

No API key.

---

# 38. Next step after PASS

Stop after REV43.

Do not automatically start current-fPER integration.

If useful FMP coverage is qualified, next work becomes:

> REV44 — fresh US latest-completed-session close + qualified FMP FY1 EPS → current FY1 fPER owner and US14 forward-valuation integration.

If FMP free entitlement also fails, stop the free-provider hunt and explicitly choose among:

1. US fPER remains `자료 부족`;
2. user authorizes a paid estimates provider;
3. issuer guidance becomes a separately labelled non-consensus valuation family where available.

Do not keep cycling through undocumented scraping sources.

---

# 39. Final principle

Business Quant's free marketing documentation did not match the actual US14 account entitlement, and the implementation correctly failed closed.

The next candidate should be tested the same way:

> documented API contract first, actual free-account smoke second, portfolio expansion only after entitlement is proven.

One clean provider qualification is more valuable than another broad scrape.
