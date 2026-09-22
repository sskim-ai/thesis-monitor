# Thesis Monitor — M12DS-R6 Market/Message Information Coverage Restoration + Night D/W/M Reproof

**Suggested work-instruction filename:**  
`20260922-m12ds-r6-market-message-information-coverage-restoration-night-dwm-reproof.md`

**Suggested result bundle:**  
`thesis-monitor-20260922-m12ds-r6-market-message-information-coverage-restoration-night-dwm-reproof-report.zip`

**Required human-review bundle:**  
`m12ds-r6-rendered-message-review.zip` + `.sha256`

**Task ID:** `M12DS-R6-20260922`

---

## 0. Objective

M12DS-R5-R2 is fully integrated.

Current local main and origin/main:

`2097645892e30d84aba435416f98e7f9545a87fa`

Candidate and main remote CI both passed, clean-clone/full validation passed, and the
accepted R4-R4 24 messages/night-futures replay stayed exact.

The user then reviewed the actual message content and identified a genuine information
coverage regression:

1. US market message no longer shows the previously expected major-index block;
2. WTI is absent;
3. US Treasury 3Y/5Y/10Y/30Y yields are absent;
4. US/KR explicit sector `TOP +3 / BOTTOM -3` blocks are absent;
5. stock messages no longer explicitly show technical support and resistance;
6. KRX night weekly data exists but is rendered as `자료 부족`;
7. KRX night monthly history is genuinely under-collected and must be backfilled.

These are now explicit user requirements, not optional polish.

R6 restores the information surface **without changing the accepted investment judgment
policy**.

R6 is a fresh production-equivalent message proof.

**Do not merge main in R6.**
Return exact messages for human review first.

After human approval, integrate R6 with a separate bounded main task and then proceed to
M12DT onboarding.

---

## 1. Frozen main baseline

Use `m12ds-r6-baseline.json`.

Main/origin-main:

`2097645892e30d84aba435416f98e7f9545a87fa`

Tree:

`436e41a4fb718d5be5dfda85a9423b555e1deb23`

R5-R2 full-success terminal:

`M12DS_R5_R2_CI_PORTABLE_MAIN_INTEGRATED_POST_MERGE_PASS`

Accepted 24-message combined SHA:

`e31d7f40576981c1f25df662f0865e1eb58e97cdb3921f9ba42230d6ad8c026e`

Branch from the exact current main.

Do not import the old private R4 history.

---

## 2. Strict semantic boundary

R6 may change:

- source date/freshness normalization needed to recover already-approved market facts;
- official night-history collection/aggregation;
- deterministic market factual rendering;
- deterministic sector ranking rendering;
- stock technical support/resistance rendering;
- price-as-of presentation;
- wording consistency;
- tests/docs required for these changes.

R6 must NOT change:

- Core investment-thesis policy;
- Pass A archetype/valuation policy;
- Pass B Overall/New Buyer/Holder semantics;
- DirectionalBalance thresholds;
- source-use authority unrelated to the requested market/message facts;
- fundamental entry valuation method;
- security/issuer separation.

If judgment semantics must change, stop:

`M12DS_R6_JUDGMENT_POLICY_SCOPE_EXPANSION_REQUIRES_CHAT`

---

# Workstream A — US market factual coverage

## 3. Inventory the previous/current US factual contract

Before editing, identify the canonical production owners for:

- major US indices;
- WTI;
- Treasury 3Y;
- Treasury 5Y;
- Treasury 10Y;
- Treasury 30Y;
- existing 10Y breakeven;
- US sectors.

Document:
- provider;
- source series/instrument;
- timestamp/date semantics;
- current suppression reason;
- renderer owner.

Do not invent a new provider if the existing approved source can satisfy the field.

---

## 4. US exchange session-date normalization

A US price/index observation must be assigned to the actual exchange-local trading session.

Do not use KST/host collection date as the session date.

Required controls around:
- ET session close;
- KST date rollover;
- weekends;
- US market holidays;
- pre/post-midnight UTC timestamp conversions.

An observation collected on 2026-09-22 KST that represents the 2026-09-21 US regular
session must own session date `2026-09-21`.

Do not simply allow a "future" date through the gate.

---

## 5. Provider-specific daily macro publication freshness

WTI and Treasury FRED-style daily series do not necessarily publish on the same host date.

Replace any unconditional "must equal current/latest market session date" requirement with
a provider/series expected-publication-date owner.

For each series determine:

- source cadence;
- expected last publication date at execution cutoff;
- weekend/holiday handling;
- provider publication lag;
- latest observed date.

Eligible only when latest observed date matches the provider-specific expected available
publication date.

If the provider is actually behind its expected publication:
- mark unavailable/stale;
- do not reuse an older value as current.

No arbitrary `N days stale is okay` constant.

### Required user-facing US macro fields

When eligible:
- WTI;
- Treasury 3Y;
- Treasury 5Y;
- Treasury 10Y;
- Treasury 30Y.

The existing 10Y breakeven may remain as an additional field.

---

## 6. US major-index block

Restore the existing canonical major-index user-facing block.

Do not assume proxies if a different canonical cash-index owner already exists.

At minimum audit the current packet's SPY / QQQ / IWM rows if they are the production
canonical index proxies.

For every rendered index:
- name;
- completed-session date;
- close/level or existing canonical value;
- daily return.

Every number must pass the existing typed market numeric provenance contract.

If one index is unavailable:
- show the available rows;
- explicitly mark only the unavailable row as unavailable when useful;
- do not suppress the entire market factual block.

---

# Workstream B — deterministic sector TOP3 / BOTTOM3

## 7. US sectors

From the canonical eligible US sector universe for the same completed session:

render:
- 상승 TOP3;
- 하락 TOP3;

with exact numeric returns.

Ranking is deterministic, not model generated.

Require:
- same session date;
- same return definition;
- eligible source;
- numeric provenance;
- stable canonical tie-break.

If fewer than three eligible sectors exist:
- render available count and explicit insufficiency;
- do not pull stale sectors from another session.

---

## 8. KR sectors

Restore explicit KR sector TOP3/BOTTOM3 while preserving venue/taxonomy ownership.

Do not combine KOSPI and KOSDAQ sector taxonomies unless an existing canonical owner
explicitly defines a comparable cross-market universe.

Preferred:
- restore the historical production contract if one exists;
- otherwise render KOSPI sector TOP3/BOTTOM3 and KOSDAQ sector TOP3/BOTTOM3 separately.

Use deterministic same-session returns.

Keep existing AI narrative interpretation as a separate section; the factual rankings must
not depend on model wording.

---

# Workstream C — stock support / resistance

## 9. Restore explicit technical levels

The internal deterministic price structure already owns:

- `active_support`
- `active_resistance`

Restore user-visible technical blocks.

Example semantic shape:

`기술적 지지: <range>`
`기술적 저항: <range>`

Only render each side when that side is valid.

If unresolved:
- omit the numeric value or say `미확정` according to existing message style;
- do not fabricate.

---

## 10. Keep three price concepts separate

Do not collapse:

### Fundamental entry range
Business/valuation fair-entry method.

### Technical support/resistance
Observed deterministic price structure.

### Tactical watch zone
Practical wait/recheck zone.

All may coexist.

The message must never call technical support/resistance or tactical zone `적정가치`.

Add tests ensuring no field is substituted for another.

---

## 11. Price as-of completion

Close carried:

`P2-PRICE-ASOF-PARTIAL`

For every stock message, if an owned quote/session timestamp exists, render a concise
price-data basis/as-of line.

This previously affected at least:
- CPNG
- MU
- SKHY
- WRD

Do not invent as-of when source ownership is absent.

---

# Workstream D — KRX night D/W/M

## 12. Authority and contract identity

Machine authority remains:

`OFFICIAL_KRX_NIGHT`

Products:
- KOSPI200
- KOSDAQ150

Use the selected current/near contract from the existing production owner.

Daily/weekly/monthly aggregation must not mix different contract codes unless an explicit
continuous-contract roll owner already exists.

No new roll-splicing logic solely for display.

Kiwoom remains cross-check only.

---

## 13. Daily

Keep the currently accepted daily behavior:

- final night session;
- O/H/L/C;
- regular-session same-contract baseline;
- point/percent change;
- reference date;
- maturity.

No regression.

---

## 14. Weekly in-progress rendering

Current weekly data can be `IN_PROGRESS` and still have valid OHLC.

Build/render for the current calendar week through the night reference date:

- contract;
- week start/end identity;
- included official night-session dates;
- expected session dates through the current reference date;
- future expected dates separately;
- O/H/L/C;
- included / elapsed-expected session count;
- quality/status.

If a valid weekly return baseline exists, show it.

If not:
- show OHLC and progress;
- render `주간 등락률: 미확정` or equivalent;
- do NOT replace the whole weekly block with `자료 부족`.

No future date may be counted as missing.

---

## 15. Monthly official-history backfill

Backfill official night history for the **same selected contract** from calendar-month
start through the current night reference date.

Build an expected night-session calendar that excludes:
- weekends;
- exchange holidays;
- known no-session dates.

For each elapsed expected session:
- fetch/use official KRX history;
- record row/finality;
- exact missing reason when absent.

Future sessions are not missing.

Aggregate:
- O/H/L/C;
- included dates;
- expected elapsed dates;
- missing elapsed dates;
- status/quality.

If all elapsed expected rows are present:
- monthly IN_PROGRESS is fully covered through reference date.

If some elapsed rows are missing:
- render partial status and exact coverage;
- do not silently treat as complete.

If return baseline is unresolved:
- render OHLC/progress and say return unresolved;
- do not collapse the whole month block to `자료 부족`.

---

## 16. D/W/M end-to-end lineage

For each product prove:

`official raw night rows`
→ `contract/date/session ownership`
→ `daily aggregate`
→ `weekly aggregate`
→ `monthly aggregate`
→ `typed message facts`
→ `production renderer`
→ `exact captured substrings`.

Include:
- row hashes;
- contract;
- dates;
- expected-session calendar;
- formulas;
- final message substrings.

---

# Workstream E — wording cleanup

## 17. Wording consistency

Close carried:

`P2-WORDING-CONSISTENCY`

Only editorial consistency:
- Korean sentence endings;
- repeated caution wording;
- headings;
- spacing.

Do not alter:
- labels;
- scores;
- evidence meaning;
- numeric values;
- stance severity.

Any wording change with semantic effect is out of scope.

---

# Validation

## 18. Offline/frozen tests before live run

Required tests include:

### US date/freshness
- ET/KST session mapping;
- weekend/holiday;
- FRED expected-publication date;
- truly stale data rejected;
- publication-lag current data accepted.

### Sector rankings
- exact top/bottom ranking;
- ties;
- missing rows;
- session mismatch rejected;
- no model ownership.

### Stock technical
- support + resistance both resolved;
- support only;
- resistance only;
- neither;
- no substitution into tactical/fundamental fields.

### Night D/W/M
- week IN_PROGRESS one session;
- multi-session week;
- future session not missing;
- current-month full elapsed coverage;
- missing historical elapsed row;
- holidays;
- contract mismatch rejected;
- no cross-contract aggregation;
- no Kiwoom authority.

### Presentation
- price as-of;
- wording-only changes preserve structured decisions.

Run full pytest / Ruff / diff-check before fresh inference.

---

## 19. Fresh current production-equivalent smoke

After implementation freeze start a NEW fresh current generation.

Collect:
- US/KR market;
- WTI / Treasury series;
- sectors;
- official KRX night history;
- all active monitored stock source/price data.

Run the current accepted production policy:

- Market 2;
- Core;
- A;
- B;

using the existing bounded one-transient-retry policy.

No target fitting.

No source fallback invented solely to make a message complete.

---

## 20. Exact final message capture

Use actual production renderer and final outbound capture sink.

Expected if population remains 22:

- MARKET_US
- MARKET_KR
- 22 stock messages
- total 24

Production sends/intents/writes remain 0.

Return exact review bundle:

`m12ds-r6-rendered-message-review.zip`

---

## 21. Mandatory human-review checklist

### MARKET_US must visibly include when eligible
- major indices;
- WTI;
- Treasury 3Y/5Y/10Y/30Y;
- sector +TOP3 / -TOP3;
- market interpretation;
- KOSPI200/KOSDAQ150 night D/W/M next-KR-session context.

### MARKET_KR
- existing index/breadth/size/flow sections;
- explicit sector +TOP3 / -TOP3 according to owned venue taxonomy;
- no stale/incorrect night duplication.

### Each stock
- Overall/New Buyer/Holder;
- fundamental range if valid;
- technical support if valid;
- technical resistance if valid;
- tactical watch zone if valid;
- price as-of when owned.

No internal refs/enums/hashes.

---

## 22. Acceptance

Full success terminal:

`M12DS_R6_MESSAGE_INFORMATION_COVERAGE_PASS_READY_FOR_HUMAN_REVIEW`

Requires:
- fresh source/inference complete;
- exact 24 captures;
- restored fields verified;
- night D/W/M E2E PASS;
- full tests/lint PASS;
- production mutations 0;
- no new P0/P1.

Main merge/push/deploy remain 0 in R6.

---

## 23. Failure terminals

- `M12DS_R6_US_MARKET_COVERAGE_FAILED`
- `M12DS_R6_SECTOR_RANKING_FAILED`
- `M12DS_R6_STOCK_TECHNICAL_RENDER_FAILED`
- `M12DS_R6_NIGHT_HISTORY_OR_DWM_FAILED`
- `M12DS_R6_CURRENT_INFERENCE_INCOMPLETE`
- `M12DS_R6_MESSAGE_CAPTURE_INCOMPLETE`
- `M12DS_R6_MESSAGE_QUALITY_FAILED`
- `M12DS_R6_LOCAL_VALIDATION_FAILED`
- `M12DS_R6_RUNTIME_OR_SECURITY_STOP`
- `M12DS_R6_JUDGMENT_POLICY_SCOPE_EXPANSION_REQUIRES_CHAT`

Return exact blocker; no silent data substitution.

---

## 24. After human approval

Perform a bounded R6 main-integration/CI task.

Only after that completes proceed to:

`M12DT_NEW_TICKER_ONBOARDING_GATE`

Lifecycle:

`REGISTERED_PENDING`
→ `SOURCE_AND_CONTRACT_READY`
→ `INITIALIZED`
→ `MONITORING_ACTIVE`.

