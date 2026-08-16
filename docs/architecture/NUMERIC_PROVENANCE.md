# Deterministic Numeric Provenance

## Problem

The former schema-4 authoring flow required Codex to type the same investment number twice: once in
user prose and again in `numeric_claims`. More quantitative reviews therefore created more omission,
field, semantic, unit, rounding, and text-location failure opportunities. The 2026-08-15 US review
exposed seven `numbers_without_provenance` errors after one correction.

## Decision

Policy `daily-review-v3.9` keeps the validated external output at schema 4 and adds a draft-only
`numeric-fact-ref-v1` binding envelope:

```text
canonical packet fact and numeric registry
  -> Codex selects fact_id, field_path, text_ref, and placeholder
  -> backend resolves value, unit, semantic, source-aware label, and formatter
  -> backend renders prose and creates numeric_claims
  -> schema, fact, semantic, location, and numeric validator
  -> renderer
```

Example draft:

```json
{
  "valuation_analysis": {
    "text": "{{numeric:current_per}}와 {{numeric:current_pbr}}를 이익의 질과 함께 봅니다.",
    "fact_ids": ["valuation:current"]
  },
  "numeric_claims": [],
  "numeric_fact_refs": [
    {
      "ref_id": "current_per",
      "fact_id": "valuation:current",
      "field_path": "fields.trailing_pe",
      "text_ref": "valuation_analysis.text"
    },
    {
      "ref_id": "current_pbr",
      "fact_id": "valuation:current",
      "field_path": "fields.price_to_book",
      "text_ref": "valuation_analysis.text"
    }
  ]
}
```

The backend replaces each placeholder exactly once, generates the final claims from the same source,
removes `numeric_fact_refs`, and validates the resulting schema-4 document. A zone endpoint may use
the deterministic role `lower` or `upper`.

## Why

One canonical source now produces the prose token and its claim, so transcription, currency,
semantic, label, and rounding cannot drift independently. Codex retains the analytical choice of
which verified fact matters and where it supports the argument, while deterministic code retains
numeric ownership and auditability.

## Rejected Alternatives

- Relax occurrence coverage or accept a claim because its digits appear nearby: permits
  same-number/different-meaning and cross-field leakage.
- Ask Codex to type corrected raw values and manual claims again: preserves the original duplicated
  authoring failure mode.
- Let the binder infer a closest fact from a prose number: can silently choose the wrong semantic,
  security basis, or currency.
- Convert issuer financials into ADR price currency inside provenance: mixes reporting, security,
  and valuation bases.

## Safety Constraints

- The final schema remains 4 and the existing validator always runs after binding.
- Only registered, prose-allowed, scope-compatible packet fields can bind.
- Each placeholder appears exactly once in its declared prose location and each fact is explicitly
  included in `facts_used`.
- Missing or malformed references and unresolved placeholders fail closed.
- Production Assist remains disabled; validation rejection cannot disable deterministic fallback.

## Ownership

- Codex owns fact selection, prose position, and investment interpretation.
- The packet numeric registry owns canonical raw value, unit, semantic, scope, and allowed prose.
- The binder owns source-aware label selection, display formatting, claim creation, and stable audit
  identity.
- The validator remains fail closed and independently rechecks every generated or legacy claim.

Codex never performs arithmetic, transcribes a raw value into prose, chooses a rounding rule, or
relabels a modeled estimate as consensus.

## Canonical Formatting

The binder has one formatter per registered semantic and unit. It covers USD/KRW/TWD price and
financial amounts, percentages, basis points, multiples, signed shares, points, oil price, chart
zones, and risk/reward. Large USD and TWD financial amounts use deterministic `M/B/T` compaction.
KRW financial amounts reuse the repository's canonical 억원/조원 formatter. Audit values remain raw.

Forward labels are source-aware. `modeled_forward` renders as an internal estimate; only a verified
consensus source may render as market or analyst expectation.

Instrument-sensitive market semantics also require a verified series identity. SPY, QQQ, and IWM
map to separate index labels; real-yield level and change have separate labels; night futures retain
their exact product. Unknown identity has no first-approved-label fallback.

Chart-zone endpoints carry a mandatory role. `zone_low` binds only as `lower` and renders with a
lower-bound label; `zone_high` binds only as `upper` and renders with an upper-bound label. Missing,
duplicated, or reversed roles reject. A single pivot remains a value and cannot impersonate a zone.

The full numeric phrase includes its canonical label and display. Korean particles are typed on the
draft reference as one of `은/는`, `이/가`, `을/를`, or `와/과`; the binder resolves the actual
particle from the canonical formatted unit. A raw particle immediately after a placeholder is
rejected. The final validator rechecks the resulting numeric span and particle, and the renderer does
not repair the sentence after binding.

Financial amount, growth, and margin semantics generated by the current packet contract require a
verified period label such as a quarter, cumulative half-year, cumulative third quarter, or annual
period. Missing period identity leaves the registry row audit-visible but prose-disallowed.

`financial-amount-period-v1` makes that label field-specific. Filing type, statement period, and
amount period are separate. Each eligible amount preserves its exact source row, account, filing,
statement basis, amount start/end, period type, and comparison period. A report ending June 30 does
not make every amount H1 cumulative; Q2 and H1 rows from one filing retain different semantics.
Ambiguous row matches or comparison periods fail closed.

RR claims also carry a mandatory basis. `current_price_risk_reward_ratio` renders as current-price
RR, while `support_entry_risk_reward_ratio` renders as a conditional dynamic-support-entry scenario.
Their labels and prose scopes are not interchangeable.

Valuation prose carries draft-only `typed-valuation-interpretation-v1` references. Historical,
peer, expectation, and trailing/forward claims identify a homogeneous Fact plus the exact visible
numeric comparison. Absolute multiples may be displayed neutrally, but an aggregate valuation Fact
cannot authorize a directional interpretation.

`valuation-coherence-v1` keeps book-value lineage homogeneous. A positive price and positive PBR
cannot coexist as an eligible multiple with non-positive BVPS on the same verified period, currency,
share, and security basis. Period or basis conflicts withhold PBR and dependent historical-PB
interpretation without suppressing independent price or audit-safe book facts.

## Failure Policy

- Missing fact, field, semantic, unit, formatter, scope, or exact placeholder: reject.
- Unregistered or prose-disallowed numeric field: reject.
- Raw prose number without a valid occurrence-specific claim: reject.
- Unsafe number may be removed by the analyst's one permitted correction; it is never replaced with
  a guessed number.
- Machine-generated correction context records the exact text location, rendered phrase, matching
  canonical candidates, approved display, and allowed actions.

The punctuation-token fix excludes a trailing sentence comma from the numeric occurrence span. This
does not relax coverage: the digits still require exact claim coverage.

## Currency And Security Basis

Earnings amounts use `financial_currency`; price and per-depositary-share valuation use their
verified price/security basis. In particular, a TSM ADR price in USD does not make preliminary issuer
revenue or operating income USD. TWD is a registered financial unit. ADR/ADS ratio and denominator
rules remain in the valuation and security-basis layer and are never repaired inside provenance.

Missing, empty, or whitespace-only `financial_currency` is normalized to `unknown`, never to the
security price currency. The raw monetary fact may remain in the packet for audit, but its registry
entry is registered with `prose_allowed=false`, a null canonical display, and no approved display
variants. A non-empty formatter-unsupported currency code keeps its original identity and follows the
same prose-denied path. The binder rejects references to either case. Revenue and operating-income
growth rates and operating margin remain available because they do not require a monetary currency.

## Validation And Telemetry

Each successful finalization archives:

- user-visible numeric token count;
- auto-bound claim count;
- remaining legacy manual claim count;
- rejected and formatting-failure counts;
- stable logical binding identifiers and exact fact/field/text references.

A rejected draft receives a validation sidecar with errors, binding telemetry, correction context,
and explicit confirmation that deterministic fallback eligibility is preserved.

## Delivery Interaction

Validation failure and network failure are separate lifecycles:

```text
AI final reject -> rejected artifact -> held deterministic fallback remains eligible
deadline -> deterministic fallback send

validated final -> persisted AI payload -> Telegram failure -> same payload and chunk cursor retry
```

Fallback network failure also retries the same deterministic payload with a bounded counter. Neither
path recollects data, regenerates a packet, reruns analysis, or increments the AI Pilot count unless a
validated AI set is fully delivered and archived.
