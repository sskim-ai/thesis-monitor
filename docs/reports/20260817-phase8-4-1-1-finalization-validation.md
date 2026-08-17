# Phase 8.4.1.1 Finalization Validation

## Repository

- Branch: `codex/phase-8-4-1-1-valuation-context-finalization`
- Exact base: `3ee719e9bc7db1ffea441f1de4b2a3ca8e8f26de`
- Implementation commit: `f6a772c`
- Production main and operating checkout: `aeb87a9d2aee0d4b840c0a8717319e01b375f5f5`
- Main merge / deployment / DB migration: none
- Provider calls / Telegram sends / operating mutations / Pilot mutations: `0 / 0 / 0 / 0`

## Root Cause

`_valuation_text()` appended selected own-history prose and then unconditionally appended
`_profile_peer_gap()`. That fixed fallback was keyed only by reasoning profile and peer absence; it
did not receive historical availability or actual-use state. It could therefore say “current
multiple only” after rendering a historical percentile.

The fix is generic. `valuation-context-wording-v1` records availability and actual use for current,
own history, peer, and forward context. The renderer selects a wording class, and the binder derives
actual use again from numeric bindings before removing the draft-only reference.

## Wording Matrix

| Current | History | Peer | Class | Result |
|---|---|---|---|---|
| used | used | unavailable | `CURRENT_PLUS_HISTORY` | Current company multiple plus own-history wording |
| used | unavailable | unavailable | `CURRENT_ONLY` | Current-only wording; both missing contexts explicit |
| used | used | used | `CURRENT_PLUS_HISTORY_PLUS_PEER` | Three contexts available for decision-based wording |
| used | unsafe | unavailable | `CURRENT_ONLY` | Unsafe history excluded; compact caution eligible |
| used | unsafe | used | `CURRENT_PLUS_PEER` | Current plus peer; unsafe history excluded |
| unavailable | any | any | `LIMITED_VALUATION` | No current cheap/expensive interpretation |

Focused matrix fixture:
`tests/test_semantic_decision_hardening.py::test_valuation_context_availability_matrix`.

## Representative Results

| Ticker | History used | Peer used | Class | Before | After |
|---|---:|---:|---|---|---|
| Samsung 005930 | yes, PBR 91.6 percentile | no | `CURRENT_PLUS_HISTORY` | Current-only contradiction | Company current multiples plus own-history position |
| POSCO 005490 | no; safe history not decision-band selected | no | `CURRENT_ONLY` | Fixed peer-gap phrase | Current context only, without claiming safe history is absent |
| Hyundai Glovis 086280 | yes, PER 92.8 percentile | no | `CURRENT_PLUS_HISTORY` | Current-only contradiction | Current multiples plus own-history position |
| Korean Re 003690 | no safe history | no | `CURRENT_ONLY` | Profile-specific fixed fallback | Current-only limitation is semantically correct |
| SK hynix 000660 | yes, safe PBR 87.0 percentile; PE denied | no | `CURRENT_PLUS_HISTORY` | Current-only contradiction | Safe company PBR plus own-history PB only |

Exact renderer output is in
[`20260817-phase8-4-1-1-final-preview.md`](20260817-phase8-4-1-1-final-preview.md).

## Semantic Validation

- Numeric bindings: 86 automatic, 0 manual, 0 rejected
- Typed valuation occurrences: 12 accepted, 0 errors
- Valuation-context references: 5 accepted, 0 errors
- Visible history plus current-only contradiction: 0 in AFTER messages
- Company/segment scope violation: 0
- Denied numeric or qualitative echo: 0
- Unsafe historical use: 0
- Full schema-4 validator: PASS
- Runtime quality receipt: PASS
- Final language and template gate: PASS

Negative fixture:
`tests/test_semantic_decision_hardening.py::test_valuation_context_rejects_history_with_current_only_wording`.
Positive fixture:
`tests/test_semantic_decision_hardening.py::test_valuation_context_accepts_current_plus_history_wording`.
Representative fixture:
`tests/test_semantic_decision_hardening.py::test_representative_valuation_context_classes_match_final_preview`.

## Regression

Decision hierarchy, historical selection, observer/holder distinction, denied-family protection,
and current-value next checks are unchanged. Samsung remains `VALID_AND_COHERENT`. SK hynix denied
earnings and PE remain absent. The Phase 8.4.1.1 messages average 1.1% more characters than Phase
8.4.1, with no line or section increase.

Focused suite: `48 passed`. Full local suite after documentation synchronization: `982 passed`, one
third-party Starlette deprecation warning. Ruff and `git diff --check`: PASS.

## Phase 8.4 Final Status

| Capability | Status |
|---|---|
| Integrated Full Message | CLOSED |
| Delta-First | CLOSED |
| Adaptive Rendering | CLOSED |
| Valuation Scope | CLOSED |
| Denied Fact Echo | CLOSED |
| Decision-Material Delta | CLOSED |
| Historical Valuation Retention | CLOSED |
| Valuation Context Wording | CLOSED |
| Observer/Holder Foundation | CLOSED |
| Unknown Foundation | CLOSED |
| Next Check Foundation | CLOSED |
| Industry-Specific Reasoning | PARTIAL |

Phase 8.4.1 Work scores were 17/16/18/16/17, average 16.8/20. Phase 8.4.1.1 is the final wording
follow-up. This closes the message-intelligence engineering foundation, not Production Assist
approval.

## Runtime Isolation

The natural KR packet `2026-08-17-kr-run-23-378ee562573e` appeared independently during this work
and was rejected pre-send for missing required current-price RR Facts on four stocks. It sent no
rejected AI text, preserved deterministic fallback eligibility, and did not advance Pilot. Actual
runtime remains KR 3/5 and US 3/5. This retrospective did not touch that packet or runtime state.

## Recommendation

Default next is Phase 8.5 Industry-Specific Investment Reasoning. If KRX approval is confirmed,
Phase 8.2A KRX Market Breadth Primary may be inserted first. Main merge and shadow deployment need a
separate user decision; Production Assist remains OFF.
