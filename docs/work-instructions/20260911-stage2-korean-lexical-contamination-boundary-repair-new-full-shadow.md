# Thesis Monitor — Stage-2 Korean Lexical Contamination Boundary Repair + New Full Monitored Shadow

## 0. Task identity

Suggested work-instruction filename:

```text
20260911-stage2-korean-lexical-contamination-boundary-repair-new-full-shadow.md
```

Suggested result bundle:

```text
thesis-monitor-20260911-stage2-korean-lexical-contamination-boundary-repair-new-full-shadow-report.zip
```

Master-workflow phase:

```text
M12AM — Integrated-Main Stage-2 Safety Matcher Repair
         A. Freeze M12AK formal fictional proof
         B. Freeze M12AL manifest-contract repair
         C. Repair Korean price/technical/supply lexical false positives
         D. Offline replay the exact stopped 047810 Stage-2 output
         E. Start a NEW full active-monitored shadow generation
         F. Complete full monolithic vs two-stage compatibility review
         G. Hand off to boundary / delta-materiality / holder policy review
```

M12AL successfully repaired the shadow manifest producer/verifier contract.

The new shadow generation passed:

```text
manifest roundtrip
historical M12AK shadow preflight replay
active monitored universe freeze
packet hash freeze
shadow model-call gate
context-01 monolithic
context-01 Stage 1
context-01 Stage 2
context-02 monolithic
context-02 Stage 1
```

The task then stopped at:

```text
context-02 / Stage 2
```

because the Stage-2 language-contamination validator falsely detected:

```text
"주가"
```

inside the ordinary fundamental phrase:

```text
"해외수주가 확대되고 ..."
```

This is a Korean lexical-boundary false positive.

It is NOT:

```text
actual price language

a timing-owned evidence reference

a supply reference

a model schema failure

a fundamental stance contract failure

a two-stage ownership failure
```

M12AM must fix the lexical safety matcher generically
without weakening genuine price/technical/supply contamination controls.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260911-shadow-frozen-context-manifest-contract-repair-new-full-shadow-report.zip
```

Verified SHA-256:

```text
7409289d73f6ecd4e9b2fbac7fb3d2ec937f9bbe931a4d11584022e31fe09535
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Independent artifact-index verification:

```text
indexed payloads = 190
ZIP payloads excluding artifact-index = 190

missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Recompute independently.

---

# 2. M12AL repository / proof status

M12AL reported:

```text
phase = M12AL

status = BLOCKED

integration branch =
codex/20260911-shadow-frozen-context-manifest-contract-repair-m12al

base integration head =
1130d9ea035e6e76b5c9c21025eb63552a165958

implementation head =
cf756daa768424dc75c632175d63b8bb00bb4339
```

At task start record actual:

```text
branch
HEAD
working tree
```

Verify no unexplained semantic drift.

---

# 3. M12AK formal fictional proof remains authoritative

M12AL correctly reused the already-completed M12AK formal fictional proof.

Formal fictional generation:

```text
20260911-m12ai-fictional-20260911T073155Z-858474603de1
```

Reuse decision:

```text
REUSE_AUTHORIZED
```

M12AL fictional model calls:

```text
0
```

M12AM must also avoid rerunning fictional models
if the repair is confined to the Stage-2 lexical safety validator
and all model-facing/semantic hashes remain otherwise unchanged.

---

# 4. M12AL shadow manifest repair — freeze successful

Canonical writer key:

```text
frozen_contexts
```

Legacy read key:

```text
contexts
```

Contract:

```text
shadow-frozen-context-manifest-v1
```

Dual key behavior:

```text
both identical → bounded read compatibility

both divergent → HARD FAIL

silent precedence → FORBIDDEN
```

Historical M12AK replay:

```text
HARNESS_CONTRACT_FIX_VALIDATED
```

New shadow gate:

```text
PASS
```

Do not reopen manifest semantics in M12AM.

---

# 5. M12AL new shadow generation

Generation:

```text
20260911-m12ai-shadow-20260911T083524Z-8740a0bb34ed
```

Task-start monitored universe:

```text
22 active names
22 local frozen packets
packet mismatch = 0
provider fetch = 0
```

Planned:

```text
6 contexts

monolithic calls = 6
Stage 1 calls = 6
Stage 2 calls = 6

total = 18
```

Completed before hard stop:

```text
6 model calls
```

Specifically:

```text
context-01:
monolithic PASS
Stage 1 PASS
Stage 2 PASS

context-02:
monolithic PASS
Stage 1 PASS
Stage 2 model call completed
Stage 2 semantic audit FAIL
```

No context-03 through context-06 model calls occurred.

---

# 6. Exact Stage-2 failure

Context-02 tickers:

```text
010120
012450
047810
086280
```

Stage-2 audit:

```text
row_count = 4
pass_count = 3

invalid_reference_count = 0

core_field_output_attempt_count = 0

price_technical_supply_contamination_count = 1
```

Failing ticker:

```text
047810
```

Error:

```text
stage2_price_technical_supply_language_contamination
```

Reported contamination token:

```text
주가
```

Timing/supply refs:

```text
[]
```

So the failure is language-only.

---

# 7. Exact 047810 output

The Stage-2 candidate is:

```text
fundamental_holder:
  stance = REVIEW

  summary =
  "현재 수익성 약화는 확인됐지만
   지속성과 회복 가능성이 미확정이어서
   즉시 축소보다 재검토가 적절하다."

  business_invalidation_condition =
  "저마진이 지속되고 양산·인도 지연과 수주잔고 감소가 구조화되며
   현금창출도 개선되지 않을 때 보유 논리가 무효화된다."

fundamental_new_buyer:
  stance = WAIT

  confirmation_business_condition =
  "양산 인도와 해외수주가 확대되고
   수익성과 현금흐름이 함께 회복될 때
   진입을 검토한다."

  summary =
  "장기 양산·수출 기회는 남아 있지만
   현재 수익성 약화가 확인돼
   회복 검증 전 진입은 이르다."
```

There is no actual:

```text
주가
차트
기술적 진입신호
수급
외국인/기관 flow
가격지지/저항
```

argument in the candidate.

---

# 8. Exact false-positive mechanism

The string:

```text
해외수주가
```

contains the Unicode substring:

```text
주가
```

because:

```text
해외 + 수주 + 가
```

includes the last syllable of `수주`
followed by the subject particle `가`.

A naive substring search:

```text
"주가" in text
```

returns true.

But linguistically:

```text
수주가 확대되고
=
orders expand
```

not:

```text
stock price expands.
```

This is the authoritative root cause unless code audit proves a narrower equivalent implementation defect.

Suggested root-cause label:

```text
KOREAN_FORBIDDEN_LEXEME_SUBSTRING_MATCH_WITHOUT_LEFT_MORPHEME_BOUNDARY
```

---

# 9. Stage-2 safety principle remains valid

Do NOT remove the language-contamination safety layer.

Stage 2 fundamental stance must still reject actual
price/technical/supply reasoning.

Examples that MUST remain hard failures:

```text
"주가가 반등하면 진입한다."

"현재 주가가 싸 보여 ATTRACTIVE다."

"차트가 개선되면 보유한다."

"기술적 지지선이 살아 있어 HOLDABLE이다."

"수급이 좋아져 신규 진입이 가능하다."

"외국인 매수세가 강해 보유를 유지한다."
```

The repair is:

```text
lexical precision
```

not:

```text
safety removal.
```

---

# 10. Evidence-reference safety remains primary

Stage-2 hard gate already separately checks:

```text
selected timing refs

selected supply refs

forbidden core-field output
```

Preserve:

```text
timing_or_supply_refs = []
```

requirement for fundamental stance evidence.

Language contamination is a second defense for uncited prose contamination.

Do not replace evidence-ownership validation with language matching.

---

# 11. Audit the entire forbidden-language lexicon

Before patching `주가`,
inventory the exact Stage-2 price/technical/supply language matcher.

Classify every lexeme into:

```text
A. lexically unambiguous with proper token boundary

B. ambiguous Korean lexeme requiring phrase/context disambiguation

C. phrase-level contamination pattern

D. unsafe substring rule that can match inside unrelated words
```

Examples to inspect if present:

```text
주가

가격

차트

기술적

지지선

저항선

수급

외국인

기관

거래량

돌파

눌림

반등
```

Do not invent new forbidden terms merely because they are listed here.

Use the actual repository matcher as authority.

---

# 12. Preferred lexical matching principle

For Korean price lexemes like:

```text
주가
```

match only when the lexeme begins at a valid lexical/morpheme boundary.

A bounded implementation may use:

```text
start-of-string
or
preceding non-Hangul/non-alphanumeric boundary
```

while allowing Korean particles or compounds AFTER the lexeme.

Desired:

```text
"주가가 상승" → MATCH

"주가는 상승" → MATCH

"주가 상승" → MATCH

"주가하락" → MATCH

"현재 주가" → MATCH
```

But:

```text
"수주가 확대" → NO MATCH

"해외수주가 확대" → NO MATCH

"신규수주가 증가" → NO MATCH

"발주가 늘었다" → NO MATCH
```

Do not hard-code only:

```text
"수주가"
```

as an exception.

Repair the lexical boundary.

---

# 13. Why left-boundary precision is important

The price lexeme:

```text
주가
```

can validly be followed by Korean particles:

```text
주가가
주가는
주가를
주가의
주가에
주가도
주가만
```

and by compound terms:

```text
주가상승
주가하락
```

Therefore a strict right word boundary alone is insufficient.

But a proper left lexical boundary prevents:

```text
수주가
발주가
```

false positives.

The implementation may use another linguistically safe mechanism,
but must satisfy the fixtures below.

---

# 14. Ambiguous term handling

Some forbidden lexemes may be semantically ambiguous.

Example if actual matcher contains:

```text
기술적
```

Possible timing use:

```text
기술적 지지선
기술적 반등
기술적 진입
```

Possible fundamental use:

```text
기술적 경쟁력
기술적 진입장벽
기술적 우위
```

Do NOT blindly treat all occurrences as timing contamination.

If the actual matcher currently does so,
classify that as a separate bounded false-positive risk
and fix with phrase-level context.

Do not broaden into a general Korean NLP rewrite.

---

# 15. Phrase-level matching

For ambiguous terms,
prefer explicit timing phrases such as:

```text
기술적 지지
기술적 저항
기술적 반등
기술적 돌파
차트상
가격 지지
가격 저항
```

only if these are already part of the intended safety contract.

Do not infer a complete new lexicon in M12AM.

The goal is preserving current intended contamination semantics
with fewer false positives.

---

# 16. Candidate-owned text only

Audit exactly which Stage-2 text is scanned.

Preferred:

```text
scan Stage-2 generated stance-owned natural-language fields
```

Do NOT scan:

```text
full prompt

evidence catalog text

frozen Stage-1 core text

market-expectation evidence prose
```

for Stage-2 output-language contamination.

Otherwise actual price words in source context
could falsely contaminate a clean stance output.

M12AL's failure appears to come from candidate output text,
but verify the scanner scope explicitly.

---

# 17. Structured fields to scan

At minimum scan Stage-2 generated prose:

```text
fundamental_new_buyer.summary

fundamental_new_buyer.confirmation_business_condition

fundamental_holder.summary

fundamental_holder.business_invalidation_condition
```

Do not scan:

```text
ticker
evidence ref IDs
schema metadata
prompt text
serialized key names
```

unless a separate contract requires it.

Record the exact scanner paths.

---

# 18. Exact M12AL 047810 offline replay

After repair,
run the exact preserved M12AL Stage-2 output through the validator.

Expected:

```text
ticker = 047810

selected timing/supply refs = 0

language contamination =
[]

status =
PASS
```

The phrase:

```text
해외수주가 확대되고
```

must NOT produce `주가`.

Do not rewrite the model output.

---

# 19. M12AL context-02 Stage-2 offline replay

Revalidate all four preserved candidates:

```text
010120
012450
047810
086280
```

Expected:

```text
4 / 4 PASS
```

provided code audit finds no separate genuine contamination.

Context-01 Stage-2 preserved output should also remain:

```text
4 / 4 PASS
```

No new false positives.

---

# 20. Mandatory Korean lexical fixtures

At minimum:

## PRICE-LEX-01

```text
"현재 주가가 상승했다"
→ CONTAMINATION
```

## PRICE-LEX-02

```text
"주가는 아직 비싸다"
→ CONTAMINATION
```

## PRICE-LEX-03

```text
"주가상승을 기다린다"
→ CONTAMINATION
```

## PRICE-LEX-04

```text
"해외수주가 확대되고 있다"
→ CLEAN
```

## PRICE-LEX-05

```text
"신규 수주가 증가했다"
→ CLEAN
```

## PRICE-LEX-06

```text
"신규수주가 늘었다"
→ CLEAN
```

## PRICE-LEX-07

```text
"발주가 회복됐다"
→ CLEAN
```

## PRICE-LEX-08

```text
"수주가 영업이익으로 전환된다"
→ CLEAN
```

These must test the actual shared matcher,
not a separate test-only helper.

---

# 21. Price phrase negative controls

If supported by the current forbidden lexicon,
retain negative controls for:

```text
"주가가 반등하면 진입한다"

"차트가 개선됐다"

"수급이 좋아졌다"

"기술적 지지선을 확인한다"

"외국인 매수세를 기다린다"
```

Expected:

```text
CONTAMINATION
```

Do not reduce genuine safety coverage.

---

# 22. Fundamental terminology positive controls

If actual matcher includes potentially ambiguous lexemes,
add positive controls.

Examples:

```text
"기술적 경쟁력이 개선됐다"

"기술적 진입장벽이 높다"

"해외수주가 늘었다"

"발주가 회복됐다"

"신규수주가 매출로 전환된다"
```

Expected:

```text
CLEAN
```

when no actual timing meaning exists.

Only include fixtures relevant to actual matcher terms.

---

# 23. No Stage-2 prompt change

Preferred:

```text
Stage 2 prompt change count = 0
```

The model did not produce an actual price claim.

Do not ask the model to avoid the Korean syllable sequence `주가`.

The validator must become linguistically correct.

---

# 24. No model schema change

Required:

```text
Stage 2 schema semantic change count = 0

Stage 1 schema semantic change count = 0

monolithic schema semantic change count = 0
```

The current structured outputs are valid.

---

# 25. No business/financial semantic change

M12AM must not change:

```text
BusinessDeltaEvidenceCapability

typed financial direction hints

financial temporal scope

monitoring transition ownership

business-delta validator

holder contract

new-buyer contract

Directional thresholds

two-stage composition

Price-Timing semantics

Renderer semantics
```

The intended change is:

```text
Stage-2 language-contamination lexical matcher only.
```

---

# 26. Formal fictional proof reuse

Before model calls,
compare semantic hashes against M12AK/M12AL.

If all model-facing and investment-semantic hashes remain unchanged
except the Stage-2 safety matcher:

```text
reuse M12AK formal fictional proof
```

No new fictional model calls.

But offline re-audit the 24 fictional Stage-2 outputs
through the repaired language matcher.

Required:

```text
fictional_stage2_language_reaudit_failure_count = 0
```

If any fictional row unexpectedly changes hard status:

```text
STOP
FICTIONAL_STAGE2_SAFETY_REAUDIT_CHANGED_STATUS
```

Do not start shadow.

---

# 27. Partial M12AL shadow is diagnostic only

The completed first 8 monitored names are useful diagnostics
but NOT a complete compatibility result.

Do not stitch them into the next formal shadow.

Partial observed same-packet differences:

## 000660

```text
monolithic:
HOLD 4.5:5.5 SELL_LEAN
WAIT
HOLDABLE

two-stage:
HOLD 4.5:5.5 SELL_LEAN
WAIT
HOLDABLE
```

No decision-material change.

## 003690

```text
monolithic:
BUY 6.0:4.0
new buyer ATTRACTIVE
holder HOLDABLE

two-stage:
BUY 6.0:4.0
new buyer WAIT
holder HOLDABLE
```

Candidate real new-buyer contract/architecture difference.

## 005490

```text
same HOLD 5.5:4.5 BUY_LEAN
same WAIT / HOLDABLE
```

No decision-material change.

## 005930

```text
monolithic:
HOLD 5.0:5.0 NEUTRAL
confidence MEDIUM

two-stage:
HOLD 4.5:5.5 SELL_LEAN
confidence LOW

stances unchanged
```

Same primary direction,
calibration/confidence difference.

## 010120

```text
monolithic:
HOLD 5.5:4.5 BUY_LEAN

two-stage:
BUY 6.0:4.0

stances:
WAIT / HOLDABLE on both paths
```

Adjacent positive threshold crossing.

## 012450

```text
monolithic:
HOLD 5.5:4.5 BUY_LEAN

two-stage:
BUY 6.0:4.0

stances:
WAIT / HOLDABLE on both paths
```

Adjacent positive threshold crossing.

## 047810

```text
monolithic:
HOLD 4.5:5.5 SELL_LEAN

two-stage Stage 1:
SELL 4.0:6.0

stances:
WAIT / REVIEW on both paths
```

Adjacent negative threshold crossing.

## 086280

```text
same HOLD 4.5:5.5 SELL_LEAN
same WAIT / REVIEW
```

No decision-material change.

These observations are:

```text
INCOMPLETE_DIAGNOSTIC_ONLY
```

because the M12AL generation hard-stopped before full cohort completion.

Do not use majority logic.

---

# 28. Important diagnostic implication

Even before full completion,
the first 8 monitored names already contain three same-packet
adjacent primary-threshold architecture differences:

```text
010120:
HOLD 5.5 → BUY 6.0

012450:
HOLD 5.5 → BUY 6.0

047810:
HOLD 5.5 negative lean → SELL 6.0
```

This is materially relevant to the later boundary-policy review.

M12AM must NOT repair or suppress these differences.

The next full 22-name shadow must measure
whether this is isolated or systematic.

---

# 29. New shadow generation is mandatory

M12AL generation stopped after 6 model calls.

M12AM will change validator code after those outputs.

Therefore:

```text
do NOT resume M12AL

do NOT stitch completed contexts with new contexts

do NOT reuse the 6 model outputs as formal M12AM comparison data
```

After offline replay validates the matcher repair,
start:

```text
NEW shadow generation ID

NEW invocation IDs

NEW runtime namespace

NEW monolithic outputs

NEW Stage 1 outputs

NEW Stage 2 outputs
```

for the complete active monitored universe.

---

# 30. Active monitored universe

At new shadow-generation start,
re-enumerate active monitored names read-only.

Last verified:

```text
22 active monitored names
```

Use actual current active set.

No registration or stop mutation.

---

# 31. Same-packet contract

For every active ticker:

```text
one reproducible local frozen evidence packet
```

Exact same packet hash feeds:

```text
monolithic

Stage 1

Stage 2 evidence context
```

No provider refresh.

Required:

```text
provider_source_fetches = 0
```

---

# 32. Shadow model/runtime contract

Use:

```text
gpt-5.6-sol / xhigh

up to 4 tickers/context

1800-second finite watchdog

wrapper retry = 0

batch split = 0
```

No Astra.

No fallback.

---

# 33. Full shadow topology

For N active names:

```text
context_count = ceil(N / 4)

monolithic calls = context_count

Stage 1 calls = context_count

Stage 2 calls = context_count

total = 3 × context_count
```

At N=22:

```text
18 calls
```

No repetitions.

No fresh unseen names.

---

# 34. Shadow hard-stop policy

Hard stop only for:

```text
runtime/schema hard failure

manifest/hash mismatch

packet mismatch

invalid evidence identity

objective financial semantic failure

business-delta capability violation

business-delta proven direction contradiction

actual Stage-2 price/technical/supply contamination

price/technical/supply Core contamination

financial-sector framework misuse

ADR/security-basis violation

Stage-2 core mutation

production side-effect attempt

aggregate finalization identity failure
```

A genuine language-contamination failure remains a hard stop.

A substring false positive must no longer occur.

---

# 35. Stage-2 language audit output

For each Stage-2 row record:

```text
scanned_text_paths

matched_contamination_spans

matched_lexeme

match_start

match_end

match_rule_id
```

For CLEAN rows:

```text
matched_contamination_spans = []
```

This makes future lexical false positives auditable.

Do not only report:

```text
["주가"]
```

without the actual span/location/rule.

---

# 36. Evidence and language contamination must be separated

Report separately:

```text
timing_or_supply_ref_contamination_count

language_contamination_count
```

Do not collapse them.

A row can fail from either.

For M12AL 047810:

```text
timing_or_supply_ref_contamination = 0
language false positive = 1
```

After repair:

```text
both = 0
```

for the exact historical output.

---

# 37. Full shadow finalization

After all contexts pass:

```text
one final comparison row per active ticker

no missing ticker

no duplicate ticker

no cross-context mismatch

packet hashes preserved

core hashes preserved
```

Aggregate outside model-context schemas.

Preserve M12AK/M12AL finalization contracts.

---

# 38. Shadow comparison taxonomy

Use:

```text
NO_DECISION_MATERIAL_CHANGE

SAME_DIRECTION_CALIBRATION_CHANGE

PRIMARY_DIRECTION_CHANGE

BUSINESS_DELTA_CHANGE

NEW_BUYER_STANCE_CHANGE

HOLDER_STANCE_CHANGE

MULTI_FIELD_DECISION_CHANGE

EXPECTED_CONTRACT_CORRECTION

POTENTIAL_ARCHITECTURE_REGRESSION

OTHER_REVIEW_REQUIRED
```

Delta sublabels remain.

Neither monolithic nor two-stage is automatically ground truth.

---

# 39. Required review for decision-material differences

Every:

```text
PRIMARY_DIRECTION_CHANGE

BUSINESS_DELTA_CHANGE

NEW_BUYER_STANCE_CHANGE

HOLDER_STANCE_CHANGE

MULTI_FIELD_DECISION_CHANGE
```

must receive:

```text
same packet hash

monolithic value

two-stage value

shared evidence

different selected evidence

Unknowns

relevant frozen contract

forensic classification
```

Resolve to:

```text
EXPECTED_CONTRACT_CORRECTION

POTENTIAL_ARCHITECTURE_REGRESSION

OTHER_REVIEW_REQUIRED
```

No silent acceptance.

---

# 40. Combined policy diagnostics

If full shadow completes,
use M12AK fictional formal proof + M12AM monitored shadow.

Focus:

```text
A. adjacent primary threshold:
   FIC-FIN-05
   + real HOLD 5.5 ↔ BUY/SELL 6.0 examples

B. delta materiality:
   FIC-FIN-02 WEAKENED/UNRESOLVED
   FIC-FIN-06 stable STRENGTHENED
   + real AI_JUDGMENT names

C. holder boundary:
   FIC-FIN-08 HOLDABLE/REVIEW
   + real uncertainty-heavy names

D. new-buyer architecture:
   partial 003690 ATTRACTIVE vs WAIT
   + full-cohort analogs
```

Do not change these policies inside M12AM.

---

# 41. No fresh unseen proof

At M12AM completion:

```text
fresh_real_proof_readiness = NOT_READY
```

even if shadow completes.

Next expected scope after a clean full shadow:

```text
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

The full monitored cohort must inform that policy review first.

---

# 42. Remote / main / production policy

M12AM is LOCAL-ONLY.

Required:

```text
remote_push_count = 0

raw_model_artifact_remote_push_count = 0

main_branch_mutations = 0

main_merges = 0

deployments = 0

automatic_monitoring_resume = 0
```

Do not ask for GitHub push permission.

No main merge.

No deployment.

Schedules remain paused.

---

# 43. Production side-effect firewall

Required:

```text
model_calls_real_fresh_unseen = 0

provider_source_fetches = 0

production_db_mutations = 0

monitoring_registrations = 0

monitoring_stops = 0

assessment_persistence_mutations = 0

warning_mutations = 0

notification_queue_writes = 0

production_sends = 0
```

---

# 44. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12am-scope-freeze

04-integrated-main-lineage-freeze

05-m12al-shadow-stop-reproduction

06-stage2-language-contamination-matcher-audit

07-047810-exact-substring-forensic

08-stage2-scanner-path-audit

09-forbidden-lexicon-risk-classification

10-korean-lexical-matching-architecture-decision
```

---

# 45. Required matcher-contract artifacts

Produce:

```text
11-stage2-language-contamination-contract-v2

12-korean-left-boundary-lexeme-contract

13-korean-particle-and-compound-follow-contract

14-ambiguous-lexeme-phrase-contract

15-stage2-candidate-text-path-contract

16-stage2-evidence-ref-contamination-no-change

17-language-match-audit-span-contract
```

---

# 46. Required exact replay artifacts

Produce:

```text
18-m12al-047810-exact-stage2-offline-replay

19-m12al-context02-stage2-four-row-replay

20-m12al-context01-stage2-four-row-regression

21-m12al-partial-eight-ticker-diagnostic-summary
```

Artifact 18 expected:

```text
PASS

timing/supply refs = 0

language contamination = 0
```

---

# 47. Required lexical fixtures

Produce:

```text
22-korean-price-lexeme-negative-fixtures

23-korean-suju-balju-positive-fixtures

24-ambiguous-technical-language-fixtures
if relevant to actual matcher

25-stage2-language-safety-regression-suite
```

At minimum include all PRICE-LEX-01 through PRICE-LEX-08.

---

# 48. Required semantic non-impact artifacts

Produce:

```text
26-model-prompt-semantic-hash-freeze

27-model-schema-semantic-hash-freeze

28-business-delta-semantic-hash-freeze

29-financial-semantic-hash-freeze

30-two-stage-semantic-hash-freeze

31-manifest-contract-freeze

32-finalization-contract-freeze

33-fictional-stage2-language-offline-reaudit

34-fictional-formal-proof-reuse-decision
```

If artifact 34 !=:

```text
REUSE_AUTHORIZED
```

STOP.

Do not run shadow with uncertain semantic drift.

---

# 49. Required tests / shadow gate

Produce:

```text
35-focused-test-results

36-full-local-test-results

37-ruff-and-diff-results

38-hosted-ci-portability-observation

39-new-shadow-model-call-gate
```

Gate requires:

```text
exact 047810 replay PASS

context-02 Stage-2 replay 4/4 PASS

context-01 Stage-2 regression 4/4 PASS

genuine price-language negative controls PASS

수주가/발주가 positive controls PASS

fictional Stage-2 offline re-audit PASS

formal fictional proof reuse authorized

manifest contract PASS

finalization contract PASS

provider refresh disabled

production firewall PASS

model = gpt-5.6-sol / xhigh
```

---

# 50. Required new shadow setup artifacts

Produce:

```text
40-shadow-generation-manifest

41-task-start-active-monitored-universe

42-shadow-packet-inventory

43-shadow-packet-hash-manifest

44-shadow-delta-capability-manifest

45-shadow-direction-hint-manifest

46-shadow-frozen-context-manifest

47-shadow-batching-manifest
```

Use a NEW generation ID.

---

# 51. Required raw shadow artifacts

For each context preserve locally:

```text
monolithic prompt/schema/raw output/receipt/log/run document

Stage 1 prompt/schema/raw output/receipt/log/run document

Stage 2 prompt/schema/raw output/receipt/log/run document
```

No remote push.

---

# 52. Required full shadow analysis artifacts

Produce:

```text
48-shadow-context-hard-semantic-audit

49-shadow-stage2-language-contamination-audit

50-shadow-final-composition-audit

51-shadow-aggregate-finalization-audit

52-shadow-per-ticker-comparison

53-shadow-business-delta-capability-audit

54-shadow-business-delta-direction-audit

55-shadow-core-direction-differences

56-shadow-business-delta-differences

57-shadow-new-buyer-differences

58-shadow-holder-differences

59-shadow-same-direction-calibration-differences

60-shadow-expected-contract-corrections

61-shadow-potential-architecture-regressions

62-shadow-unresolved-review-required

63-shadow-financial-sector-audit

64-shadow-adr-security-basis-audit

65-shadow-cyclical-valuation-audit

66-shadow-core-immutability-audit

67-shadow-runtime-audit

68-shadow-aggregate-summary

69-shadow-architecture-decision
```

---

# 53. Required combined diagnostics

Produce:

```text
70-fic-fin-05-vs-monitored-primary-boundary-analogs

71-fic-fin-02-vs-monitored-delta-materiality-analogs

72-fic-fin-06-vs-monitored-positive-delta-analogs

73-fic-fin-08-vs-monitored-holder-analogs

74-new-buyer-monolithic-vs-two-stage-analogs

75-real-architecture-compatibility-lessons

76-combined-fictional-monitored-root-cause-summary

77-next-bounded-policy-decision
```

---

# 54. Required final completion artifacts

Produce:

```text
78-stage2-language-matcher-repair-success-decision

79-formal-fictional-proof-reuse-success-decision

80-full-shadow-completion-decision

81-existing-monitored-impact-summary

82-two-stage-shadow-compatibility-decision

83-fresh-real-proof-readiness-decision

84-final-main-merge-readiness-note

85-production-no-change

86-schedule-pause-observation

87-remote-push-prohibition-audit

88-master-workflow-update

89-program-completion
```

---

# 55. Full shadow acceptance

Require:

```text
all planned shadow model calls complete

all active tickers represented exactly once

all context hard semantic gates PASS

actual Stage-2 language contamination count = 0
or only genuinely forbidden cases explicitly classified

false-positive lexical contamination count = 0

invalid refs = 0

financial hard semantic failures = 0

business-delta capability violations = 0

business-delta proven direction contradictions = 0

price/technical/supply Core contamination = 0

financial-sector framework misuse = 0

ADR/security-basis violation = 0

Stage-2 core mutation = 0

aggregate finalization PASS

production side effects = 0
```

If a model genuinely writes price/technical/supply stance reasoning:

```text
hard stop remains correct.
```

---

# 56. Compatibility decision

After full shadow:

```text
potential architecture regressions = 0
unresolved review required = 0
```

allows:

```text
TWO_STAGE_COMPATIBILITY_CLEAN
```

or:

```text
TWO_STAGE_COMPATIBILITY_CLEAN_WITH_EXPECTED_CORRECTIONS
```

Otherwise classify bounded/systemic regression honestly.

No percentage threshold.

---

# 57. Failure handling

## A. Exact 047810 output still fails

```text
next_scope =
STAGE2_LANGUAGE_SAFETY_MATCHER_ARCHITECTURE_REVIEW
```

No shadow model calls.

## B. Fix allows genuine "주가" price language

```text
STOP
LANGUAGE_MATCHER_REPAIR_TOO_PERMISSIVE
```

## C. Fictional Stage-2 re-audit changes status

```text
STOP
FICTIONAL_SAFETY_STATUS_DRIFT
```

## D. Full shadow reveals genuine Stage-2 price contamination

Stop per hard-gate policy.

Do not suppress the safety signal.

## E. Full shadow completes

Expected next scope:

```text
DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN
```

---

# 58. Program-completion fields

Include at least:

```text
base_integration_head_sha

integration_branch

latest_result_zip_sha256
latest_result_integrity

stage2_language_matcher_root_cause

stage2_language_matcher_contract_version

forbidden_lexeme_count

ambiguous_lexeme_count

substring_rule_count_before
substring_rule_count_after

m12al_047810_exact_replay_status

m12al_047810_false_positive_token
m12al_047810_false_positive_source_span

m12al_context02_stage2_reaudit_pass_count
m12al_context02_stage2_reaudit_fail_count

korean_price_negative_fixture_count
korean_price_negative_fixture_pass_count

korean_suju_balju_positive_fixture_count
korean_suju_balju_positive_fixture_pass_count

fictional_stage2_language_reaudit_failure_count
formal_fictional_reuse_status

model_prompt_semantic_change_count
model_schema_semantic_change_count
business_delta_semantic_change_count
financial_semantic_change_count
two_stage_semantic_change_count

task_start_active_monitor_count
task_start_active_monitor_tickers

shadow_generation_id

shadow_packet_available_count
shadow_packet_unavailable_count
shadow_packet_mismatch_count

shadow_context_count
shadow_monolithic_model_calls
shadow_stage1_model_calls
shadow_stage2_model_calls
shadow_model_calls_total

shadow_completed_ticker_count
shadow_final_composition_count
shadow_aggregate_finalization_status

shadow_stage2_timing_supply_ref_contamination_count
shadow_stage2_language_contamination_count
shadow_stage2_language_false_positive_count

shadow_no_decision_material_change_count
shadow_same_direction_calibration_change_count
shadow_primary_direction_change_count
shadow_business_delta_change_count
shadow_new_buyer_change_count
shadow_holder_change_count
shadow_multi_field_change_count

shadow_expected_contract_correction_count
shadow_potential_architecture_regression_count
shadow_unresolved_review_required_count

shadow_financial_sector_framework_failure_count
shadow_adr_security_basis_failure_count
shadow_cyclical_valuation_framework_failure_count

shadow_core_mutation_after_stance_count

shadow_runtime_timeout_count
shadow_runtime_orphan_count
shadow_wrapper_retry_count

provider_source_fetches

production_db_mutations
monitoring_registrations
monitoring_stops
assessment_persistence_mutations
warning_mutations
notification_queue_writes
production_sends

remote_push_count
raw_model_artifact_remote_push_count

main_branch_mutations
main_merges
deployments

observed_paused_schedule_count
scheduler_mutation_count
automatic_monitoring_resume

two_stage_shadow_compatibility_classification

fresh_real_proof_readiness
final_main_merge_readiness
production_readiness

next_scope

focused_test_result
full_test_result
ruff_result
git_diff_check

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count
```

Anything unmeasured:

```text
NOT_MEASURED
```

---

# 59. Artifact integrity

Freeze all local artifacts before final artifact index.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

Do not push raw/report artifacts to GitHub.

---

# 60. Final task principle

M12AL successfully fixed the shadow manifest contract.

The new stop is not a new investment-logic problem.

The Stage-2 validator saw:

```text
"해외수주가 확대되고"
```

and performed a raw substring match:

```text
"주가" in "수주가"
```

which incorrectly transformed:

```text
orders expand
```

into:

```text
stock-price language contamination.
```

The correct next flow is:

```text
preserve the Stage-2 price/technical/supply safety layer

→ make Korean forbidden-lexeme matching boundary-aware

→ prove "주가" still catches real price language

→ prove "수주가 / 신규수주가 / 발주가" remain clean

→ offline replay the exact stopped 047810 output

→ offline re-audit the reused fictional Stage-2 outputs

→ start a brand-new full monitored shadow generation

→ complete all active monitored same-packet comparisons

→ only then perform the true boundary / delta-materiality / holder policy review
```

Do NOT:

```text
remove the Stage-2 language safety gate

whitelist only the exact phrase "해외수주가"

tell the model not to write "수주가"

change Stage-2 prompt/schema

change business-delta semantics

change two-stage architecture

resume/stitch the stopped M12AL generation

rerun fictional model calls unnecessarily

push raw artifacts to GitHub

merge into main

deploy

start fresh unseen proof

return to Astra

resume monitoring
```

Fix the Korean lexical matcher,
not the investment judgment.
