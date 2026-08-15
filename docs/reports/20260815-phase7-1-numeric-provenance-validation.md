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
Removing only the unsupported HUT `$0.59` token, one of the machine-authorized correction actions,
produced `1 -> 0` uncovered occurrences. The source evidence file was not modified.

The immutable packet and original validator-result artifact were not present in the handoff ZIP,
repository, or available Library copy. Therefore this report does not claim a full same-packet
schema/fact validator PASS. It records the exact reproducible coverage diagnostics from the rejected
review and code, plus focused regression tests. A full retrospective must reuse the original packet;
canonical fact identity, source currency, or ADR basis must never be reconstructed from AI prose.

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

The Pilot cohort remains `ai-assisted-pilot-v3` with KR 1/5 and US 0/5. Schema remains 4, Production
Assist remains disabled, and policy changes to `daily-review-v3.9`. Historical v3.8 archives and
cohort evidence are not rewritten.

The Scheduled-task lookup exposed three unrelated inactive/completed automations and none of the four
thesis-monitor local-project tasks. Consequently their ACTIVE state and v3.9 prompt migration are not
verified. No standalone web duplicates were created. The owning ChatGPT desktop environment must
apply `docs/operations/SCHEDULED_TASK_CONTRACTS.md` and confirm all four tasks before Pilot resumes.
