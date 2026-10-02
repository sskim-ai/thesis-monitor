# Thesis Monitor — R2B-R9-REV41
## US14 Free Exact-Horizon FY1 / NTM EPS Source Qualification
### Start from accepted REV40-R2 remote-preserved code
### No main merge / no model calls / no production writes / no broad full-fresh run

---

# 0. Decision on sequencing

Do **not** spend another maintenance cycle trying to delete the remaining historical worktrees before this task.

The completed worktree consolidation already removed the low-risk bulk:

- registered worktrees: `198 -> 40`
- removed: `158`
- actual immediate APFS free-space increase during approved removal: about `17.42 GiB`
- latest observed free space in the disk-accounting addendum: about `19.09 GiB`

The remaining worktrees were intentionally retained because they contain one or more of:

- protected auth/config/DB state;
- non-Git evidence whose immutable archive replacement is not yet proven;
- dirty/untracked evidence;
- commit history containing raw artifacts not approved for remote export.

Those are higher-risk cleanup targets and are not required for a bounded US source-qualification task.

Therefore:

> Proceed to US forward-EPS source qualification now.

A second-stage worktree cleanup may be revisited **before a later broad full-fresh all22 integration** if disk headroom falls below the standing guard.

---

# 1. Accepted repository base

Do not start REV41 from operating `main`.

Operating main remains:

`b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

and does not contain the accepted KR REV40-R2 implementation.

The accepted KR implementation is remotely preserved at:

```text
refs/heads/archive/worktree-cleanup/20261001/codex-r2b-r9-rev40-r2-frozen-kr8
```

Exact remote SHA:

`3ed46521c7bd50565665747ff35d872d3e601f7d`

REV40-R2 accepted result terminal:

`R2B_R9_REV40_R2_KR8_FROZEN_SOURCE_8_MESSAGE_PASS_READY_FOR_BLIND_REVIEW`

Create a **new REV41 worktree/branch from that exact remote-preserved SHA**, not from `main`.

Suggested branch:

`codex/r2b-r9-rev41-us-forward-eps-source-qualification`

First prove:

```text
REV41 base HEAD == 3ed46521c7bd50565665747ff35d872d3e601f7d
```

No main merge is authorized in REV41.

---

# 2. Task purpose

The Korean forward valuation path is now solved.

The remaining valuation gap is the US side:

> Find and formally qualify a free, exact-horizon source for US FY1 EPS or exact NTM EPS that can be used to derive forward valuation without relying on ambiguous generic `forwardPE`.

This task is **source qualification only**.

It is not yet:

- a US14 full-fresh collection;
- a US14 Core/A/B run;
- a message proof;
- a combined all22 proof;
- a main merge;
- a renderer cleanup.

---

# 3. US14 subjects

Evaluate exactly these current US monitoring subjects:

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

All 14 must receive a deterministic typed source state.

Numeric coverage does **not** have to be 14/14.

Unsupported must remain typed unavailable.

---

# 4. Existing known constraints

Preserve the already-established facts.

## Finnhub

Existing provider-native trailing valuation is allowed where already qualified.

However:

```text
/stock/eps-estimate?freq=annual
```

previously returned:

`HTTP 403 Premium`

Therefore:

- do not assume Finnhub FY1 EPS is free;
- do not repeatedly burn requests probing the same premium route;
- one control revalidation is optional only if necessary to prove the entitlement state has changed;
- otherwise use the sealed prior evidence.

Generic Finnhub `forwardPE` is **not** an acceptable exact forward owner because the exact horizon is not owned.

Do not promote it.

## Alpha Vantage

Standing user policy:

- treat daily budget as `25 calls/day`;
- keep Alpha Vantage usage at `0` whenever possible.

For REV41:

`ALPHA_VANTAGE_CALLS = 0`

Do not spend the budget merely to explore.

If Alpha Vantage later appears uniquely promising from documentation, record it as a future candidate rather than calling it in REV41.

---

# 5. What qualifies as an exact forward-EPS source

A source is acceptable only when it deterministically owns:

## Security identity
Exact monitored security/listing.

## Estimate metric
EPS per share, not just a precomputed PE multiple.

## Horizon
One of:

### FY1
The first provider-owned forecast fiscal year after the latest completed fiscal year.

or

### Exact NTM / next-12-month EPS
Only if the provider explicitly defines the metric as a rolling next-twelve-month EPS value.

A label such as:

- forward EPS;
- forward PE;
- next-year estimate;

without exact period/horizon semantics is insufficient.

## Period identity
For FY1:
- explicit fiscal period end or year identity.

## Estimate date / source snapshot
Provider-owned estimate-as-of/publication/update date when supplied.

Do not substitute retrieval timestamp for provider estimate date.

If the provider is documented as a latest-snapshot service with no estimate date:
record `estimate_asof=null` and preserve the provider-latest semantic explicitly.

## Currency
Exact EPS currency or deterministic security-local currency semantics.

## Share basis
Exact per-share basis of the monitored listing.

For ADRs or depositary receipts:
the ratio/basis must be owned by the source or bound through an authoritative issuer/depositary/SEC document.

No silent ordinary-share-to-ADR transfer.

---

# 6. US identity and ADR rule

Do not transfer forward EPS between securities merely because they represent the same issuer.

Especially inspect:

- `TSM`
- `SKHY`
- `WRD`

and any other ADR/depositary structure.

For each:

1. identify the exact monitored listing;
2. identify whether the candidate EPS estimate is already expressed per listed ADS/ADR/share;
3. if not, identify an authoritative depositary ratio;
4. prove currency and share-unit conversion;
5. otherwise state:

`ADR_BASIS_UNRESOLVED`.

No cross-security valuation transfer.

---

# 7. Official-source role

Issuer IR, SEC filings and depositary documentation may be used to establish:

- exact security identity;
- fiscal-year calendar;
- completed fiscal year;
- ADR/depositary ratio;
- share-unit/currency semantics.

Do **not** assume SEC or issuer filings provide analyst consensus FY1 EPS.

Company guidance is not automatically interchangeable with analyst consensus.

If issuer guidance contains EPS:
record it as:

`ISSUER_GUIDANCE_EPS`

not as analyst consensus.

Do not silently mix guidance and analyst estimates in one owner family.

---

# 8. Candidate-source discovery

Perform a bounded source survey.

Maximum:

`10` candidate provider/source families.

Prefer, in order:

1. documented public/free provider APIs;
2. documented provider JSON/XHR endpoints available without paid entitlement;
3. stable public provider pages with explicit FY1 EPS + fiscal period;
4. issuer/depositary sources for identity/basis support.

Do not:

- bypass paywalls;
- bypass CAPTCHAs;
- circumvent authentication;
- use stolen/session cookies;
- scrape private logged-in content;
- create paid accounts;
- sign up for trials requiring payment information.

Normal public web access and existing already-configured provider credentials are allowed.

---

# 9. Candidate ledger

Create:

`us-forward-eps-candidate-ledger.json`

For every candidate record:

```text
provider
route/url family
access class
authentication required?
free entitlement?
rate limit
documented metric name
documented horizon
period-end available?
estimate-asof available?
currency available?
share basis available?
ADR support?
machine-readable?
stability concerns
terms/access notes
smoke result
qualification state
rejection reason
```

Never store secret values.

---

# 10. Staged qualification

Do not immediately call every candidate for all 14 symbols.

Use three stages.

## Stage A — documentation/contract research

No portfolio-wide provider calls.

Determine whether the source could theoretically satisfy:

- exact EPS;
- exact horizon;
- period identity;
- security identity;
- share basis.

Reject semantically insufficient sources before network testing.

Examples of immediate rejection:

```text
HORIZON_AMBIGUOUS
FORWARD_PE_ONLY
NO_EPS_VALUE
NO_PERIOD_IDENTITY
PAYWALL_REQUIRED
ADR_BASIS_UNOWNED
```

## Stage B — representative smoke set

For each semantically promising source, test only a bounded representative set:

```text
GOOGL
MU
TSM
```

This covers:
- ordinary US-listed equity;
- semiconductor/AI-sensitive name;
- ADR/depositary case.

If SKHY requires a different identity route, it may be the fourth smoke subject.

No other symbols until the source passes smoke semantics.

## Stage C — US14 matrix

Only a source that passes Stage B may be evaluated across US14.

Do not continue hammering rejected sources.

---

# 11. Request budget

Keep the task bounded.

Per candidate source:

- documentation requests: reasonable;
- live API/data smoke requests: max `4`;
- if qualified for Stage C: max `16` additional requests unless the provider supports batching.

Total live candidate-data requests across all candidates:

`<= 50`

This cap excludes ordinary documentation page fetches.

If a source would require more to establish basic semantics:
stop and report the gap.

Alpha Vantage remains `0`.

---

# 12. Raw evidence handling

For every live source response used in qualification:

save:

- URL/route family;
- retrieval timestamp;
- status code;
- response headers needed for provenance/rate-limit evidence;
- raw response bytes;
- SHA-256;
- parsed canonical projection.

Redact/omit:

- API keys;
- bearer tokens;
- cookies;
- session identifiers;
- secrets.

Never print secrets in terminal/report.

---

# 13. Typed qualification states

Each US14 subject must end in one of:

```text
QUALIFIED_FY1_EPS
QUALIFIED_EXACT_NTM_EPS
UNAVAILABLE_ESTIMATE
SOURCE_UNSUPPORTED_SECURITY
SOURCE_PAYWALL
IDENTITY_MISMATCH
HORIZON_AMBIGUOUS
PERIOD_IDENTITY_UNRESOLVED
ESTIMATE_DATE_UNAVAILABLE_ACCEPTED_LATEST_SNAPSHOT
CURRENCY_BASIS_UNRESOLVED
SHARE_BASIS_UNRESOLVED
ADR_BASIS_UNRESOLVED
SOURCE_RESPONSE_INVALID
SOURCE_ACCESS_UNSTABLE
```

Use the narrowest truthful state.

Do not map provider/network/parser failure to `UNAVAILABLE_ESTIMATE`.

---

# 14. Canonical US forward-EPS record

Design a typed record, but do not yet wire it into live US messages.

Suggested semantic fields:

```text
security
security_identity
provider
provider_security_id
metric = EPS
horizon_kind = FY1 | NTM
fiscal_period_end
fiscal_year
latest_completed_fiscal_year
eps_value
eps_currency
share_basis
adr_ratio
estimate_asof
retrieved_at
source_route
source_raw_sha256
qualification_state
denial_reasons[]
```

No `forwardPE` field may substitute for EPS.

---

# 15. FY1 selection rule

For a candidate with annual estimate rows:

1. resolve exact issuer fiscal year;
2. resolve latest completed annual fiscal period;
3. select the first provider forecast annual period strictly after that completed period;
4. require the provider row itself to be forecast/estimate, not actual;
5. store its explicit fiscal period end.

Do not select simply:

`MAX(year)`.

Do not assume calendar-year issuers.

---

# 16. Exact NTM rule

If a source provides NTM EPS:

accept only if provider documentation explicitly defines it as rolling next-twelve-month EPS.

Require:

- exact security;
- EPS/share basis;
- currency;
- source snapshot semantic.

Do not infer NTM from:
- generic `forward`;
- blended PE;
- undocumented consensus field.

If both FY1 and exact NTM exist:
store them as separate owner families.

Do not overwrite one with the other.

---

# 17. Source hierarchy / composite owner

Prefer a single consistent provider if it satisfies the contract.

However a forced single-provider requirement is not necessary.

A composite US forward-EPS owner is permitted only when:

- every source family is independently qualified;
- every security has exact source identity;
- all records share the same typed schema;
- provider/source identity remains visible per security;
- no metric is silently substituted;
- unavailable states remain typed.

Do not merge values by preference/ranking without an explicit deterministic owner rule.

---

# 18. No forward-valuation integration yet

REV41 does **not** need a fresh US completed-session close.

Do not run full US14 price collection merely to compute fPER.

The purpose is to close the EPS denominator authority first.

At most, if needed for a share-basis sanity check, use a frozen/local test price fixture.

Do not create a current user-facing fPER value in REV41.

The next task will combine:

```text
latest completed-session US close
/
qualified exact FY1 or NTM EPS
```

after denominator qualification passes.

---

# 19. Existing valuation families remain unchanged

Do not modify the accepted provider-native current/trailing valuation owner.

Current US valuation remains:

- current PER where qualified;
- current PBR where qualified;
- current fPER:
  unresolved until REV41 source qualification succeeds and a later integration task derives it.

No cross-family leakage.

---

# 20. Model / message scope

Hard zero:

```text
MODEL_CALLS = 0
USER_MESSAGES = 0
TELEGRAM_SENDS = 0
```

No:

- Core;
- Pass A;
- Pass B;
- Market model;
- final renderer;
- sender boundary proof.

This is source authority work only.

---

# 21. KR scope

Do not recollect Korean data.

Do not call KIS.

Do not modify KR FY1 owner semantics.

KR code must remain regression-green because REV41 starts from the accepted REV40-R2 SHA.

Required:

`KR_PROVIDER_CALLS = 0`

---

# 22. Storage guard

At REV41 start, record actual APFS free bytes.

Latest prior audit observed roughly:

`19.09 GiB`

but that value is only historical; remeasure.

For this bounded source-qualification task:

hard floor:

`>= 12 GiB`

preferred:

`>= 16 GiB`.

If free <12 GiB:
stop with:

`R2B_R9_REV41_STORAGE_HEADROOM_GAP`

Do not begin a second-stage worktree deletion automatically inside REV41.

Return the disk state and request a separate cleanup task.

---

# 23. No further worktree cleanup in this task

The remaining 40 worktree registrations are not REV41 scope.

Do not:

- push their raw-artifact histories;
- delete their protected auth/DB state;
- archive ambiguous evidence;
- run further bulk worktree removal.

Only create the new REV41 worktree from the accepted remote-preserved REV40-R2 commit.

This prevents source research and storage forensics from becoming entangled.

---

# 24. Validation

Add focused tests for:

- exact FY1 selection;
- non-calendar fiscal years;
- actual-vs-estimate row polarity;
- period-end ownership;
- horizon ambiguity rejection;
- no generic forwardPE promotion;
- estimate-date-null latest-snapshot semantics;
- security identity mismatch;
- currency mismatch;
- share-basis mismatch;
- ADR ratio required;
- typed unavailable vs provider failure;
- composite-source provenance isolation.

Run:

- focused tests;
- full pytest;
- Ruff;
- `git diff --check`;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No production source calls in tests.

---

# 25. Qualification matrix

Create:

`us14-forward-eps-qualification-matrix.json`

and a human-readable table containing exactly US14.

Columns:

```text
ticker
provider
provider_security_id
horizon_kind
latest_completed_fy
target_period_end
eps
currency
share_basis
estimate_asof
adr_ratio_state
qualification_state
reason
raw_sha256
```

Every subject must have one row.

---

# 26. Provider comparison

For all semantically plausible sources compare:

```text
exact horizon quality
US14 coverage
GOOGL coverage
MU coverage
TSM ADR correctness
SKHY identity support
estimate date quality
fiscal period quality
currency/share basis
machine-readability
free entitlement
rate-limit practicality
stability
reproducibility
```

Do not score/rank with arbitrary points.

State factual tradeoffs.

Then select:

- `ADOPTABLE`
- `SECONDARY_ONLY`
- `REJECTED`

per source.

---

# 27. Success definition

Numeric coverage does not need to be 14/14.

REV41 passes when:

1. base is exact accepted REV40-R2 remote SHA;
2. storage guard passes;
3. Alpha Vantage calls = 0;
4. no model/message/production calls;
5. candidate survey is bounded and documented;
6. at least one source family satisfies the exact forward-EPS semantic contract for at least one US monitored security;
7. every US14 subject has a deterministic typed state;
8. any qualified EPS value owns exact security + horizon + fiscal period + currency/share basis;
9. ADRs fail closed unless basis is proven;
10. generic forwardPE is never promoted;
11. raw evidence and hashes are sealed;
12. replay/parser tests are deterministic;
13. full validation passes;
14. secrets scan passes.

Success terminal:

`R2B_R9_REV41_US14_EXACT_FORWARD_EPS_SOURCE_QUALIFICATION_PASS_READY_FOR_INTEGRATION_DESIGN`

The success report must clearly state numeric coverage:

```text
FY1 qualified: X/14
NTM qualified: Y/14
typed unavailable/blocked: Z/14
```

Do not hide partial coverage behind PASS.

---

# 28. Honest stop terminals

Use the narrowest applicable stop:

```text
R2B_R9_REV41_NO_FREE_EXACT_FORWARD_EPS_SOURCE
R2B_R9_REV41_ONLY_AMBIGUOUS_FORWARD_METRICS_FOUND
R2B_R9_REV41_SOURCE_PAYWALL_GAP
R2B_R9_REV41_ADR_BASIS_GAP
R2B_R9_REV41_SOURCE_STABILITY_GAP
R2B_R9_REV41_STORAGE_HEADROOM_GAP
R2B_R9_REV41_VALIDATION_GAP
```

A truthful negative result is acceptable.

Do not weaken exact-horizon requirements to force PASS.

---

# 29. Required result bundle

Create immutable:

`thesis-monitor-20261001-r2b-r9-rev41-us14-forward-eps-source-qualification-report.zip`

+ `.sha256`.

Include at minimum:

```text
REPORT.md
summary.json
repository-identities.json
storage-preflight.json
candidate-ledger.json
provider-documentation-ledger.json
smoke-request-ledger.json
us14-forward-eps-qualification-matrix.json
authority-contract.json
ADR-basis-ledger.json
raw-evidence-manifest.json
parser/replay receipts
validation receipts
secret-scan.json
production-isolation.json
bundle-manifest.json
```

No secret values.

---

# 30. No automatic next integration

After REV41 result is produced:

stop.

Do not automatically start a full-fresh US14 run.

The next instruction must be based on the actual qualified source result.

Possible next step:

- if exact source coverage is useful:
  `REV42 US current-price FY1/NTM fPER integration`
- if no useful free source exists:
  decide whether to:
  - accept US fPER as 자료부족;
  - use a paid provider;
  - use issuer guidance as a separate non-consensus valuation family.

---

# 31. Final principle

The worktree cleanup has already delivered enough headroom for bounded source research.

Do not risk protected historical evidence merely to make the local tree prettier.

Now close the real product gap:

> obtain an exact, source-owned US forward EPS denominator.

Only after that denominator is formally qualified should the project derive US current fPER and return to a combined all22 integration proof.
