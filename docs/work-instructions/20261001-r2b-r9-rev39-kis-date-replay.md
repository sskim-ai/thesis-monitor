# Thesis Monitor — R2B-R9-REV39
## KIS Corporate-Action Date Parser Coverage Repair
### YYYY/MM/DD + Slash-Date Interval Support
### Exact Sealed REV38 Action/Price/EPS Replay — Provider Calls 0
### Correct Unresolved-Date vs Proven Post-Estimate Action Semantics
### Complete 010120 Current FY1 fPER and 7/7 Eligible KR Forward-Valuation Proof
### No Broad Full-Fresh / No Models / No 24-Message Run

**REV39 supersedes every prior unexecuted post-REV38 current-FY1-fPER instruction. Execute only REV39.**

REV38 successfully closed almost all of the current FY1 fPER owner.

Qualified current FY1 fPER:
- 000660: `4.69x`
- 005930: `5.81x`
- 005490: `10.47x`
- 012450: `20.20x`
- 047810: `54.27x`
- 086280: `8.73x`

003690:
- `UNAVAILABLE_EPS`

010120 alone was denied because the generic corporate-action date parser does not support:
- `YYYY/MM/DD`
- `YYYY/MM/DD ~ YYYY/MM/DD`.

The exact KIS source row is not evidence of a post-estimate action.
It is evidence of a historical face-value change that completed before the KIS FY1 estimate date.

REV39 must repair the generic date parser and denial semantics, replay the exact sealed REV38 evidence, and complete the
current FY1 fPER owner without any new provider call.

---

# 0. Newest SoT

Adopt REV38 as newest current-FY1-fPER SoT.

REV38 result ZIP:
`thesis-monitor-20261001-r2b-r9-rev38-exact-security-guard-report.zip`

SHA-256:
`534ea1efcf78d4362546f227f57697c556e529ff6266f29e15c7e44c0293492e`

Independent verification:
- uploaded sidecar: exact match;
- ZIP CRC: PASS;
- ZIP members: `667`;
- internal manifest entries: `666`;
- manifest missing: `0`;
- hash mismatch: `0`;
- size mismatch: `0`;
- unmanifested payload files: `0`.

REV38 terminal:
`R2B_R9_REV38_CURRENT_FY1_FPER_GAP`

Repository:
- base: `f1b4e6bc37cd4614eeb77975e2541c0afa44d3ea`
- branch: `codex/r2b-r9-rev38-exact-security-guard`
- instruction: `aa29d030f7d19d1ec627f211e538920221376e87`
- frozen implementation: `0c59ec444d18c5a5f4b0c87a1c54bbe9bd1430ae`
- final: `ef9582c4d4c2b76d4462dcbcb260bd6032a27b00`
- operating/main: `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean: true.

Validation:
- focused: `491 passed / 0 failed`
- full: `7537 passed / 63 skipped / 0 failed / 0 errors`
- Ruff: PASS
- git diff --check: PASS
- Investment Knowledge: PASS
- Chart Knowledge: PASS
- secret scan: PASS.

REV38 live proof:
- auth: `1`
- action requests: `42`
- action HTTP/provider success: `42/42`
- continuation: `0`
- retries: `0`
- identity conflicts: `0`
- source-incomplete: `0`
- price refresh: `0`
- estimate refresh: `0`
- models: `0`
- messages: `0/24`.

---

# 1. Exact bounded blocker

Affected security: `010120`

FY1 EPS estimate date: `2026-08-27`

REV37 sealed completed-session price:
- date: `2026-09-30`
- unadjusted close: `205000 KRW`.

REV36 qualified FY1 EPS:
`3680.2 KRW/share`

Exact REV38 KIS face-value-schedule row:
```json
{
  "record_date": "20260409",
  "sht_cd": "010120",
  "isin_name": "엘에스일렉트릭",
  "inter_bf_face_amt": "000005000",
  "inter_af_face_amt": "000001000",
  "td_stop_dt": "2026/04/08 ~ 2026/04/12",
  "list_dt": "2026/04/13"
}
```

Raw response SHA-256:
`b3caf897ed05300e26c9153ee2ce908ea0efc42c2aac5dbe9f8ffb4229ff7840`

Exact query:
- route: `/uapi/domestic-stock/v1/ksdinfo/rev-split`
- TR: `HHKDB669105C0`
- security: `010120`
- F_DT: `20250827`
- T_DT: `20270930`
- HTTP: `200`
- KIS rt_cd: `0`
- tr_cont: `E`.

No transport/source gap exists.

---

# 2. Current parser defect

REV38 `_dates()` supports:
- `YYYYMMDD`
- `YYYY-MM-DD`
- `YYYY.MM.DD`
and same-format `~` intervals.

It does not support:
- `YYYY/MM/DD`
- `YYYY/MM/DD ~ YYYY/MM/DD`.

Therefore it currently produces:
- record_date: parsed `2026-04-09`
- list_dt: unresolved
- td_stop_dt: unresolved.

That forces:
`AMBIGUOUS_EXACT_SECURITY_ACTION`

and the coarse compatibility owner then reports:
`POST_ESTIMATE_SHARE_UNIT_ACTION_PRESENT`.

The latter label is semantically wrong when the actual state is unresolved-date parsing.

REV39 must repair both problems.

---

# 3. Narrow parser expansion

Extend the generic date parser to support exact full-year slash form:
`YYYY/MM/DD`

Format:
`%Y/%m/%d`

Also support an exact same-format interval:
`YYYY/MM/DD ~ YYYY/MM/DD`

Whitespace around `~` may be optional.

No year inference.
No two-digit-year support.
No month/day-only support.
No fuzzy date parsing.
No locale parsing.
No silent normalization of invalid calendar dates.

PASS:
- `2026/04/13`
- `2026/04/08 ~ 2026/04/12`
- `2026/04/08~2026/04/12`.

FAIL:
- `26/04/13`
- `04/13/2026`
- `2026/13/01`
- `2026/04/12 ~ 2026/04/08`
- partial date.

Preserve all existing accepted formats unchanged.

---

# 4. Interval semantics

For a parsed interval:
return both exact boundary dates.

Do not expand every day in the interval.
Do not invent an effective date.

For:
`2026/04/08 ~ 2026/04/12`

the source-owned date set is:
- `2026-04-08`
- `2026-04-12`.

Existing event-decision logic may then classify the overall action from all source-owned dates.

---

# 5. Correct 010120 replay classification

After parser repair, the exact 010120 source dates must parse as:
- td_stop start: `2026-04-08`
- record date: `2026-04-09`
- td_stop end: `2026-04-12`
- list date: `2026-04-13`.

KIS FY1 estimate date:
`2026-08-27`

Price date:
`2026-09-30`.

Every relevant source-owned date is:
`<= estimate_date`.

Therefore the exact action event classification must become:
`WHOLLY_ON_OR_BEFORE_ESTIMATE`

with:
`blocks = false`.

Do not hardcode 010120.
The result must emerge from the generic parser and event-decision policy.

---

# 6. Distinguish unresolved source dates from proven post-estimate action

A source date parse failure must never be labelled:
`POST_ESTIMATE_SHARE_UNIT_ACTION_PRESENT`

unless a different successfully parsed source-owned date independently proves an in-window/post-estimate action.

Required distinction:

## Proven action
Use:
`POST_ESTIMATE_SHARE_UNIT_ACTION_PRESENT`

only when source-owned parsed dates prove a blocking share-unit-changing action.

## Unresolved date/source
Use:
`CORPORATE_ACTION_DATE_UNRESOLVED`

or repository-equivalent typed state when:
- exact-security row exists;
- required date fields cannot be fully parsed;
- no separate parsed date independently proves a blocker.

This state blocks fPER qualification, but must not falsely assert a post-estimate action.

## Incomplete source
Keep:
`CORPORATE_ACTION_SOURCE_INCOMPLETE`
for transport/continuation/missing-family incompleteness.

Do not conflate parser coverage with provider incompleteness.

---

# 7. EventDecisionState contract

Prefer explicit event-level states:
- `WHOLLY_ON_OR_BEFORE_ESTIMATE`
- `WHOLLY_AFTER_PRICE`
- `CRITICAL_WINDOW_DATE`
- `STRADDLING_ACTION_PROCESS`
- `AMBIGUOUS_EXACT_SECURITY_ACTION`.

Compatibility aggregation must distinguish:
- proven blocker;
- unresolved action semantics;
- source incomplete;
- clear/no relevant share-unit action.

No boolean-only collapse before the typed reason is recorded.

---

# 8. No provider calls

REV39 provider calls:
`0`

Do not call KIS, OpenDART, Kiwoom, Finnhub, or any source.

This is an offline sealed-evidence replay.

If any required REV38 raw evidence is missing or hash-invalid:
`R2B_R9_REV39_SEALED_ACTION_EVIDENCE_GAP`

Do not recollect.

---

# 9. Preserve all REV38 sealed action families

Replay all:
- seven FY1-EPS-qualified securities;
- six corporate-action variants per security;
- total `42` family receipts.

Require byte/source identity against REV38.

Do not replay only 010120.

Expected source facts:
- 41 action responses: zero rows;
- 010120 rev_split: one exact-security row.

No source content changes.

---

# 10. Rebuild CorporateActionCompatibilityReceiptV2 offline

Using the new frozen implementation, rebuild all seven compatibility receipts.

Expected six unchanged positives:
- 000660
- 005930
- 005490
- 012450
- 047810
- 086280

remain:
`NO_RELEVANT_SHARE_UNIT_ACTION_FOUND_V1`.

010120 must become the same clear state only through generic parsing.

Any new ambiguity:
fail closed.

---

# 11. Reuse sealed price and EPS receipts

No refresh.

For 010120 require:
- FY1 EPS: `3680.2`
- estimate date: `2026-08-27`
- unadjusted completed-session close: `205000`
- session: `2026-09-30`.

Verify receipt/source hashes from REV36/37/38.

These are expected sealed fixture values only, not production constants.

---

# 12. Complete 010120 current FY1 fPER

Only after repaired V2 guard qualifies:

compute with the existing Decimal owner:
`205000 / 3680.2`

Expected sealed-fixture quotient:
`55.703494375305689908157165371447203956306722460736`

Expected 2-decimal ROUND_HALF_UP display:
`55.70x`

Production calculation must use the EPS, price and compatibility receipts.

No manual result injection.

---

# 13. Final KR8 matrix expected shape

Expected replay:
- 000660: QUALIFIED_CURRENT_PRICE_FY1_FPER
- 005930: QUALIFIED_CURRENT_PRICE_FY1_FPER
- 003690: UNAVAILABLE_EPS
- 005490: QUALIFIED_CURRENT_PRICE_FY1_FPER
- 010120: QUALIFIED_CURRENT_PRICE_FY1_FPER
- 012450: QUALIFIED_CURRENT_PRICE_FY1_FPER
- 047810: QUALIFIED_CURRENT_PRICE_FY1_FPER
- 086280: QUALIFIED_CURRENT_PRICE_FY1_FPER.

This is an expected replay outcome, not a coverage target.

If another subject changes unexpectedly:
fail closed.

---

# 14. Preserve old six fPER values

Expected unchanged:
- 000660 `4.69`
- 005930 `5.81`
- 005490 `10.47`
- 012450 `20.20`
- 047810 `54.27`
- 086280 `8.73`.

010120 is the only intended metric-state change.

Provider FY1 PER remains separate and unchanged.

---

# 15. Parser regression tests

Existing formats must remain PASS:
- compact;
- hyphen;
- dot;
- their supported intervals.

New slash:
- single PASS;
- interval PASS.

Invalid/reverse forms fail closed.

No fuzzy parser.

---

# 16. Boundary tests

For estimate `2026-08-27`, price `2026-09-30`:

Nonblocking:
- event exactly on estimate date;
- wholly before estimate;
- wholly after price.

Blocking:
- `2026-08-28`;
- `2026-09-30`;
- interval straddling into critical window.

Preserve `start < d <= end`.

---

# 17. Denial-label tests

Required:

- unresolved date with no proven blocker:
  typed unresolved date, NOT post-estimate action.

- parsed critical-window date plus another unresolved field:
  proven blocker may remain post-estimate action while retaining unresolved audit detail.

- route/continuation incomplete:
  source incomplete, not date-unresolved and not proven event.

---

# 18. No policy/arithmetic changes

Preserve:
- `BOUNDED_EXACT_SECURITY_SHARE_UNIT_GUARD_V1`
- `SHARE_UNIT_GUARD_ENVELOPE_V1`
- exact-security action topology
- current fPER formula
- Decimal precision
- valuation-only authority.

No changes to:
- KIS FY1 EPS owner;
- provider FY1 PER;
- current trailing PER/PBR;
- Core/A.

---

# 19. Validation

Require:
- slash-date tests;
- slash-interval tests;
- invalid/reverse negatives;
- denial-label tests;
- REV38 exact action-guard tests;
- REV32–38 KIS regressions;
- exact sealed 42-family replay;
- exact sealed 7 price replay;
- exact sealed 8 EPS-state replay;
- arithmetic replay;
- current PER/PBR regression;
- valuation authority isolation;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

Network/provider calls remain zero.

---

# 20. Disk

REV38 final free bytes:
`9,198,985,216`

REV39 is bounded/offline.

No broad GC or full-fresh.

Safe pytest scratch cleanup may be recorded.

REV40 must perform archive-backed GC before broad full-fresh if free remains below 12 GiB.

---

# 21. External transmission

Provider/source transmission:
`0`

Model transmission:
`0`

Messages:
`0/24`

After secret scan, result ZIP/SHA may be uploaded to the existing iCloud Drive / Thesis Monitor folder.

Still prohibited:
Telegram, broker/trading, production DB writes, scheduler mutation, deploy, merge, push, restart.

---

# 22. Success terminal

Use only:

`R2B_R9_REV39_DATE_PARSER_REPLAY_CURRENT_FY1_FPER_PASS_READY_FOR_FULL_FRESH_INTEGRATION`

Require:
1. REV38 integrity PASS;
2. slash-date support PASS;
3. slash-interval support PASS;
4. invalid/reverse fail closed;
5. unresolved-date vs proven-event states separated;
6. exact 42 action families replay;
7. no source-byte change;
8. old six fPER receipts reproduce;
9. 010120 becomes wholly pre-estimate through generic parsing;
10. 010120 V2 guard becomes clear;
11. 010120 current fPER actually computed;
12. KR8 typed matrix complete;
13. provider calls 0;
14. estimate calls 0;
15. price calls 0;
16. models 0;
17. messages 0;
18. production side effects 0;
19. full validation green;
20. secret scan PASS.

---

# 23. Honest stop terminals

- `R2B_R9_REV39_SEALED_ACTION_EVIDENCE_GAP`
- `R2B_R9_REV39_DATE_PARSER_CONTRACT_GAP`
- `R2B_R9_REV39_ACTION_DENIAL_SEMANTIC_GAP`
- `R2B_R9_REV39_ACTION_REPLAY_REGRESSION`
- `R2B_R9_REV39_010120_ACTION_STILL_AMBIGUOUS`
- `R2B_R9_REV39_010120_FY1_FPER_GAP`
- `R2B_R9_REV39_CODE_OWNER_REGISTRY_GAP`
- `R2B_R9_REV39_VALIDATION_GAP`.

Do not solve by source refresh, deleting date fields, hardcoding 010120, or substituting provider PER.

---

# 24. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum include:
- REPORT.md / summary.json;
- REV38 identity/SHA;
- repository identities;
- changed files;
- manifest;
- old/new parser contract;
- parser tests;
- denial-state mapping tests;
- exact 42-family replay;
- seven compatibility receipts;
- seven price identities;
- eight EPS-state identities;
- 010120 original row + parsed dates + repaired classification;
- 010120 current fPER arithmetic receipt;
- final KR8 matrix;
- unchanged six-subject reproduction;
- focused/full/Ruff/diff/knowledge/secret scan;
- provider/model/message counters all zero.

---

# 25. Next-stage handoff

If PASS, REV40 should be the full production-integration proof:

1. archive-backed GC if free <12 GiB;
2. fresh KR KIS estimate-perform;
3. FY1 EPS qualification;
4. fresh unadjusted completed-session close;
5. fresh exact-security corporate-action guard;
6. fresh current FY1 fPER;
7. secondary KIS provider FY1 PER;
8. existing current PER/PBR;
9. valuation only in Valuation + B/NewBuyer/Holder;
10. whole-source replay twice;
11. fresh Market/Core/A/B;
12. exact 24 messages;
13. no valuation authority in Overall/Core/A.

Do not execute REV40 inside REV39.

---

# 26. Final principle

REV38 proved the exact-security guard topology works.

The only remaining gap is deterministic date-format coverage:
KIS returned a historical 010120 face-value-change row using slash-formatted dates.

All of those dates are before the FY1 estimate snapshot.

Repair the parser generically, replay the sealed evidence, and let the existing arithmetic owner qualify 010120 naturally.

Do not recollect source data and do not special-case LS ELECTRIC.
