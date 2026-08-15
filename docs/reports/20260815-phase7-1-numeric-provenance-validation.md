# Phase 7.1 Numeric Provenance Validation

Date: 2026-08-15

Policy: `daily-review-v3.9`

Final output schema: `4`
Base commit: `b1b495879b1d5bdbedc38a1dfe45a0cafcfd1ca0`

## Scope

This phase moves numeric transcription, labeling, formatting, and claim construction from Codex into
a deterministic backend binder. The validator remains independent and fail closed. It also separates
TSM issuer financial currency from ADR price currency and preserves deterministic fallback through AI
validation rejection and bounded network retries.

## 2026-08-15 US Rejection

The handed-off rejected review contains the following seven exact uncovered-number diagnostics when
the repository's occurrence scanner and claim ranges are applied:

1. `CORZ:numbers_without_provenance:business_earnings.text:164201000`
2. `HUT:numbers_without_provenance:valuation_analysis.text:0.59`
3. `IBM:numbers_without_provenance:business_earnings.text:17162000000`
4. `RXRX:numbers_without_provenance:business_earnings.text:7670000`
5. `TSLA:numbers_without_provenance:business_earnings.text:28236000000`
6. `TSM:numbers_without_provenance:core_judgment.text:1.27038e+12`
7. `TSM:numbers_without_provenance:business_earnings.text:1.27038e+12`

All seven are `UNCOVERED_NUMBER`. One is a real missing occurrence claim: HUT `$0.59`. The other six
are punctuation-span false negatives: the old scanner included the sentence comma after an integer in
the numeric token while the exact claim usage correctly stopped before the comma. The fix excludes
trailing punctuation from the token span; it does not exempt the digits from coverage. HUT remains a
hard reject unless the unsafe number is removed or supplied through a valid canonical fact reference.

| Error | Required taxonomy | Root cause |
|---|---|---|
| CORZ `164201000` | `UNCOVERED_NUMBER` | punctuation included in validator token span |
| HUT `0.59` | `UNCOVERED_NUMBER` | `OMITTED_CLAIM` sub-cause; no fact occurrence binding |
| IBM `17162000000` | `UNCOVERED_NUMBER` | punctuation included in validator token span |
| RXRX `7670000` | `UNCOVERED_NUMBER` | punctuation included in validator token span |
| TSLA `28236000000` | `UNCOVERED_NUMBER` | punctuation included in validator token span |
| TSM `1.27038e+12` core | `UNCOVERED_NUMBER` | punctuation included in validator token span |
| TSM `1.27038e+12` earnings | `UNCOVERED_NUMBER` | punctuation included in validator token span |

No rejected occurrence was attributed to `WRONG_FIELD`, `WRONG_SEMANTIC`, `WRONG_UNIT`,
`ROUNDING_MISMATCH`, or `WRONG_TEXT_REF`. TSM did reveal a separate packet-construction currency-basis
defect: earnings amounts could inherit USD from the ADR price field. That issue is fixed independently
and covered by the TWD/USD split regression.

## Before And After Evidence

| Contract | Before | After |
|---|---:|---:|
| Integer followed by sentence comma | 6 uncovered false negatives | 0; exact claims cover the digit span |
| HUT `$0.59` without a claim/ref | 1 uncovered error | Still rejected |
| HUT value removed from prose | Not applicable | 0 uncovered occurrences |
| HUT valid canonical fact reference | Manual transcription required | Backend renders value and creates claim |
| TSM preliminary revenue/operating income | Could inherit USD ADR price currency | Uses `financial_currency` (TWD) |

An in-memory occurrence replay of the unchanged rejected review produced `7 -> 1` when only the
token-span implementation changed: the six punctuation false negatives disappeared and HUT remained.
Replacing only the HUT occurrence with its exact canonical numeric reference produced `1 -> 0`
uncovered occurrences. The source evidence file was not modified.

The operating archive contained the immutable packet, both rejected attempts, and the original
validator-result artifact. The packet SHA-256 is
`9487b6a89a679ca29d66f2aca6b68f4d882f23c6664f0b14e3942094515634b1`; the seven-error rejected
attempt SHA-256 is `7b0fa31e4cd899772d689b8cbf28490e74a5c85c793f0399c9c5fb8362ae8144`.
Using a SQLite backup and the unchanged artifacts, the old validator reproduced the seven specified
errors. v3.9 reduced the unchanged review to only HUT `$0.59`. The packet contains the exact
`valuation:current` / `fields.forward_eps` / `USD` / `forward_eps` registry row, so the retrospective
draft replaced `선행 EPS $0.59` with one `{{numeric:hut_forward_eps}}` reference. The backend bound
`예상 EPS $0.59`, generated the exact claim, and the full validator passed with zero errors. The
packet and rejected-review hashes remained unchanged; no packet was regenerated.

The original v3.8 packet retains its historical TSM USD financial-currency defect and was not
rewritten. A separate structural foreign-issuer fixture under v3.9 produced USD ADR price,
TWD revenue `NT$1.27T`, and TWD operating income `NT$766.6B` without an ADR-ratio conversion.

## Regression Coverage

- Draft references render canonical values and generate final schema-4 claims without mutating input.
- Missing facts, fields, semantics, scopes, placeholders, and formatters fail closed.
- Source-aware forward labels distinguish modeled estimates from consensus.
- USD, KRW, and TWD amounts; percentages; basis points; multiples; shares; points; zones; and
  risk/reward use deterministic display rules.
- A trailing sentence comma no longer produces a false uncovered span.
- HUT `$0.59` without provenance remains rejected.
- TSM earnings use TWD while ADR price uses USD.
- Finalization persists the bound schema-4 output and numeric-binding telemetry.
- AI rejection preserves the held deterministic fallback and does not count as a Pilot success.
- Network failure retries the identical persisted fallback payload without analysis, packet, or
  rendering reruns.

## Operational Decision

The operating checkout was fast-forwarded to
`130719fb1b018fe0857259acc7cd9a46977a080a` (tree
`00dd9014726a31545821056baa0d436302a12388`) and the API LaunchAgent was restarted. API and US/KR AI
health checks passed. Schema remains 4 and Production Assist remains disabled.

The binder matrix auto-bound 13 representative values across USD, KRW, TWD, percentages, basis
points, multiples, signed shares, zone endpoints, and futures points. It left the draft unchanged,
removed all draft refs, emitted no unresolved placeholder, and recorded unique stable logical IDs.
All 16 independent negative cases rejected without a guessed replacement; each produced machine
context whose only actions were reference correction, wording correction, or unsafe-number removal.

The isolated delivery tests preserved held fallback eligibility after AI rejection, delivered only
the stored deterministic fallback at deadline, retried byte-identical persisted content, stopped
after three retries, and archived late AI without sending or counting it.

All four local-project Scheduled Tasks are ACTIVE and now use policy v3.9, schema 4, structure v2,
Pilot v3, renderer v3, and the exact documented claim commands. No duplicate task was created.

Runtime evidence shows the 2026-08-15 US v3.8 session had already passed validation, sent 14/14
AI-assisted messages, and completed its archive at 08:40 KST before this retrospective. The verified
current cohort is therefore KR 1/5 and US 1/5. This retrospective sent zero Telegram messages and
made zero official database or Pilot-counter mutations.
