# Thesis Monitor — Maturity Polarity Single-Source Convergence + Full22 Reproof + Final Market-Context Handoff

## 0. Task identity

Suggested work-instruction filename:

```text
20260916-maturity-polarity-single-source-convergence-full22-reproof-final-market-context-handoff.md
```

Suggested result bundle:

```text
thesis-monitor-20260916-maturity-polarity-single-source-convergence-full22-reproof-final-market-context-handoff-report.zip
```

Master-workflow phase:

```text
M12BZ — Reuse Existing Polarity Architecture, Do Not Invent Another One

TRACK A — Stage-2 maturity-reference polarity convergence
  A1. Freeze all successful M12BY batch/identity closure work
  A2. Reproduce the exact CORZ maturity_reference_polarity_overlap
  A3. BEFORE writing a repair, audit the existing 2026-08-29
      decision-evidence-polarity-v1 implementation and current consumers
  A4. Determine whether current Stage-2 maturity validation duplicates,
      bypasses, or conflicts with that existing polarity architecture
  A5. Determine the correct atomic identity for maturity support/opposition:
      source ref vs canonical claim/subclaim identity
  A6. Reuse existing canonical polarity/claim ownership services wherever possible
  A7. Do NOT build a second free-form polarity classifier
  A8. Preserve fail-closed behavior when claim-level disambiguation is impossible
  A9. Add mixed-source positive/negative fixtures
  A10. Run full deterministic regression
  A11. Create a NEW complete US14 + KR8 proof generation
  A12. Run all required calls from call 1
  A13. No fallback / judge / repair / selective rerun

TRACK B — Market-context readiness preservation
  B1. Freeze recovered Kiwoom KOSPI200 night-futures implementation
  B2. Freeze restored US Treasury DGS3/DGS5/DGS10/DGS30 + DFII10 + T10YIE
  B3. Re-run local market-context regressions
  B4. Audit exact Kiwoom read-only gateway configuration requirements
      without exposing or fabricating credentials
  B5. If an authenticated read-only gateway is already configured, perform
      ONE capability/quote smoke with ZERO order calls
  B6. If unavailable, produce an exact operator enablement contract
      (environment/config NAMES only, never secret values)
  B7. Do NOT deploy in M12BZ
```

Important anti-repeat rule:

```text
The current maturity-polarity failure MUST first be compared against the
existing 2026-08-29 polarity repair before any new polarity logic is written.
```

The user has repeatedly asked to avoid rebuilding functionality that already exists
on another path.

M12BZ must explicitly answer whether this is another path-convergence defect.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260916-fundamental-core-batch-completeness-identity-closure-full22-reproof-market-context-final-readiness-report.zip
```

Verified SHA-256:

```text
07459f1a9e84c56b875ea91a54678e9deb70eecdf7dfbba73460a1c124005927
```

Recompute independently.

Sidecar must match exactly.

Independent archive verification:

```text
artifact manifest payload count = 141

ZIP entries =
141 indexed payloads
+ artifact-manifest.json
= 142

missing = 0

extra = 0

hash mismatch = 0

size mismatch = 0.
```

Recompute secret scan independently.

---

# 2. M12BY deterministic success — freeze

M12BY closed the Fundamental Core batch/identity class.

Contract:

```text
fundamental-core-batch-identity-v1.
```

Successful deterministic/model results before Stage-2:

```text
all five reached US FUNDAMENTAL_CORE batches =
PASS

US core subjects =
14 / 14

batch cardinality failures =
0

ticker-set failures =
0

duplicate tickers =
0

missing tickers =
0

extra tickers =
0

top-level identity mismatches =
0

exact-ref violations =
0

IBM present exactly once =
true.
```

Dynamic schema capabilities confirmed:

```text
equal minItems/maxItems =
supported

ticker enum =
supported.
```

Do NOT reopen batch completeness or identity closure in M12BZ.

---

# 3. M12BY local regression baseline

Freeze:

```text
focused =
167 passed, 3 skipped

market focused =
94 passed

full local =
4035 passed, 63 skipped, 2 warnings

Ruff =
PASS

git diff --check =
PASS.
```

No production mutation occurred.

---

# 4. Exact M12BY blocker

Generation:

```text
20260916-uskr22-m12by-20260915T232729Z-3a22a8fb167e
```

Planned calls:

```text
16.
```

Started/completed/usable:

```text
6 / 6 / 6.
```

The run stopped at:

```text
US Stage-2 batch 1
call ordinal 6.
```

Ticker:

```text
CORZ.
```

Failure:

```text
maturity_reference_polarity_overlap.
```

Path:

```text
$.candidates[0].driver_maturity[2].
```

Overlapping ref:

```text
decision-evidence:acea5134d19f8ded2449.
```

The same ref appeared in both:

```text
supporting_evidence_refs

contradicting_evidence_refs.
```

The current Pydantic validator failed closed.

Do NOT disable the failure before understanding whether the ref is an atomic polarity unit.

---

# 5. Exact CORZ maturity row — freeze

The failed row was approximately:

```text
driver =
"높은 기대에 비해 실행과 현금흐름 검증이 덜 성숙하다."

maturity =
MIXED

as_of =
2026-09-15

supporting refs =
[
  decision-evidence:464fa6687c0246031611,
  decision-evidence:acea5134d19f8ded2449
]

contradicting refs =
[
  decision-evidence:acea5134d19f8ded2449
].
```

This is not a fabricated-ref failure.

All refs are exact catalog members.

---

# 6. Critical mixed-source fact

The overlapping source:

```text
decision-evidence:acea5134d19f8ded2449
```

is NOT a simple one-polarity fact.

Its frozen thesis statement includes BOTH:

Positive / thesis-supporting content:

```text
AI/HPC colocation transition is materially advanced

~83% of revenue comes from colocation

colocation gross margin ~59%

437MW billing

~1.1GW leased customer power

large contracted/potential value.
```

Negative / thesis-risk content:

```text
high CAPEX

~$4.3B long-term debt

potential dilution

internal-control issues.
```

Therefore source-ref identity alone may be too coarse
to represent claim polarity.

M12BZ must NOT assume:

```text
one ref = one polarity.
```

---

# 7. Historical polarity contract already exists

Repository state explicitly records:

```text
contract =
decision-evidence-polarity-v1

instruction commit =
0bba7c9

implementation commit =
86b9fc44006c45431ccc1822131df3b4a74eb1ca

branch =
codex/20260829-decision-evidence-polarity-renderer-p1-repair.
```

Historical design statement:

```text
Decision-relative support/opposition remains intact,
while decision-evidence-polarity-v1 independently owns
BULLISH, BEARISH, and NEUTRAL claims.
```

The production canary renderer and artifact validator consumed the same structured plan.

No free-form sentiment classifier or ticker exception was allowed.

This architecture must be audited BEFORE creating any new polarity logic.

---

# 8. Historical polarity proof — freeze

Historical 2026-08-29 result:

```text
GOOGL bullish evidence no longer appeared under SELL

RXRX neutral quality evidence no longer appeared under SELL

two historical BUY fixtures passed common polarity validation

003690 / 000660 / GOOGL / RXRX decision outputs remained unchanged

polarity_repair_changed_decision = 0

full local pytest then =
1903 PASS.
```

This is strong evidence that claim-level polarity separation was already solved
for another decision/rendering path.

M12BZ must determine why Stage-2 maturity does not consume the same ownership.

---

# 9. Required provenance audit before repair

Inspect the historical commit and current code for:

```text
decision-evidence-polarity-v1

structured claim representation

claim IDs / subclaim IDs

BULLISH / BEARISH / NEUTRAL ownership

decision-relative support/opposition representation

renderer consumers

validator consumers

packet adapters.
```

Record:

```text
historical module/function

current module/function

still present?

still used?

input shape

output shape

claim identity granularity

current consumers

Stage-2 consumer status.
```

---

# 10. Classify current Stage-2 relationship to historical polarity contract

Choose exactly one:

```text
CANONICAL_POLARITY_SERVICE_ALREADY_REUSABLE_BUT_BYPASSED

CANONICAL_POLARITY_SERVICE_REQUIRES_THIN_STAGE2_ADAPTER

HISTORICAL_POLARITY_SERVICE_IS_RENDERER_ONLY_NOT_SEMANTICALLY_REUSABLE

HISTORICAL_POLARITY_SERVICE_REMOVED_OR_OBSOLETE

POLARITY_CONTRACT_CONFLICT_REQUIRES_DESIGN_AMENDMENT.
```

Do not write the repair before this classification.

---

# 11. Distinguish two different concepts

M12BZ must keep these separate:

## Absolute/decision evidence polarity

Examples:

```text
BULLISH

BEARISH

NEUTRAL.
```

Owned by the existing polarity contract if still canonical.

## Driver-relative maturity relationship

Examples:

```text
supports this specific driver statement

contradicts this specific driver statement.
```

A BULLISH claim may contradict a bearish driver.

A BEARISH claim may support a bearish driver.

Do NOT equate:

```text
supporting = BULLISH

contradicting = BEARISH.
```

The old polarity architecture is reusable only where its semantics match.

---

# 12. Required atomic identity decision

Determine the correct unit for driver-maturity support/opposition.

Candidates:

```text
SOURCE_REF

CANONICAL_ATOMIC_CLAIM_ID

POLARITY_QUALIFIED_CLAIM_ID

EXISTING_STRUCTURED_PLAN_CLAIM_ID

OTHER_EXISTING_CANONICAL_SUBCLAIM_ID.
```

Acceptance principle:

```text
The same ATOMIC claim must never be both supporting and contradicting
for the same driver maturity row.
```

But:

```text
the same SOURCE document/ref may legitimately contain distinct atomic claims
on opposite sides.
```

---

# 13. Do not weaken to raw ref overlap acceptance

Forbidden shortcut:

```text
simply remove the supporting/contradicting disjointness check
because acea... is mixed.
```

That would allow the exact same undifferentiated claim
to appear on both sides.

If source-level overlap can be valid,
claim-level identity must preserve disjointness.

---

# 14. Do not force ref-level disjointness if source is mixed

Also forbidden shortcut:

```text
tell the model "never reuse the same source ref"
without providing a more precise claim identity
when the source contains multiple opposing claims.
```

That can force the model to hide valid contradictory evidence
or cite a weaker unrelated ref merely to satisfy the validator.

The contract must reflect actual evidence granularity.

---

# 15. Preferred architecture if historical atomic claims already exist

If the current/historical polarity service already exposes stable atomic claim IDs:

reuse them.

Preferred Stage-2 maturity representation may become conceptually:

```text
supporting_claim_refs

contradicting_claim_refs
```

where each claim ref retains its parent source evidence ref for provenance.

Do not invent new claim IDs if canonical ones already exist.

---

# 16. Preferred architecture if historical plan has polarity-qualified claims

If the prior structured plan owns claims like:

```text
claim_id

source_ref

polarity

text/proposition

basis
```

then Stage-2 should consume a deterministic projection of that plan.

Driver-relative support/opposition must reference those existing claim identities.

No new free-form sentiment inference.

---

# 17. If no reusable atomic claim identity exists

Do NOT immediately relax the validator.

Stop before model calls with:

```text
MATURITY_POLARITY_ATOMIC_CLAIM_IDENTITY_GAP.
```

Produce a bounded design for:

```text
deterministic claim atomization / ownership
```

that reuses historical polarity semantics where possible.

Do not perform a broad evidence-packet redesign and full reproof in one unbounded task.

---

# 18. Claim atomization must not use a new model call

If deterministic atomization is required:

it must derive from existing structured source fields / existing canonical claim objects.

Do NOT call an LLM to split one mixed source into positive/negative sentences
inside the validator.

No free-form sentiment classifier.

---

# 19. Existing compound thesis text

For legacy/mixed thesis evidence such as CORZ acea...,
audit whether the project already created:

```text
accepted decision claims

driver claims

polarity claims

thesis subclaims
```

elsewhere.

Prefer reusing those.

Do not write a new Korean sentence splitter
unless no structured ownership exists and a separate bounded task approves it.

---

# 20. Stage-2 model-facing contract

After canonical claim identity is resolved,
the Stage-2 prompt/schema must make the allowed maturity evidence identities explicit.

Use exact catalog restrictions analogous to:

```text
model-output-exact-ref-fidelity-v1.
```

If claim IDs are used:

```text
claim refs must be exact catalog members.
```

No invented claim IDs.

---

# 21. Source provenance retention

Every maturity claim identity must retain traceability to:

```text
parent source evidence ref

source date

source category

original statement / structured fact

polarity metadata if applicable.
```

The user-visible message does not need these IDs,
but the audit must remain possible.

---

# 22. Maturity support/opposition disjointness

After repair, enforce:

```text
supporting atomic claim set
∩
contradicting atomic claim set
=
empty.
```

Source-ref sets may overlap ONLY when:

```text
the overlapping parent source contains distinct,
canonically identified atomic claims
assigned to opposite sides.
```

No claim-level overlap.

---

# 23. Mixed-source positive fixture

Use an evidence source analogous to CORZ acea... containing:

```text
one positive operating-progress claim

one negative capital-structure claim.
```

For a mixed maturity driver:

```text
positive child claim may contradict the driver

negative child claim may support the driver

same parent source is allowed

atomic claim IDs remain disjoint.
```

Expected:

```text
PASS.
```

---

# 24. Same-atomic-claim negative fixture

The exact same canonical atomic claim is placed in both:

```text
supporting

contradicting.
```

Expected:

```text
hard FAIL.
```

---

# 25. Single-polarity-source overlap negative fixture

A source with only one atomic claim is used on both sides.

Expected:

```text
hard FAIL.
```

No special-case allowance based on same parent ref.

---

# 26. Missing-claim-identity negative fixture

A mixed parent source is used on both sides,
but there is no canonical atomic child identity proving distinct claims.

Expected:

```text
fail closed.
```

Do not infer the split from free text at validation time.

---

# 27. Historical polarity regression fixtures

Re-run the important 2026-08-29 controls if available:

```text
GOOGL bullish evidence polarity

RXRX neutral quality evidence polarity

DB/insurance polarity control

SK hynix polarity control

historical BUY fixtures.
```

Required:

```text
existing decision-evidence-polarity-v1 behavior unchanged.
```

Do not break the old renderer/canary semantics.

---

# 28. No decision-policy change

Expected:

```text
decision thresholds unchanged

BUY/HOLD/SELL semantics unchanged

new-buyer semantics unchanged

holder semantics unchanged

BusinessDelta unchanged

market expectation unchanged

valuation unchanged.
```

The repair is evidence identity/ownership convergence only.

---

# 29. Freeze M12BY successful batch identity closure

Do NOT change:

```text
fundamental-core-batch-identity-v1.
```

Required regression:

```text
cardinality failure = 0

ticker-set failure = 0

duplicate = 0

missing = 0

extra = 0

identity mismatch = 0.
```

---

# 30. Freeze Stage-2 typed contracts

Do NOT change:

```text
Stage-2 typed-string closure

driver_maturity concrete date requirement

exact-ref fidelity

frozen-core ownership

post-confirmation maturity rule.
```

Required regressions:

```text
noncanonical date = 0

symbolic date fabrication = 0

fabricated ref = 0

exact-ref violation = 0

frozen-core false positive = 0

maturity contract conflict = 0.
```

---

# 31. Freeze three-axis / timing / expectation-valuation

Do NOT change:

```text
three-axis renderer

REVIEW copy

core vs price/timing ownership

holder fundamental ownership

expectation/valuation overlap ownership.
```

No GOOGL target direction.

---

# 32. Deterministic pre-model gate

Before model calls run:

```text
historical polarity provenance audit

existing polarity regression tests

new maturity atomic-identity tests

mixed-source positive fixture

same-atomic-claim negative fixture

single-polarity overlap negative fixture

missing-claim-identity negative fixture

batch completeness regressions

exact-ref regressions

Stage-2 typed-date regressions

frozen-core ownership regressions

post-confirmation regressions

three-axis/core-timing/expectation regressions

BusinessDelta regressions

full local pytest

Ruff

git diff --check.
```

All must PASS.

If no safe atomic identity architecture is available:

do NOT run model calls.

---

# 33. Frozen full22 inputs

Use the exact frozen monitored packets:

US:

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
WULF.
```

KR:

```text
000660
003690
005490
005930
010120
012450
047810
086280.
```

Packet hashes:

```text
US =
2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228

KR =
819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597.
```

No provider refetch.

No semantic packet mutation.

A deterministic claim-identity projection is allowed only if it is fully derived
from already frozen canonical evidence and separately hash-audited.

---

# 34. New complete proof generation

Any Stage-2 model-facing maturity evidence contract change requires:

```text
NEW full proof generation.
```

Do NOT reuse or stitch:

```text
M12BY

M12BX

M12BW

earlier partial outputs.
```

Run complete architecture from call 1.

---

# 35. Model

Use:

```text
gpt-5.6-sol

reasoning effort =
xhigh.
```

No Astra.

No fallback.

No judge.

No repair model.

No selective rerun.

No per-ticker retry.

---

# 36. Full22 PASS criteria

Require:

```text
22 / 22 subjects represented

all required calls complete

Fundamental Core batch completeness = PASS

Fundamental Core identity = PASS

Fundamental Core exact refs = PASS

Fundamental Core semantics = PASS

Stage-2 schema = PASS

Stage-2 typed contract = PASS

Stage-2 exact refs = PASS

Stage-2 semantics = PASS

maturity atomic claim identity = PASS

maturity same-atomic-claim overlap count = 0

maturity unproven source-overlap count = 0

noncanonical dates = 0

symbolic date fabrication = 0

fabricated refs/claim refs = 0

frozen-core false positives = 0

post-confirmation maturity conflicts = 0

final compositions = 22

BusinessDelta hard failures = 0

price/timing core mutation = 0

price/timing holder mutation = 0

expectation/valuation duplicate anchors = 0

core mutation = 0

canonical bypass = 0

legacy duplicate semantic engine participation = 0

fallback / judge / repair / selective rerun = 0.
```

No target direction distribution.

---

# 37. CORZ required dossier

Report:

```text
driver maturity row

driver statement

maturity

supporting source refs

contradicting source refs

supporting atomic claim IDs

contradicting atomic claim IDs

parent-source overlap

atomic-claim overlap

absolute polarity metadata

driver-relative support/opposition

date ownership.
```

Required:

```text
atomic claim overlap = 0.
```

If the same parent source appears on both sides,
the distinct child-claim identities must be visible in the audit.

---

# 38. GOOGL / SKHY / RXRX / IBM regressions

GOOGL:

```text
price/timing core anchor = 0

expectation/valuation duplicate anchor = 0

frozen-core ownership PASS.
```

SKHY:

```text
driver_maturity dates canonical

no symbolic/padded date.
```

RXRX:

```text
fabricated ref = 0.
```

IBM:

```text
core present exactly once.
```

No target investment direction.

---

# 39. Three-axis local render

After clean proof:

```text
종합 방향 visible = 22

신규 관찰자 visible = 22

보유자 visible = 22

REVIEW copy safe

mechanical stance mapping = 0.
```

No deployment in M12BZ.

---

# 40. TRACK B — freeze restored market context

Do NOT repeat historical recovery.

Kiwoom recovered implementation:

```text
commit =
28f4f70700046f98d5d899ee491d3e5f45922e9a

contract =
krx-night-futures-session-quote-v1

reuse =
HISTORICAL_IMPLEMENTATION_REUSABLE_WITH_ADAPTER

KOSPI200 2026-09-01 =
PASS

KOSPI200 2026-09-02 =
PASS

KOSPI200 2026-09-03 =
PASS

KOSDAQ150 historical actual fixture =
NOT FOUND.
```

Current local adapter:

```text
krx-night-leading-market-adapter-v1

status =
PASS.
```

No fabricated change_pct without a source-owned basis.

---

# 41. Freeze restored US Treasury curve

Historical final implementation:

```text
commit =
4407cd11a78579e11681b503b2d4e72ee3c3d60f

provider =
FRED.
```

Nominal Treasury series:

```text
DGS3

DGS5

DGS10

DGS30.
```

Direct companion series:

```text
DFII10 =
10Y real yield

T10YIE =
10Y breakeven inflation.
```

Current local:

```text
parser = PASS

bp change = PASS

as-of = PASS

message rendering = PASS.
```

Frequency:

```text
daily
```

not intraday live.

---

# 42. Kiwoom gateway gap — current factual state

M12BY:

```text
gateway configured =
false

URL configured =
false

API key configured =
false

transport type =
null

live read-only calls =
0

order calls =
0.
```

Status:

```text
LIVE_KIWOOM_NIGHT_GATEWAY_UNAVAILABLE.
```

This is a runtime/config gap,
not a missing parser/adapter.

---

# 43. Historical Kiwoom auth contract

Recovered historical live path:

```text
Windows Kiwoom OpenAPI+ authenticated gateway

capability endpoint =
/v1/night-futures/capabilities

consumer scope =
read-only market data

order/account operations required by consumer =
false.
```

M12BZ must identify the current code's configuration contract for this gateway.

Do NOT expose secret values.

---

# 44. Gateway configuration audit

Inspect current configuration/code for the exact variable/config NAMES needed for:

```text
gateway base URL

API/auth token or key if required

timeout

read-only capability mode

instrument/contract selection if configured.
```

Output:

```text
name

required/optional

safe description

currently configured yes/no

secret yes/no.
```

Never output the value of a secret field.

---

# 45. No trading permission

The user has approved read-only market-data access,
not trading.

M12BZ may perform a live smoke only if the existing gateway contract can guarantee
the path is quote/capability-only.

Required:

```text
order call count = 0

modify call count = 0

cancel call count = 0

portfolio mutation count = 0.
```

If that guarantee cannot be made:

do NOT call the gateway.

---

# 46. Conditional live Kiwoom smoke

If the configured authenticated read-only gateway exists:

perform ONE bounded sequence:

```text
capability check

KOSPI200 night-futures read-only quote
```

according to the existing historical/current API contract.

Record:

```text
instrument

session

business date

price/level fields

reference basis if actually owned

as-of if actually owned

source freshness.
```

Do not send orders.

If the source does not own a safe comparison basis:

```text
suppress change/change_pct.
```

---

# 47. If gateway is still unavailable

Do NOT build a new connector.

Produce an exact operator enablement checklist containing ONLY:

```text
required config variable names

required service/platform type

required read-only capability

expected health/capability endpoint

local verification command shape with placeholders

security restrictions.
```

No secret values.

Next scope may be:

```text
KIWOOM_READONLY_GATEWAY_CONFIGURATION_AND_FINAL_MESSAGE_SMOKE.
```

---

# 48. Market-context regressions

Re-run locally:

```text
Kiwoom 9/1–9/3 adapter fixtures

basis-suppression tests

KOSPI200 night message preview

FRED DGS3/DGS5/DGS10/DGS30 parser/render

DFII10/T10YIE parser/render

Treasury bp-change tests

Treasury per-series as-of tests

completed-session / daily-rates / night-leading layering

night-futures → BusinessDelta negative test

night-futures → holder fundamental negative test

Treasury → BusinessDelta negative test

Treasury → holder fundamental negative test.
```

Expected:

```text
PASS.
```

---

# 49. Market message target after final deployment

Freeze the intended hierarchy for the later final smoke:

```text
1. 완료된 시장

2. 금리·인플레이션
   - 미국채 3Y
   - 미국채 5Y
   - 미국채 10Y
   - 미국채 30Y
   - 10Y 실질금리
   - 10Y 기대인플레이션

3. 현재 선행시장 / 야간선물
   - KOSPI200 night/evening futures when safe/current

4. 해석

5. 다음 확인.
```

Every layer owns its own as-of date/time.

No synthetic common timestamp.

---

# 50. No deployment in M12BZ

Even if Track A passes and a live Kiwoom smoke succeeds:

```text
deployments = 0

main merges = 0.
```

M12BZ produces readiness evidence.

The later final task will:

```text
merge/deploy

collect current US/KR data

render Treasury + night futures + market messages

render all monitored ticker messages

review three-axis GOOGL/etc output

keep automation/sends off until explicit review.
```

---

# 51. Track result taxonomy

TRACK A:

```text
MATURITY_POLARITY_SINGLE_SOURCE_CONVERGENCE_FULL22_PASS

MATURITY_POLARITY_ATOMIC_CLAIM_IDENTITY_GAP

FULL22_REPROOF_NEW_HARD_FAILURE

MODEL_TRANSPORT_INCOMPLETE

PREMODEL_TEST_GATE_FAILURE.
```

TRACK B:

```text
MARKET_CONTEXT_READY_KIWOOM_LIVE_READ_PASS

MARKET_CONTEXT_READY_KIWOOM_GATEWAY_UNAVAILABLE

MARKET_CONTEXT_REGRESSION.
```

---

# 52. Combined top-level result

Choose exactly one:

```text
M12BZ_MODEL_AND_MARKET_CONTEXT_READY_FOR_FINAL_SMOKE

M12BZ_MODEL_READY_KIWOOM_CONFIGURATION_PENDING

M12BZ_MODEL_CONTRACT_BLOCKED_MARKET_CONTEXT_READY

M12BZ_MULTIPLE_BLOCKERS.
```

---

# 53. Next scope rules

## Track A PASS + Kiwoom live read PASS

```text
next_scope =
FINAL_DEPLOY_CURRENT_US_KR_MARKET_AND_TICKER_MESSAGE_SMOKE_WITH_NIGHT_FUTURES_AND_TREASURY_CURVE.
```

## Track A PASS + Kiwoom gateway unavailable

```text
next_scope =
KIWOOM_READONLY_GATEWAY_CONFIGURATION_AND_FINAL_MESSAGE_SMOKE.
```

## Track A blocked on atomic identity design

```text
next_scope =
BOUNDED_MATURITY_ATOMIC_CLAIM_IDENTITY_CONVERGENCE_REPAIR.
```

Do NOT fall back to raw-ref overlap heuristics.

## Track A new hard failure

Choose the smallest bounded contract category from exact evidence.

No hotfix in M12BZ.

---

# 54. Production firewall

Required throughout:

```text
production DB mutations = 0

assessment production writes = 0

warning production mutations = 0

notification queue writes = 0

production sends = 0

monitoring registrations = 0

monitoring stops = 0

scheduler mutations = 0

automatic monitoring resume = 0

V2 production gates remain OFF

main merge = 0

deployment = 0

raw model artifact remote push = 0.
```

External model calls for the frozen full22 proof are authorized.

Conditional Kiwoom quote access is authorized only through the existing
read-only market-data path.

---

# 55. Required polarity provenance artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bz-scope-freeze

04-m12by-failure-freeze

05-corz-maturity-overlap-forensic

06-acea-mixed-evidence-forensic

07-historical-20260829-polarity-contract-freeze

08-historical-polarity-code-provenance

09-current-polarity-consumer-map

10-stage2-maturity-current-polarity-bypass-audit

11-polarity-contract-reuse-classification

12-maturity-atomic-identity-options

13-maturity-atomic-identity-decision

14-maturity-polarity-single-source-contract.
```

---

# 56. Required polarity implementation/tests

If a safe reuse/adapter exists:

```text
15-stage2-maturity-polarity-adapter-implementation

16-stage2-maturity-prompt-contract

17-stage2-maturity-schema-contract-if-required

18-mixed-parent-source-positive-fixture

19-same-atomic-claim-overlap-negative-fixture

20-single-polarity-source-overlap-negative-fixture

21-missing-atomic-identity-negative-fixture

22-cross-source-ordinary-maturity-fixture

23-historical-polarity-regression-suite

24-old-corz-output-offline-replay

25-no-freeform-polarity-classifier-proof.
```

If no safe atomic identity exists:

mark implementation artifacts:

```text
NOT_RUN_ATOMIC_IDENTITY_GAP
```

and stop Track A before model calls.

---

# 57. Required deterministic test artifacts

Produce:

```text
26-batch-identity-regressions

27-exact-ref-regressions

28-stage2-typed-contract-regressions

29-frozen-core-regressions

30-postconfirmation-regressions

31-three-axis-core-timing-expectation-regressions

32-business-delta-regressions

33-full-local-test-result

34-ruff-diff-result

35-model-facing-hash-manifest.
```

---

# 58. Required full22 proof artifacts

If Track A proceeds:

```text
36-frozen22-input-identity-manifest

37-new-full22-generation-manifest

38-full22-call-plan-with-polarity-contract-hashes

39-fundamental-core-model-artifacts

40-stage2-model-artifacts

41-fundamental-core-batch-identity-audit

42-exact-ref-fidelity-audit

43-stage2-typed-contract-audit

44-maturity-atomic-identity-audit

45-maturity-polarity-audit

46-frozen-core-ownership-audit

47-postconfirmation-maturity-audit

48-price-timing-immutability-audit

49-expectation-valuation-audit

50-business-delta-audit

51-canonical-semantic-audit

52-final-composition-audit

53-per-ticker-result-matrix

54-corz-polarity-dossier

55-googl-skhy-rxrx-ibm-regression-dossier

56-three-axis-render-audit

57-track-a-decision.
```

---

# 59. Required market-context artifacts

Produce independently:

```text
58-kiwoom-restoration-freeze

59-treasury-restoration-freeze

60-market-context-local-regression

61-kiwoom-gateway-config-contract-audit

62-kiwoom-gateway-current-config-status

63-kiwoom-readonly-capability-smoke-if-available

64-kiwoom-zero-trading-call-proof

65-us-treasury-curve-local-preview

66-kr-night-market-local-preview

67-market-time-layer-regression

68-market-context-fundamental-ownership-negative-tests

69-track-b-decision.
```

---

# 60. Required final decisions

Produce:

```text
70-maturity-polarity-convergence-decision

71-full22-reproof-decision

72-message-model-contract-readiness

73-market-context-readiness

74-deployment-readiness

75-next-scope-decision

76-master-workflow-update

77-program-completion.
```

---

# 61. Program-completion fields

Include at least:

```text
base_main_sha
implementation_branch
implementation_head_sha

latest_result_zip_sha256
latest_result_integrity

m12by_failure_ticker
m12by_failure_path
m12by_overlap_source_ref

m12by_overlap_source_is_mixed_claim_evidence

historical_polarity_contract
historical_polarity_instruction_commit
historical_polarity_implementation_commit
historical_polarity_service_present
historical_polarity_current_consumer_count

stage2_maturity_polarity_reuse_classification

maturity_atomic_identity_kind
maturity_atomic_identity_contract_version

mixed_parent_source_allowed_with_distinct_claims
same_atomic_claim_overlap_allowed

freeform_polarity_classifier_count

maturity_source_ref_overlap_count
maturity_atomic_claim_overlap_count
maturity_unproven_source_overlap_count

fundamental_core_batch_contract_change_count
exact_ref_contract_change_count
stage2_typed_contract_change_count
frozen_core_ownership_change_count
postconfirmation_contract_change_count
three_axis_contract_change_count
expectation_valuation_contract_change_count
business_delta_contract_change_count
persistence_v2_contract_change_count

model_prompt_semantic_change_count
model_schema_semantic_change_count
canonical_semantic_classifier_change_count

focused_test_result
full_test_result
ruff_result
git_diff_check

frozen_us_packet_sha
frozen_kr_packet_sha
frozen_ticker_count

new_reproof_generation_id
planned_model_call_count
model_calls_started
model_calls_completed
model_calls_with_usable_output

fundamental_core_valid_count
fundamental_core_batch_failure_count
fundamental_core_identity_failure_count
fundamental_core_exact_ref_violation_count

stage2_schema_valid_count
stage2_semantic_valid_count
stage2_typed_contract_violation_count
stage2_exact_ref_violation_count
stage2_fabricated_ref_count
stage2_noncanonical_date_count

maturity_atomic_identity_failure_count
maturity_same_atomic_claim_overlap_count
maturity_unproven_source_overlap_count

frozen_core_revalidation_false_positive_count
postconfirmation_maturity_conflict_count

final_composition_valid_count

business_delta_hard_failure_count
price_timing_core_mutation_count
price_timing_holder_mutation_count
expectation_valuation_duplicate_anchor_count
core_mutation_count

canonical_bypass_count
legacy_duplicate_semantic_participation_count

wrapper_retry_count
fallback_model_call_count
judge_call_count
repair_call_count
selective_rerun_count

three_axis_visible_count
three_axis_missing_count

corz_parent_source_overlap_count
corz_atomic_claim_overlap_count

googl_price_timing_core_anchor_count
googl_expectation_valuation_overlap_class
skhy_noncanonical_date_count
rxrx_fabricated_ref_count
ibm_core_present_count

track_a_result

kiwoom_historical_commit
kiwoom_adapter_status
kiwoom_gateway_configured
kiwoom_gateway_required_config_names
kiwoom_gateway_secret_config_names
kiwoom_live_capability_reachable
kiwoom_live_readonly_call_count
kiwoom_live_order_call_count
kiwoom_live_modify_call_count
kiwoom_live_cancel_call_count

treasury_historical_commit
treasury_provider
treasury_nominal_series
treasury_real_series
treasury_breakeven_series
treasury_local_regression_status

market_context_time_layer_status
market_context_fundamental_violation_count

track_b_result

message_model_contract_readiness
market_context_readiness
deployment_readiness

production_db_mutations
assessment_production_writes
warning_production_mutations
notification_production_queue_writes
production_sends
scheduler_mutation_count
automatic_monitoring_resume

main_merges
deployments
remote_push_count
raw_model_artifact_remote_push_count

top_level_result
next_scope

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count.
```

Use:

```text
NOT_FOUND

NOT_APPLICABLE

NOT_MEASURED

LIVE_GATEWAY_UNAVAILABLE

NOT_RUN_ATOMIC_IDENTITY_GAP
```

where appropriate.

Do not replace unknown with zero.

---

# 62. Expected clean polarity architecture

Preferred result if the historical canonical claim architecture is reusable:

```text
historical_polarity_contract =
decision-evidence-polarity-v1

stage2_maturity_polarity_reuse_classification =
CANONICAL_POLARITY_SERVICE_REQUIRES_THIN_STAGE2_ADAPTER
or
CANONICAL_POLARITY_SERVICE_ALREADY_REUSABLE_BUT_BYPASSED

freeform_polarity_classifier_count =
0

same_atomic_claim_overlap_allowed =
false

mixed_parent_source_allowed_with_distinct_claims =
true

maturity_atomic_claim_overlap_count =
0

maturity_unproven_source_overlap_count =
0.
```

Do NOT force the exact reuse classification if code evidence differs.

---

# 63. Expected full22 clean result

If Track A proceeds and passes:

```text
track_a_result =
MATURITY_POLARITY_SINGLE_SOURCE_CONVERGENCE_FULL22_PASS

fundamental_core_valid_count = 22

stage2_semantic_valid_count = 22

maturity_atomic_identity_failure_count = 0

maturity_same_atomic_claim_overlap_count = 0

maturity_unproven_source_overlap_count = 0

exact-ref violations = 0

noncanonical dates = 0

postconfirmation conflicts = 0

final_composition_valid_count = 22

BusinessDelta hard failures = 0

price/timing core mutation = 0

price/timing holder mutation = 0

expectation/valuation duplicate anchors = 0

core mutation = 0

canonical bypass = 0

legacy duplicate semantic participation = 0

three_axis_visible_count = 22.
```

No forced investment directions.

---

# 64. Expected market-context state

Treasury local:

```text
provider =
FRED

nominal =
[DGS3, DGS5, DGS10, DGS30]

real =
[DFII10]

breakeven =
[T10YIE]

frequency =
daily

local regression =
PASS.
```

Kiwoom local:

```text
historical 9/1–9/3 =
PASS

LeadingMarketSnapshot adapter =
PASS

KOSPI200 =
supported locally

KOSDAQ150 =
unproven.
```

Kiwoom live:

```text
PASS_READ_ONLY
```

only when a configured authenticated gateway truly exists.

Otherwise:

```text
LIVE_GATEWAY_UNAVAILABLE.
```

No fake live readiness.

---

# 65. Failure handling

## A. Historical polarity service already solves the same claim identity

Reuse it.

Do NOT create another classifier.

## B. Historical polarity service is renderer-only

Document why it cannot own maturity semantics.

Then choose a thin adapter to existing atomic claim ownership if available.

Do not misrepresent renderer polarity as driver-relative support.

## C. No canonical atomic claim identity exists

```text
STOP Track A before model calls

MATURITY_POLARITY_ATOMIC_CLAIM_IDENTITY_GAP.
```

Do not relax overlap validation.

## D. Same atomic claim appears on both sides

Hard FAIL.

No exception.

## E. Mixed parent source has distinct canonical child claims

Allow parent-source overlap,
but only with disjoint canonical child claim IDs.

## F. New full22 hard failure

No repair inside M12BZ.

Market context work remains independently preserved.

## G. Kiwoom gateway absent

Do not build a new connector.

Produce exact configuration checklist without secret values.

---

# 66. Production firewall

M12BZ is non-deploying.

Required:

```text
production DB mutations = 0

assessment writes = 0

warning mutations = 0

notification queue writes = 0

production sends = 0

monitoring registrations = 0

monitoring stops = 0

scheduler mutations = 0

automatic monitoring resume = 0

V2 production gates remain OFF

main merges = 0

deployments = 0

raw model artifact remote pushes = 0.
```

External model calls for the frozen proof are allowed.

Kiwoom read-only market-data smoke is conditionally allowed as specified.

---

# 67. Final task principle

M12BY closed the Fundamental Core omission problem:

```text
IBM is now present exactly once,
all US Fundamental Core batches passed,
and batch identity is structurally closed.
```

The new failure is:

```text
CORZ driver maturity used one MIXED thesis source
on both the supporting and contradicting sides.
```

That source genuinely contains both:

```text
positive operating-progress claims
and
negative capital-structure/risk claims.
```

Therefore a raw ref-level disjointness rule may be too coarse.

More importantly,
this project already solved an evidence-polarity architecture on 2026-08-29:

```text
decision-evidence-polarity-v1

implementation =
86b9fc44006c45431ccc1822131df3b4a74eb1ca.
```

The correct next action is NOT another one-off prompt instruction.

It is:

```text
audit the existing polarity/claim architecture

→ reuse it if semantically compatible

→ keep absolute polarity separate from driver-relative support/opposition

→ identify the canonical atomic claim identity

→ forbid the SAME atomic claim on both sides

→ permit a mixed parent source on both sides only when distinct canonical child claims prove it

→ never use a new free-form sentiment classifier

→ run a wholly new complete 22-subject proof.
```

Market context is independently ready locally:

```text
Kiwoom KOSPI200 night futures recovered and adapted

Treasury DGS3/DGS5/DGS10/DGS30 restored

DFII10 and T10YIE restored.
```

The only current market runtime gap is the missing authenticated
read-only Kiwoom gateway configuration.

Do NOT:

```text
special-case CORZ

simply allow raw ref overlap

simply ban raw ref overlap

build another polarity engine

rerun the historical Kiwoom recovery

rewrite Treasury support

force a decision enum

merge/deploy

resume automation.
```
