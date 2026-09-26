# Thesis Monitor — M12DS-R6-R5F-R2B0
## One-Shot Live Stock Source Acquisition
### Stop Recovering Missing Historical Envelopes; Collect the 88 Real Stock Roles Once and Close STOCK_MATERIALIZATION

**Purpose:** replace further historical-response recovery work with one bounded, real, source-only acquisition of the exact missing stock roles. Capture the request/response ownership receipts prospectively, then build and validate the pure US14/KR8 stock materializer from those newly captured responses. Do not run AI, render messages, send, or activate schedulers in this task.

---

# 0. Newest accepted SoT

Adopt R5F-R2A-R5 as the newest source-of-truth for this scope.

R2A-R5 result ZIP SHA-256:

`4ddc75eae2e189c6f81a1a989f9956c64f2837f610524829e55f4af0700ee23e`

Terminal:

`M12DS_R6_R5F_R2A_R5_TWO_BLOCKER_GAP_REMAINS`

Accepted findings:

- `KRX_ACQUISITION_HISTORY_REPLAY = PASS`
- sole remaining blocker:
  `STOCK_MATERIALIZATION`
- canonical universe:
  - US14
  - KR8
- missing original role-bound receipt chains:
  `88`
- required role set per subject:
  - `adjusted_daily`
  - `adjusted_weekly`
  - `adjusted_monthly`
  - `unadjusted_weekly_valuation`
- 22 subjects x 4 roles = 88 source reads
- prior archives contain normalized chart fingerprints but not the original role-bound request/response envelopes;
- prior assessments/rendered output are not acceptable replacements;
- optional forward estimates / CF-WC are not separate blockers;
- KRX historical component is already closed and must not be reworked.

Current gates:

- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = false`
- `complete_source_adapter_qualified = false`
- `complete_ai_adapter_qualified = false`
- `source_gate = FAILED_CLOSED`
- R2B not generated/executed;
- R3 blocked.

Repository identities from R2A-R5:

- base:
  `e4cdb436a6affe20ebf0dc4f9f48e517f7f3c248`
- instruction:
  `7ea8dfdfb51e75ff27afa5fe8c5a9c8ef812d15a`
- implementation:
  `55039053dca19902b5b6ec01cfe01a15f337ba6d`
- final:
  `fdc1a1e69f3941676927b38c4d81ba4b4d6d369c`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Do not overwrite or reinterpret the R2A-R5 historical result.

---

# 1. Product decision for this task

Do **not** attempt to reconstruct the 88 missing historical response envelopes.

Do **not** continue searching old report directories for a complete set of original response bodies.

Instead:

> collect the exact 88 stock source roles once from the currently configured production source owners, capture the source receipts prospectively, and use those real captured responses to close the stock materializer.

This is an explicit bounded source-only acquisition authorization.

It is **not** scheduler activation and is **not** a production message run.

---

# 2. Execution-time semantics

This task may run outside normal market schedule, including weekend/off-hours.

Because it is a source-adapter proof:

- dynamically resolve the latest available/completed session context through the existing market/session owners;
- preserve the actual returned row/session dates;
- do not relabel data as “today” or “intraday” when markets are closed;
- do not pretend this is an 08:10 US or 16:00 KR production cycle;
- do not send investment messages.

The goal is request/response/source ownership and materializer closure.

A later R2B task will perform a genuine production-equivalent current cohort.

---

# 3. Exact stock universe

Freeze the canonical universe before the first request.

## US14

- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- SKHY
- SNDK
- TSLA
- TSM
- WRD
- WULF

## KR8

- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280

If repository canonical configuration differs from this accepted R2A-R5 universe, stop before network access and report the exact mismatch. Do not silently substitute.

---

# 4. Exact authorized source roles

For every one of the 22 subjects collect exactly:

1. `adjusted_daily`
2. `adjusted_weekly`
3. `adjusted_monthly`
4. `unadjusted_weekly_valuation`

Stock-role data requests:

`22 x 4 = 88`

This is the frozen expected stock request count.

Before execution, generate a deterministic request-plan JSON containing all 88 entries and hash it.

Each entry must include at least:

- market;
- subject;
- canonical identity;
- provider;
- endpoint/source owner;
- route/exchange where applicable;
- timeframe;
- adjusted/raw basis;
- role;
- expected query/session semantics.

Do not begin network access until:
- plan count = 88;
- no duplicates;
- no missing subject/role;
- no prohibited provider.

---

# 5. Provider policy

Use only the existing configured production stock source owner(s) for these roles.

Explicitly prohibited:

- Alpha Vantage
- Massive
- mock provider
- undeclared fallback provider
- browser/manual web price source
- reconstructed historical response
- prior normalized packet presented as new response

For this task:

`Alpha Vantage calls = 0`

If an existing owner tries to fall back to Alpha/Massive/another undeclared provider:
- deny fallback;
- mark the affected role failed;
- continue remaining planned requests;
- do not substitute.

---

# 6. One pass, no automatic retries

This task is intentionally bounded.

For the 88 planned stock-role reads:

- issue each planned role at most once;
- provider/internal pagination that is an intrinsic part of one declared role must be explicitly receipted and counted separately in transport evidence, but must not create a second logical role acquisition;
- no full-task retry;
- no retry because a result is inconvenient;
- no backfill from prior archive;
- no cache substitution unless the existing owner proves the cache artifact was created by **this exact request** and binds it prospectively to the receipt.

If one request fails:
- preserve the exact error;
- continue all remaining 87/86/etc planned roles.

Classify only after all 88 logical roles have been attempted.

---

# 7. Required owner-bound receipt for every role

For each role preserve:

- run ID;
- acquisition ID;
- logical request-plan entry ID;
- market;
- subject;
- canonical security identity;
- provider;
- route/exchange;
- endpoint/source owner;
- role;
- timeframe;
- adjusted/raw basis;
- request start timestamp;
- response/source-open timestamp;
- provider/request identity;
- sanitized request hash;
- exact raw response bytes or immutable source artifact;
- source SHA-256;
- returned row dates;
- latest available/completed session interpretation;
- normalized OHLCV/result hash;
- existing validator result;
- source-to-normalization lineage;
- success/failure;
- external attempt ordinal.

Do not store tokens/secrets.

A normalized OHLC fingerprint without source bytes/artifact binding is not sufficient.

---

# 8. No cross-role / cross-subject substitution

Strictly prohibit:

- daily response standing in for weekly;
- adjusted response standing in for unadjusted;
- one symbol's response copied to another;
- prior archive response substituted for a failed current read;
- previous attempt/run response substituted;
- later manual reconstruction.

Each of the 88 logical roles owns exactly its captured source receipt or an explicit failure.

---

# 9. Completion rule for acquisition

## COMPLETE

Require:

- 88/88 logical role requests attempted;
- 88/88 usable role-bound receipts;
- all 22 subjects have all 4 roles;
- every role passes identity/date/basis/schema validation;
- no prohibited provider/fallback;
- no missing raw/source artifact.

Suggested acquisition state:

`ONE_SHOT_STOCK_SOURCE_ACQUISITION_COMPLETE`

## PARTIAL

If any role is missing/unusable:

- preserve all successful real receipts;
- do not fabricate missing ones;
- do not call AI;
- do not assemble a production-qualified packet;
- return exact missing subject/role/provider/error list.

Suggested terminal:

`M12DS_R6_R5F_R2B0_ONE_SHOT_SOURCE_ACQUISITION_PARTIAL`

Do not automatically rerun the whole 88 inside this task.

---

# 10. Pure stock materializer implementation

If and only if 88/88 acquisition is complete:

use the newly captured source receipts to implement/finish the pure source-only stock materializer.

The materializer must not read:

- prior AI assessments;
- prior rendered messages/reports;
- undeclared implicit caches;
- prior run decision packets;
- delivery state.

Allowed inputs:

- the four newly captured stock role receipts;
- already accepted read-only Class-B/Class-C owners and persisted evidence;
- explicit optional-unavailable states;
- frozen code/config/owner identities.

---

# 11. Business/financial evidence

Do not re-download fundamentals merely because stock OHLCV is newly captured.

Use the already accepted acquisition-class rules:

- Class A price/chart = newly captured here;
- Class B = run-fresh-once only when the later full run requires it;
- Class C = versioned persisted allowed;
- optional unavailable remains unavailable.

For this stock-materializer proof:

- bind eligible existing thesis/identity/financial/business evidence through accepted read-only projections;
- preserve original source/as-of/version;
- no relabel as current fresh;
- no new SEC/OpenDART/FRED/EIA/ECOS fetch;
- no Alpha estimates.

Observed-business union must remain non-empty under the existing Core contract.

If a subject lacks a qualified observed-business proposition:
- fail that subject honestly;
- do not insert thesis text or prior AI output as observed evidence.

---

# 12. Materializer positive proof

For each of US14 + KR8 prove:

- exact subject identity;
- all four new price-role receipts present;
- adjusted/raw basis correct;
- returned session/as-of dates preserved;
- technical/chart inputs derived only from the new captured source;
- valuation current-price role uses the correct unadjusted source;
- business evidence has owner lineage;
- financial evidence has owner lineage;
- optional estimate/CF-WC absence handled per existing policy;
- numeric registry/fact refs consistent;
- no prior assessment/rendered prose;
- typed stock packet validates;
- deterministic materializer output hash.

Required:

`22/22 stock packets`

for materializer closure.

---

# 13. Materializer negative proof

At minimum test:

- missing one of four role receipts -> fail;
- source hash tamper -> fail;
- symbol mismatch -> fail;
- wrong timeframe -> fail;
- wrong adjusted/raw basis -> fail;
- wrong date/session ownership -> fail;
- prior-run response -> fail;
- prior AI assessment injected -> fail;
- empty observed-business union -> fail;
- numeric registry/source-ref mismatch -> fail;
- optional estimate unavailable -> does not automatically fail;
- optional CF/WC unavailable -> does not automatically fail.

Do not weaken existing validators.

---

# 14. What to do with the already-closed KRX history blocker

Do not recollect or reconstruct it.

Adopt the accepted R2A-R5 KRX component:

`KRX_ACQUISITION_HISTORY_REPLAY = PASS`

Owner output SHA-256:

`68991ed322b5d067f46e6d0a1ae4f9151533ff10177e4d31ab61997c39210937`

Aggregate SHA-256:

`27ff01fb38ccae666ff254a5f5c8c0ebad011d76fa9828db85181afca1b30ee0`

It remains historical/offline proof and is not to be relabelled as a current live source.

R2B will collect/qualify the current production cohort separately.

---

# 15. Network-free prequalification after real stock capture

If:

- 88/88 real stock-role receipts PASS;
- 22/22 stock materializers PASS;
- all previously accepted market/Class-B/Class-C owner mechanics remain valid;

then rebuild the offline/prequalification source adapter with the new real stock receipts.

At minimum prove:

- US14 stock branch complete;
- KR8 stock branch complete;
- no old normalized-only stock archive dependency;
- no prohibited provider;
- deterministic run seed;
- deterministic stock packet hashes;
- KRX historical component remains independently verified.

You may set:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`

only if the complete consumed source graph can now be assembled under existing accepted offline owner contracts.

Keep:

`complete_source_adapter_qualified = false`

until a genuine current full production cohort is executed in R2B.

---

# 16. Generate R2B instruction after success

If 88/88 + 22/22 + network-free prequalification PASS:

generate a separate immutable R5F-R2B work instruction.

R2B must:

1. freeze exact **current full source cohort** call plan before any network access;
2. collect current Class-A US/KR price/market roles;
3. acquire required Class-B once per run;
4. reuse eligible Class-C projections;
5. no Alpha/Massive/mock fallback;
6. qualify the complete live source adapter;
7. connect existing Market/Core/A/B/validators/renderer/delivery;
8. run production-equivalent dry-run:
   - US market 1 + US14 stocks = 15;
   - KR market 1 + KR8 stocks = 9;
   - total = 24 rendered messages;
9. Telegram sends = 0;
10. production delivery intents = 0;
11. scheduler mutation = 0;
12. package all 24 messages for direct review.

Do not execute R2B inside this task.

---

# 17. Scheduler / operational state

R2B0 must not:

- activate US 08:10 schedule;
- activate KR 16:00 schedule;
- restore primary/backup jobs;
- mutate scheduler state;
- send Telegram;
- deploy;
- restart.

The unified operational schedule remains:

US:
08:10 -> incomplete only 08:15 -> incomplete only 08:20.

KR:
16:00 -> incomplete only 16:05 -> incomplete only 16:10.

R3 scheduler cutover remains blocked until accepted R2B.

---

# 18. Safety counters

Allowed:
- only the frozen source-only production-owner data requests needed for the 88 stock roles.

Required zero:

- Alpha Vantage calls = 0
- Massive calls = 0
- external model calls = 0
- Market/Core/A/B calls = 0
- rendered messages = 0
- Telegram sends = 0
- production delivery intents = 0
- broker actions = 0
- production DB decision/warning writes = 0
- scheduler mutations = 0
- notification mutations = 0
- deploy = 0
- service restart = 0.

Record actual provider/auth/transport call counts separately from the 88 logical role count.

---

# 19. Environment/config discipline

Before first network request capture:

- worktree HEAD/clean;
- operating main HEAD/clean;
- tracked config hashes;
- secret-safe env fingerprint;
- provider configuration fingerprint;
- scheduler state;
- canonical universe hash;
- exact 88-request-plan SHA.

After task capture again and prove no unauthorized configuration/scheduler mutation.

No secret values in artifacts.

---

# 20. Validation

Required:

- request-plan completeness tests;
- real receipt schema validation;
- 88-role coverage validator;
- source hash/identity/date/basis tests;
- stock materializer focused tests;
- 22-subject positive proof;
- materializer negative tests;
- provider fallback exclusion tests;
- prior R2A/R2A-R2/R2A-R3/R2A-R4/R2A-R5 regression;
- disabled unified entrypoint smoke;
- full pytest for code changes;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- skip/xfail identity check.

Do not alter prompts, thresholds, historical FAIL pins or validators merely to obtain PASS.

---

# 21. PASS criteria

Use:

`M12DS_R6_R5F_R2B0_ONE_SHOT_STOCK_SOURCE_MATERIALIZATION_PASS`

only if:

1. exact 88-request plan frozen before acquisition;
2. 88/88 real logical stock roles captured;
3. every role has request/source/normalization receipt;
4. no prohibited provider/fallback used;
5. 22/22 pure stock materializers pass;
6. no prior assessment/rendered output used;
7. existing business/financial owner semantics preserved;
8. materializer negative suite passes;
9. network-free adapter can now be prequalified from the accepted owner graph;
10. no model/render/send/scheduler work occurs;
11. full validation passes;
12. R2B next instruction is generated and frozen.

If source collection is incomplete:

`M12DS_R6_R5F_R2B0_ONE_SHOT_SOURCE_ACQUISITION_PARTIAL`

If acquisition is complete but materializer still has a real code/owner blocker:

`M12DS_R6_R5F_R2B0_STOCK_MATERIALIZER_GAP_REMAINS`

Do not return to historical-envelope recovery.

---

# 22. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R2A-R5 identity/SHA receipt
- repository identities
- exact 88-request plan + SHA
- canonical US14/KR8 receipt
- per-role request/response receipts
- raw/source artifact hashes
- normalized hashes
- actual provider/auth/transport counts
- 88-role coverage matrix
- failure matrix if any
- US14 materializer matrix
- KR8 materializer matrix
- observed-business-union proof
- financial owner binding proof
- optional estimate/CF-WC state
- materializer negative-test receipts
- network-free prequalification receipt if reached
- execution counters
- config/env/scheduler before-after proof
- focused/full validation logs
- secret scan
- R2B next instruction + SHA if PASS
- bundle manifest.

---

# 23. Final principle

From this task forward:

> missing historical source envelopes are not a reason to keep reconstructing old evidence.

The system must prove source ownership prospectively from the next real acquisition onward.

Historical archives remain historical evidence; they are not fabricated into request/response receipts.
