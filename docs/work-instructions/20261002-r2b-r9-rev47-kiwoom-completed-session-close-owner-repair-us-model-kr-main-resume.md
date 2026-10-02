# Thesis Monitor — R2B-R9-REV47
## Kiwoom US Completed-Session Close Authority Repair
## → Reuse REV46 Fresh Corpus, No Broad US Recollection
## → US14 Source Seal / Models / Messages
## → Fresh KR8 2026-10-02
## → Main Integration Only After Both PASS

---

# 0. Why REV47 exists

REV46 successfully closed the US14 scoped source/model/capture architecture and then collected a fresh US14 corpus.

The fresh corpus exposed a separate completed-session price-authority problem:

`usa06012` latest-row `cur_prc` cannot be treated as the completed regular-session close merely because the row `dt`
equals the latest completed session.

REV46 resume1 correctly failed closed before any model call.

REV47 must repair the source contract first, then resume from the already-collected fresh corpus.

Do **not** recollect the entire US source generation.

---

# 1. Verify both REV46 immutable reports

## 1.1 Initial REV46 pre-dispatch stop

ZIP:

`thesis-monitor-20261002-r2b-r9-rev46-us14-scoped-source-model-fresh-resume-report.zip`

Expected SHA-256:

`c59a86a583f46b375749a2df3d57b8e2f1946c5f6b3f6c9ffae3481ea8ce1cc0`

Expected:
- ZIP members: `83`
- manifest payload: `82`
- CRC PASS
- manifest missing/hash/size/extra: `0/0/0/0`
- terminal: `R2B_R9_REV46_US_SOURCE_GAP`
- reason: malformed `.env` comment syntax
- provider/model/message calls: `0/0/0`.

## 1.2 REV46 resume1 fresh source result

ZIP:

`thesis-monitor-20261002-r2b-r9-rev46-resume1-env-comment-correction-fresh-proof-report.zip`

Expected SHA-256:

`7af591881e28f9df272c0583b9624a92ac1e5c3da46985a77748a613117f7219`

Expected:
- ZIP members: `5470`
- manifest payload: `5469`
- CRC PASS
- manifest missing/hash/size/extra: `0/0/0/0`
- terminal: `R2B_R9_REV46_US_SOURCE_GAP`
- stop stage: `US_WHOLE_SOURCE_REPLAY`
- fresh generation:
  `rev46-us14-resume1-20261002T064847Z`
- implementation/final:
  `075d9aa559b3dd5899745164bedff4db2914f770`
- provider attempts: `392`
- retries: `0`
- model calls: `0`
- messages: `0`
- Telegram: `0`
- full pytest: `8036 / 0 failures / 63 skipped`
- focused: `276 passed`
- production isolation: PASS.

Do not alter either report.

---

# 2. Preserve the authorized `.env` correction

REV46 resume1 contains the user-authorized correction:

```text
two rows only:
"//" comment prefix -> "# "
changed bytes = 4
credential value bytes changed = 0
other env bytes changed = 0
file mode unchanged
Settings load = PASS
```

Expected resulting `.env` SHA-256:

`6ae4351daecaeb473c2cec89f8ec40af6f7c4f77e5b45604165d578655f1062e`

Do not modify `.env` again in REV47.

If this exact authorized state is not present:
stop and report drift.

---

# 3. Fresh corpus is valuable and must be reused

REV46 resume1 already spent:

```text
392 provider requests
```

with all provider requests PASS and zero retries.

Observed provider counts:

```text
Kiwoom            254
SEC EDGAR           65
Finnhub             28
Google News RSS     14
FRED                13
KRX night futures    9
OpenDART              5
EIA                   3
ECOS                  1
```

Do not repeat these calls merely because the completed-session price owner changes.

All non-price source evidence from this generation is eligible for immutable replay if its original freshness/date/identity
contract still passes.

REV47 is a source-owner repair + bounded price supplement, not a second broad full-fresh collection.

---

# 4. Root cause is broader than three out-of-range rows

REV46 surfaced explicit integrity failures for:

```text
CORZ
HUT
WRD
```

because latest target-row `cur_prc` fell outside the same row's regular OHLC high/low range.

Captured raw target rows:

```text
CORZ 2026-10-01:
  cur_prc = 16.5000
  high    = 16.4800
  low     = 15.5100

HUT 2026-10-01:
  cur_prc = 87.4200
  high    = 86.5550
  low     = 82.1001

WRD 2026-10-01:
  cur_prc = 5.1200
  high    = 5.3500
  low     = 5.1700
```

The existing `ohlcv-provider-integrity-v1` correctly rejected these rows.

However:

> a latest-row `cur_prc` being inside the historical high/low range is not sufficient evidence that it is the completed
> regular-session close.

Therefore REV47 must change the authority contract for **all US14**, not add three ticker-specific exceptions.

Do not clamp close into high/low.
Do not widen the high/low range.
Do not waive OHLC integrity.
Do not accept the other 11 latest `usa06012 cur_prc` values merely because they happened to fall inside the range.

---

# 5. `usa06012` role after REV47

`usa06012` remains useful for chart/history acquisition.

But its **latest row** must no longer own:

```text
COMPLETED_REGULAR_SESSION_CLOSE
```

for the target completed session.

Create an explicit state:

```text
LATEST_USA06012_CUR_PRC_NOT_COMPLETED_SESSION_CLOSE_AUTHORITY
```

for current-price ownership.

Historical rows strictly before the latest row may remain available under their existing historical chart contract if unchanged.

Do not globally invalidate Kiwoom charts.

---

# 6. Candidate authoritative route — Kiwoom `usa20590`

Qualify the official Kiwoom route:

```text
API ID: usa20590
API: 미국주식 일별주가
URL family: /api/us/mrkcond
```

Use official Kiwoom API documentation / official downloadable API specification as the semantic authority.

Required documented fields:

```text
dt
cur_prc
pred_pre
flu_rt
acc_trde_qty
open_pric
high_pric
low_pric
base_pric
```

Required request fields:

```text
stex_tp
stk_cd
base_dt
```

The route must support querying historical daily prices at an explicit `base_dt`.

Do not qualify from a third-party wrapper alone.

Third-party/reference sites may be used only as diagnostics, never as production authority.

---

# 7. New completed-session owner

Implement:

`kiwoom-us-completed-session-price-v2`

or an equivalent repository name.

For each US security require:

1. exact monitored canonical security;
2. exact Kiwoom exchange/security route;
3. `base_dt = target_completed_session`;
4. returned row `dt == target_completed_session`;
5. positive finite `cur_prc`;
6. internally valid:
   `low_pric <= cur_prc <= high_pric`;
7. internally valid open/high/low values;
8. exact USD/no FX conversion under the accepted US route;
9. same target XNYS completed-session calendar receipt;
10. no contradictory corporate-action event for raw-vs-adjusted use.

Owner output:

```text
price_role = COMPLETED_REGULAR_SESSION_CLOSE
price = usa20590.cur_prc
date = exact target session
basis = provider historical daily close
```

Do not call this "real-time current price".

---

# 8. Stage A — bounded live qualification controls

Before broad US14 supplement, query `usa20590` exactly once for these controls:

```text
CORZ
HUT
WRD
GOOGL
TSLA
```

These five calls are part of the eventual US14 total; never repeat them during Stage B.

Target:

`base_dt = 20261001`

For each control save raw response and exact request metadata.

Require:
- HTTP/API success;
- exact security route;
- target 2026-10-01 row;
- internally coherent OHLC;
- finite positive close;
- no current-session/overnight date contamination.

If the route cannot deterministically produce the completed 2026-10-01 daily row:
stop:

`R2B_R9_REV47_USA20590_COMPLETED_CLOSE_CONTRACT_GAP`

Do not fall back to `usa06012 cur_prc`.

---

# 9. Diagnostic cross-check, not authority

For controls only, it is permitted to compare the `usa20590` historical close to:

- target-row regular OHLC range in the already sealed `usa06012` response;
- `pred_pre` / prior-session close arithmetic where meaningful;
- an independent public historical-price source.

These are diagnostics.

The production owner is Kiwoom `usa20590` after its official field contract and live behavior qualify.

No cross-provider averaging.

---

# 10. Stage B — remaining US9 exactly once

If Stage A PASS:

query `usa20590` once for:

```text
CPNG
CRCL
IBM
MU
RXRX
SKHY
SNDK
TSM
WULF
```

Total new Kiwoom daily-price requests in REV47:

```text
target = 14
normal maximum = 14
```

No duplicate ticker calls.

Transport retry:
at most one only when no valid provider response was received.

Do not retry semantic failures.

---

# 11. Build a new immutable REV47 US source lineage

Do not mutate the REV46 resume1 raw corpus.

Create a new US source lineage:

```text
REV47 source =
  immutable REV46 resume1 fresh corpus
  +
  exact 14-ticker usa20590 completed-session supplement
```

Every inherited item must retain:
- original generation ID;
- original retrieval time;
- raw SHA;
- source role.

Every new close item must retain:
- REV47 supplement generation ID;
- request receipt;
- raw SHA.

Create a new whole-source seed over the complete declared lineage.

This is not "partial patching from stale history":
all inherited source evidence is fresh 2026-10-02 evidence for the same intended 2026-10-01 US completed-session proof and
is explicitly lineage-bound before any model call.

If any inherited role fails freshness at REV47 execution time:
recollect **only that expired role**, not the entire US corpus.

---

# 12. Close-only target price policy

For `price_and_positioning.price.current_price` and valuation/current-price roles:

use only:

`usa20590 target-session cur_prc`.

Do not require target-session `usa06012` close/high/low consistency to admit this close owner.

Keep chart integrity and completed-session close integrity as different contracts.

This avoids an unrelated chart-field anomaly suppressing a separately authoritative historical close.

---

# 13. Target-row technical consumer audit

Audit all consumers of the latest `usa06012` row.

No model input may silently consume its latest `cur_prc` as the 2026-10-01 completed close after REV47.

For close-based technicals:

- use `usa20590` target close for the target-session close point;
- use prior finalized chart rows for historical close series.

For any target-session OHLC/volume-based indicator:

- use `usa20590` target OHLC/volume if exact field/basis compatibility is proven;
- otherwise mark only that optional indicator unavailable.

Do not synthesize target volume/OHLC by mixing incompatible adjusted/raw fields.

---

# 14. Adjustment / corporate-action guard

`usa06012 adjusted_daily` and `usa20590` may have different adjustment roles.

Before using `usa20590` target OHLC in an adjusted technical series:

require the existing exact-security corporate-action guard to prove no target-boundary event requiring a transformation.

If an event exists:
- do not invent an adjustment factor;
- keep the raw completed-session close owner for price display/valuation if valid;
- suppress incompatible technical target-row transformation unless an exact factor owner exists.

---

# 15. Re-run all US14 owner diagnostics offline

After the 14 `usa20590` receipts:

replay all US14 stock owners.

Expected first question:

> Does replacing the completed-session price owner close the CORZ/HUT/WRD owner failures?

Do not assume yes.

If an `observed_business_union` blocker remains after price ownership is repaired:
diagnose it using the already-collected fresh SEC/news/financial/event corpus.

Do not recollect all 392 sources.

Repair only if:
- same-generation eligible evidence actually exists;
- the blocker is a bounded materializer/owner bug.

If no eligible evidence exists:
preserve typed unavailable and apply the existing rule for whether the packet is mandatory or optional.

Never fabricate a business observation.

---

# 16. Whole-source seal

US source may be sealed only when:

- US14 primary scope exact;
- declared SKHY auxiliary issuer dependency exact;
- no auxiliary KR valuation leakage;
- completed-session close v2 PASS for every mandatory price role;
- Finnhub provider-native valuation identity rules PASS/fail-closed per ticker;
- fPER(FY1) policy from REV45/46 unchanged;
- whole-source seed deterministic;
- source-only validator PASS.

Seal before models.

No provider calls afterward.

---

# 17. Finnhub FY1 policy remains unchanged

Do not reopen:

```text
forwardPE
→ provider-native fPER(FY1)
→ horizon authority = USER_AUTHORIZED_PRODUCT_POLICY
```

No implied EPS.

Existing valuation rules:

```text
peTTM       -> PER
pbQuarterly -> PBR
forwardPE   -> fPER(FY1)
```

for qualified direct-US securities only.

ADR/home-security mismatches remain fail-closed.

---

# 18. US models and messages

After US source seal:

run current production-equivalent US-only topology.

Expected:

```text
Market = 1 logical role
Core = 5 batches
A = 5 batches
B = 5 batches
```

Use current exact batching if repository code derives another equivalent partition.

Timeout:

`600 sec per attempt`

Retry:
maximum `2` only for a failed logical request.

No source recollection after model start.

Generate canonical US previews only.

No Telegram.

Expected canonical set if unchanged:

```text
1 US Market
14 US stocks
= 15 messages
```

---

# 19. US PASS gate

Required:

- exact target `2026-10-01`;
- completed-session price v2 PASS;
- source-only seal;
- model chain PASS;
- validators PASS;
- renderer PASS;
- exact message count PASS;
- no post-seal provider call;
- no Telegram;
- no production DB/scheduler mutation.

Terminal:

`R2B_R9_REV47_US14_FRESH_COMPLETED_CLOSE_FY1_FORWARDPE_MESSAGE_PASS`

If US fails:
stop before KR/main.

---

# 20. KR stage is now eligible by wall-clock only if runtime gate agrees

At the time REV47 was authored, Korean 2026-10-02 regular trading had already ended.

Still use runtime XKRX/session authority.

Proceed to KR only if:

```text
latest completed XKRX session == 2026-10-02
accepted post-close collection boundary is open
```

Do not infer from wall-clock alone.

If not:
stop with the exact gate receipt.

---

# 21. Fresh KR8 after US PASS

If KR gate PASS:

perform one fresh current KR proof for:

```text
000660
003690
005490
005930
010120
012450
047810
086280
```

Use the accepted KR production source/model/message architecture.

Do not reuse the US auxiliary `000660` source role as the KR stock packet.

Acquire the full KR security role freshly.

---

# 22. KR valuation contract

Preserve:

```text
KIS completed-session unadjusted close
/
qualified KIS house-research FY1 EPS
=
KR current-price fPER(FY1)
```

Keep:
- corporate-action guard;
- exact fiscal-period ownership;
- current Kiwoom provider-native PER/PBR where already qualified;
- valuation excluded from Core/A/Overall.

Typed unavailable is acceptable for optional estimates.

---

# 23. KR models/messages

Order:

```text
fresh KR source
→ validator
→ source seal
→ KR Market/Core/A/B
→ renderer
```

Timeout:
`600 sec`

Retry:
max `2` per failed logical request.

No Telegram.

Expected if canonical format unchanged:

```text
1 KR Market
8 KR stocks
= 9 messages
```

---

# 24. Combined proof and main merge

Only after US PASS + KR PASS.

Then:

1. seal combined result;
2. commit REV47 implementation;
3. secret-scan;
4. preserve feature branch remotely;
5. fresh-fetch origin;
6. reconcile local main and origin/main non-destructively;
7. create explicit merge commit;
8. run full merged-main validation;
9. re-fetch immediately before push;
10. normal non-force push only if origin/main unchanged.

No rebase of accepted history.
No force push.

On semantic conflict:
`R2B_R9_REV47_MAIN_RECONCILIATION_CONFLICT_REVIEW_REQUIRED`.

---

# 25. Merged-main validation

On actual merged main:

- completed-session price v2 tests;
- usa06012 latest-row negative tests;
- US14 source/issuer/model/capture tests;
- Finnhub FY1 tests;
- KR KIS FY1 tests;
- ALL22 legacy regression;
- full pytest;
- Ruff;
- git diff check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- protected-state comparison.

Only merged-main PASS permits remote main push.

---

# 26. No deployment

Even after main push:

```text
deploy = 0
restart = 0
scheduler mutation = 0
Telegram send = 0
production DB write = 0
broker action = 0
```

Stop at repository integration.

---

# 27. Required negative tests for the new price contract

At minimum:

1. `usa06012` latest row date exact but `cur_prc` out of range:
   not accepted as completed close.
2. `usa06012` latest row `cur_prc` inside range:
   still not sufficient completed-close authority.
3. `usa20590` exact target row valid:
   accepted.
4. `usa20590` wrong date:
   reject.
5. missing target row:
   reject.
6. close outside its own 20590 high/low:
   reject.
7. zero/negative/nonfinite close:
   reject.
8. wrong exchange/security:
   reject.
9. duplicate target rows with conflicting values:
   reject.
10. stale base date:
   reject.
11. corporate-action incompatibility:
   close display may remain raw only under exact owner; incompatible technical injection denied.
12. model/capture source seal changes after price supplement:
   reject.

---

# 28. Result artifacts

At minimum:

## Price qualification
- official Kiwoom usa20590 documentation receipt
- five-control smoke receipts
- US14 usa20590 request ledger
- completed-session price-v2 matrix
- usa06012 latest-row disqualification matrix
- corporate-action compatibility receipt
- technical-consumer audit

## US proof
- inherited REV46 source lineage manifest
- REV47 close supplement manifest
- new whole-source seed
- US14 owner matrix
- source-only seal ZIP + SHA
- model lineage
- 15 message previews or canonical exact equivalent
- US proof ZIP + SHA

## KR proof
- fresh KR source ZIP + SHA
- KR valuation matrix
- model lineage
- exact message previews
- KR proof ZIP + SHA

## Main
- combined proof
- feature remote preservation receipt
- main reconciliation receipt
- merged-main validation
- origin/main push receipt if performed
- secret scan
- production isolation
- bundle manifest.

Suggested final:

`thesis-monitor-20261002-r2b-r9-rev47-completed-session-close-us-kr-main-integration-report.zip`

+ `.sha256`

---

# 29. Honest terminals

Use the narrowest truthful state:

```text
R2B_R9_REV47_USA20590_COMPLETED_CLOSE_CONTRACT_GAP
R2B_R9_REV47_US_COMPLETED_CLOSE_SUPPLEMENT_GAP
R2B_R9_REV47_US_BUSINESS_OWNER_REPLAY_GAP
R2B_R9_REV47_US_SOURCE_SEAL_GAP
R2B_R9_REV47_US_MODEL_MESSAGE_GAP
R2B_R9_REV47_US14_FRESH_COMPLETED_CLOSE_FY1_FORWARDPE_MESSAGE_PASS
R2B_R9_REV47_KR_SESSION_GATE_GAP
R2B_R9_REV47_KR_SOURCE_GAP
R2B_R9_REV47_KR_MODEL_MESSAGE_GAP
R2B_R9_REV47_COMBINED_VALIDATION_GAP
R2B_R9_REV47_MAIN_RECONCILIATION_CONFLICT_REVIEW_REQUIRED
R2B_R9_REV47_MERGED_MAIN_VALIDATION_GAP
R2B_R9_REV47_REMOTE_MAIN_MOVED_REVIEW_REQUIRED
R2B_R9_REV47_COMPLETED_CLOSE_US_KR_FRESH_MESSAGES_MAIN_INTEGRATION_PASS
```

---

# 30. Final principle

The failure is not:

> three tickers have slightly odd OHLC.

The source-contract lesson is:

> the latest `usa06012 cur_prc` is not a safe completed-session close owner for any ticker merely because its row carries
> the target date.

REV47 must move completed-session close authority to a historical daily-price route designed for explicit base-date
retrieval, while preserving `usa06012` as chart/history evidence.

No favorable-value patching.
No stale substitution.
No broad recollection when the fresh corpus already exists.
