# Thesis Monitor — R2B-R9-REV42
## Business Quant Free API — US14 Exact FY1 EPS Qualification
### Authorized API route / 30-call free-plan budget / no Alpha Vantage
### Preserve REV41 negative result; do not reuse Yahoo as production feed
### No model calls / no messages / no production writes

---

# 0. Task identity

REV41 completed correctly and honestly stopped at:

`R2B_R9_REV41_SOURCE_STABILITY_GAP`

because Yahoo provided useful FY1 semantics but did not provide an acceptable automated-access contract for the intended recurring pipeline.

REV42 is a bounded follow-up to qualify a newly identified candidate:

> **Business Quant Analyst Estimates API**

Official documentation indicates:

- Analyst Estimates API is free to use.
- API returns Wall Street consensus EPS by annual and quarterly fiscal periods.
- Annual rows distinguish `reported` vs `estimate`.
- `value_estimate` is consensus mean EPS and is explicitly per-share.
- API is the provider-authorized route for automated access.
- Free plan has 30 API calls/day and does not require a credit card.
- Free plan includes analyst estimates with forward coverage.
- Terms permit API use for internal research/analysis subject to plan limits.

Official references:

- `https://businessquant.com/docs/api/estimates`
- `https://businessquant.com/docs/api/overview`
- `https://businessquant.com/pricing`
- `https://businessquant.com/terms-of-use`

Do not scrape Business Quant web pages for numeric portfolio data.
Numeric data must come only through its documented API.

---

# 1. REV41 integrity / newest SoT

Verify the uploaded REV41 result before work.

Expected result ZIP:

`thesis-monitor-20261001-r2b-r9-rev41-us14-forward-eps-source-qualification-report.zip`

Expected SHA-256:

`1266d19cde3224f1ae42ad29dd46cdddfafecb73133c449578cf2eddb717efe0`

Expected internal integrity:

- CRC PASS
- 82 ZIP members
- bundle manifest payload `81/81`
- missing `0`
- hash mismatch `0`
- size mismatch `0`
- extra `0`.

REV41 accepted facts:

- final terminal:
  `R2B_R9_REV41_SOURCE_STABILITY_GAP`
- semantic Yahoo FY1:
  `11/14`
- exact NTM:
  `0/14`
- automated adoptable sources:
  `0`
- Alpha Vantage:
  `0`
- model calls:
  `0`
- production side effects:
  `0`
- validation:
  PASS.

Preserve REV41 as a negative/semantic reference.

Do not convert its Yahoo source into a recurring production feed.

---

# 2. Repository base and preservation

REV41 final local head:

`e28a747c66c2ff93edc402011f2cf543eb0b5709`

REV41 tested implementation:

`5efffa765c7f18adae2c2fe3ba764449e4d463f2`

The final delta after the tested implementation is documentation-only and was validated byte-identical for code/tests.

Before creating REV42:

1. verify current REV41 branch/head;
2. secret-scan the outgoing commit range;
3. push the exact REV41 branch/history to GitHub using a normal fast-forward/non-destructive ref;
4. fetch and verify the remote exact SHA.

Preferred remote preservation ref:

`archive/worktree-cleanup/20261001/codex-r2b-r9-rev41-us-forward-eps-source-qualification`

Remote SHA must equal:

`e28a747c66c2ff93edc402011f2cf543eb0b5709`

No force push.
No main merge.
No remote ref deletion.

Create REV42 from that exact remote-preserved SHA.

Suggested branch:

`codex/r2b-r9-rev42-businessquant-us-forward-eps`

---

# 3. Credential gate

Business Quant requires a free API key.

Do not print, archive or commit the key.

Check only whether an existing configured credential is available using accepted secret/config mechanisms.

Recognize reasonable local names such as:

```text
BUSINESSQUANT_API_KEY
BUSINESS_QUANT_API_KEY
BQ_API_KEY
```

but do not create compatibility aliases in committed source unless the repository's credential abstraction requires one.

If no Business Quant key is configured:

stop immediately with:

`R2B_R9_REV42_BUSINESSQUANT_CREDENTIAL_REQUIRED`

The result must tell the user:

- free account/API key is required;
- no credit card is required according to current provider pricing;
- set the key locally in the normal secret configuration;
- do not paste the secret into reports/chat/logs.

Do not create an account on the user's behalf.

Do not fall back to Yahoo scraping.

---

# 4. Free-plan quota guard

Treat Business Quant free-plan budget as:

`30 API calls/day`

REV42 hard cap:

`<= 20 Business Quant data calls`

Preferred:

`14 calls`

This leaves safety headroom for the user's account.

Do not aggregate multiple accounts/keys/IPs.

Do not retry to evade limits.

Record:

- calls attempted
- successful
- failed
- remaining estimated daily headroom.

Alpha Vantage:

`0 calls`.

---

# 5. Exact US14 universe

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

Every ticker must receive a deterministic typed state.

Numeric coverage is not a PASS requirement.

---

# 6. Only documented Business Quant API route

Use:

`GET https://data.businessquant.com/estimates`

Parameters:

```text
ticker=<exact monitored ticker>
mode=eps
api_key=<secret>
```

One request per ticker is preferred.

Do not use Business Quant website scraping.

Do not use undocumented internal/XHR routes.

Do not query revenue mode unless necessary for a tightly justified identity diagnostic.

---

# 7. Expected response contract

Bind only documented fields.

Metadata:

```text
cik
ticker
companyname
companyname_short
mode
metric_display
```

Annual/quarterly arrays:

```text
dimension
period
sno
data_type
value_estimate
value_reported
high_estimate
low_estimate
```

Provider documentation states:

- annual `period` is a fiscal-period label;
- `data_type=reported` means completed;
- `data_type=estimate` means forward;
- EPS-mode `value_estimate` is consensus mean analyst EPS;
- EPS values are per-share.

Do not invent undocumented fields.

---

# 8. FY1 owner

For each ticker:

1. require metadata ticker exact match;
2. bind CIK to accepted security identity where available;
3. select annual dimension only;
4. identify the latest annual row with:
   `data_type=reported`;
5. select the first later annual row with:
   `data_type=estimate`;
6. label that row:
   `FY1`.

Store:

```text
provider = BUSINESS_QUANT
metric = EPS
estimate_family = WALL_STREET_CONSENSUS
horizon_kind = FY1
fiscal_year = period
eps = value_estimate
high = high_estimate
low = low_estimate
latest_completed_fy = latest reported period
estimate_asof = null unless provider response owns a date
retrieved_at
provider_cik
provider_ticker
raw_sha256
```

Do not use `MAX(period)`.

Do not use quarterly sums as FY1.

---

# 9. Estimate-date semantics

Current public Business Quant documentation does not establish a per-row estimate publication timestamp.

Therefore default:

```text
estimate_asof = null
estimate_date_state =
  ESTIMATE_DATE_UNAVAILABLE_ACCEPTED_LATEST_PROVIDER_SNAPSHOT
```

Only change this if the actual documented API response owns an explicit provider timestamp with clear semantics.

Retrieval time is not estimate-as-of.

---

# 10. Accounting-basis semantics

Do not label Business Quant EPS as GAAP or normalized/non-GAAP unless provider documentation or deterministic historical calibration proves the basis.

Default:

`PROVIDER_CONSENSUS_ACCOUNTING_BASIS_UNSPECIFIED`

This state is not automatically fatal for source qualification if all other denominator semantics are exact.

However:

- never display it as GAAP;
- never display it as adjusted/non-GAAP;
- preserve the provider-consensus label in future valuation output.

If historical `value_reported` values deterministically match an authoritative issuer/SEC EPS basis across sufficient periods, record the calibration separately.

Do not rewrite the provider's consensus family based on one coincidental match.

---

# 11. Currency / share-basis qualification

The biggest remaining semantic question is whether the returned per-share EPS can be safely combined with the monitored listing's USD close.

Use strict typed qualification.

## Common US-listed securities

For:

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

- exact ticker identity;
- exact issuer/CIK;
- monitored security is common/listed share;
- issuer's EPS reporting currency/share basis is compatible with the returned provider series.

Use accepted SEC/issuer identity evidence already available in REV41/repository where sufficient.

If currency/share basis cannot be proven:

`CURRENCY_OR_SHARE_BASIS_UNRESOLVED`.

Do not assume USD merely from quote currency.

## ADR / ADS securities

For:

```text
TSM
SKHY
WRD
```

fail closed until the Business Quant EPS basis is proven.

Existing accepted ratios:

- TSM:
  `5 ordinary shares per ADS`
- SKHY:
  `0.1 ordinary share per ADS`
- WRD:
  `3 ordinary shares per ADS`

The ratio alone does not prove whether Business Quant's EPS response is:

- ordinary-share EPS;
- ADS EPS;
- converted USD EPS;
- issuer reporting-currency EPS.

No automatic multiplication/division/FX conversion.

---

# 12. Same-response historical calibration

The Business Quant EPS response includes historical reported annual rows.

Use them as a diagnostic.

For each security where basis is ambiguous:

compare one or more provider `value_reported` annual rows against authoritative issuer/SEC historical EPS evidence.

Classification examples:

```text
DIRECT_LISTED_SHARE_BASIS_PROVEN
ORDINARY_SHARE_BASIS_PROVEN
ADS_BASIS_PROVEN
CURRENCY_CONVERSION_PRESENT_PROVEN
BASIS_UNRESOLVED
```

Require deterministic equality/rounding logic with documented tolerance.

Do not infer a basis from approximate similarity.

For ADRs, if exact basis is not proven:
withhold FY1 consumption even if a number is returned.

---

# 13. FY1 numeric validity

Negative or zero EPS remains a valid forecast observation.

Typed states:

```text
QUALIFIED_FY1_EPS_POSITIVE
QUALIFIED_FY1_EPS_NONPOSITIVE
```

Only positive EPS will later be eligible for a numeric fPER denominator.

Do not classify negative EPS as missing.

---

# 14. Coverage states

Each US14 row ends in exactly one primary state:

```text
QUALIFIED_FY1_EPS_POSITIVE
QUALIFIED_FY1_EPS_NONPOSITIVE
UNAVAILABLE_ESTIMATE
SOURCE_UNSUPPORTED_SECURITY
IDENTITY_MISMATCH
PERIOD_IDENTITY_UNRESOLVED
CURRENCY_OR_SHARE_BASIS_UNRESOLVED
ADR_BASIS_UNRESOLVED
SOURCE_RESPONSE_INVALID
SOURCE_ENTITLEMENT_GAP
SOURCE_RATE_LIMIT
```

Additional nonfatal metadata may include:

```text
ACCOUNTING_BASIS_UNSPECIFIED
ESTIMATE_DATE_UNAVAILABLE_ACCEPTED_LATEST_PROVIDER_SNAPSHOT
```

Do not hide provider failures as unavailable estimates.

---

# 15. Request staging

To minimize quota risk:

## Stage A — documentation only

Revalidate current official:

- estimates API docs;
- API overview;
- pricing;
- terms.

Confirm:

- free analyst estimates;
- API is authorized automated route;
- free plan call budget;
- internal research use compatibility.

No data calls yet.

## Stage B — 3-symbol smoke

Use exactly:

```text
GOOGL
MU
TSM
```

3 API calls.

Require:

- HTTP success;
- exact metadata identity;
- annual reported/estimate rows;
- deterministic FY1 selection;
- no schema mismatch.

TSM may remain ADR blocked without failing the common-share smoke.

If GOOGL/MU both fail contractually:
stop before US14 expansion.

## Stage C — remaining US11

Only after Stage B passes common-share semantics.

Call each remaining ticker once.

Target total:

`14 data calls`.

Max:

`20`.

---

# 16. No Business Quant profile calls by default

Do not spend another 14 calls on the profile endpoint unless truly necessary.

The estimates response already owns ticker and CIK metadata.

Use:

- accepted repository security identity;
- SEC/issuer evidence;
- existing REV41 identity ledger

for exact listing checks.

A Business Quant profile call is permitted only for a bounded unresolved identity diagnostic.

Maximum profile calls:

`3`.

They count toward the 20-call hard cap.

---

# 17. No current-price fPER yet

REV42 qualifies the denominator.

Do not perform a fresh all-US price collection.

Do not calculate user-facing current fPER yet.

No model calls.

No final messages.

After successful qualification, REV43 may combine:

```text
latest completed-session close
/
qualified Business Quant FY1 EPS
```

for eligible securities.

---

# 18. Compare with REV41 Yahoo semantic snapshot

For diagnostic purposes only, compare Business Quant FY1 EPS with the sealed REV41 Yahoo semantic values where both are available.

Do not require equality.

Record:

```text
ticker
Business Quant FY1
Yahoo sealed FY1
absolute difference
relative difference
accounting-basis labels
period labels
```

Interpretation:

- differences may reflect different consensus sources/methodologies;
- do not select whichever value looks better;
- do not average them.

Yahoo remains non-production secondary evidence.

---

# 19. Terms / licensing receipt

Create:

`businessquant-access-contract.json`

Record only public terms facts, including:

```text
authorized_automated_route = API
free_plan = true
credit_card_required = false
free_daily_call_limit = 30
analyst_estimates_in_free_plan = true
internal_research_use = permitted
public_web_scraping = prohibited
redistribution = restricted
```

This Thesis Monitor use is an internal/private research workflow.

Do not publish Business Quant raw data publicly.

Do not upload raw API data to a public GitHub repository.

---

# 20. Raw evidence / secret handling

For each API request save locally:

- request route without secret;
- ticker;
- retrieved_at;
- HTTP status;
- relevant quota headers if present;
- raw response SHA;
- raw response body.

Never persist the API key in:

- URL logs;
- reports;
- Git;
- result ZIP;
- test fixtures;
- screenshots.

If the HTTP client records query URLs:
redact `api_key` before logging.

Export only redacted request metadata.

Raw response data may be sealed in the private result archive if secret scan passes.

Do not commit raw portfolio responses to Git.

---

# 21. Replay

After acquisition:

- disable network;
- replay every saved Business Quant response twice;
- require exact canonical semantic equality.

Parser must be deterministic.

No provider calls during replay.

---

# 22. Canonical qualification matrix

Create:

`us14-businessquant-fy1-eps-matrix.json`

Exactly 14 rows:

```text
ticker
provider
provider_ticker
provider_cik
latest_completed_fy
fy1_fiscal_year
fy1_eps
high_estimate
low_estimate
accounting_basis_state
estimate_asof
estimate_date_state
security_kind
currency_basis_state
share_basis_state
adr_ratio_state
qualification_state
additional_states[]
raw_sha256
```

---

# 23. Success criteria

REV42 PASS requires:

1. REV41 bundle integrity PASS;
2. REV41 final branch preserved remotely at exact SHA;
3. REV42 based on exact REV41 final SHA;
4. Business Quant free API credential configured without secret exposure;
5. official access contract confirms API-authorized automated use;
6. free-plan budget respected;
7. Alpha Vantage 0;
8. Stage B GOOGL/MU API + FY1 semantics PASS;
9. all US14 receive typed states;
10. exact ticker/CIK identity enforced;
11. first future annual estimate selection deterministic;
12. per-share metric semantics bound;
13. ADRs fail closed unless basis proven;
14. no price/fPER integration;
15. model calls 0;
16. messages 0;
17. KR provider calls 0;
18. offline replay twice PASS;
19. full validation PASS;
20. secret scan PASS;
21. production isolation PASS.

Numeric coverage may be partial.

Success terminal:

`R2B_R9_REV42_BUSINESSQUANT_US14_FY1_EPS_QUALIFICATION_PASS_READY_FOR_CURRENT_FPER_INTEGRATION`

Report exact coverage:

```text
qualified positive FY1: X/14
qualified nonpositive FY1: Y/14
basis/ADR blocked: Z/14
unavailable/provider failure: N/14
```

---

# 24. Honest stops

Use the narrowest:

```text
R2B_R9_REV42_BUSINESSQUANT_CREDENTIAL_REQUIRED
R2B_R9_REV42_BUSINESSQUANT_FREE_ENTITLEMENT_GAP
R2B_R9_REV42_BUSINESSQUANT_SCHEMA_GAP
R2B_R9_REV42_BUSINESSQUANT_COMMON_SHARE_BASIS_GAP
R2B_R9_REV42_BUSINESSQUANT_ADR_BASIS_GAP
R2B_R9_REV42_BUSINESSQUANT_RATE_LIMIT_GAP
R2B_R9_REV42_STORAGE_HEADROOM_GAP
R2B_R9_REV42_VALIDATION_GAP
```

Do not fall back to Yahoo scraping to force success.

---

# 25. Validation

Add tests for:

- Business Quant exact metadata ticker/CIK;
- annual dimension selection;
- latest reported -> first estimate FY1;
- non-calendar fiscal-year labels;
- negative EPS preservation;
- missing annual estimate;
- malformed response;
- accounting-basis unspecified state;
- estimate-asof null state;
- common-share basis qualification;
- ADR fail-closed;
- exact replay;
- secret/API-key redaction;
- 20-call budget guard;
- no Alpha Vantage;
- no model/messages.

Then run:

- focused tests;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

---

# 26. Result bundle

Return:

`thesis-monitor-20261001-r2b-r9-rev42-businessquant-us14-fy1-eps-qualification-report.zip`

+ `.sha256`.

Include at minimum:

```text
REPORT.md
summary.json
REV41-integrity.json
repository-identities.json
remote-preservation-receipt.json
storage-preflight.json
businessquant-documentation-ledger.json
businessquant-access-contract.json
credential-capability.json
request-ledger.json
quota-ledger.json
security-identity-ledger.json
ADR-basis-ledger.json
us14-businessquant-fy1-eps-matrix.json
rev41-yahoo-comparison.json
raw-evidence-manifest.json
replay-1.json
replay-2.json
validation.json
secret-scan.json
production-isolation.json
bundle-manifest.json
```

---

# 27. Next step after PASS

Do not automatically perform it inside REV42.

If REV42 gives useful qualified common-share coverage:

next task:

> REV43 — fresh US latest-completed-session close + qualified Business Quant FY1 EPS → current fPER owner, with exact corporate-action/share-basis guard and US14 integration.

ADRs that remain unresolved must continue to show forward valuation unavailable.

Only after REV43 is proven should the project run a fresh US model/message proof.

---

# 28. Final principle

REV41 already found the numbers.

Its blocker was permission and production-grade source authority.

REV42 should solve that exact gap using a provider whose documented API is explicitly intended for automated analyst-estimate access.

Do not loosen semantic standards, do not reuse a web scrape as a production feed, and do not spend the user's Alpha Vantage budget.
