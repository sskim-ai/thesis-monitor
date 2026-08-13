# AI-Assisted Telegram Single-Delivery Pilot Validation

## Repository

- Repository: `sskim-ai/thesis-monitor`
- Branch: `main`
- Base: `23d01eb6d13666ceb21c09686db18a94895b1e09`
- DB migration: none
- Public Action schema: unchanged, `0.4.5`, operationId `20/20`
- AI review mode: `shadow`
- Delivery pilot: enabled separately
- GitHub Actions: pending at report creation

## Delivery Policy

Normal pilot sessions now choose exactly one user delivery representation:

```text
deterministic evaluation
-> exact deterministic payload archived and held
-> validated AI output available
-> deterministic status/numbers + validated AI narrative
-> one AI-assisted Telegram set
```

If no validated output exists at the hard deadline, the held deterministic payload is restored and
sent without rerunning event collection, macro calculation, valuation, or thesis evaluation. A late
AI result after fallback is archive-only. Internal `_ai_assisted_pilot` metadata is excluded from the
logical content hash and never rendered to Telegram.

## KR Flow

- 16:05: close collection and deterministic assessment; Telegram is held.
- 16:15: Codex Primary.
- 16:55: Codex Backup after the claim lease window.
- 17:10: deterministic fallback deadline.

## US Flow

- 07:50: deterministic assessment.
- 08:00-08:45: existing KRX night-futures gate.
- Gate ready/deadline: final deterministic context is archived and held.
- 08:50: Codex Primary.
- 09:30: Codex Backup.
- 09:45: deterministic fallback deadline.

The KRX readiness and session-freshness rules are unchanged. Gate retries still refresh only night
futures and do not rerun company or macro evaluation.

## Delivery Identity and Retry

- Market: `ai-assisted-pilot-v1:<packet_id>:market`
- Stock: `ai-assisted-pilot-v1:<packet_id>:stock:<ticker>`
- The existing `NotificationDelivery` row is reused, so no schema change is required.
- The deterministic payload remains embedded as an internal fallback snapshot and in the exact archive.
- Switching from deterministic HOLD to AI-assisted content resets attempt and chunk progress.
- Once AI-assisted delivery is pending or partially sent, retries continue the same rendered AI content.
- A deterministic full report is never injected after AI delivery has begun.
- Repeated monitor/digest queue calls cannot overwrite a pilot-owned pending digest.

## Status Source

The official Telegram header remains deterministic. An AI disagreement is available only as prose;
it cannot create a second official thesis status. Deterministic warnings, invalidation state, earnings
state, price, supply, valuation, and data cautions remain in the final message.

## Archive

Each packet uses `data/ai_review/pilot/history/YYYY/MM/<packet_id>/` and preserves:

- immutable packet
- exact deterministic messages
- validated AI review
- deterministic/AI comparison
- validator result
- exact AI-assisted or fallback messages
- delivery result and mode

The pilot state counts unique successful assessment dates, not task attempts or packet reruns. A
fallback day is operationally successful but does not increment the AI-assisted success counter.
Each market returns to deterministic delivery after five successful dates; Production Assist is not
enabled.

## 2026-08-13 KR Exception

The approved one-day duplicate exception reused the already validated packet
`2026-08-13-kr-run-15-e395aed1df4d`; no AI re-analysis occurred.

- Existing deterministic set: already sent before pilot activation.
- AI-assisted dispatch: 2026-08-13 17:15 KST.
- Market messages: 1/1 sent.
- Stock messages: 7/7 sent.
- Pending: 0.
- Pilot counter: KR Day 1/5.
- Internal metadata leakage scan: none.

All later sessions use the single-delivery rule; the duplicate exception is not encoded as a general
date bypass and can only be invoked by the explicit one-off CLI flag.

## Tests

- Starting baseline: `502 passed`, one third-party deprecation warning.
- Final local suite: `511 passed`, one unchanged third-party deprecation warning.
- Ruff: passed.
- `git diff --check`: passed.
- Knowledge v3 checksum: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`.
- Public Action schema: `0.4.5`, operationId `20/20`.

Coverage includes AI success single delivery, deterministic fallback, fallback-before-late-AI
fencing, AI delivery retry without representation mixing, explicit one-off duplicate authorization,
pilot stop after five successful market dates, unrelated-notification scope, monitor retry payload
preservation, KR close HOLD, and US morning-gate HOLD.

## Existing Regression

The full suite retains deterministic baseline/delta evaluation, thesis-version and fingerprint
isolation, warning lifecycle, canonical facts, numeric provenance, structured industry routing,
Knowledge v3, claim lease/flock/fencing, morning KRX gate, night futures freshness, historical and
forward valuation safety, provisional earnings, treasury materiality, supply, FX, ADR, macro,
deferred FIFO, and Telegram chunk resume.

## Remaining Gap

Production Assist remains disabled. The pilot still requires four more successful KR dates and five
successful US dates, followed by human review; no automatic promotion occurs.
