# Thesis Monitor — Three-Axis Decision UX + Core/Timing Separation + Overnight/Leading Futures Context

## 0. Task identity

Suggested work-instruction filename:

```text
20260915-three-axis-decision-core-timing-separation-leading-futures-message-repair.md
```

Suggested result bundle:

```text
thesis-monitor-20260915-three-axis-decision-core-timing-separation-leading-futures-message-repair-report.zip
```

Master-workflow phase:

```text
M12BS — Decision / Message Contract Refinement
         A. Freeze the deployed M12BR canonical analysis baseline
         B. Expose three distinct user-facing decision axes
         C. Make REVIEW understandable as "보유 근거 재검토", not a sell order
         D. Audit and eliminate price/timing contamination of overall_direction
         E. Prevent expectation/valuation double-counting of the same underlying signal
         F. Preserve independent market-expectation and valuation evidence when genuinely independent
         G. Add current leading-market / overnight-futures collection and message blocks
         H. Keep completed-session data and leading-market data explicitly separate
         I. Fix the three already-known presentation defects from M12BR
         J. Re-prove affected model/message contracts before deploy
         K. Deploy the bounded repair
         L. Re-run one controlled US/KR collection + market/ticker message smoke test
         M. Keep assessment/warning/outbox/scheduler/real sends OFF
```

This task implements the user's three requested improvements:

```text
1. 사용자에게
   종합 방향 / 신규 관찰자 / 보유자
   를 명시적으로 분리한다.

2. GOOGL 같은 사례에서
   가격 확인선·지지/저항·단기 타이밍이
   종합 방향을 과도하게 끌어내리지 않게 하고,
   시장 기대와 Valuation이 같은 신호를 이중 벌점하지 않게 한다.

3. 야간선물 / 현재 선행시장 신호를
   시장환경 메시지에 별도 블록으로 반영한다.
```

Do NOT hard-code GOOGL to BUY.

Do NOT create a deterministic score resolver.

Do NOT mechanically map overall direction to new-buyer or holder stance.

---

# 1. Authoritative deployed baseline

Use the latest controlled deploy/message result:

```text
thesis-monitor-20260915-final-main-merge-controlled-deploy-manual-us-kr-message-e2e-report(1).zip
```

Verified report result:

```text
deployed_commit_sha =
9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479

deployment_result =
PASS

deployment_health_status =
PASS

active monitored tickers =
22

ticker collection =
22 / 22 success

stock messages =
22 / 22 generated

canonical semantic failures =
0

Business Delta message violations =
0

new-buyer / holder structured-dimension violations =
0

valuation safety violations =
0

price/positioning fundamental-scope violations =
0

unsupported numeric claims =
0.
```

Production automation remains:

```text
Persistence V2 writer = OFF

V2 current-read preference = OFF

V2 warning automation = OFF

V2 outbox delivery = OFF

scheduler = PAUSED

real notification delivery = OFF.
```

Freeze these gates throughout M12BS.

---

# 2. Current known message defects — freeze

M12BR already identified:

```text
market:us
→ user-facing heading missing explicit as-of date

stock:CPNG
→ core thesis terminal phrase incomplete

stock:047810
→ internal label wording leaks into downside reassessment.
```

M12BS should fix these presentation issues while touching the message layer.

Do not leave automation readiness blocked on already-known wording defects.

---

# 3. GOOGL baseline — required regression case

Current deployed GOOGL message:

```text
overall direction =
HOLD

balance =
BUY 5 : SELL 5

confidence =
중간

market expectation =
높음

valuation =
다소 할인

current PER =
12.4x

historical PER median =
16.0x

historical PER percentile =
14th

current PBR =
6.6x

historical PBR median =
6.6x

historical PBR percentile =
48th.
```

Current core sentence includes:

```text
"높은 기대 속 지지 이탈과 미도달 확인 전환이
현재 BUY 지속을 정당화하지 못한다."
```

Current price/timing evidence includes:

```text
support / resistance

existing confirmation price $375

price not reaching confirmation line.
```

M12BS must determine where this price/timing language entered the overall-direction rationale.

Do NOT assume the model stage is at fault without tracing the actual call/composer path.

---

# 4. Root-cause audit: decision ownership

Trace the real monitored analysis path from:

```text
current packet

directional/core model stage

price/timing stage

final composition

message renderer.
```

For each output field identify who owns:

```text
overall_direction

directional_balance

directional_confidence

business_thesis_change

market_expectation_context

valuation_context

new_buyer_stance

holder_stance

price/timing view

confirmation price status

support/resistance context

final core judgment text.
```

Produce an ownership map before changing code.

---

# 5. Fundamental core contract

`overall_direction` must be a judgment of current investment attractiveness
based on fundamental/economic evidence such as:

```text
business quality / business trajectory

earnings quality

financial evidence

market expectations

valuation

material structural risks

relevant macro transmission where genuinely company-value relevant.
```

It must NOT be directly created or downgraded solely by:

```text
technical support/resistance

confirmation-price reached/not reached

short-term price trend

short-term supply/flow

foreign/institutional positioning

overnight futures

intraday futures

chart pattern.
```

Those belong to timing / entry / positioning.

---

# 6. Price/timing immutability contract

Introduce or enforce a contract such as:

```text
DirectionalCoreImmutableAgainstPriceTimingV1
```

or repository-equivalent.

After the fundamental core is frozen,
a price/timing stage may enrich:

```text
new-buyer timing

price view

confirmation status

support/resistance

short-term positioning

risk-of-entry timing.
```

It must NOT mutate:

```text
overall_direction

directional_balance

directional_confidence

business_thesis_change

fundamental material anchors

holder fundamental stance.
```

If the current architecture intentionally allows price to affect confidence,
audit that policy explicitly before changing it.

Default expectation:

```text
price/timing does not change core confidence either.
```

---

# 7. Fundamental holder vs timing

Holder stance remains fundamental.

Price/technical/timing alone must not create:

```text
REVIEW

REDUCE.
```

This rule already exists conceptually and must remain hard.

A holder message may mention price risk separately,
but the holder enum remains tied to fundamental holding risk.

---

# 8. New-buyer timing contract

New-buyer stance may legitimately incorporate:

```text
valuation

market expectations

confirmation need

price/timing

entry asymmetry

current uncertainty.
```

Therefore a valid combination may be:

```text
overall direction = BUY

new buyer = WAIT

holder = HOLDABLE.
```

This is NOT a contradiction.

The UI must make this understandable.

---

# 9. Do not force GOOGL BUY

The GOOGL regression requirement is NOT:

```text
GOOGL must become BUY.
```

The requirement is:

```text
GOOGL overall_direction and core rationale
must be supportable without
support/resistance / $375 confirmation / price-timing evidence.
```

If the corrected core remains HOLD:

the rationale must be fundamental / expectation / valuation based.

If it becomes BUY:

new-buyer may still be WAIT due timing/confirmation.

No target enum.

---

# 10. Market expectation vs valuation — no double counting

Audit the current prompt/composer for this failure mode:

```text
"expectations are high"
+
"valuation is high"
```

when both judgments come from the SAME valuation evidence.

The same valuation multiple must not become two independent directional penalties.

Example forbidden reasoning:

```text
PBR is elevated
→ market expectation is high

and separately

PBR is elevated
→ valuation is expensive

then count both as two independent sell anchors.
```

---

# 11. Expectation/valuation independence contract

Introduce an explicit interaction rule.

Classify the relationship between market-expectation evidence and valuation evidence as:

```text
INDEPENDENT

PARTIALLY_OVERLAPPING

VALUATION_DERIVED_EXPECTATION_ONLY

UNKNOWN.
```

Exact enum naming may follow repository conventions.

This relationship is for evidence weighting / explanation,
not a new investment-direction resolver.

---

# 12. Independent expectation evidence

Market expectation may remain an independent directional/contextual input when supported by evidence such as:

```text
consensus-implied growth

company guidance expectations

embedded margin expectations

orders/backlog expectations

narrative/speculative market assumptions

optionality expectations

industry demand expectations

explicit expectation evidence independent of the current multiple.
```

Valuation can then separately answer:

```text
what price is being paid for those expectations.
```

Both may matter.

---

# 13. Valuation-derived expectation only

If the ONLY reason market expectation is labeled high/elevated is:

```text
the current valuation multiple itself,
```

then:

```text
market expectation remains contextual

but must not become a second independent sell/buy anchor
on top of the same valuation evidence.
```

Do not erase the expectation label.

Prevent duplicate directional weight.

---

# 14. Partially overlapping evidence

If expectation and valuation evidence partially overlap:

```text
preserve both contexts

identify the overlap

do not count the shared evidence twice as independent material anchors.
```

No numerical weighting system is required.

A claim/evidence ownership rule is preferred.

---

# 15. Expectation/valuation regression fixtures

Add deterministic fixtures:

## EV-01

```text
Only high PBR supports:
expectation=high
valuation=expensive

Expected:
one underlying directional anchor,
not two.
```

## EV-02

```text
explicit aggressive growth expectations
+
historically high valuation

Expected:
two independent concepts may both matter.
```

## EV-03

```text
high market expectations
+
historically discounted valuation

Expected:
no automatic HOLD/SELL.
The model must reason through the tension.
```

GOOGL should exercise EV-03-like behavior.

No expected direction hard-code.

---

# 16. Three-axis user-facing header

Every monitored ticker message must expose, near the top:

```text
종합 방향: BUY / HOLD / SELL

신규 관찰자: ATTRACTIVE / WAIT / AVOID

보유자: HOLDABLE / REVIEW / REDUCE
```

Use user-friendly Korean labels with enum optionally shown.

Recommended display mapping:

```text
ATTRACTIVE
→ 신규 진입 매력 있음

WAIT
→ 확인 대기 / 관망

AVOID
→ 신규 진입 보류

HOLDABLE
→ 보유 유지 가능

REVIEW
→ 보유 근거 재검토

REDUCE
→ 노출 축소 검토.
```

Do not use these translations if repository product copy already has a preferred equivalent;
preserve meaning.

---

# 17. REVIEW explanatory contract

`REVIEW` must never read like an automatic sell instruction.

User-facing explanation should communicate:

```text
확인된 중요한 fundamental 위험이 있어
보유 근거를 다시 점검할 단계이지만,

현재 근거만으로 비중 축소/매도를
자동으로 정당화하는 상태는 아니다.
```

Keep it concise.

Do NOT add this long explanation to every message.

Use:

```text
보유자: 보유 근거 재검토 (REVIEW)
```

and show a short reason when REVIEW is active.

---

# 18. REDUCE explanatory contract

`REDUCE` means:

```text
fundamental downside is sufficiently severe/persistent
that unchanged exposure is no longer justified.
```

It is not:

```text
technical stop-loss.
```

The user-facing label should preserve this.

---

# 19. No mechanical three-axis mapping

Hard negative fixtures:

```text
overall BUY
does not force ATTRACTIVE

overall SELL
does not force REDUCE

overall HOLD
does not force WAIT

BusinessDelta UNCHANGED
does not force HOLDABLE.
```

Renderer must print the actual structured stances,
not derive them from overall direction.

---

# 20. Header example — GOOGL-like case

Acceptable UX structure:

```text
종합 방향: BUY
신규 관찰자: 확인 대기 (WAIT)
보유자: 보유 유지 가능 (HOLDABLE)

투자 논리: 유지
시장 기대: 높음
Valuation: 다소 할인
가격/타이밍: 확인 대기
```

This is an EXAMPLE of axis separation.

Do NOT force GOOGL to these exact enums.

---

# 21. Message body hierarchy

Recommended order:

```text
1. three-axis decision header

2. one-line core judgment

3. investment-logic delta

4. business / earnings facts

5. market expectations

6. valuation

7. new-buyer / holder reasons where material

8. price / timing / positioning

9. reevaluation / warning conditions

10. next checks.
```

Price/technical content should not dominate the fundamental message.

---

# 22. Existing presentation repairs

Fix:

```text
US market message heading:
add explicit as-of/session date

CPNG:
repair the incomplete terminal core-thesis phrase

047810:
replace internal label wording with user-facing Korean.
```

Add exact regression tests.

No semantic decision changes required for these three repairs.

---

# 23. Leading-market / overnight-futures contract

Add a separate market-data concept such as:

```text
LeadingMarketSnapshotV1
```

or repository-equivalent.

It must NEVER overwrite completed-session observations.

Market message must distinguish:

```text
완료된 시장

현재 선행시장 / 야간선물.
```

---

# 24. US leading-market coverage

Collect current supported equity-index futures where safe.

Minimum desired:

```text
S&P 500 futures

Nasdaq-100 futures.
```

Optional if already supported and reliable:

```text
Dow futures

Russell 2000 futures.
```

Do not add a paid dependency.

Do not web-scrape an unstable HTML page.

Use an existing supported free/provider connector or a bounded new free connector.

---

# 25. KR leading-market coverage

Collect current KOSPI 200 night/evening futures
when the existing supported provider can identify:

```text
instrument identity

session

prior settlement/reference

current price/change

as-of timestamp.
```

If provider terminology is:

```text
야간선물
evening futures
night session
```

normalize user-facing wording carefully.

Do not call an unrelated derivative "KOSPI200 야간선물".

---

# 26. Provider discovery gate

Before implementing a new provider:

audit existing connectors for:

```text
KR domestic futures

overseas index futures

Kiwoom-supported futures

existing macro/market price provider futures symbols.
```

Prefer an existing connector.

If no supported free source can provide safe current futures data:

do NOT fabricate.

Report:

```text
LEADING_FUTURES_SOURCE_UNAVAILABLE
```

and stop that subcomponent before deployment.

Do not silently substitute ETF after-hours moves
and label them futures.

---

# 27. Futures source safety

Every leading-market observation requires:

```text
instrument identity

market/session identity

current/reference price basis

change calculation basis

as-of timestamp with timezone

source/provider

freshness status.
```

No number without a traceable basis.

---

# 28. Futures change basis

Prefer change versus:

```text
prior official settlement
```

or the provider's explicitly documented comparable reference.

Do NOT compare:

```text
futures current price
to cash-index arbitrary previous close
```

and call it a futures return unless the contract explicitly defines that transform.

Record the basis internally.

---

# 29. Session semantics

Distinguish:

```text
COMPLETED_CASH_SESSION

ACTIVE_FUTURES_SESSION

PREOPEN_FUTURES_SESSION

STALE_FUTURES_SESSION

CLOSED_NO_CURRENT_FUTURES.
```

Exact enum names may follow repository style.

Do not present stale futures as current.

---

# 30. Freshness

Define explicit leading-market freshness thresholds
based on the session/source.

Do not reuse generic daily-close staleness blindly.

If current leading data is stale:

```text
message should say unavailable/stale
or omit the directional interpretation.
```

No stale directional signal.

---

# 31. Market message structure

US example:

```text
🇺🇸 미국 시장환경 점검 · 완료 세션 YYYY-MM-DD

완료된 시장
• S&P / Nasdaq / small cap / semiconductor...

현재 선행시장 · HH:MM KST
• S&P500 futures ...
• Nasdaq100 futures ...

해석
• 전일 위험회피 이후 선물 반등 시도
or
• 정규장 약세가 선행시장에서도 이어짐

주의
• 선물은 현재 선행 신호이며 정규장 확정 신호가 아님.
```

KR example:

```text
🇰🇷 한국 시장환경 점검 · YYYY-MM-DD

장마감
...

현재 선행시장 / 야간선물 · HH:MM KST
• KOSPI200 night/evening futures ...

해석
...
```

Do not use a futures block when there is no safe current data.

---

# 32. Leading market is timing context

Futures/overnight signals may affect:

```text
current market risk appetite

next-session gap/timing risk

new-buyer timing commentary

short-term positioning context.
```

They must NOT create:

```text
BusinessDelta

fundamental holder REVIEW/REDUCE

fundamental invalidation

company earnings change.
```

Hard negative tests required.

---

# 33. No cash-session overwrite

If:

```text
completed S&P session = -1.5%

current S&P futures = +0.8%
```

the message must preserve BOTH.

Forbidden:

```text
"미국 시장은 +0.8%"
```

based solely on futures.

Required semantic:

```text
"정규장은 약세로 마감했고,
현재 선물은 반등 중."
```

---

# 34. Market-risk interpretation

Leading-market interpretation may refine:

```text
약세 지속

반등 시도

방향 혼재

선행 신호 부재.
```

Do not call it:

```text
fundamental recovery.
```

No structural macro thesis change from futures alone.

---

# 35. Korea-US handoff

For KR morning / post-close market context,
current US futures may be relevant.

But distinguish:

```text
latest completed US session

current US futures

KR completed/current session

KR night/evening futures.
```

Use exact as-of times.

No time-zone ambiguity.

---

# 36. Timezone contract

Use offset-aware timestamps.

User-facing:

```text
KST
```

for current leading-market as-of time unless product contract says otherwise.

Internally preserve source timezone/UTC.

No naive timestamps.

---

# 37. Model input policy for futures

Do not automatically feed raw futures ticks into every company fundamental core.

Preferred:

```text
market-context / price-timing input only.
```

If used in the model:

tag as:

```text
LEADING_MARKET_TIMING_CONTEXT
```

or equivalent.

Canonical ownership rules must prevent it from becoming fundamental evidence.

---

# 38. Deterministic market-message generation preferred

Where possible:

```text
completed-session block

leading-market block
```

should be deterministic renderings of validated observations.

Do not spend model calls merely to restate futures numbers.

Model interpretation may consume the compact validated block if current architecture does so.

---

# 39. Data-unavailable UX

If leading futures are unavailable:

show at most:

```text
현재 선행시장: 확인 가능한 최신 야간선물 데이터 없음
```

only when useful.

Do not produce a noisy empty section in every message.

---

# 40. Model-facing change audit

Before implementation classify changes into:

```text
RENDERER_ONLY

DETERMINISTIC_MARKET_CONTEXT

MONITORED_MODEL_PROMPT_CONTRACT

SHARED_MODEL_PROMPT_CONTRACT

CANONICAL_SEMANTIC_CONTRACT.
```

Expected:

```text
three-axis exposure = RENDERER_ONLY

overnight futures = DETERMINISTIC_MARKET_CONTEXT + timing input

core/timing separation =
possibly MONITORED_MODEL_PROMPT_CONTRACT / composer contract

expectation/valuation double-count =
possibly monitored/shared model contract.
```

Do not pretend a prompt change is presentation-only.

---

# 41. Reproof gate

If any model-facing prompt/schema/decision contract changes:

run an appropriate formal reproof BEFORE deploy.

Minimum if monitored-only model contract changes:

```text
replay the frozen M12BR 22 monitored input packets
or another exact frozen 22-packet compatible set

all active monitored cases

same canonical audit

no selective rerun

no enum target.
```

If shared fresh/monitored prompt contract changes:

also replay the frozen M12BQ 12 fresh-unseen cohort.

Do not deploy a model-facing decision change without the required frozen reproof.

---

# 42. GOOGL regression proof

Use the frozen deployed GOOGL input as a targeted regression.

Required:

```text
price confirmation/support/resistance
must not be a material overall_direction anchor.

new-buyer timing may reference it.

holder fundamental stance may not be created by it.

expectation/valuation overlap must be auditable.
```

Direction may be:

```text
BUY
HOLD
SELL
```

if independently justified.

No expected enum.

---

# 43. Additional anti-regression subjects

Use representative cases from the deployed 22:

```text
000660
047810
CORZ
GOOGL
TSLA
MU.
```

Reason:

```text
high expectation

strong business / high valuation tension

price/timing sensitivity

cyclical valuation

SELL/HOLD boundaries.
```

Verify the repair does not globally bias toward BUY.

---

# 44. Do not create pro-BUY bias

Negative acceptance:

```text
TSLA should not become less cautious merely because
price timing is removed from core.
```

If fundamental/valuation evidence supports SELL,
SELL remains valid.

Likewise:

```text
WULF / HUT / CRCL
```

must remain free to produce SELL.

No systematic bullish correction.

---

# 45. User-facing decision rationale

For each of the three axes,
where useful show one short reason:

```text
종합 방향:
사업/기대/Valuation 기반 한 줄

신규 관찰자:
진입/확인/Valuation/타이밍 한 줄

보유자:
fundamental holding risk 한 줄.
```

Do not triple the whole message length.

Avoid repeating identical sentences.

---

# 46. Message verbosity budget

The three-axis header should make the message easier to scan,
not substantially longer.

Target:

```text
header + short reasons
within roughly 5-8 lines.
```

The existing long price-structure block may be shortened
if needed to preserve readability.

Do not remove useful exact price-rule info
when configured and currently relevant.

---

# 47. Existing confirmation price UX

Configured confirmation price should be labeled:

```text
진입/가격 확인
```

not:

```text
fundamental confirmation
```

unless the configured contract truly refers to fundamental confirmation.

GOOGL `$375` belongs to price/timing.

Do not let wording imply that Search/Cloud thesis is unconfirmed merely because price has not reached $375.

---

# 48. Early Warning / Kill Condition separation

Preserve:

```text
price recheck

fundamental kill condition
```

as separate concepts.

Overnight futures cannot trigger a fundamental kill condition.

Technical confirmation cannot substitute for a business invalidation.

---

# 49. Message audit matrix additions

Add columns:

```text
overall_direction_visible

new_buyer_visible

holder_visible

review_user_label_safe

price_timing_in_core_anchor_count

price_timing_in_holder_anchor_count

expectation_valuation_overlap_class

duplicate_directional_anchor_count

completed_session_block_present

leading_market_block_status

leading_market_asof_present

leading_market_stale_misrepresentation_count.
```

---

# 50. Hard acceptance counts

Required after repair:

```text
three_axis_missing_count = 0

mechanical_stance_mapping_count = 0

price_timing_in_core_anchor_count = 0

price_timing_in_holder_anchor_count = 0

expectation_valuation_duplicate_anchor_count = 0

futures_to_business_delta_violation_count = 0

futures_to_holder_fundamental_violation_count = 0

completed_session_overwritten_by_futures_count = 0

stale_futures_presented_as_current_count = 0

unsupported_numeric_claim_count = 0

internal_metadata_leak_count = 0.
```

---

# 51. Existing three presentation issues acceptance

Required:

```text
US market as-of date issue = fixed

CPNG incomplete phrase = fixed

047810 internal label leak = fixed.
```

Add snapshot/text regressions.

---

# 52. Local test sequence

Before deployment:

```text
focused renderer tests

three-axis tests

GOOGL core/timing regression

expectation/valuation overlap tests

leading-market source/parser tests

session/freshness tests

market-message rendering tests

existing BusinessDelta regressions

existing holder/new-buyer regressions

existing financial/valuation regressions

full local pytest

Ruff

git diff --check.
```

All must PASS.

---

# 53. Model reproof sequence

If model-facing contracts changed:

run the required frozen reproof from section 41.

Required:

```text
canonical hard failures = 0

core mutation = 0

price/timing ownership violations = 0

expectation/valuation duplicate-anchor violations = 0.
```

Decision enum differences are diagnostic unless they violate policy.

No exact GOOGL target.

---

# 54. Deployment policy

Only after:

```text
tests PASS

required reproof PASS

leading-market source safety PASS
```

deploy via the existing mechanism used by M12BR.

Record:

```text
predeploy SHA

postdeploy SHA

health

rollback SHA.
```

No new deployment mechanism.

---

# 55. Production gates remain OFF

Even after deploy:

```text
Persistence V2 writer = OFF

V2 current-read preference = OFF

V2 warning automation = OFF

V2 outbox delivery = OFF

scheduler = PAUSED

real notification delivery = OFF.
```

This task is still a controlled smoke test.

---

# 56. Manual current-data smoke test

After healthy deploy:

run one current US/KR collection and message-generation cycle.

Re-enumerate active monitored tickers read-only.

Generate:

```text
US market message

KR market message

all active monitored stock messages.
```

Do not send them.

Do not persist automated assessments.

Do not mutate warnings.

---

# 57. Futures smoke-test timing

Run/record leading-market collection at a time when the relevant futures session state
can be observed if possible.

But do NOT delay or fake data solely to get an ACTIVE status.

If session is closed:

validate:

```text
CLOSED_NO_CURRENT_FUTURES
```

rendering correctly.

If active:

validate live leading block.

No forced active-session result.

---

# 58. Current market message review

Manually/code-assisted review both market messages for:

```text
completed-session facts

current leading-market facts

correct as-of dates/times

no futures/cash conflation

reasonable interpretation

no structural macro overclaim.
```

---

# 59. Current stock message review

Review all active stock messages.

Specifically inspect:

```text
GOOGL

000660

047810

CORZ

TSLA

MU

CPNG.
```

Verify:

```text
three axes visible

no price/timing core contamination

no mechanical stance mapping

no internal label leak

no incomplete sentence.
```

---

# 60. GOOGL post-repair acceptance

Required qualitative result:

```text
A reader can understand independently:

what the company/fundamental valuation direction is,

whether a new investor should enter now,

whether an existing holder should continue holding.
```

If overall direction remains HOLD,
the core reason must not rely on:

```text
$375 not reached

support broken

resistance

short-term price structure.
```

If overall becomes BUY,
new buyer may still be WAIT.

No target direction.

---

# 61. Automation readiness

If M12BS passes:

```text
automation_enable_readiness =
READY_FOR_EXPLICIT_USER_REVIEW.
```

Do NOT resume automatically.

The user should first inspect regenerated messages.

A later task may selectively enable:

```text
scheduler

V2 writer

warning automation

outbox delivery

actual notification channels.
```

No bundle enablement assumption.

---

# 62. Top-level result taxonomy

Choose exactly one:

```text
THREE_AXIS_LEADING_MARKET_MESSAGE_REPAIR_PASS

MESSAGE_REPAIR_MODEL_CONTRACT_REPROOF_FAIL

LEADING_FUTURES_SOURCE_CONTRACT_BLOCKED

MESSAGE_REPAIR_REGRESSION_FAIL

DEPLOYMENT_FAILED_ROLLED_BACK.
```

---

# 63. PASS criteria

PASS requires:

```text
three-axis visible on every stock message

REVIEW wording safe

no mechanical stance mapping

price/timing cannot mutate core direction

price/timing cannot create holder fundamental stance

expectation/valuation duplicate anchor count = 0

leading-market source contract safe

completed vs leading market separated

as-of timestamps present

futures never create Business Delta

known presentation defects fixed

required model reproof PASS

full tests PASS

deploy health PASS

manual current-data smoke test PASS

unsupported numeric claims = 0

internal metadata leaks = 0

production automated writes/sends = 0

scheduler remains paused.
```

---

# 64. Failure handling — source unavailable

If no safe free/provider source exists for one leading-market component:

Do NOT fabricate.

If:

```text
US futures safe, KR night futures unavailable
```

report exact partial status.

Because the user explicitly requested night-futures reflection,
top-level should be:

```text
LEADING_FUTURES_SOURCE_CONTRACT_BLOCKED
```

unless a product decision explicitly accepts partial coverage.

Do not silently declare full PASS.

---

# 65. Failure handling — model contract

If separating price/timing causes systematic unexpected decision failures:

Do NOT patch output enums.

Report:

```text
exact affected tickers

old vs new decision

fundamental evidence change? no

price/timing ownership effect

whether change is policy-compatible.
```

If hard semantic/policy violation:

stop.

If only valid judgment changes:

they are diagnostic.

---

# 66. Failure handling — expectation/valuation

If an overlap classifier cannot be constructed without a new semantic engine:

prefer a prompt/evidence-ownership clarification
over a heuristic score.

Do not build a hidden numeric penalty system.

If ambiguity remains:

```text
stop with a bounded expectation-valuation evidence ownership task.
```

---

# 67. No decision resolver

Forbidden:

```text
if valuation discounted → force BUY

if expectation high → cap at HOLD

if price below confirmation → force WAIT/HOLD

if holder HOLDABLE → prevent SELL

if new-buyer WAIT → force HOLD.
```

The three axes are intentionally independent.

---

# 68. Required forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-m12br-baseline-freeze

03-m12bs-scope-freeze

04-monitored-decision-ownership-callgraph

05-googl-price-timing-contamination-reproduction

06-expectation-valuation-overlap-reproduction

07-leading-market-provider-inventory

08-leading-market-source-decision

09-leading-market-session-contract

10-user-facing-three-axis-copy-contract.
```

---

# 69. Required implementation artifacts

Produce:

```text
11-three-axis-renderer-implementation

12-review-user-copy-implementation

13-core-price-timing-ownership-implementation

14-expectation-valuation-overlap-implementation

15-leading-market-snapshot-implementation

16-us-futures-collection-implementation

17-kr-night-futures-collection-implementation

18-market-message-leading-block-implementation

19-us-asof-heading-repair

20-cpng-truncation-repair

21-047810-internal-label-repair.
```

If one futures source uses an existing connector,
artifact names may reference that connector instead.

---

# 70. Required deterministic proof artifacts

Produce:

```text
22-three-axis-renderer-tests

23-review-copy-tests

24-mechanical-mapping-negative-tests

25-googl-core-timing-regression

26-core-timing-immutability-tests

27-expectation-valuation-overlap-tests

28-futures-session-freshness-tests

29-futures-change-basis-tests

30-completed-vs-leading-market-render-tests

31-futures-fundamental-ownership-negative-tests

32-existing-presentation-regressions.
```

---

# 71. Required model reproof artifacts

If model-facing change:

```text
33-model-facing-change-classification

34-frozen-monitored-reproof-manifest

35-frozen-monitored-reproof-results

36-frozen-fresh-reproof-manifest-if-required

37-frozen-fresh-reproof-results-if-required

38-reproof-decision.
```

If no model-facing change:

mark these:

```text
NOT_REQUIRED_RENDERER_DETERMINISTIC_ONLY
```

with code-hash evidence.

---

# 72. Required deploy/smoke artifacts

Produce:

```text
39-full-local-test-result

40-ruff-diff-result

41-predeploy-feature-gates

42-deployment-result

43-deployed-sha-health

44-current-leading-market-collection

45-current-us-market-message

46-current-kr-market-message

47-current-stock-message-manifest

48-current-all-messages

49-postrepair-message-validation-matrix

50-postrepair-googl-review

51-postrepair-known-issue-review

52-production-firewall-proof.
```

---

# 73. Required final decisions

Produce:

```text
53-three-axis-decision-contract-decision

54-core-timing-separation-decision

55-expectation-valuation-overlap-decision

56-leading-market-context-decision

57-message-quality-decision

58-automation-enable-readiness-decision

59-next-scope-decision

60-program-completion.
```

---

# 74. Program-completion fields

Include at least:

```text
base_main_sha
implementation_branch
implementation_head_sha
deployed_sha

three_axis_contract_version

stock_message_count
three_axis_visible_count
three_axis_missing_count

review_message_count
review_copy_safe_count

mechanical_stance_mapping_count

price_timing_in_core_anchor_count
price_timing_in_holder_anchor_count

expectation_valuation_overlap_case_count
expectation_valuation_duplicate_anchor_count

leading_market_contract_version

us_futures_source_status
us_futures_instrument_count
us_futures_asof

kr_night_futures_source_status
kr_night_futures_instrument_count
kr_night_futures_asof

stale_futures_presented_as_current_count
completed_session_overwritten_by_futures_count
futures_to_business_delta_violation_count
futures_to_holder_fundamental_violation_count

us_market_asof_heading_status
cpng_terminal_phrase_status
ticker_047810_internal_label_status

gooogl_or_googl_regression_ticker
googl_overall_direction_before
googl_overall_direction_after
googl_new_buyer_after
googl_holder_after
googl_price_timing_core_anchor_count_after
googl_expectation_valuation_overlap_class

model_prompt_semantic_change_count
model_schema_semantic_change_count
canonical_semantic_service_change_count
decision_policy_change_count

monitored_reproof_required
monitored_reproof_status
fresh_reproof_required
fresh_reproof_status

focused_test_result
full_test_result
ruff_result
git_diff_check

deployment_result
deployment_health_status

current_market_message_count
current_stock_message_count

unsupported_numeric_claim_count
internal_metadata_leak_count

production_db_mutations
assessment_production_writes
warning_production_mutations
notification_production_queue_writes
production_sends

v2_production_writer_enabled
v2_production_read_preference_enabled
v2_production_warning_enabled
v2_production_outbox_delivery_enabled

scheduler_mutation_count
automatic_monitoring_resume

top_level_result

automation_enable_readiness

next_scope

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count.
```

Use the correct key spelling:

```text
googl_...
```

not a typo, in the actual implementation report.

---

# 75. Expected clean outcome

If all three requested improvements work:

```text
top_level_result =
THREE_AXIS_LEADING_MARKET_MESSAGE_REPAIR_PASS

three_axis_missing_count = 0

mechanical_stance_mapping_count = 0

price_timing_in_core_anchor_count = 0

price_timing_in_holder_anchor_count = 0

expectation_valuation_duplicate_anchor_count = 0

stale_futures_presented_as_current_count = 0

completed_session_overwritten_by_futures_count = 0

futures_to_business_delta_violation_count = 0

futures_to_holder_fundamental_violation_count = 0

US as-of issue = fixed

CPNG phrase issue = fixed

047810 internal label = fixed

unsupported_numeric_claim_count = 0

internal_metadata_leak_count = 0

production automated writes/sends = 0

scheduler remains paused

automation_enable_readiness =
READY_FOR_EXPLICIT_USER_REVIEW.
```

No required GOOGL enum.

---

# 76. Local/production firewall

Allowed:

```text
bounded code changes

tests

required frozen model reproof

deploy via current existing mechanism

read-only/current provider collection

manual message generation.
```

Forbidden:

```text
production assessment writes

warning state mutation

notification queue writes

real notification sends

scheduler resume

monitoring registration/stop

V2 production gate enablement

force push

raw model artifact remote push.
```

---

# 77. Artifact integrity

Final report:

```text
hash mismatch = 0

size mismatch = 0

secret scan failure = 0.
```

Do not package provider/deployment secrets.

---

# 78. Final task principle

The current system already produces semantically valid monitored decisions,
but the first live message review exposed three product-level improvements:

```text
the three decision dimensions exist internally
but are not visible enough to the user;

price/timing can appear inside the core investment-direction explanation,
making a GOOGL-like fundamentally attractive-but-timing-unconfirmed case
look more conservative than intended;

and market messages stop at completed cash-session data,
without a clearly separated current overnight/leading-futures view.
```

The correct repair is:

```text
expose all three decision axes

→ keep overall_direction fundamental/economic

→ route price/confirmation/technical signals to new-buyer timing and price view

→ keep holder fundamental

→ prevent the same valuation evidence from being counted twice
   as both "high expectation" and "expensive valuation"

→ preserve genuinely independent expectation evidence

→ add validated US futures + KR night/evening futures as a separate current leading block

→ never overwrite completed-session facts

→ never let futures create Business Delta or holder fundamental risk

→ fix the three known presentation defects

→ formally re-prove any model-facing changes

→ deploy and regenerate all current messages

→ keep automation OFF until the user reviews the improved output.
```

Do NOT:

```text
hard-code GOOGL BUY

create a bullish bias

turn WAIT into HOLD

turn SELL into REDUCE

build a hidden score resolver

treat futures as completed market returns

treat futures as business evidence

double-count valuation and expectations

enable automation automatically.
```
