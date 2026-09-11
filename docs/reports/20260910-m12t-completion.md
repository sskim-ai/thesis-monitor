# M12T Completion: Partial, Stopped at First Failed Context

## Decision

- Status: **PARTIAL_STOPPED**
- Fresh real proof: **NOT_READY**
- Production readiness: **NOT_READY**
- Next: **BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR_GPT6_ASTRA**
- Additional bounded scope: **BOUNDED_ASTRA_BOUNDARY_CALIBRATION_REPAIR**
- No hotfix, retry, timeout extension, batch split or remaining-context continuation.

## Repository and Provenance

| Field | Value |
|---|---|
| Branch | `codex/20260910-astra-transport-review-m12t` |
| Base | `be3ee8d17e97edcf82ab2c8535d222c03b13667f` |
| Work instruction | `09f434f3353db01e75af8b6c7b1526679f16fe99` |
| Frozen implementation | `695464f2b122bfe6e5378476b066cd945415eb61` |
| Main, unchanged | `d18e68b1e944d7749d093b08797fcd9498412680` |
| Latest M12F ZIP SHA-256 | `e04c88c992cdf7e13415e2d0fb945d343c404a8e6cc620e00f26a91a3bb20383` |
| M12F integrity | 202 indexed payloads; missing/extra/hash/size/duplicate errors 0 |
| Authoring / judgment | gpt-6-astra / xhigh, actual provenance confirmed |
| Code/config drift after freeze | 664 Python files + 6 config files, 0 changes |

The report commit and final HEAD are bound in the exported program-completion JSON after Git
commit/CI observation. Production checkout, service and schedules were not changed.

## Transport Review

M12E and M12F used the same CLI 0.153.4, model, effort, 4-subject shared contexts,
1800-second watchdog and wrapper retry 0. Prompt and schema content is byte-identical after
normalizing only generation identity.

| Generation | Context 1 | Context 2 | CLI internal retries | Wrapper retries |
|---|---:|---:|---:|---:|
| M12E | 371.47s, returned | 329.53s, returned | 0 | 0 |
| M12F | 1133.48s, returned | 1800.01s, timed out | 2 | 0 |
| M12T | 321.70s, returned | 331.91s, returned | 0 | 0 |

Context prompt sizes: 28,025 / 19,420 bytes. Schema sizes: 44,296 / 44,191 bytes.
Unique invocation/runtime/working-directory/session identities were verified. The watchdog
terminated the M12F timed-out process group with SIGTERM and exit -15. No old canary process
remained at preflight, and no new canary process remained after M12T stopped.

Frozen classification: **TRANSIENT_WEBSOCKET_OR_SERVICE_DEGRADATION_LIKELY**.
This is an inference, not a proven backend root cause. Historical resource contention and
backend sampling-request totals were not measured. Normal M12T latency supports recovery,
but only 2/6 intended contexts ran; this is not a complete transport stability proof.
No timeout, retry, batch-size, financial-semantic or calibration change was made.

## New Generation

`20260910-m12t-fictional-20260909T162127Z-9bdf3fffd52c`

Source lock: `7c4caae13c41f0a966ba527476199331cc957fcc7b17e33cc1b39aebf203e10b`

| Measure | Result |
|---|---|
| Calls | 2/6 attempted; 2/2 transport returned |
| Raw schema | 8/8 emitted rows PASS |
| Final row gates | 6/8 PASS, 2 FAIL |
| Remaining | 4 contexts / 16 rows NOT_RUN |
| Timeout / capacity / orphan | 0 / 0 / 0 |
| Internal CLI / wrapper retry | 0 / 0 |
| Typed financial refs selected / used | 15 / 15 |
| Grounding / invalid references | 0 / 0 failures |
| Price/technical/supply leakage | 0 |
| QTD/YTD false accept/reject | 0 in emitted rows |
| Full formal/core/stance stability | NOT_MEASURED |

The old runner's context-02 audit `pass_count=3` is before the calibration wrapper.
After its FIC-FIN-05 failure, final context-02 rows pass 2/4; total acceptance is **6/8**,
not 7/8. Original receipts/run documents remain unchanged. Separate final aggregation records this.

## Emitted Rows

| Subject | Direction | BUY:SELL | New Buyer | Holder | Final Gate |
|---|---|---|---|---|---|
| FIC-FIN-01 | BUY | 6:4 | ATTRACTIVE | HOLDABLE | PASS |
| FIC-FIN-02 | HOLD | 4.5:5.5 | WAIT | REVIEW | PASS |
| FIC-FIN-03 | HOLD | 5.5:4.5 | WAIT | REVIEW | PASS |
| FIC-FIN-04 | HOLD | 5:5 | WAIT | HOLDABLE | PASS |
| FIC-FIN-05 | SELL | 4:6 | AVOID | REDUCE | FAIL |
| FIC-FIN-06 | HOLD | 5.5:4.5 | WAIT | HOLDABLE | PASS |
| FIC-FIN-07 | HOLD | 5:5 | WAIT | HOLDABLE | PASS |
| FIC-FIN-08 | HOLD | 5:5 | WAIT | REVIEW | FAIL |

## Open Findings

1. **P1: FIC-FIN-08 exclusion false reject.** The text explicitly says:
   “일반 사업회사의 부채·운전자본 틀은 적용 대상이 아니다.”
   The existing suffix recognizer does not cover this nominal complement and classifies the
   working-capital mention as UNCERTAIN_OR_AMBIGUOUS. The generic-financial-sector validator
   then rejects it. Candidate-wide authoring review found no actual industrial-framework
   application elsewhere, and selected financial refs are empty. Original FAIL is preserved.
   Follow-up should test generic assertion/exclusion scope, including mixed and conditional
   negative controls, not whitelist this ticker or exact sentence.

2. **P1: FIC-FIN-05 frozen leverage bucket violation.** Expected HOLD 4.5:5.5 SELL_LEAN;
   observed SELL 4:6, AVOID/REDUCE, while business thesis change remains UNCHANGED.
   The model explicitly treats supplied E07, “Expectations do not appear to allow for a
   prolonged refinancing burden,” as a second negative anchor beside debt/cash resilience.
   This source exists, so the failure is not a fabricated expectation or simply missing
   refinancing data treated as bearish. The frozen target remains violated. The smallest
   next review must adjudicate whether that expectation supplies independent negative
   confirmation in this full source pattern. Do not force the historical Sol SELL label,
   remove E07 post hoc, relax the 6.0 threshold, or modify this generation.

3. **P1: Hosted CI portability.** Implementation Actions 34376081552:
   3,174 PASS / 5 FAIL, lint skipped. The same five failures as M12F remain:
   three missing historical Git objects and two local-only ZIP dependencies.
   New M12T failing tests: 0. Keep a separate portability repair; CI is not green.

Open P0: 0. Open P1: 3. Reporting aggregation wording is a P2 advisory.
The financial-validator raw rejection count is 1 (authoring-reviewed false positive);
ordinal calibration violation count is 1. Total final row-gate errors: 2.
This does not mean two actual financial-framework misuses.

## Validation and Safety

- Phase A focused: 140 PASS; full local: 3,179 PASS, two existing warnings.
- Ruff and git diff check: PASS.
- New generation code/config remained frozen.
- Real issuer calls, judge calls, provider fetches, production DB/warning/notification writes,
  sends, main merges, deployments, schedule changes and automatic resume: all 0.
- Approved schedules: 8 PAUSED at start and end.
- Historical M12E/M12F raw evidence is in `experiment/historical/`; excluded from new sample.
- No full message-specificity advisory or repeated stance measurement: sample incomplete.
- No real proof or production exposure authorized by this partial result.

## Next Work

Close the explicit-non-applicability false reject and the full-source leverage/expectation
boundary in a separately frozen bounded task. Preserve financial source, ownership, thresholds,
Price-Timing and renderer contracts. Only then authorize a completely new full fictional
generation. Transport remains an observed risk, not a demonstrated deterministic defect.

The official configuration reference was consulted without changing internal retry settings:
[OpenAI configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).
It does not establish the cause of the recorded disconnect.
