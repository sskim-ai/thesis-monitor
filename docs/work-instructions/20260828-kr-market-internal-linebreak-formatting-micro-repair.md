# thesis-monitor — KR Market Internal Section Line-Break Formatting Micro Repair
## `📊 시장 내부` 가독성 개선
## Formatting only — no data/ranking/selection/Price Structure logic changes

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-28 KST`
- Workstream: `KR_MARKET_INTERNAL_LINEBREAK_FORMATTING_MICRO_REPAIR`
- Task class: `BOUNDED_RENDERER_FORMATTING_REPAIR`
- Scope: KR afternoon/close market digest formatting only
- Production Assist: preserve `OFF`
- KR market TOP3: preserve `ON`
- KR Price Structure: preserve `ON`
- US Price Structure: preserve `OFF`
- Telegram production-recipient test send: `0`
- Manual production scheduler execution: `0`
- DB / assessment mutation: `0`

### Latest known enabled state

Previous successful pre-enable / enable result:

```text
Final main / operating:
d00b5b6c89e67748d6b1d376e709770ae747566c

Test delivery:
market 1 + stock 7 = 8/8 exactly once

KR TOP3:
ON

KR Price Structure:
ON

US Price Structure:
OFF

Production Assist:
OFF

KR rollout:
ENABLED_AWAITING_NATURAL_PROOF

Open P0/P1:
0/0
```

Before implementation:

1. `git fetch origin`
2. verify clean worktree
3. resolve actual latest safe `origin/main`
4. resolve current operating SHA
5. require current operating lineage to include the enabled KR rollout above
6. do not alter runtime feature states except normal deployment of this formatting fix

---

# 1. Objective

Improve readability of the already-correct `📊 시장 내부` section.

Current content is semantically correct but too dense because:

```text
규모별: ...; KOSDAQ...
업종 상대 강세: ...; KOSDAQ...
업종 상대 약세: ...; KOSDAQ...
```

is rendered as long inline sentences.

Change only presentation:

```text
section heading
blank line
subheading
KOSPI line
KOSDAQ line
blank line
next subheading
...
```

No market evidence selection changes.

---

# 2. Required target format

The target user-facing structure should be semantically equivalent to:

```text
📊 시장 내부

규모별
• KOSPI: 대형 +1.66% · 중형 +0.22% · 소형 -0.13%
• KOSDAQ: 100 +1.94% · MID300 +0.76% · SMALL +0.44%

업종 상대 강세
• KOSPI: 전기·전자 +2.62% · 금속 +2.30% · 제조 +2.04%
• KOSDAQ: 금융 +3.21% · 전기·전자 +3.08% · 기계·장비 +2.48%

업종 상대 약세
• KOSPI: 유통 -2.36% · 전기·가스 -2.05% · 음식료·담배 -1.56%
• KOSDAQ: 오락·문화 -1.29% · 출판·매체복제 -1.11% · 통신 -0.82%
```

The exact numeric values above are regression examples only.

Do NOT hard-code them.

---

# 3. Formatting contract

Required:

```text
📊 시장 내부
→ followed by one blank line

규모별
→ standalone line

KOSPI size row
→ standalone line

KOSDAQ size row
→ standalone line

blank line

업종 상대 강세
→ standalone line

KOSPI strong TOP3
→ standalone line

KOSDAQ strong TOP3
→ standalone line

blank line

업종 상대 약세
→ standalone line

KOSPI weak TOP3
→ standalone line

KOSDAQ weak TOP3
→ standalone line
```

Recommended bullet:

`•`

Use existing renderer conventions if a canonical bullet already exists.

---

# 4. Hard scope boundary

Do NOT change:

```text
KOSPI/KOSDAQ direction
breadth
foreign/institution/retail flow
size/style data
TOP3 sector ranking
TOP3 sector selection
sector numeric values
numeric provenance
KR local-first ownership
AI/fallback evidence selection
next-check logic
Price Structure logic
Price Structure flags
US logic
business thesis
```

Hard:

```text
DATA_VALUE_DIFF = 0
TOP3_RANKING_DIFF = 0
EVIDENCE_SELECTION_DIFF = 0
NUMERIC_PROVENANCE_DIFF = 0
PRICE_STRUCTURE_CODE_DIFF = 0
US_MARKET_CODE_DIFF = 0
```

---

# 5. AI / deterministic fallback formatting parity

Both AI and deterministic fallback must use the same structural layout contract.

The AI may produce different explanatory prose outside `📊 시장 내부`.

Inside the section, both paths must preserve:

```text
same size rows
same strong TOP3
same weak TOP3
same line-break hierarchy
```

Hard:

```text
AI_FALLBACK_MARKET_INTERNAL_DATA_PARITY = PASS
AI_FALLBACK_MARKET_INTERNAL_LAYOUT_PARITY = PASS
```

---

# 6. No user-facing English leader/laggard

Preserve:

```text
업종 상대 강세
업종 상대 약세
```

Hard:

`USER_FACING_LEADER_LAGGARD_TERM = 0`

---

# 7. Telegram rendering safety

The output must remain safe in Telegram plain-text/Markdown mode.

Verify:

```text
no unintended markdown list nesting
no bullet escaping issue
no collapsed blank lines
no truncation
no broken emoji
no malformed percentage symbols
```

Hard:

```text
TELEGRAM_MARKDOWN_BREAKAGE = 0
MESSAGE_TRUNCATED = 0
```

---

# 8. Test-sink validation

Use the already configured dedicated non-production test sink.

Do NOT send to production recipient.

Generate one production-equivalent KR market digest using the latest completed safe KR session.

Send exactly once to test sink.

Hard:

```text
TEST_MARKET_MESSAGE_COUNT = 1
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

No stock-message test send is required because Price Structure is out of scope.

---

# 9. Exact payload validation

Compare:

```text
renderer output
outbound test payload
receipt-linked/received payload
```

Hard:

`TEST_EXACT_PAYLOAD_MATCH = PASS`

---

# 10. Received-message visual review

Confirm actual received test message shows:

```text
📊 시장 내부

규모별
• KOSPI ...
• KOSDAQ ...

업종 상대 강세
• KOSPI ...
• KOSDAQ ...

업종 상대 약세
• KOSPI ...
• KOSDAQ ...
```

Hard:

```text
MARKET_INTERNAL_SECTION_LINEBREAKS = PASS
SIZE_SECTION_READABILITY = PASS
STRONG_SECTOR_SECTION_READABILITY = PASS
WEAK_SECTOR_SECTION_READABILITY = PASS
TEST_MESSAGE_QUALITY = PASS
```

---

# 11. Existing live feature state must remain unchanged

During implementation/test:

```text
KR market TOP3 = ON
KR Price Structure = ON
US Price Structure = OFF
Production Assist = OFF
```

Hard:

```text
KR_TOP3_FLAG_DIFF = 0
KR_PRICE_STRUCTURE_FLAG_DIFF = 0
US_PRICE_STRUCTURE_ENABLED = 0
PRODUCTION_ASSIST = OFF
```

---

# 12. Price Structure isolation

This formatting repair must not alter:

```text
daily coverage
SR
nearest/major semantics
Fib
wave/family consensus
stored-rule ownership
```

Hard:

```text
PRICE_STRUCTURE_CODE_DIFF = 0
PRICE_STRUCTURE_RUNTIME_DIFF = 0
```

---

# 13. Operating promotion

After test-sink PASS:

promote the formatting-only commit through the normal deployment path.

Then verify:

```text
API health
KR market renderer smoke
KR TOP3 still ON
KR Price Structure still ON
US Price Structure still OFF
```

No feature toggle sequence is needed because the features are already enabled.

---

# 14. Natural proof status

This task does not claim final KR rollout `LIVE_PASS`.

The next natural KR market message remains the production proof.

Expected after deployment:

```text
KR_ROLLOUT = ENABLED_AWAITING_NATURAL_PROOF
```

Then verify on the next natural KR close:

```text
new line-break layout visible
TOP3 data correct
exactly once
```

---

# 15. Focused tests

Required:

```text
market-internal renderer unit test
AI path layout
fallback path layout
TOP3 data equality
size/style data equality
blank-line preservation
Telegram bullet rendering
empty/partial-safe market side handling
```

Test partial-safe examples:

```text
KOSPI available / KOSDAQ unavailable
fewer than 3 sectors
size/style partial-safe
```

No empty heading should remain.

---

# 16. Full regression

Required:

```text
focused formatting tests
KR market digest tests
KR local-first tests
TOP3 tests
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

# 17. Required reports

Create:

1. `docs/reports/20260828-kr-market-internal-formatting-before-after.md`
2. `docs/reports/20260828-kr-market-internal-layout-contract.md`
3. `docs/reports/20260828-kr-market-internal-ai-fallback-parity.md`
4. `docs/reports/20260828-kr-market-internal-test-delivery.md`
5. `docs/reports/20260828-kr-market-internal-exact-test-message.md`
6. `docs/reports/20260828-kr-market-internal-message-quality.md`
7. `docs/reports/20260828-kr-market-internal-safety-parity.md`
8. `docs/reports/20260828-kr-market-internal-readiness.md`
9. `docs/reports/20260828-kr-market-internal-artifact-index.md`

---

# 18. Required gates

Set exactly:

```text
MARKET_INTERNAL_FORMATTING_POLICY =
PASS / FAIL

MARKET_INTERNAL_SECTION_LINEBREAKS =
PASS / FAIL

SIZE_SECTION_READABILITY =
PASS / FAIL

STRONG_SECTOR_SECTION_READABILITY =
PASS / FAIL

WEAK_SECTOR_SECTION_READABILITY =
PASS / FAIL

AI_FALLBACK_MARKET_INTERNAL_DATA_PARITY =
PASS / FAIL

AI_FALLBACK_MARKET_INTERNAL_LAYOUT_PARITY =
PASS / FAIL

DATA_VALUE_DIFF =
0 / NONZERO

TOP3_RANKING_DIFF =
0 / NONZERO

EVIDENCE_SELECTION_DIFF =
0 / NONZERO

NUMERIC_PROVENANCE_DIFF =
0 / NONZERO

USER_FACING_LEADER_LAGGARD_TERM =
0 / NONZERO

TELEGRAM_MARKDOWN_BREAKAGE =
0 / NONZERO

MESSAGE_TRUNCATED =
0 / NONZERO

TEST_MARKET_MESSAGE_COUNT =
1 / OTHER

TEST_DUPLICATE =
0 / NONZERO

TEST_ORPHAN =
0 / NONZERO

TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

TEST_EXACT_PAYLOAD_MATCH =
PASS / FAIL

TEST_MESSAGE_QUALITY =
PASS / FAIL

KR_TOP3_FLAG_DIFF =
0 / NONZERO

KR_PRICE_STRUCTURE_FLAG_DIFF =
0 / NONZERO

US_PRICE_STRUCTURE_ENABLED =
0 / NONZERO

PRODUCTION_ASSIST =
OFF / OTHER

PRICE_STRUCTURE_CODE_DIFF =
0 / NONZERO

PRICE_STRUCTURE_RUNTIME_DIFF =
0 / NONZERO

OPERATING_PROMOTION =
PASS / NOT_RUN / FAIL

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

KR_MARKET_INTERNAL_FORMATTING =
DEPLOYED_AWAITING_NATURAL_PROOF /
FAIL
```

---

# 19. PASS rule

PASS only if:

```text
formatting changed exactly as intended
market values unchanged
TOP3 order unchanged
provenance unchanged
AI/fallback layout parity PASS
test sink actual received message readable
exact payload match
no Telegram formatting break
feature states unchanged
Price Structure unchanged
US unchanged
P0/P1 = 0/0
```

Then:

```text
KR_MARKET_INTERNAL_FORMATTING =
DEPLOYED_AWAITING_NATURAL_PROOF
```

---

# 20. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
BASE_SHA = ...
BRANCH = ...
IMPLEMENTATION_SHA = ...
REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

MARKET_INTERNAL_FORMATTING_POLICY = ...

MARKET_INTERNAL_SECTION_LINEBREAKS = ...
SIZE_SECTION_READABILITY = ...
STRONG_SECTOR_SECTION_READABILITY = ...
WEAK_SECTOR_SECTION_READABILITY = ...

AI_FALLBACK_MARKET_INTERNAL_DATA_PARITY = ...
AI_FALLBACK_MARKET_INTERNAL_LAYOUT_PARITY = ...

DATA_VALUE_DIFF = 0
TOP3_RANKING_DIFF = 0
EVIDENCE_SELECTION_DIFF = 0
NUMERIC_PROVENANCE_DIFF = 0

USER_FACING_LEADER_LAGGARD_TERM = 0
TELEGRAM_MARKDOWN_BREAKAGE = 0
MESSAGE_TRUNCATED = 0

TEST_MARKET_MESSAGE_COUNT = 1
TEST_DUPLICATE = 0
TEST_ORPHAN = 0
TEST_MESSAGE_SENT_TO_PRODUCTION_RECIPIENT = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0

TEST_EXACT_PAYLOAD_MATCH = ...
TEST_MESSAGE_QUALITY = ...

EXACT_TEST_MESSAGE =
...

KR_TOP3_FLAG_DIFF = 0
KR_PRICE_STRUCTURE_FLAG_DIFF = 0
US_PRICE_STRUCTURE_ENABLED = 0
PRODUCTION_ASSIST = OFF

PRICE_STRUCTURE_CODE_DIFF = 0
PRICE_STRUCTURE_RUNTIME_DIFF = 0

OPERATING_PROMOTION = ...

FOCUSED_TESTS = ...
FULL_PYTEST = ...
RUFF = ...
DIFF_CHECK = ...
KNOWLEDGE_PARITY = ...
PUBLIC_ACTION = ...
OPERATION_ID = ...
CI = ...
API_HEALTH = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

KR_MARKET_INTERNAL_FORMATTING =
DEPLOYED_AWAITING_NATURAL_PROOF /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_KR_MARKET_MESSAGE /
BOUNDED_REPAIR

ZIP = ...
ZIP_SHA256 = ...
```

---

# 21. Mandatory completion ZIP

Create:

`20260828-kr-market-internal-linebreak-formatting-micro-repair-bundle.zip`

Include:

```text
exact instruction
before/after layout
layout contract
AI/fallback parity
test delivery
exact test message
message quality
safety parity
readiness
test/CI summary
artifact index
```

Exclude:

```text
raw sink IDs
secrets
tokens
auth headers
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 22. Final principle

This is a readability fix only.

The market evidence is already correct.

Do not change:

```text
what is selected
what is ranked
what is calculated
what is enabled
```

Only change:

```text
how `📊 시장 내부` is visually grouped for the user.
```
