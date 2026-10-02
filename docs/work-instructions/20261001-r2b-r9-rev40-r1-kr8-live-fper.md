# Thesis Monitor — R2B-R9-REV40-R1
## KR8-Only KIS Current FY1 fPER Live Integration Proof
### Archive-Backed GC → Fresh KR8 + KR Market Context Only
### Fresh KIS FY1 EPS + Unadjusted Completed-Session Close + Exact-Security Corporate-Action Guard
### Current FY1 fPER → KR8 Core/A/B → Exact 8 Korean Stock Messages
### US14 / US Market / US Models / US Messages = 0

**REV40-R1 supersedes REV40. Execute only REV40-R1.**

The prior REV40 scope was unnecessarily broad.

The newly completed source capability is specifically:

> Korean FY1 forward valuation using KIS.

US forward valuation is **not** complete:
- no exact free US FY1/NTM EPS owner;
- Finnhub generic `forwardPE` remains horizon-ambiguous;
- premium EPS-estimate route remains unavailable;
- ADR forward valuation remains unresolved.

Therefore REV40-R1 must prove only the Korean integration.

Do not recollect or rerun US14 merely because the common pipeline can do so.

---

# 0. Newest SoT

Adopt REV39 as newest Korean-forward-valuation SoT.

REV39 result ZIP:

`thesis-monitor-20261001-r2b-r9-rev39-kis-date-replay-report.zip`

SHA-256:

`9a7b7931561ba820aeb5d964c8337137ee8d70f83c724a909e54108136729639`

Terminal:

`R2B_R9_REV39_DATE_PARSER_REPLAY_CURRENT_FY1_FPER_PASS_READY_FOR_FULL_FRESH_INTEGRATION`

REV39 proved offline:

- FY1 EPS qualified for 7/8 KR securities;
- current-price FY1 fPER qualified for all 7 FY1-EPS-eligible securities;
- 003690:
  `UNAVAILABLE_EPS`;
- exact-security corporate-action guard;
- slash-date/interval parser;
- provider calls 0;
- models 0.

Preserve all accepted REV39 contracts.

---

# 1. Exact task scope

Fresh/current scope:

## Required stock subjects — KR8 only
- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280.

## Optional/supporting Market source
Acquire only the Korean Market/context data required by the existing KR8 model-input contract.

This may include:
- KOSPI/KOSDAQ;
- KR sectors/breadth/flow where already configured;
- USD/KRW;
- KOSPI200 night typed state where current policy requires it.

Do not generate a separate KR Market user message unless the current KR8 proof harness strictly requires the Market
model output to construct stock inputs.

If Market model execution is required by the frozen architecture:
run **KR Market only**.

---

# 2. Explicit zero scope

REV40-R1 must not acquire, execute or render:

- US14 fresh source;
- US Market fresh source;
- US macro source solely for US Market;
- US Market model;
- US Core;
- US Pass A;
- US Pass B;
- US stock messages;
- MARKET_US message.

Required counters:

`US_PROVIDER_CALLS_FOR_US_ONLY_ROLES = 0`

`US_MODEL_CALLS = 0`

`US_MESSAGES = 0`

Do not treat common US source code being present in the repository as permission to execute it.

---

# 3. Why KR-only proof is sufficient

The changed/new capability affects only:

- KIS Korean forecast EPS;
- KIS Korean forward PER snapshot;
- Korean unadjusted completed-session close;
- Korean KSD corporate-action guard;
- derived Korean current FY1 fPER;
- KR NewBuyer/Holder valuation context;
- KR final valuation renderer.

US valuation/source/model semantics are unchanged.

A KR8 proof is therefore sufficient to establish the new capability without spending:
- US provider quota;
- model calls;
- disk;
- execution time.

US fPER will be handled in a separate future source task.

---

# 4. Preserve three Korean valuation families

For each KR security keep independently:

## Current PER/PBR
Existing Kiwoom current provider snapshot.

## KIS research FY1 PER
Secondary dated research-snapshot metric when available.

Label:
`KIS 리서치 fPER(FY1)`

## Current-price FY1 fPER
Primary actionable forward metric:

`fresh KIS unadjusted completed-session close / fresh qualified KIS FY1 EPS`.

Label:
`현재가 기준 fPER(FY1)`.

Do not collapse the two forward PERs.

---

# 5. Authority boundary

All forward valuation metrics:

Allowed:
- Valuation section;
- NewBuyer valuation context;
- Holder valuation context;
- valuation-specific caution/confidence.

Forbidden:
- Overall direction;
- Fundamental Core direction;
- Pass-A business direction;
- supporting/contradicting directional refs.

`overall_direction_use=false`.

---

# 6. Storage GC

REV39 free space is below the standing broad fresh proof threshold.

Before fresh KR8 acquisition:

verify immutable archives/fixtures, then run archive-backed GC.

Hard precollection threshold for this KR-only run:

`>= 10 GiB`

Preferred:

`>= 12 GiB`

This is lower than the previous all22 12-GiB hard floor because:
- no US14 acquisition;
- no US model/output corpus;
- no 24-message proof.

However, if the existing standing repository controller enforces 12 GiB globally, obey the stricter controller.

Never weaken an existing hard runtime guard merely because this instruction allows 10 GiB.

Record:
- before/after free bytes;
- deleted/skipped paths;
- protected paths;
- fixture identities.

No protected evidence deletion.

---

# 7. Fresh KR generation

Start a new Korean generation after GC.

Do not reuse REV36–39 current values.

Freshly reacquire for KR8:

- business/financial source owners;
- selected financial owner;
- events;
- quality;
- current price/OHLCV/technical;
- flow/positioning;
- current PER/PBR;
- KIS estimate-perform;
- exact FY1 EPS state;
- KIS provider FY1 PER state;
- KIS unadjusted completed-session close where FY1 EPS qualifies;
- exact-security corporate-action guard;
- current-price FY1 fPER.

No US stock source calls.

---

# 8. Fresh KIS estimate-perform

For each KR8:

use official:

`/uapi/domestic-stock/v1/quotations/estimate-perform`

with exact six-digit security.

Use accepted generic semantics:

- full layout:
  row1 EPS / row3 PER;
- shortened layout:
  structural EPS/growth owner;
- output3 scale:
  raw / 10;
- exact fiscal owner;
- exact FY1 selection;
- KIS house-research semantics.

No hardcoded numeric values.

No-estimate:
typed unavailable, not source failure.

---

# 9. Fresh completed-session unadjusted close

For every fresh FY1-EPS-qualified KR subject:

use KIS daily-price with:

`FID_ORG_ADJ_PRC=0`

and choose the exact latest completed KR session.

No intraday row.
No adjusted close.

Create fresh `CurrentFY1PriceReceipt`.

---

# 10. Fresh exact-security corporate-action guard

For every FY1-EPS-qualified KR subject:

query exact six-digit security across:

- merger_split
- rev_split
- bonus_issue
- paidin_capin_gb1
- paidin_capin_gb2
- cap_dcrs.

Use accepted:

`BOUNDED_EXACT_SECURITY_SHARE_UNIT_GUARD_V1`

with the accepted wide guard envelope.

Use REV39 parser support including:
- YYYYMMDD
- YYYY-MM-DD
- YYYY.MM.DD
- YYYY/MM/DD
- supported full-year intervals.

No all-security query topology.

---

# 11. Fresh current FY1 fPER

When:

- FY1 EPS > 0;
- exact KIS unadjusted completed-session close exists;
- exact same security;
- corporate-action guard qualifies;

compute:

`CurrentFY1Fper = close / FY1 EPS`

with Decimal.

Store:
- exact numerator;
- denominator;
- exact quotient;
- display rounded to 2 decimals;
- estimate date;
- price date;
- guard receipt.

If EPS <=0:
`N/M`.

If EPS unavailable:
typed unavailable.

---

# 12. KR8 valuation matrix

For all KR8 independently record:

- current PER;
- current PBR;
- FY1 EPS;
- FY1 estimate date;
- KIS provider FY1 PER;
- current-price FY1 fPER;
- exact unavailable reasons.

No numeric coverage target.

Do not require 003690 to have a number merely because the other seven did historically.

---

# 13. KR supporting Market context only

If the KR stock model contract requires current market context:

freshly build only:

`MARKET_KR`

source/model input.

No US Market.

If Market model is required:
maximum logical Market calls:

`1`

KR only.

If current architecture permits deterministic KR market context without Market model for stock stages:
do not introduce a new architecture change; use the existing accepted path.

---

# 14. Source closure

Require:

- KR stock source:
  `8/8`
- KR forward valuation states:
  `8/8`
- KR Market/context:
  complete according to current KR contract.

Do not require US source closure.

Do not create a fake all22 PASS marker.

The result must explicitly identify scope:

`KR8_ONLY`.

---

# 15. Replay twice

Freeze the KR source corpus.

Disable network.

Replay twice for:

- KR8 source packets;
- selected financial owners;
- events/quality;
- current price/technical;
- current PER/PBR;
- KIS FY1 EPS;
- provider FY1 PER;
- unadjusted close;
- corporate-action guard;
- current FY1 fPER;
- KR Market/context;
- KR authority graph/code-owner inventory.

Exact semantic equality required.

No US replay requirement beyond normal global unit/regression tests.

---

# 16. Blind source-only KR artifact

Before any model call, create:

`r2b-r9-rev40-r1-kr8-source-only-review.zip`

and SHA.

Include:
- KR Market/context facts used by KR stocks;
- KR8 source-only evidence;
- business/financial/events/quality;
- current price/technical/flow;
- current PER/PBR;
- FY1 EPS;
- current fPER(FY1);
- KIS provider FY1 PER.

Exclude:
- KR model decisions;
- Core/A/B outputs;
- final stock messages;
- prior human judgments.

Seal before first model call.

This allows a KR-only blind review if desired.

---

# 17. Model visibility

Forward valuation must be:

## Core
absent.

## Pass A
absent.

## Pass B
present only in typed valuation context.

Require deterministic visibility audit for KR8 before model calls.

No model call if valuation leaks to direction surfaces.

---

# 18. KR8 model execution only

After all source/replay/visibility/disk gates:

run only Korean subjects.

Required:

- Core:
  `8/8`
- A:
  `8/8`
- B:
  `8/8`.

If the architecture requires the KR Market model:
- MARKET_KR:
  `1/1`.

Do not invoke US batches.

No selective result-driven reruns.
No fallback/judge model.
Transport retry only under existing frozen policy.

---

# 19. Final output scope

Capture exact sender-boundary payloads for:

- KR8 stock messages only.

Required stock messages:

`8/8`

Do not produce:
- US14 messages;
- MARKET_US.

A KR Market message is optional only if the existing proof harness necessarily generates it as part of the KR stock run;
if generated, keep it as a separate supporting artifact and do not redefine the success count.

Primary success count:

`KR_STOCK_MESSAGES = 8/8`.

---

# 20. KR Valuation renderer

For each KR stock:

render independently where qualified:

- current PER
- current PBR
- `현재가 기준 fPER(FY1)`
- `KIS 리서치 fPER(FY1)` with estimate date
- `FY1 EPS` with KIS Research estimate date.

Never label KIS:
- consensus;
- NTM;
- 12M forward.

Do not show an unavailable metric as zero.

---

# 21. Renderer scope limitation

Do not perform the broader detailed-message renderer restoration here.

Still separate:
- English `Reported ...` prose;
- missing thesis/risk/market-expectation sections;
- static evidence-maturity presentation;
- other detailed-format backlog.

REV40-R1 only proves Korean forward valuation integration and its valuation lines.

---

# 22. External transmission approval

The user explicitly approves for REV40-R1:

## Provider reads
Existing Korean source providers and KIS routes necessary for KR8 + KR supporting Market context.

No US-only provider reads.

## Model transmission
Existing official:
`GPT-5.6 Sol / xhigh`

for:
- KR Market if required;
- KR8 Core/A/B only.

No US models.

## Result upload
After secret scan:
- result ZIP/SHA;
- KR8 source-only ZIP/SHA;
- KR8 human-review ZIP/SHA

may be uploaded to the existing iCloud Drive / Thesis Monitor folder.

---

# 23. Delivery / production effects

`delivery_disabled=true`

Hard zero:
- Telegram recipient sends;
- production DB/warning writes;
- scheduler mutation;
- broker/trading;
- deploy;
- main merge;
- remote push;
- restart.

---

# 24. Human-review artifact

Create:

`r2b-r9-rev40-r1-kr8-human-review.zip`

+ SHA.

Include:
- exact 8 KR stock sender payloads;
- message hashes;
- KR valuation matrix;
- valuation visibility/use audit;
- KR source/replay identities;
- model ledger;
- production isolation.

No US messages.

---

# 25. Validation

Before live model proof require:

- REV39 forward owner regressions;
- KR acquisition-plan tests;
- no-US-execution tests;
- KR8 exact source closure;
- replay twice;
- valuation visibility/isolation;
- current PER/PBR regression;
- full pytest;
- Ruff;
- diff;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

Full repository suite remains required even though live execution scope is KR-only.

---

# 26. Success terminal

Use only:

`R2B_R9_REV40_R1_KR8_FULL_FRESH_CURRENT_FY1_FPER_8_MESSAGE_PASS_READY_FOR_REVIEW`

Require:

1. REV39 integrity PASS;
2. GC/headroom PASS;
3. fresh KR generation;
4. US-only provider calls 0;
5. US models 0;
6. US messages 0;
7. KR source 8/8;
8. KR forward valuation typed states 8/8;
9. fresh FY1 EPS owner PASS;
10. fresh unadjusted close owner PASS for eligible subjects;
11. fresh corporate-action guard PASS/typed denial;
12. fresh current FY1 fPER states 8/8;
13. current PER/PBR preserved;
14. provider FY1 PER separate;
15. KR source replay twice PASS;
16. KR valuation absent Core/A;
17. KR valuation visible B;
18. KR source-only ZIP sealed before models;
19. KR Core 8/8;
20. KR A 8/8;
21. KR B 8/8;
22. exact KR stock messages 8/8;
23. valuation renderer distinct/qualified;
24. Telegram 0;
25. production mutations 0;
26. secret scan PASS;
27. result/source-only/human-review artifacts generated.

---

# 27. Honest stop terminals

- `R2B_R9_REV40_R1_STORAGE_GC_GAP`
- `R2B_R9_REV40_R1_KR_SOURCE_PARTIAL`
- `R2B_R9_REV40_R1_KIS_FY1_GAP`
- `R2B_R9_REV40_R1_KIS_PRICE_GAP`
- `R2B_R9_REV40_R1_CORPORATE_ACTION_GAP`
- `R2B_R9_REV40_R1_CURRENT_FY1_FPER_GAP`
- `R2B_R9_REV40_R1_VALUATION_VISIBILITY_GAP`
- `R2B_R9_REV40_R1_VALUATION_DIRECTION_LEAK`
- `R2B_R9_REV40_R1_REPLAY_GAP`
- `R2B_R9_REV40_R1_SOURCE_ONLY_SEAL_GAP`
- exact KR model/render failure.

Do not expand to US to compensate for a KR failure.

---

# 28. Required result bundle

Return immutable ZIP + SHA plus standalone:

- KR8 source-only ZIP + SHA
- KR8 human-review ZIP + SHA.

At minimum include:

- REPORT.md / summary.json
- scope receipt:
  `KR8_ONLY`
- REV39 identity
- storage GC receipts
- KR provider plan/counters
- explicit US provider/model/message zero receipts
- KR8 source matrix
- KR valuation matrix
- KIS FY1 raw/receipts
- unadjusted close receipts
- action guard receipts
- current fPER receipts
- replay twice
- valuation visibility audit
- KR model ledger
- exact 8 messages
- secret scan
- production isolation.

---

# 29. Next work after PASS

After REV40-R1:

1. independently review the KR8 source-only artifact if another blind comparison is desired;
2. inspect how current FY1 fPER changed NewBuyer/Holder conclusions;
3. do **not** treat the Korean proof as evidence that US fPER is solved;
4. start a separate US-free-forward-EPS discovery task for:
   - MU
   - TSM
   - GOOGL
   - other US14 subjects;
5. only after a US exact FY1/NTM owner exists should a combined US+KR all22 proof be run.

---

# 30. Final principle

The new source capability is Korean.

Therefore the correct proof population is Korean.

Do not pay the cost and risk of a US full-fresh/model run while US forward valuation remains unresolved and unchanged.

Prove KIS FY1 EPS/current fPER on KR8 first.

Then solve US forward EPS separately.

Only after both markets have their intended forward-valuation sources should the project return to a combined all22
end-to-end proof.
