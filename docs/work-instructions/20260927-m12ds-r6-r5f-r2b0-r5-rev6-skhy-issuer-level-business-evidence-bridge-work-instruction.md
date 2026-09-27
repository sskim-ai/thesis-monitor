# Thesis Monitor — M12DS-R6-R5F-R2B0-R5-REV6
## SKHY Issuer-Level Business-Evidence Bridge
### Prove legal-issuer identity first; only then permit issuer-level OpenDART financial evidence to satisfy SKHY business evidence

**Purpose:** resolve the sole remaining 21/22 source/business blocker without expanding SEC crawling or dropping SKHY. REV5 exhausted two bounded SEC filing windows for SKHY and found no qualified financial-purpose source. The next legitimate route is to determine whether monitored security `SKHY` and Korean security `000660` are securities of the **same legal issuer** and, if that identity is proven, permit only **issuer-level business/fundamental evidence** to be shared through a generic cross-security issuer bridge.

This task must never substitute 000660 price/technical/security-specific/per-share evidence into SKHY. It does not run models or messages.

---

# 0. Newest accepted SoT

Adopt R5-REV5 as newest SoT.

REV5 result ZIP SHA-256:

`3d0b90627ff48bb782c75dc6d1c95d693b13c9089118418606ca753b1325bc6e`

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV5_SKHY_FINAL_COVERAGE_BLOCK`

Result integrity independently rechecked:

- ZIP/sidecar exact;
- manifest entries: `235/235`;
- missing: `0`;
- hash/size mismatch: `0`;
- extra manifest-scope files: `0`.

Repository identities:

- base:
  `9aa2ec1d47bd31dbe0111bf5b85edfa2e030efd0`
- REV5 instruction:
  `b68098ed3bbfd4748e784189d7e1bbe54ff2788b`
- implementation/final/acquisition:
  `0558dcbf205d689fd6b08930421b71a6afdbed0b`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Accepted state:

- complete stock packets: `21/22`
- sole blocked subject:
  `SKHY`
- TSM: PASS
- WRD: PASS
- 19 REV4 controls remained invariant
- full validation:
  - focused `887 PASS`
  - full `5875 PASS / 63 unchanged skips`
  - Ruff/diff/Investment Knowledge/Chart Knowledge/disabled smoke PASS
- production side effects: `0`.

SKHY bounded SEC state is final for the current automatic route:

- first candidate window: 8
- second candidate window: 8
- third window: `0`
- second-window phase1:
  - `16/16` logical/HTTP
  - retry `0`
- second-window phase2:
  - `0` eligible exhibits
- no new submissions/discovery
- final denials include:
  - `NO_EXACT_FIELD_OBSERVATION`
  - `FPI_FINANCIAL_PURPOSE_BOUND_EXHAUSTED`
  - `LATEST_SELECTED_PERIOD_UNAVAILABLE_NO_OLDER_SUBSTITUTION`
  - `NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_PHASE1_AND_NO_PHASE2_ELIGIBLE_EXHIBIT`
  - `NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_TWO_BOUNDED_WINDOWS`
  - `FPI_FINANCIAL_PURPOSE_COVERAGE_EXHAUSTED_FINAL`

Do not add another automatic SEC candidate window in REV6.

---

# 1. Product/source decision being evaluated

The candidate route is:

> If two monitored securities are proven to be securities of the **same legal issuer**, issuer-level business/fundamental evidence may be reused across those securities while security-level evidence remains isolated.

For the current case:

- monitored US security: `SKHY`
- Korean security: `000660`
- SEC captured issuer:
  `SK hynix Inc.`
- SEC CIK observed in sealed SKHY sources:
  `0002120882`
- existing 000660 financial evidence issuer ID includes:
  `DART:00164779`

This information is a **candidate relation**, not proof of a bridge.

Do not authorize the bridge from ticker/name similarity alone.

---

# 2. Generic contract — no SKHY hardcode

Implement/evaluate a generic contract such as:

`SAME_LEGAL_ISSUER_BUSINESS_EVIDENCE_BRIDGE`

The code must operate on:

- canonical security IDs;
- canonical legal issuer IDs;
- official issuer identity evidence;
- explicit security→issuer ownership;
- evidence scope.

It must not contain:

- `if ticker == "SKHY"`
- `if ticker == "000660"`
- company-name exceptions
- hardcoded CIK↔DART mappings without an owned identity record
- manual value substitution.

SKHY/000660 are fixtures for the generic bridge.

---

# 3. First phase — offline identity audit

Before any network request, audit all existing local/sealed identity sources for:

## SKHY

- canonical security ID;
- exact security type;
- SEC issuer CIK;
- SEC legal issuer name;
- security/issuer ownership record;
- exchange/market;
- depositary/ADR status if applicable;
- underlying security relationship if applicable;
- ratio/conversion data if present;
- identity provenance and source tier.

## 000660

- canonical security ID;
- DART corp code;
- exact legal issuer name;
- stock code;
- legal/corporate identifier if retained;
- security/issuer ownership record;
- identity provenance and source tier.

Produce:

`SKHY-000660-issuer-identity-audit.json`

Do not fill missing fields by inference.

---

# 4. Legal-issuer identity proof standard

The bridge may activate only if identity is **affirmatively proven**.

Acceptable proof requires a deterministic owned crosswalk sufficient to establish:

`SKHY security -> legal issuer X`
and
`000660 security -> legal issuer X`

using official or already-qualified identity evidence.

Evidence may include, where actually available:

- canonical internal issuer master with source provenance;
- official SEC issuer/security registration evidence;
- official OpenDART corporation/security identity evidence;
- official exchange/depositary instrument relationship;
- exact legal-entity identifier common to both source systems;
- another existing approved identity owner.

Not sufficient alone:

- same/similar company name;
- same brand;
- parent/subsidiary inference;
- ticker similarity;
- search-engine result;
- AI inference;
- economic exposure similarity.

If exact same legal issuer cannot be proven:
- bridge remains disabled;
- SKHY remains blocked.

---

# 5. Optional bounded official identity verification

Only if offline identity evidence is insufficient, generate a separate immutable identity-verification plan before network access.

Allowed source families are **official identity/documentation only**.

No market-data call.

Maximum new logical identity/document requests:

`4`

Potential official sources may include:

- SEC issuer/cover-page/company registration document already tied to CIK 2120882;
- OpenDART corporation identity endpoint/document for corp code 00164779;
- official exchange/depositary/security registration source necessary to prove instrument→issuer relationship.

Do not use generic web/news sources.

The exact URL/endpoint/request list and theoretical max must be frozen before the first request.

Timeout:
`600s`

Transient retries:
- max 2
- total attempts max 3
- byte-identical only.

No retry for semantic/identity mismatch.

Alpha Vantage:
`0`

---

# 6. Bridge evidence scope — issuer-level only

If same legal issuer is proven, the bridge may share only evidence whose economic subject is the **issuer/business**, not the security instrument.

Potentially allowed:

- revenue;
- operating income;
- net income;
- cash flow;
- working-capital facts;
- issuer-level balance sheet;
- issuer-level financial direction;
- issuer-level business events/filings;
- canonical business/fundamental evidence explicitly owned by the issuer.

Every shared fact retains:

- original provider;
- original issuer ID;
- original filing/report ID;
- original period;
- original currency/unit;
- original occurrence IDs;
- original source-use/quality state;
- exact source refs.

Do not relabel DART evidence as SEC evidence.

---

# 7. Security-level evidence is strictly isolated

The bridge must **not** share from 000660 to SKHY:

- price;
- OHLCV;
- technical indicators;
- support/resistance;
- trading volume/value;
- KR investor flows;
- KR security-specific market data;
- KR listing/market mechanics;
- KR per-share price;
- KR EPS or per-share metrics without a separately proven security-basis conversion;
- PE/PB derived from 000660 price;
- market cap derived from 000660 security price/share count;
- security-specific dividend yield;
- any value requiring ADR/depositary ratio;
- any security-specific valuation denominator.

SKHY retains its own sealed:

- price source;
- OHLCV;
- technical evidence;
- current price;
- market/security context.

No cross-security price mixing.

---

# 8. Depositary / share-ratio rule

If SKHY is a depositary receipt or another instrument requiring a security conversion relationship:

- do not infer the ratio;
- do not use issuer-level per-share values in SKHY valuation without an exact ratio owner;
- do not block issuer-level business evidence merely because per-share conversion is unavailable, unless the downstream business-evidence schema genuinely requires that conversion.

Produce separate states:

- `ISSUER_BUSINESS_EVIDENCE_ELIGIBLE`
- `SECURITY_PER_SHARE_BRIDGE_ELIGIBLE`
- `SECURITY_VALUATION_BRIDGE_ELIGIBLE`

The first may be true while the latter two remain false.

---

# 9. 000660 source evidence eligible for reuse

Do not automatically reuse every 000660 fact.

Audit the currently qualified 000660 evidence field-by-field.

For every candidate issuer-level financial/business fact record:

- provider: OpenDART;
- DART issuer/corp ID;
- filing/report ID;
- source occurrence IDs;
- statement/report period;
- current/prior period role;
- CFS/OFS basis;
- currency/unit;
- source quality;
- taint/quality status;
- context eligibility;
- direction eligibility;
- exact current stock-owner usage.

Only facts that already pass the existing 000660 owner may be bridged.

Existing 000660 denials remain denials.

REV5 explicitly requires 000660 denied operating/net comparison state to remain unchanged where applicable.

Do not revalidate a denied field merely because it would help SKHY.

---

# 10. Directional evidence under the bridge

Issuer-level direction may be used for SKHY only when the original OpenDART field already has valid directional authority:

- exact current/prior comparative lineage;
- compatible period;
- statement basis;
- currency/unit;
- quality/source-use.

A context-only absolute field remains context-only after bridging.

The bridge cannot upgrade:

`context_eligible`
to
`direction_eligible`.

---

# 11. Provenance representation

A bridged fact must make the bridge explicit.

Required chain:

`SKHY monitored security`
→ `same-legal-issuer identity bridge`
→ `legal issuer`
→ `OpenDART issuer source`
→ `filing/report`
→ `field occurrence(s)`

Add a source/reference type equivalent to:

`ISSUER_LEVEL_CROSS_SECURITY_EVIDENCE`

Do not make the final evidence appear natively owned by the SKHY SEC filing.

Preserve both:

- monitored security ID;
- legal issuer ID.

---

# 12. Stock-owner integration

If issuer identity and candidate 000660 evidence pass:

re-run the existing complete stock owner for SKHY using:

## Security-level inputs
unchanged SKHY:
- 4 sealed stock roles;
- price/current-price;
- anomaly/technical context;
- local thesis/security metadata.

## Issuer-level business inputs
qualified bridged OpenDART evidence only.

Do not introduce 000660 technical/price facts.

The existing observed-business union may accept the bridged evidence only if the union is semantically **issuer-business scoped**, not explicitly security-source-family scoped.

Audit this before changing it.

If current typed contract incorrectly assumes all business evidence must come from the monitored security's market/provider, make the smallest generic issuer/security distinction.

Do not lower union cardinality or quality thresholds.

---

# 13. Generic positive/negative tests

At minimum:

## Identity

1. two securities with same proven legal issuer -> bridge identity PASS;
2. same/similar names but different issuer IDs -> FAIL;
3. parent/subsidiary -> FAIL unless contract explicitly supports that relationship (REV6 does not);
4. missing issuer mapping -> FAIL;
5. conflicting issuer mappings -> FAIL;
6. wrong CIK/DART relation -> FAIL.

## Evidence scope

7. issuer revenue -> eligible if original field eligible;
8. issuer operating income -> only original eligibility preserved;
9. denied original field -> remains denied;
10. issuer event -> allowed only if issuer-level;
11. 000660 price -> blocked;
12. 000660 technical -> blocked;
13. KR investor flow -> blocked;
14. per-share/EPS -> blocked without ratio/basis owner;
15. PE/PB from KR price -> blocked.

## Provenance

16. bridge chain must be explicit;
17. source provider remains OpenDART;
18. filing/period/currency/occurrence preserved;
19. tampered issuer bridge -> fail;
20. missing bridge receipt -> fail.

No SKHY-specific branch in implementation.

---

# 14. Frozen cohort replay before any network

Run offline first.

Use:

- sealed REV5 SKHY security/source state;
- sealed 000660 complete packet/evidence;
- existing local identity master;
- existing source receipts.

Expected outcomes:

## A. legal issuer identity already proven offline
No network.

Proceed to bridge proof.

## B. identity not sufficiently proven
Generate/freeze bounded official identity-verification plan.

Do not activate bridge yet.

---

# 15. Identity-verification budget if needed

Before any network request produce:

`skhy-issuer-bridge-identity-plan.json`

Required:

- exact source;
- URL/endpoint;
- purpose;
- request hash;
- logical request count;
- theoretical max;
- retry budget.

Maximum logical requests:
`4`

Maximum theoretical attempts:
`12`

No request outside manifest.

Do not fetch financial market data.

Do not broaden into general research.

---

# 16. 21 complete subjects are invariance controls

All current complete subjects must remain complete for the same accepted evidence:

- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- SNDK
- TSLA
- TSM
- WULF
- WRD
- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280

Preserve:

- CPNG anomaly handling;
- TSM/WRD REV5 financial semantics;
- SNDK event authority;
- 000660 existing denials/qualified fields;
- 003690 insurance revenue semantics;
- 005930/047810 accepted evidence.

Any unrelated regression blocks PASS.

---

# 17. Completion outcomes

## Outcome A — issuer bridge closes SKHY

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV6_SKHY_ISSUER_BUSINESS_BRIDGE_PASS`

Require:

- exact same legal issuer proven;
- only issuer-level business evidence bridged;
- security-level isolation tests PASS;
- SKHY complete packet PASS;
- 22/22 complete;
- 21 controls invariant;
- full validation PASS;
- production side effects 0.

Then rebuild full network-free source prequalification.

If it passes:
- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`;
- generate bounded R2B current-source + 24-message instruction;
- do not execute R2B here.

## Outcome B — identity not proven

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV6_SKHY_ISSUER_IDENTITY_UNPROVEN`

SKHY remains blocked.

Do not substitute 000660.

Return exact missing official identity relation.

## Outcome C — same issuer proven but business bridge incompatible

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV6_ISSUER_EVIDENCE_CONTRACT_GAP`

Return exact typed owner/schema constraint.

Do not weaken source quality.

## Outcome D — same issuer proven but 000660 has no usable issuer-level evidence

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV6_NO_ELIGIBLE_ISSUER_BUSINESS_EVIDENCE`

Preserve original denials.

---

# 18. No automatic coverage-policy weakening

REV6 does not authorize:

- dropping SKHY;
- allowing empty observed-business union;
- treating thesis as observed evidence;
- broadening event search;
- adding a third SEC coverage window;
- using generic “no event” as business evidence;
- lowering financial quality.

If REV6 cannot establish the issuer bridge, a later explicit product decision is required.

---

# 19. Safety / network

Required zero:

- SEC financial discovery/window expansion;
- SEC market data;
- OpenDART financial acquisition;
- OHLCV;
- Alpha Vantage;
- Massive;
- model;
- Market/Core/A/B;
- renderer;
- Telegram;
- recipient intent;
- production DB writes;
- scheduler mutation;
- broker;
- deploy;
- main merge/push/restart.

Allowed only if necessary:
- max 4 official identity/document verification requests from the frozen REV6 identity plan.

No model or message generation.

---

# 20. Validation

Required:

- issuer/security identity bridge tests;
- same-name/different-issuer negative;
- parent/subsidiary negative;
- evidence-scope tests;
- per-share/valuation isolation tests;
- original-field eligibility preservation;
- provenance-chain tests;
- SKHY complete owner replay;
- 21-control invariance;
- prior REV2/REV3/REV4/REV5 regressions;
- full pytest;
- Ruff;
- `git diff --check`;
- Investment Knowledge;
- Chart Knowledge;
- disabled unified entrypoint smoke;
- secret scan;
- no new unexplained skip/xfail.

No thresholds/prompts/investment policy changes.

---

# 21. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- REV5 result identity/SHA receipt
- repository identities
- changed-file inventory

## Identity
- SKHY security identity matrix
- 000660 security identity matrix
- legal issuer crosswalk evidence
- conflict/negative audit
- identity-verification plan + receipts if executed

## Bridge
- generic issuer-business bridge contract
- evidence-scope allow/deny matrix
- security/per-share isolation matrix
- provenance-chain schema
- original 000660 eligible/denied field matrix
- bridged SKHY business evidence matrix

## Cohort
- SKHY before/after packet
- 21-control invariance
- full 22 matrix/hashes
- exact remaining blockers if any
- network-free prequalification if 22/22
- R2B next instruction + SHA only if permitted

## Safety
- execution counters
- config/env/scheduler before-after
- validation logs
- secret scan
- bundle manifest.

---

# 22. Final principle

Financial statements describe the legal issuer, not a particular quote feed.

If SKHY and 000660 are proven to represent securities of the same legal issuer, issuer-level business evidence may be shareable **without** sharing security-level prices, technicals, flows, per-share values or valuation denominators.

If the legal-issuer bridge cannot be proven, SKHY remains honestly blocked.
