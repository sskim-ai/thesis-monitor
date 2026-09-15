# Thesis Monitor — Stage-2 Typed Contract Closure + Full22 Reproof + Market Context Restoration

## 0. Task identity

Suggested work-instruction filename:

```text
20260916-stage2-typed-contract-closure-full22-reproof-market-context-restoration.md
```

Suggested result bundle:

```text
thesis-monitor-20260916-stage2-typed-contract-closure-full22-reproof-market-context-restoration-report.zip
```

Master-workflow phase:

```text
M12BX — Three Independent Tracks

TRACK A — Stage-2 typed-contract closure
  A1. Freeze all previously successful semantic/model contracts
  A2. Audit EVERY Stage-2 schema field that is currently represented as free string
  A3. Classify each string as genuinely free text vs typed/closed-domain data
  A4. Close date / datetime / enum / ID / ref / status / maturity / currency /
      instrument / session / contract-like fields structurally where safe
  A5. Fix driver_maturity[].as_of generically; do NOT patch "latest000..."
  A6. Prove the model can only emit valid typed values
  A7. Run a NEW full US14 + KR8 proof from call 1
  A8. No fallback / judge / repair / selective rerun

TRACK B — Recovered Kiwoom KOSPI200 night-futures reintegration
  B1. Do NOT search for the old implementation again
  B2. Reuse the recovered 2026-09-01 / 09-02 / 09-03 implementation and fixtures
  B3. Build the current LeadingMarketSnapshot adapter locally
  B4. Preserve completed-session vs night-session separation
  B5. Use read-only Kiwoom market-data access only if an authenticated gateway is available
  B6. Never fabricate reference/settlement/change_pct
  B7. Add market-message rendering/tests
  B8. Do NOT enable production automation or deploy in M12BX

TRACK C — Historical US Treasury curve provenance + restoration
  C1. Search history before writing new Treasury code
  C2. Specifically audit prior 5Y / 10Y / 30Y nominal Treasury display
  C3. Search DGS5 / DGS10 / DGS30 and user-facing 5년 / 10년 / 30년 labels
  C4. Also preserve any historical 10Y real-yield / breakeven implementation found
      (e.g. DFII10 / T10YIE or repository equivalents)
  C5. Reproduce historical fixtures/data contracts where available
  C6. If the historical supported source/connector still exists, wire the curve block
      into the current market-environment message locally
  C7. Do NOT invent a new provider before provenance search is complete
  C8. Do NOT call daily FRED-style data "live intraday" data
```

These tracks are independent after the deterministic repository/test gate.

A model-proof failure in Track A must NOT prevent Tracks B/C from completing.

A market-data integration failure in Tracks B/C must NOT cause semantic/model changes in Track A.

No deployment in M12BX.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260915-stage2-frozen-core-validation-scope-repair-full22-reproof-report.zip
```

Verified SHA-256:

```text
eba76698cb11d24c1d7c2347927ff8180f21b69f79c574223230246e334c8ffc
```

Recompute independently.

Sidecar must match exactly.

Latest artifact index:

```text
indexed payloads = 151

ZIP entries =
151 indexed payloads
+ artifact-manifest.json
= 152

artifact hash mismatch = 0

artifact size mismatch = 0

artifact secret scan failure = 0.
```

Recompute independently.

---

# 2. M12BW authoritative status

M12BW:

```text
status =
FAIL

top_level_result =
M12BW_FULL22_REPROOF_NEW_HARD_FAILURE

next_scope =
STAGE2_DRIVER_MATURITY_AS_OF_DATE_CONTRACT_REPAIR_AND_NEW_FULL22_REPROOF.
```

Deterministic tests before model proof:

```text
full local =
3998 passed, 63 skipped, 1 warning

Ruff =
PASS

git diff --check =
PASS.
```

New proof generation:

```text
20260915-uskr22-m12bw-20260915T145754Z-b2387c92ee05
```

Planned model calls:

```text
16
```

Started/completed/usable:

```text
8 / 8 / 8
```

The proof stopped on the first new hard failure.

---

# 3. Exact M12BW blocker — freeze

Ticker:

```text
SKHY
```

Stage:

```text
PRICE_TIMING / Stage-2

US batch 3

model call ordinal 8.
```

Field:

```text
$.candidates[2].driver_maturity[2].as_of
```

Invalid emitted value:

```text
latest00000000000
```

Failure class:

```text
STAGE2_DRIVER_MATURITY_AS_OF_NOT_CANONICAL_DATE.
```

Validator error:

```text
future_maturity_evidence:최신 재무자료의 검증 상태가 불충분하다.
```

This is NOT an investment-semantic failure.

It is a model-facing type/domain contract gap.

---

# 4. Evidence available to the failed SKHY Stage-2 call

The M12BW forensic report shows source evidence including:

```text
canonical:earnings:latest
  as_of = latest

canonical:financial_quality:latest
  as_of = latest

decision-evidence:8b7febdf06f514f5954d
  as_of = 2026-09-15.
```

The model emitted:

```text
latest00000000000
```

which appears to satisfy a loose string/minLength shape
while violating the actual date semantics.

Do NOT patch this literal.

---

# 5. Root-cause principle

The next repair must answer a broader question:

> Which Stage-2 fields are modeled as arbitrary strings even though their actual
> product/validator contract is a closed enum, ISO date, timestamp, identifier,
> catalog member, currency, session, instrument, hash, status, or other typed value?

The goal is to eliminate the current whack-a-mole pattern.

Do NOT make a one-field regex patch only for:

```text
driver_maturity[].as_of.
```

---

# 6. Freeze prior successful repairs

Do NOT reopen:

```text
stage2-frozen-core-ownership-v1

fundamental-core-exact-ref-fidelity-v1

stage2-exact-ref-fidelity-v1

model-output-exact-ref-fidelity-v1

post_confirmation_hold maturity invariant

three-axis user-facing decision contract

REVIEW user copy

fundamental core vs price/timing separation

expectation/valuation duplicate-anchor protection

BusinessDeltaEvidenceView

MarketExpectationEvidenceView

ConfiguredSignalEvidenceView

financial / FCF / net-debt / WC / financial-sector semantics

Persistence V2

KR-financial cold-start repair.
```

M12BW already proved:

```text
frozen-core revalidation false positives = 0

Stage-2-owned unsupported-metric failures = 0

exact-ref violations = 0

fabricated refs = 0

post-confirmation maturity conflicts = 0

price/timing core mutation = 0

price/timing holder mutation = 0

expectation/valuation duplicate anchors = 0

GOOGL old frozen-core replay = PASS.
```

Preserve these.

---

# 7. TRACK A — complete Stage-2 string-field inventory

Inspect the actual current Stage-2 JSON schema recursively.

For EVERY node currently represented as:

```text
type: string
```

or an array/object containing strings,
record:

```text
JSON path

field name

owner stage

current schema constraints

current prompt contract

current hard-validator constraints

actual semantic domain

examples observed in frozen contexts/outputs

whether the field is genuinely free text.
```

Do not rely on field-name heuristics only.

---

# 8. Required Stage-2 string semantic kinds

Classify each string into exactly one primary semantic kind:

```text
FREE_TEXT

ISO_DATE

OFFSET_DATETIME

CLOSED_ENUM

EXACT_EVIDENCE_REF

EXACT_CATALOG_ID

HASH

TICKER_IDENTITY

CURRENCY_CODE

INSTRUMENT_ID

SESSION_ID_OR_ENUM

CONTRACT_MONTH_OR_ID

STATUS_CODE

VERSION_ID

BOUNDED_SYMBOLIC_TOKEN

OPAQUE_PROVIDER_VALUE

OTHER_TYPED_STRING.
```

If a field cannot be classified safely:

```text
UNKNOWN_TYPED_STRING
```

and document why.

Do NOT silently treat unknown typed data as FREE_TEXT.

---

# 9. Genuine free text must remain free

Examples that may legitimately remain free text:

```text
reasoning prose

summary

risk explanation

new-buyer explanation

holder explanation

scenario narrative

valuation interpretation

timing rationale.
```

Do NOT overconstrain narrative strings.

This task is about semantic types,
not turning prose into enums.

---

# 10. Closed-domain fields must stop using loose minLength-only contracts

For fields whose actual contract is closed/typed,
prefer structural schema constraints already supported by the model runtime.

Examples:

```text
enum

pattern

min/max length appropriate to actual typed syntax

array-items enum

exact catalog enum.
```

Do NOT use unsupported JSON Schema keywords.

Run capability tests before relying on:

```text
format

if/then

dependentSchemas

complex conditionals.
```

---

# 11. ISO date contract

For fields whose actual meaning is a calendar date,
use a strict supported contract equivalent to:

```text
YYYY-MM-DD
```

with real calendar validation in deterministic code.

A lexical pattern alone is insufficient for invalid dates such as:

```text
2026-99-99.
```

Preferred:

```text
schema lexical constraint
+
hard deterministic date parser.
```

No arbitrary padded strings.

---

# 12. driver_maturity[].as_of — explicit audit

Determine the authoritative meaning of:

```text
driver_maturity[].as_of.
```

Questions:

```text
Is it the date of the cited evidence?

Is it the date of the maturity judgment?

Is it assessment_date?

May it ever be a symbolic token such as "latest"?

Does the hard validator already require a concrete date?
```

Use current code/prompt/schema/validator evidence.

Do not infer from the failed output alone.

---

# 13. Preferred driver_maturity as_of outcome

If the existing validator/product contract confirms the field is a concrete evidence date:

use:

```text
ISO_DATE only.
```

Prompt equivalent:

```text
driver_maturity.as_of must be a concrete YYYY-MM-DD date supported by
the cited evidence. Do not write "latest", "current", placeholders, or padded text.
```

Schema:

```text
strict date lexical shape
```

plus deterministic date parsing.

---

# 14. Symbolic source as_of must not be fabricated into a date

If a source evidence ref exposes:

```text
as_of = latest
```

that symbolic token must NOT be transformed by the model into:

```text
latest00000000000

today

current

2026-09-15
```

unless a concrete date is deterministically owned elsewhere in the frozen packet.

No model date invention.

---

# 15. Resolve symbolic "latest" upstream only when deterministic

Audit whether:

```text
canonical:earnings:latest

canonical:financial_quality:latest
```

have an authoritative resolved date elsewhere in the SAME frozen packet,
for example:

```text
source statement date

checkpoint date

snapshot as-of

filing date

assessment-bound evidence date.
```

If YES:

preferred architecture:

```text
include the resolved concrete date in the Stage-2 visible evidence catalog
deterministically.
```

Do not ask the model to guess it.

If NO:

the symbolic source cannot satisfy a field that requires a concrete evidence date.

---

# 16. Required evidence-date feasibility audit

Before model calls,
run the frozen 22 Stage-2 contexts through a deterministic feasibility audit.

For every required `driver_maturity` row:

```text
selected/citable evidence refs

source as_of values

resolved concrete date if available

whether the Stage-2 contract can be satisfied without invention.
```

Required:

```text
unsatisfiable required date count = 0.
```

If nonzero:

STOP before model calls with:

```text
STAGE2_REQUIRED_DATE_SOURCE_NORMALIZATION_GAP.
```

Do not make the model invent dates.

---

# 17. If "latest" is truly an allowed output token

Only if repository evidence proves that `driver_maturity.as_of`
is intentionally a date-or-symbolic-token union:

define an explicit closed union such as:

```text
ISO date
or exact enum token "latest".
```

Then align the hard validator.

However:

do NOT weaken a current canonical date requirement merely to make SKHY pass.

Any validator contract change requires separate proof/evidence.

Default expectation:

```text
concrete date is required.
```

---

# 18. Audit all other date-like fields

Search Stage-2 schema/prompt/validators for paths containing concepts such as:

```text
as_of

date

effective

generated

observed

maturity date

confirmation date

session date

assessment date.
```

For each:

```text
align model-facing schema and validator domain.
```

Do not leave another minLength-only date field.

---

# 19. Audit enum-like fields

Search all Stage-2 strings whose validator/prompt already implies a finite vocabulary.

Examples may include:

```text
overall_maturity

driver maturity state

factual safety state

timing classification

market expectation level

pricing requirement state

scenario class

confirmation status

reasoning grade

new-buyer stance

holder-related Stage-2 status

session state.
```

Use the ACTUAL current schema.

If already enum-constrained:

leave unchanged.

If validator expects a finite set but schema is loose:

close it structurally.

---

# 20. Audit identifier-like fields

Audit:

```text
ticker

hashes

contract/version IDs

source IDs

session IDs

instrument IDs

catalog IDs

provider keys.
```

If a model should merely copy a supplied identifier:

prefer exact catalog enum or strict identity pattern.

Do not allow model-generated arbitrary identifiers.

---

# 21. Evidence refs remain under the existing exact-ref contract

Do NOT redesign evidence refs.

Use the existing proven exact-ref catalogs.

This audit should simply verify:

```text
all evidence-ref paths are already structurally closed.
```

Expected:

```text
exact-ref contract change count = 0.
```

---

# 22. Currency / instrument / session fields

If Stage-2 itself emits any:

```text
currency

instrument

session

market
```

typed strings:

they must come from:

```text
exact supplied catalog

or supported closed enum.
```

Do not let the model invent:

```text
"USD-ish"

"night maybe"

"latest session".
```

---

# 23. Opaque provider values

A truly provider-owned opaque string may remain:

```text
OPAQUE_PROVIDER_VALUE
```

only when:

```text
the model is not expected to generate it,
or it must copy an exact supplied value.
```

If model-generated:

prefer exact catalog restriction.

---

# 24. Cross-field conditions

Do not attempt to encode every business relationship in JSON Schema.

Keep complex semantics in hard validators.

This task only closes primitive/domain contracts.

Examples:

```text
post_confirmation_hold ↔ maturity
```

remains prompt + hard validator if conditional schema unsupported.

Do not re-open it.

---

# 25. Type-contract mismatch matrix

Produce one matrix:

```text
field path

semantic kind

old schema

validator requirement

new schema

prompt clarification needed?

upstream normalization needed?

model-facing change?

hard validator change?

status.
```

Acceptance target:

```text
typed_free_string_gap_count_after = 0
```

for proof-critical Stage-2 fields.

---

# 26. SKHY exact old output replay

Replay the exact M12BW SKHY Stage-2 candidate.

Expected:

```text
latest00000000000
→ schema/type validation FAIL.
```

No auto-rewrite.

No fuzzy normalization.

No date fabrication.

Old candidate remains invalid.

---

# 27. Positive SKHY-equivalent fixture

Construct a candidate using a legitimate concrete dated evidence ref.

Example based on frozen evidence if actually owned:

```text
driver_maturity.as_of = 2026-09-15
```

with the matching dated evidence identity.

Expected:

```text
schema PASS

date parser PASS

evidence/date consistency PASS.
```

Do not use the example if the actual fixture cannot safely bind it.

---

# 28. Negative typed-string fixtures

At minimum include:

```text
latest00000000000

latest

current

today

2026-9-15

2026-99-99

empty padded whitespace

unknown enum literal

modified hash/id

unapproved session token

unapproved currency token.
```

Each should fail at the earliest appropriate contract boundary
for fields where that value is invalid.

Do not apply every fixture to every field indiscriminately.

---

# 29. Positive free-text fixture

Prove narrative fields remain capable of ordinary Korean/English free prose.

No accidental enum/pattern restriction on reasoning text.

---

# 30. Model-facing change scope

Expected M12BX Track-A changes:

```text
Stage-2 schema semantic change = yes

Stage-2 prompt semantic change = possibly yes

Stage-2 deterministic input normalization = possibly yes

FUNDAMENTAL_CORE prompt/schema = unchanged

canonical investment semantic classifiers = unchanged

exact-ref contracts = unchanged

three-axis contract = unchanged

core/timing ownership = unchanged

expectation/valuation ownership = unchanged

Persistence V2 = unchanged.
```

Any canonical semantic-policy change:

```text
STOP
TYPED_CONTRACT_AUDIT_EXPANDED_INTO_SEMANTIC_POLICY_CHANGE.
```

---

# 31. Deterministic Track-A gate

Before external model calls:

run:

```text
complete string-field inventory tests

date feasibility audit

typed-domain schema tests

SKHY old-output replay

free-text negative-regression tests

exact-ref regressions

frozen-core ownership regressions

post-confirmation maturity regressions

three-axis regressions

core/timing regressions

expectation/valuation regressions

BusinessDelta regressions

full local pytest

Ruff

git diff --check.
```

All must PASS.

---

# 32. Frozen 22 monitored proof inputs

Use the exact frozen packets:

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

Packet SHAs:

```text
US =
2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228

KR =
819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597.
```

No provider refetch.

No packet mutation except deterministic model-facing typed normalization
explicitly authorized and hash-audited by this task.

If normalization changes the semantic evidence packet itself rather than
the model-facing projection:

```text
STOP
FROZEN_PACKET_SEMANTIC_IDENTITY_CHANGED.
```

---

# 33. New full proof generation

Because Stage-2 schema/model-facing typed contract changes:

create a NEW complete proof generation.

No reuse/stitching from M12BW/M12BV/etc.

Derive the full current call plan before call 1.

Recent expected plan:

```text
16 calls.
```

Freeze:

```text
call ordinal

market

stage

batch

tickers

prompt hash

schema hash

ref catalog hash

typed-contract hash.
```

---

# 34. Model

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

No per-subject retry.

---

# 35. Full 22 PASS criteria — Track A

Require:

```text
22 / 22 subjects represented

all required calls complete

FUNDAMENTAL_CORE schema valid = 22

FUNDAMENTAL_CORE semantic valid = 22

Stage-2 schema valid = 22

Stage-2 semantic valid = 22

typed-free-string violation count = 0

noncanonical-date output count = 0

symbolic-date-fabrication count = 0

exact-ref violation count = 0

fabricated-ref count = 0

frozen-core revalidation false-positive count = 0

Stage-2-owned unsupported-metric failure count = 0

post-confirmation maturity conflict count = 0

final composition valid = 22

BusinessDelta hard failure count = 0

price/timing core mutation count = 0

price/timing holder mutation count = 0

expectation/valuation duplicate-anchor count = 0

core mutation count = 0

canonical bypass count = 0

legacy duplicate semantic participation count = 0

fallback / judge / repair / selective rerun = 0.
```

No target decision distribution.

---

# 36. SKHY dossier

Report:

```text
overall direction

new-buyer stance

holder stance

every driver_maturity row

every driver_maturity as_of

cited evidence refs

resolved evidence dates

typed contract validation

symbolic-source usage

date invention count.
```

Required:

```text
noncanonical date = 0

fabricated date = 0.
```

No expected direction.

---

# 37. GOOGL / RXRX / CORZ regressions

GOOGL:

```text
price/timing core anchor = 0

duplicate expectation/valuation anchor = 0

frozen-core ownership PASS.
```

RXRX:

```text
fabricated ref = 0.
```

CORZ:

```text
fabricated Stage-2 ref = 0

post-confirmation maturity conflict = 0.
```

No expected directions.

---

# 38. Three-axis local render

After clean proof:

```text
종합 방향 visible = 22

신규 관찰자 visible = 22

보유자 visible = 22

REVIEW user copy safe

mechanical stance mapping = 0.
```

No deployment in M12BX.

---

# 39. TRACK B — recovered Kiwoom implementation is already proven

Do NOT repeat historical search.

Freeze recovered identity:

```text
historical final commit =
28f4f70700046f98d5d899ee491d3e5f45922e9a

service =
app/services/krx_night_session_contract_service.py

fixture =
fixtures/20260905-kiwoom-kospi200-night-futures-fixture.json

tests =
tests/test_krx_night_session_contract_service.py

reuse decision =
HISTORICAL_IMPLEMENTATION_REUSABLE_WITH_ADAPTER

disconnect root cause =
CODE_STILL_EXISTS_NOT_WIRED.
```

Historical parser reproductions:

```text
2026-09-01 = NORMALIZATION_ONLY_PASS

2026-09-02 = NORMALIZATION_ONLY_PASS

2026-09-03 = NORMALIZATION_ONLY_PASS.
```

Historical verified scope:

```text
KOSPI200 night futures = yes

KOSDAQ150 actual historical Kiwoom fixture = no

US futures historical Kiwoom scope = no.
```

Do not claim broader historical coverage.

---

# 40. Historical KOSPI200 sample contract — freeze

The recovered historical contract safely owns:

```text
contract_month

instrument

session_type

session_business_date

open

high

low

close

volume.
```

It does NOT by itself safely own:

```text
observation timestamp

prior settlement/reference basis

change

change percent

current session status.
```

Do not fabricate those.

---

# 41. Build current KOSPI200 night-futures adapter locally

Implement a bounded adapter from the existing/recovered typed quote contract
into the current:

```text
LeadingMarketSnapshot
```

or actual current equivalent.

Map safely:

```text
instrument_id =
XKRX:KOSPI200:FUTURES

session =
NIGHT / current canonical equivalent

business date

current/last price when owned

provider/source identity

source timezone =
Asia/Seoul.
```

Use actual current schema names.

---

# 42. Current live quote path — read only

Audit whether an existing authenticated Kiwoom night-session gateway is available.

Historical contract:

```text
Windows Kiwoom OpenAPI+ authenticated gateway

read-only market-data consumer

order/account data not required by consumer.
```

If available and explicitly safe:

allow ONE read-only current quote smoke.

Forbidden:

```text
orders

order modification

order cancellation

account mutation

portfolio mutation.
```

If unavailable:

```text
LIVE_KIWOOM_NIGHT_GATEWAY_UNAVAILABLE
```

is acceptable in M12BX.

Offline adapter/tests still proceed.

---

# 43. No fake current change percentage

Only render:

```text
change

change_pct
```

when the current typed source explicitly owns a safe comparison basis.

Accepted basis examples only if actually supplied/defined:

```text
prior night settlement

prior comparable night close

provider-documented reference.
```

Do NOT compare night futures arbitrarily to:

```text
KOSPI200 cash close
```

and label it night-futures return.

If no safe reference:

render:

```text
현재 레벨 / session only
```

without fabricated percentage.

---

# 44. Completed vs night session

Market message must keep:

```text
한국 정규장 마감

KOSPI200 야간선물 / 선행시장
```

in separate blocks.

Night futures never overwrite:

```text
KOSPI/KOSPI200 completed cash-session return.
```

---

# 45. Night-futures ownership firewall

Night futures may influence only:

```text
시장환경 점검

현재 위험선호

다음 세션 gap/timing context

신규 관찰자 timing commentary.
```

Hard forbidden:

```text
BusinessDelta

holder REVIEW/REDUCE

fundamental invalidation

earnings change

fundamental overall direction anchor.
```

Add negative tests.

---

# 46. KOSDAQ150 behavior

Because historical actual Kiwoom fixture was NOT recovered:

do NOT claim current KOSDAQ150 night-futures support.

Use:

```text
UNAVAILABLE_NOT_YET_PROVEN
```

or omit the block.

No synthetic extension from the KOSPI200 parser.

---

# 47. TRACK C — US Treasury historical provenance search first

Before writing or restoring Treasury message code,
search repository history/branches/artifacts for the prior implementation.

Explicit target:

```text
US Treasury 5Y

US Treasury 10Y

US Treasury 30Y.
```

Search terms:

```text
DGS5

DGS10

DGS30

5Y

10Y

30Y

5-year

10-year

30-year

5년물

10년물

30년물

Treasury

국채금리

yield curve

nominal yield.
```

Also search known/possible companion series:

```text
DFII10

T10YIE

real yield

실질금리

breakeven

기대인플레이션.
```

Do not assume they were all in the same implementation.

---

# 48. Treasury provenance search surfaces

Search read-only:

```text
current source

git log --all

branches

tags

reflogs

historical commits

tracked tests/fixtures

market/macro reports

artifact manifests

message snapshots.
```

Do not modify history.

Do not `git gc`.

---

# 49. Treasury historical implementation record

For each candidate implementation record:

```text
commit SHA

timestamp

paths

provider/source

series IDs

test/fixture paths

message-rendering path

change-bp calculation basis

as-of handling.
```

Identify the final historically used implementation,
not merely an early prototype.

---

# 50. Treasury source authenticity

Determine whether historical nominal yields were from:

```text
FRED

Treasury source

another supported free provider.
```

Use the actual code.

Do not replace the source based on memory.

No paid source.

---

# 51. Treasury 5Y/10Y/30Y restoration target

If historical evidence confirms the intended set:

```text
DGS5 / 5Y nominal

DGS10 / 10Y nominal

DGS30 / 30Y nominal
```

restore that exact curve set into the current market environment.

If historical evidence shows a different set:

report the actual set.

Do not force 5/10/30 merely because the user remembers it,
but explicitly compare the history to the recalled contract.

---

# 52. Real yield / breakeven preservation

If historical/current code owns:

```text
10Y real yield
and/or
10Y breakeven inflation,
```

preserve them as separate metrics.

Common historical IDs may be:

```text
DFII10

T10YIE.
```

Use actual repository IDs.

Do NOT calculate real yield as:

```text
nominal - inflation
```

unless the existing audited contract explicitly does so.

Prefer the direct supported series.

---

# 53. Treasury daily-data semantics

If the source is a daily series such as FRED:

the message must say/behave as:

```text
latest available daily observation
```

not:

```text
live current intraday Treasury yield.
```

Include explicit:

```text
as-of date.
```

Do not mix a stale daily rate with live futures without labeling different timestamps.

---

# 54. Treasury bp-change calculation

If historical code computes daily change:

```text
bp change =
(current valid yield - previous valid yield) * 100
```

for percentage-point yield series.

Confirm the exact stored units first.

Do not multiply twice.

Do not compare to an arbitrary calendar previous day if it has missing data.

Use previous valid comparable observation.

---

# 55. Treasury missing/stale handling

For each maturity/series:

```text
current value

previous comparable value

as_of

previous_as_of

freshness.
```

If a series is missing/stale:

do not fill from another maturity.

Do not interpolate.

Render unavailable or omit according to current UX.

---

# 56. Treasury user-facing block

If provenance and source contract pass,
render a compact block such as:

```text
금리·인플레이션 · 기준 YYYY-MM-DD

미국채 5Y   x.xx%  (±x bp)
미국채 10Y  x.xx%  (±x bp)
미국채 30Y  x.xx%  (±x bp)

10Y 실질금리      x.xx%  (±x bp)   [if supported]
10Y 기대인플레    x.xx%  (±x bp)   [if supported]
```

Use repository copy conventions.

Do not render unsupported lines.

---

# 57. Treasury interpretation scope

Treasury curve data may influence:

```text
시장환경 점검

discount-rate context

growth/long-duration valuation pressure

financial conditions

company-specific macro transmission where explicitly relevant.
```

It must NOT directly create:

```text
BusinessDelta

holder REDUCE/REVIEW

company earnings fact

fundamental invalidation
```

without company-specific transmission evidence.

Add negative tests.

---

# 58. Curve interpretation

If the message discusses curve shape:

only use deterministic relationships supported by the displayed maturities.

Examples:

```text
5Y vs 10Y

10Y vs 30Y.
```

Do not label:

```text
2s10s

5s30s
```

unless those exact maturities are available and the current contract owns the spread.

No unsupported recession call from curve shape alone.

---

# 59. Treasury / futures time-layer separation

Market environment may contain:

```text
completed cash session

latest daily Treasury observations

current night/leading futures.
```

Each must retain its own:

```text
as-of date/time

source

session/frequency.
```

Do not synthesize them into one fake common timestamp.

---

# 60. Current market message hierarchy

Target structure after Tracks B/C:

```text
1. 완료된 시장
2. 금리·인플레이션
3. 현재 선행시장 / 야간선물
4. 해석
5. 주요 모니터링 포인트.
```

Exact section names may follow existing UX.

Do not make the message excessively long.

---

# 61. Market-data code reuse principle

For both night futures and Treasury yields:

```text
recover/reuse the historical proven implementation first.
```

Only if historical source/transport is obsolete or truly absent
may the next task consider a new source.

No duplicate provider logic.

---

# 62. TRACK B/C local-only integration

M12BX may implement local/current pipeline adapters and deterministic renderers.

It must NOT:

```text
deploy

enable scheduler

send notifications

enable V2 writer

mutate production warnings.
```

If a live read-only source is available,
a bounded read-only smoke is allowed.

No trading operations.

---

# 63. Market-context deterministic tests

Add at minimum:

```text
historical 9/1 Kiwoom KOSPI200 reproduction

historical 9/2 reproduction

historical 9/3 reproduction

LeadingMarketSnapshot adapter mapping

no change_pct without reference basis

cash-session not overwritten by night futures

night futures cannot create BusinessDelta

night futures cannot create holder fundamental state

Treasury 5Y/10Y/30Y fixture parsing if historical implementation found

Treasury bp-change unit test

Treasury missing previous observation test

Treasury as-of labeling test

Treasury cannot create BusinessDelta

Treasury cannot create holder fundamental state

daily Treasury vs live futures time-layer rendering.
```

---

# 64. Independent track completion policy

Track A model failure must NOT erase successful B/C artifacts.

Track B source unavailability must NOT invalidate Track A semantic proof.

Track C historical implementation not found must NOT invalidate Track A.

Report each track independently.

Top-level result should summarize all three.

---

# 65. No deployment in M12BX

Even if all tracks pass:

```text
deployment_readiness =
READY_FOR_FINAL_MESSAGE_SMOKE
```

but:

```text
deployments = 0.
```

Next task performs:

```text
final deploy

current US/KR collection

night-futures live/read-only check if gateway available

Treasury current-data collection

all current market/ticker message generation

human review.
```

---

# 66. Required Track-A forensic artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12bx-scope-freeze

04-m12bw-failure-freeze

05-stage2-complete-string-field-inventory

06-stage2-string-semantic-kind-matrix

07-stage2-validator-schema-domain-mismatch-matrix

08-driver-maturity-asof-contract-audit

09-symbolic-latest-resolution-audit

10-frozen22-required-date-feasibility-audit

11-stage2-typed-contract-closure-decision.
```

---

# 67. Required Track-A implementation/tests

Produce:

```text
12-stage2-typed-schema-implementation

13-stage2-typed-prompt-clarification

14-upstream-dated-evidence-normalization-if-required

15-skhy-old-output-replay

16-skhy-positive-dated-fixture

17-typed-string-negative-fixtures

18-free-text-nonregression-fixtures

19-exact-ref-regressions

20-frozen-core-regressions

21-postconfirmation-regressions

22-three-axis-core-timing-expectation-regressions

23-business-delta-regressions

24-full-local-test-result

25-ruff-diff-result

26-model-facing-hash-manifest.
```

---

# 68. Required Track-A full proof artifacts

Produce:

```text
27-frozen22-input-identity-manifest

28-new-full22-generation-manifest

29-full22-call-plan-with-typed-contract-hashes

30-fundamental-core-model-artifacts

31-stage2-model-artifacts

32-stage2-typed-contract-audit

33-stage2-date-audit

34-exact-ref-fidelity-audit

35-frozen-core-ownership-audit

36-postconfirmation-maturity-audit

37-price-timing-immutability-audit

38-expectation-valuation-audit

39-business-delta-audit

40-canonical-semantic-audit

41-final-composition-audit

42-per-ticker-result-matrix

43-skhy-postrepair-dossier

44-googl-regression-dossier

45-rxrx-regression-dossier

46-corz-regression-dossier

47-three-axis-render-audit

48-track-a-decision.
```

---

# 69. Required Track-B Kiwoom artifacts

Produce:

```text
49-recovered-kiwoom-contract-freeze

50-kiwoom-leading-market-adapter-design

51-kiwoom-leading-market-adapter-implementation

52-kiwoom-20260901-adapter-replay

53-kiwoom-20260902-adapter-replay

54-kiwoom-20260903-adapter-replay

55-kiwoom-reference-basis-safety-audit

56-kiwoom-readonly-live-gateway-status

57-kospi200-night-message-render-test

58-night-futures-fundamental-ownership-negative-tests

59-track-b-decision.
```

---

# 70. Required Track-C Treasury artifacts

Produce:

```text
60-treasury-historical-search-plan

61-treasury-git-history-results

62-treasury-implementation-candidates

63-treasury-final-historical-implementation-identity

64-treasury-series-scope-decision

65-treasury-5y-provenance

66-treasury-10y-provenance

67-treasury-30y-provenance

68-treasury-real-yield-provenance

69-treasury-breakeven-provenance

70-treasury-source-contract

71-treasury-parser-reproduction

72-treasury-current-adapter-design

73-treasury-current-adapter-implementation-if-reusable

74-treasury-bp-change-tests

75-treasury-asof-freshness-tests

76-treasury-market-message-render-tests

77-treasury-fundamental-ownership-negative-tests

78-track-c-decision.
```

If historical implementation is not found,
artifacts 71-77 may be:

```text
NOT_RUN_HISTORICAL_IMPLEMENTATION_NOT_FOUND
```

with exhaustive search evidence.

Do not write a new provider connector in that case.

---

# 71. Required combined message artifacts

Produce locally:

```text
79-market-context-layer-contract

80-completed-session-rate-leading-time-separation-tests

81-local-us-market-message-preview

82-local-kr-market-message-preview

83-market-message-numeric-provenance-audit

84-market-message-internal-metadata-leak-audit.
```

Use historical/current safe fixture data.

Do not deploy.

---

# 72. Required final decisions

Produce:

```text
85-stage2-typed-contract-closure-decision

86-full22-reproof-decision

87-kiwoom-night-futures-reintegration-readiness

88-us-treasury-curve-restoration-decision

89-market-context-message-readiness

90-deployment-readiness

91-next-scope-decision

92-master-workflow-update

93-program-completion.
```

---

# 73. Program-completion fields

Include at least:

```text
base_main_sha
implementation_branch
implementation_head_sha

latest_result_zip_sha256
latest_result_integrity

m12bw_failure_ticker
m12bw_failure_path
m12bw_failure_value
m12bw_failure_class

stage2_string_field_count
stage2_free_text_field_count
stage2_typed_string_field_count
stage2_unknown_typed_string_count

typed_free_string_gap_count_before
typed_free_string_gap_count_after

stage2_iso_date_field_count
stage2_closed_enum_field_count
stage2_exact_catalog_id_field_count
stage2_other_typed_string_field_count

driver_maturity_asof_contract
symbolic_latest_allowed_in_driver_maturity_asof
required_date_unsatisfiable_count
upstream_dated_evidence_normalization_count

skhy_old_output_replay_status
skhy_noncanonical_date_count_after
skhy_fabricated_date_count_after

stage2_prompt_semantic_change_count
stage2_schema_semantic_change_count
canonical_semantic_policy_change_count
exact_ref_contract_change_count
three_axis_contract_change_count
expectation_valuation_contract_change_count
persistence_v2_contract_change_count

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
stage2_schema_valid_count
stage2_semantic_valid_count
stage2_typed_contract_violation_count
stage2_noncanonical_date_count
stage2_symbolic_date_fabrication_count
exact_ref_fidelity_violation_count
fabricated_ref_count
frozen_core_revalidation_false_positive_count
stage2_owned_unsupported_metric_failure_count
postconfirmation_maturity_conflict_count
final_composition_valid_count
business_delta_hard_failure_count
price_timing_core_mutation_count
price_timing_holder_mutation_count
expectation_valuation_duplicate_anchor_count
core_mutation_count

wrapper_retry_count
fallback_model_call_count
judge_call_count
repair_call_count
selective_rerun_count

three_axis_visible_count
three_axis_missing_count

track_a_result

kiwoom_historical_commit
kiwoom_reuse_decision
kiwoom_adapter_status
kiwoom_20260901_replay
kiwoom_20260902_replay
kiwoom_20260903_replay
kiwoom_live_gateway_status
kiwoom_live_readonly_call_count
kiwoom_live_order_call_count
kiwoom_change_pct_suppressed_without_basis_count
kospi200_night_message_render_status
kosdaq150_night_support_status

track_b_result

treasury_historical_search_status
treasury_historical_final_commit
treasury_source_provider

treasury_5y_historical_found
treasury_5y_series_id
treasury_10y_historical_found
treasury_10y_series_id
treasury_30y_historical_found
treasury_30y_series_id

treasury_10y_real_historical_found
treasury_10y_real_series_id
treasury_10y_breakeven_historical_found
treasury_10y_breakeven_series_id

treasury_parser_reproduction_status
treasury_current_adapter_status
treasury_5y_render_status
treasury_10y_render_status
treasury_30y_render_status
treasury_10y_real_render_status
treasury_breakeven_render_status
treasury_bp_change_unit_status
treasury_asof_label_status

track_c_result

night_futures_to_business_delta_violation_count
night_futures_to_holder_violation_count
treasury_to_business_delta_violation_count
treasury_to_holder_violation_count
completed_session_overwritten_count
time_layer_conflation_count

market_context_message_readiness
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
```

where appropriate.

Do not replace unknown with zero.

---

# 74. Track-A expected clean outcome

If the typed-contract closure works:

```text
track_a_result =
STAGE2_TYPED_CONTRACT_CLOSURE_FULL22_PASS

typed_free_string_gap_count_after = 0

required_date_unsatisfiable_count = 0

stage2_noncanonical_date_count = 0

stage2_symbolic_date_fabrication_count = 0

exact_ref_fidelity_violation_count = 0

fabricated_ref_count = 0

frozen_core_revalidation_false_positive_count = 0

postconfirmation_maturity_conflict_count = 0

final_composition_valid_count = 22

business_delta_hard_failure_count = 0

price_timing_core_mutation_count = 0

price_timing_holder_mutation_count = 0

expectation_valuation_duplicate_anchor_count = 0

core_mutation_count = 0

three_axis_visible_count = 22.
```

Do not force decision enums.

---

# 75. Track-B expected outcome

Expected offline:

```text
kiwoom_reuse_decision =
HISTORICAL_IMPLEMENTATION_REUSABLE_WITH_ADAPTER

9/1 = PASS

9/2 = PASS

9/3 = PASS

KOSPI200 night message rendering = PASS

KOSDAQ150 support =
UNAVAILABLE_NOT_YET_PROVEN.
```

Live gateway may remain unavailable.

Do not fail offline reintegration solely because Windows/authenticated gateway
is not present in the current execution environment.

But do NOT call the integration fully live-ready if no read-only live quote was verified.

---

# 76. Track-C desired outcome

Preferred if historical code confirms the user's recalled curve:

```text
5Y nominal = recovered

10Y nominal = recovered

30Y nominal = recovered

10Y real = preserved if historically supported

10Y breakeven = preserved if historically supported

bp change = audited

as-of = explicit

market message block = PASS.
```

Do NOT force this result.

If only a subset is historically supported:

report the subset exactly.

Do not write a new provider until the provenance result is reviewed.

---

# 77. Combined top-level result taxonomy

Choose one overall result while preserving per-track results:

```text
M12BX_ALL_TRACKS_READY_FOR_FINAL_MESSAGE_SMOKE

M12BX_MODEL_CONTRACT_BLOCKED_MARKET_CONTEXT_READY

M12BX_MODEL_CONTRACT_READY_MARKET_CONTEXT_PARTIAL

M12BX_TYPED_CONTRACT_PREMODEL_BLOCKED

M12BX_MULTIPLE_BLOCKERS.
```

Do not collapse independent failures into one vague FAIL.

---

# 78. Next-scope rules

## If Track A PASS + Kiwoom local adapter PASS + Treasury restoration PASS

```text
next_scope =
FINAL_DEPLOY_CURRENT_US_KR_MARKET_AND_TICKER_MESSAGE_SMOKE_WITH_NIGHT_FUTURES_AND_TREASURY_CURVE.
```

## If Track A PASS + Kiwoom PASS + Treasury historical implementation not found

```text
next_scope =
TREASURY_HISTORICAL_BACKUP_RECOVERY_OR_SAFE_SOURCE_DECISION_BEFORE_FINAL_SMOKE.
```

## If Track A PASS + Kiwoom live gateway unavailable

The final smoke may still deploy only if product explicitly accepts:

```text
night-futures block unavailable when gateway unavailable.
```

Otherwise:

```text
next_scope =
KIWOOM_READONLY_GATEWAY_ENABLEMENT_AND_FINAL_SMOKE.
```

## If Track A FAIL

No model hotfix in M12BX.

Market tracks still remain frozen for later use.

Choose the smallest bounded model-contract follow-up.

---

# 79. Production firewall

Throughout M12BX:

```text
production DB mutations = 0

assessment production writes = 0

warning production mutations = 0

notification queue writes = 0

production sends = 0

scheduler mutations = 0

automatic monitoring resume = 0

V2 production gates remain OFF

main merge = 0

deployment = 0

raw model artifact remote push = 0.
```

Read-only market-data calls are permitted only under existing safe credentials/connectors.

For Kiwoom:

```text
market-data read only

order calls = 0.
```

---

# 80. Final task principle

The current repeated proof failures have moved through DIFFERENT structural holes:

```text
CORZ maturity contract

RXRX exact ref

CORZ Stage-2 exact ref

GOOGL frozen-core validation ownership

SKHY date-like free string.
```

The first four are now individually closed.

Do NOT continue with another literal patch for:

```text
latest00000000000.
```

M12BX must close the entire remaining class:

```text
typed-but-free-string Stage-2 fields.
```

The correct flow is:

```text
inventory every Stage-2 string

→ distinguish real prose from typed domains

→ structurally close dates/enums/IDs/statuses/catalog values

→ deterministically resolve source dates where actually owned

→ prove no required typed field is impossible to satisfy

→ run a brand-new complete 22-subject proof.
```

At the same time, market-context restoration must no longer be forgotten:

```text
reuse the already recovered Kiwoom KOSPI200 9/1-9/3 implementation

→ wire it locally into LeadingMarketSnapshot

→ never fabricate futures change_pct without a real basis

→ search and recover the historical US Treasury 5Y/10Y/30Y implementation

→ preserve 10Y real yield / breakeven if actually present

→ keep daily rates, completed sessions, and live/night futures on separate time layers

→ never let market timing/rates directly create BusinessDelta or holder fundamental state.
```

Do NOT:

```text
patch only SKHY

permit "latest000..."

guess dates

overconstrain narrative prose

reopen exact-ref semantics

re-search Kiwoom history

invent KOSDAQ150 coverage

write a new Treasury provider before history search

call daily Treasury data live intraday

fabricate futures returns

merge/deploy

resume automation.
```
