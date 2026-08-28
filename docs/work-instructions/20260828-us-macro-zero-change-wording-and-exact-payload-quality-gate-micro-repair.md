# thesis-monitor — US Macro Zero-Change Wording + Exact-Payload Quality Gate Micro Repair
## Fix `변화 없음했습니다` and make message-quality validation derive from the exact received payload
## Formatting / bounded renderer-quality repair only
## US Price Structure remains ON and unchanged

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-28 KST`
- Workstream: `US_MACRO_ZERO_CHANGE_WORDING_AND_EXACT_PAYLOAD_QUALITY_GATE_MICRO_REPAIR`
- Task class: `BOUNDED_RENDERER_AND_QUALITY_VALIDATOR_MICRO_REPAIR`
- Target product: US morning market digest
- US full-message current state: `DEPLOYED_AWAITING_NATURAL_PROOF`
- US Price Structure current state: `ENABLED_AWAITING_NATURAL_PROOF`
- KR market TOP3: preserve `ON`
- KR Price Structure: preserve `ON`
- Production Assist: preserve `OFF`
- Manual production scheduler: `0`
- Production-recipient test send: `0`
- DB / assessment mutation: `0`
- Historical archive rewrite: `0`

### Latest supplied rollout lineage

The supplied rollout bundle reports:

```text
Master instruction:
2ee201690787136780c7d5c8a046506d44227633

Base:
178bc7e825c6ae9aea21fbd4687f7a4b83af9973

Implementation:
1ba463571060a1fc9a5868afcdeab3de15f2bbe6

Report / final main / operating:
f4369c829c82d3d4fae6a5692dc62e9263f1d8b3
```

Current enabled runtime:

```text
KR market TOP3 = ON
KR Price Structure = ON
US Price Structure = ON
Production Assist = OFF
```

Before implementation:

1. `git fetch origin`
2. verify clean worktrees
3. resolve actual latest safe `origin/main`
4. resolve current operating SHA
5. require lineage to contain `f4369c...` or a safe linear descendant
6. do not alter current feature states except normal deployment of this micro-repair

---

# 1. Source-supported defect

The supplied exact US test-message artifact contains:

```text
🌐 보조 시장환경
• 보조 거시 맥락에서는 거시 지표가 변화 없음했습니다.
```

The exact payload SHA-256 is recorded as:

`23bfd679e8c1249f3d12ea23a16e19a3172adaf5aca08d52305baf9501bcf822`

The receipt artifact confirms:

```text
rendered_sha256 = outbound_sha256 = received_sha256
```

for that exact message.

However the supplied quality report states:

```text
The invalid phrase `변화 없음했습니다` is absent.

TEST_MESSAGE_QUALITY = PASS
```

Therefore two separate issues exist:

```text
A. user-facing macro wording defect
B. quality-report / exact-payload validation mismatch
```

This task must fix both.

---

# 2. Root-cause audit

Trace the exact path:

```text
shared UsMarketDigestPlan
→ MACRO_CONTEXT slot
→ claim_text
→ full-message renderer
→ test outbound payload
→ received payload
→ message-quality validator
→ quality report
```

Record:

```text
macro evidence refs
temporal roles
observation dates
claim_text source
renderer decision
exact received text
quality-validator input
quality-validator rule
quality-report evidence
```

Hard:

```text
MACRO_ZERO_CHANGE_ROOT_CAUSE = PASS
QUALITY_PAYLOAD_MISMATCH_ROOT_CAUSE = PASS
```

Do not assume the report-generator bug is the only cause until traced.

---

# 3. Macro no-change semantic policy

A generic no-change macro claim such as:

```text
거시 지표가 변화 없음
거시 지표 변화 없음
보조 거시 맥락 변화 없음
```

is normally not material enough to deserve a `🌐 보조 시장환경` section.

Preferred policy:

```text
generic neutral / no-material-change macro
→ OMITTED_SAFE_NOT_MATERIAL
→ omit the macro section entirely
```

when no concrete material macro fact needs user-facing mention.

Do not emit a vacuous section merely to fill the layout.

Hard:

```text
GENERIC_NO_CHANGE_MACRO_SECTION_VISIBLE = 0
```

---

# 4. If a neutral macro fact is genuinely material

A specific current or explicitly dated macro fact may still be shown when useful.

Examples of acceptable semantics:

```text
• 미 10년물 금리는 전 세션과 큰 변화가 없었습니다.
• 공식 관측(8/27) VIX는 큰 변화 없이 유지됐습니다.
```

Only when supported by:

```text
specific evidence ref
specific series
observation date
temporal role
material selection reason
```

Do not render generic:

```text
거시 지표가 변화 없음했습니다
```

Hard:

```text
GENERIC_MACRO_WITHOUT_SPECIFIC_EVIDENCE_VISIBLE = 0
```

---

# 5. Grammar-safe zero-change wording

Do not mechanically concatenate:

```text
"변화 없음" + "했습니다"
```

or equivalent enum/display label + Korean verb ending.

Use semantic templates.

Allowed grammar-safe forms include:

```text
뚜렷한 변화가 없었습니다.
큰 변화 없이 유지됐습니다.
전 세션과 큰 차이가 없었습니다.
```

depending on the actual fact.

Do not hard-code one sentence for every series.

Hard:

```text
MALFORMED_ZERO_CHANGE_KOREAN = 0
```

---

# 6. Renderer fail-closed rule

Even if a legacy/stored plan contains malformed generic macro prose:

the final renderer must not blindly expose it.

For a selected `MACRO_CONTEXT` item require:

```text
safe macro evidence ownership
valid temporal binding
specific/material claim semantics
grammar-safe render template
```

Otherwise:

```text
omit macro section safely
```

Hard:

```text
LEGACY_MALFORMED_MACRO_CLAIM_VISIBLE = 0
```

---

# 7. Preserve temporal safety

Do not weaken the existing temporal gate.

Preserve:

```text
CURRENT_OBSERVATION
PRIOR_MARKET_SESSION
REFERENCE_LAGGING
STALE_FOR_DAILY_SIGNAL
UNAVAILABLE
```

Hard:

```text
SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING = 0
PRIOR_YIELD_AS_TODAY = 0
PRIOR_VIX_AS_TODAY = 0
LAGGING_WTI_AS_TODAY = 0
STALE_MACRO_AS_CURRENT = 0
```

---

# 8. Exact received payload is the quality source of truth

Message-quality validation must evaluate the exact payload that was actually sent/received.

Required ownership:

```text
rendered payload
→ outbound payload
→ received/receipt-linked payload
→ exact-payload quality validator
→ quality report
```

The quality report must not independently describe a different candidate string.

Hard:

```text
QUALITY_VALIDATOR_INPUT = EXACT_RECEIVED_PAYLOAD
```

---

# 9. Quality-report parity

If:

```text
rendered_sha256
outbound_sha256
received_sha256
```

match, the quality report must derive its text assertions from that same payload hash.

Required:

```text
QUALITY_REPORT_PAYLOAD_SHA256 = received_sha256
```

Hard:

```text
QUALITY_REPORT_PAYLOAD_HASH_MISMATCH = 0
REPORT_PAYLOAD_QUALITY_PARITY = PASS
```

---

# 10. Prohibited-phrase validator

Add a small deterministic user-facing Korean quality check for known malformed phrases.

At minimum the historical defect:

```text
변화 없음했습니다
```

must fail.

Do NOT rely solely on one literal substring forever.

Prefer bounded semantic/grammar rules for:

```text
noun/status label + 했습니다
```

where the underlying phrase is not a grammatical predicate.

Do not build a broad Korean grammar engine.

Hard:

```text
HISTORICAL_MALFORMED_PHRASE_REJECTED = PASS
```

---

# 11. Historical broken payload must fail

Use the exact supplied historical payload as a regression fixture.

Expected:

```text
RUN43_EXACT_BAD_PAYLOAD_NEW_QUALITY_GATE = FAIL_AS_EXPECTED
```

It must fail due to the malformed macro sentence and/or invalid generic no-change macro section.

Do not rewrite the historical receipt.

---

# 12. Positive control — macro omitted

Create a candidate with:

```text
index block
market internal
no material safe macro
next check
```

Expected:

```text
🌐 보조 시장환경
```

is omitted entirely.

Quality:

`PASS`

---

# 13. Positive control — specific neutral macro

Create a candidate with a specific safely bound neutral macro fact.

Expected:

```text
grammar-safe sentence
specific evidence provenance
correct temporal qualification
```

Quality:

`PASS`

---

# 14. Preserve required US market sections

This repair must not change the already validated:

```text
🇺🇸 미국시장 마감

📈 주요 지수
SPY / QQQ / IWM / SOXX / RSP numeric returns

🔎 시장 내부
RSP participation/style
strongest sector numeric
weakest sector numeric

🌙 한국 야간선물
conditional safe visibility

📌 다음 확인
```

Hard:

```text
INDEX_BLOCK_DIFF = 0
MARKET_INTERNAL_DIFF = 0
NIGHT_FUTURES_POLICY_DIFF = 0
SECTOR_SELECTION_DIFF = 0
RSP_INTERPRETATION_POLICY_DIFF = 0
```

except unavoidable character-position shifts caused by macro-section omission.

---

# 15. Night-futures isolation

Run-43 had night futures `NOT_AVAILABLE`.

That safe omission remains valid.

Do not change acquisition/session mapping in this task.

Hard:

```text
NIGHT_FUTURES_CODE_DIFF = 0
STALE_NIGHT_FUTURES_AS_CURRENT = 0
```

---

# 16. US Price Structure isolation

US Price Structure is already enabled and is NOT part of this repair.

Do not modify:

```text
SR calculations
proximity semantics
Fib/wave/family consensus
stored-rule ownership
US Price Structure flags
```

Hard:

```text
US_PRICE_STRUCTURE_CODE_DIFF = 0
US_PRICE_STRUCTURE_FLAG_DIFF = 0
```

---

# 17. KR isolation

Hard:

```text
KR_MARKET_DIGEST_CODE_DIFF = 0
KR_PRICE_STRUCTURE_CODE_DIFF = 0
KR_RUNTIME_POLICY_DIFF = 0
```

unless a shared generic quality helper changes; if so prove exact KR parity.

---

# 18. Business / valuation isolation

Hard:

```text
BUSINESS_THESIS_MUTATION = 0
VALUATION_TEXT_DIFF = 0
```

---

# 19. Test-sink validation

Use the existing dedicated non-production test sink.

Generate one current production-equivalent US morning market message.

Do NOT send stock messages in this task.

Default:

```text
TEST_US_MARKET_MESSAGE_COUNT = 1
```

Hard:

```text
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

---

# 20. Exact payload proof

Compare:

```text
rendered payload
outbound payload
received payload
```

Hard:

```text
TEST_EXACT_PAYLOAD_MATCH = PASS
```

Then run quality validation against the `received` payload itself.

---

# 21. Test-message quality gates

Required:

```text
TEST_MESSAGE_QUALITY = PASS
MALFORMED_ZERO_CHANGE_KOREAN = 0
GENERIC_NO_CHANGE_MACRO_SECTION_VISIBLE = 0
LEGACY_MALFORMED_MACRO_CLAIM_VISIBLE = 0
QUALITY_REPORT_PAYLOAD_HASH_MISMATCH = 0
REPORT_PAYLOAD_QUALITY_PARITY = PASS
```

---

# 22. Test exact message report

The report must include:

```text
exact received text
received payload SHA-256
quality validator result
specific quality rules checked
```

Do not write assertions like:

```text
phrase X is absent
```

unless the exact received payload was programmatically checked.

---

# 23. Message quality report generation

The report generator must consume the validator result.

It must not hard-code prose such as:

```text
The invalid phrase ... is absent.
```

without a boolean/evidence result derived from the exact payload.

Hard:

```text
HARDCODED_UNVERIFIED_QUALITY_ASSERTION = 0
```

---

# 24. Deployment

After test-sink PASS:

deploy the micro-repair through the normal operating path.

Preserve current flags:

```text
KR market TOP3 = ON
KR Price Structure = ON
US Price Structure = ON
Production Assist = OFF
```

Run:

```text
API health
US full-message smoke
US Price Structure smoke/parity
KR parity smoke
```

---

# 25. Natural proof

The next natural US morning message must be reviewed read-only.

Verify:

```text
no malformed no-change Korean
no vacuous generic macro section
specific macro only when material/safe
index block intact
market internal intact
night futures safe
exactly once
```

Until then:

```text
US_FULL_MESSAGE =
DEPLOYED_AWAITING_NATURAL_PROOF
```

---

# 26. Focused tests

Required:

### Grammar / semantic macro
```text
"변화 없음했습니다" → FAIL
generic "변화 없음" macro → omitted
specific 10Y neutral fact → grammar-safe PASS
specific VIX neutral fact → grammar-safe PASS
prior-session neutral fact → date-qualified PASS
lagging WTI generic neutral → omitted
```

### Exact-payload quality
```text
bad historical exact payload → FAIL
render/outbound/received identical good payload → PASS
quality report uses same SHA
changed candidate but stale report payload → FAIL
```

### Layout
```text
macro omitted → section order remains valid
macro present → section order remains valid
night futures absent/present
```

---

# 27. Full regression

Required:

```text
focused macro-quality tests
US full-message tests
shared US market-plan tests
evidence-utilization tests
night-futures tests
US Price Structure regression smoke
KR exact parity smoke

full pytest
Ruff
git diff --check
Knowledge parity
Public Action/schema parity
operationId uniqueness
CI
API health
```

No Public Action change expected.

---

# 28. Required architecture / policy docs

Create/update:

```text
docs/architecture/US_MORNING_MESSAGE_LAYOUT.md
docs/architecture/US_MACRO_MESSAGE_RENDERING.md
docs/architecture/EXACT_PAYLOAD_MESSAGE_QUALITY_VALIDATION.md
```

Document:

```text
generic no-change macro omission
specific neutral macro grammar-safe templates
exact received payload as quality source of truth
quality-report payload hash parity
```

---

# 29. Required reports

Create:

1. `docs/reports/20260828-us-macro-zero-change-root-cause.md`
2. `docs/reports/20260828-us-macro-neutral-render-policy.md`
3. `docs/reports/20260828-us-exact-payload-quality-root-cause.md`
4. `docs/reports/20260828-us-exact-payload-quality-contract.md`
5. `docs/reports/20260828-us-broken-payload-regression.md`
6. `docs/reports/20260828-us-macro-quality-before-after.md`
7. `docs/reports/20260828-us-macro-quality-test-delivery.md`
8. `docs/reports/20260828-us-macro-quality-exact-test-message.md`
9. `docs/reports/20260828-us-macro-quality-safety-parity.md`
10. `docs/reports/20260828-us-macro-quality-readiness.md`
11. `docs/reports/20260828-us-macro-quality-natural-proof-status.md`
12. `docs/reports/20260828-us-macro-quality-artifact-index.md`

Machine-readable:

```text
docs/reports/20260828-us-macro-quality-readiness.json
docs/reports/20260828-us-macro-quality-test-receipt.json
```

---

# 30. Required gates

Set exactly:

```text
MACRO_ZERO_CHANGE_ROOT_CAUSE =
PASS / FAIL

QUALITY_PAYLOAD_MISMATCH_ROOT_CAUSE =
PASS / FAIL

GENERIC_NO_CHANGE_MACRO_SECTION_VISIBLE =
0 / NONZERO

GENERIC_MACRO_WITHOUT_SPECIFIC_EVIDENCE_VISIBLE =
0 / NONZERO

MALFORMED_ZERO_CHANGE_KOREAN =
0 / NONZERO

LEGACY_MALFORMED_MACRO_CLAIM_VISIBLE =
0 / NONZERO

QUALITY_VALIDATOR_INPUT =
EXACT_RECEIVED_PAYLOAD / OTHER

QUALITY_REPORT_PAYLOAD_HASH_MISMATCH =
0 / NONZERO

REPORT_PAYLOAD_QUALITY_PARITY =
PASS / FAIL

HISTORICAL_MALFORMED_PHRASE_REJECTED =
PASS / FAIL

RUN43_EXACT_BAD_PAYLOAD_NEW_QUALITY_GATE =
FAIL_AS_EXPECTED / UNEXPECTED_PASS

HARDCODED_UNVERIFIED_QUALITY_ASSERTION =
0 / NONZERO

SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING =
0 / NONZERO

PRIOR_YIELD_AS_TODAY =
0 / NONZERO

PRIOR_VIX_AS_TODAY =
0 / NONZERO

LAGGING_WTI_AS_TODAY =
0 / NONZERO

STALE_MACRO_AS_CURRENT =
0 / NONZERO

INDEX_BLOCK_DIFF =
0 / NONZERO

MARKET_INTERNAL_DIFF =
0 / NONZERO

NIGHT_FUTURES_POLICY_DIFF =
0 / NONZERO

SECTOR_SELECTION_DIFF =
0 / NONZERO

RSP_INTERPRETATION_POLICY_DIFF =
0 / NONZERO

US_PRICE_STRUCTURE_CODE_DIFF =
0 / NONZERO

US_PRICE_STRUCTURE_FLAG_DIFF =
0 / NONZERO

KR_MARKET_DIGEST_CODE_DIFF =
0 / NONZERO

KR_PRICE_STRUCTURE_CODE_DIFF =
0 / NONZERO

BUSINESS_THESIS_MUTATION =
0 / NONZERO

VALUATION_TEXT_DIFF =
0 / NONZERO

TEST_US_MARKET_MESSAGE_COUNT =
1 / OTHER

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL / NOT_SENT

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

TEST_MESSAGE_QUALITY =
PASS / FAIL / NOT_SENT

OPERATING_PROMOTION =
PASS / NOT_RUN / FAIL

PRODUCTION_ASSIST =
OFF / OTHER

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

US_MACRO_QUALITY_REPAIR =
DEPLOYED_AWAITING_NATURAL_PROOF /
FAIL
```

---

# 31. PASS rule

PASS only if:

```text
generic no-change macro is omitted
specific neutral macro uses grammar-safe wording
historical bad run-43 payload fails the new quality gate
quality validator inspects exact received payload
quality report uses the same received payload hash
test-sink exact payload passes
current US market sections remain unchanged
US Price Structure remains unchanged
KR remains unchanged
P0/P1 = 0/0
```

Then:

```text
US_MACRO_QUALITY_REPAIR =
DEPLOYED_AWAITING_NATURAL_PROOF
```

---

# 32. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BASE_SHA = ...
BRANCH = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

MACRO_ZERO_CHANGE_ROOT_CAUSE = ...
QUALITY_PAYLOAD_MISMATCH_ROOT_CAUSE = ...

GENERIC_NO_CHANGE_MACRO_SECTION_VISIBLE = 0
GENERIC_MACRO_WITHOUT_SPECIFIC_EVIDENCE_VISIBLE = 0
MALFORMED_ZERO_CHANGE_KOREAN = 0
LEGACY_MALFORMED_MACRO_CLAIM_VISIBLE = 0

QUALITY_VALIDATOR_INPUT = EXACT_RECEIVED_PAYLOAD
QUALITY_REPORT_PAYLOAD_SHA256 = ...
RECEIVED_PAYLOAD_SHA256 = ...
QUALITY_REPORT_PAYLOAD_HASH_MISMATCH = 0
REPORT_PAYLOAD_QUALITY_PARITY = PASS

HISTORICAL_MALFORMED_PHRASE_REJECTED = PASS
RUN43_EXACT_BAD_PAYLOAD_NEW_QUALITY_GATE = FAIL_AS_EXPECTED
HARDCODED_UNVERIFIED_QUALITY_ASSERTION = 0

EXACT_TEST_MESSAGE =
...

TEST_US_MARKET_MESSAGE_COUNT = 1
TEST_EXACT_PAYLOAD_MATCH = ...
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
TEST_MESSAGE_QUALITY = ...

INDEX_BLOCK_DIFF = 0
MARKET_INTERNAL_DIFF = 0
NIGHT_FUTURES_POLICY_DIFF = 0
SECTOR_SELECTION_DIFF = 0
RSP_INTERPRETATION_POLICY_DIFF = 0

US_PRICE_STRUCTURE_CODE_DIFF = 0
US_PRICE_STRUCTURE_FLAG_DIFF = 0
KR_MARKET_DIGEST_CODE_DIFF = 0
KR_PRICE_STRUCTURE_CODE_DIFF = 0

BUSINESS_THESIS_MUTATION = 0
VALUATION_TEXT_DIFF = 0

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...
API_HEALTH = ...

OPERATING_PROMOTION = ...
PRODUCTION_ASSIST = OFF

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

US_MACRO_QUALITY_REPAIR =
DEPLOYED_AWAITING_NATURAL_PROOF /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_US_MORNING /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 33. Mandatory completion ZIP

Create:

`20260828-us-macro-zero-change-wording-and-exact-payload-quality-gate-micro-repair-bundle.zip`

Include:

```text
exact instruction
root-cause reports
macro-neutral render policy
exact-payload quality contract
historical broken-payload regression
before/after exact message
test delivery
exact test receipt
quality report
safety parity
readiness
natural-proof status
test/CI summary
artifact index
```

Exclude:

```text
secrets
raw sink IDs
auth headers
tokens
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 34. Final principle

The user-visible message and the quality report must describe the same bytes.

If the exact received Telegram message contains:

```text
변화 없음했습니다
```

the validator must fail.

And if macro has no material specific message:

```text
omit the macro section
```

rather than filling it with generic no-change prose.

This repair is complete when the exact payload is grammatical, useful, and the quality report is mechanically
bound to that exact payload.
