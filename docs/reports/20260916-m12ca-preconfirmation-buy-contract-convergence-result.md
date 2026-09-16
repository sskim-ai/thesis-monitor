# M12CA Pre-Confirmation BUY Contract Convergence Result

## Decision

M12CA recovered and reused the historical pre-confirmation BUY lifecycle contract. The new
generation proves that the prior GOOGL failure is closed without coupling the overall decision to
entry timing:

```text
overall BUY + PARTIAL maturity + pre_confirmation_buy=true
+ new buyer WAIT + holder HOLDABLE + timing UNFAVORABLE
```

GOOGL passes the existing hard semantic validator with all six explanation claims. Its decision was
not forced or post-processed. The full 22-subject proof is nevertheless incomplete because a new,
independent validator-scope defect stopped the immutable generation at call 9.

## Repository

- Base documentation SHA: `29878d2ecc5ff96add09b25fb7fe0fb2b216b43e`
- Origin main observed: `9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479`
- Work-instruction commit: `b586303`
- Deterministic implementation: `663d69eade2ba601c0248635d5656dec242563dc`
- Branch: `codex/20260916-m12ca-preconfirmation-buy-contract-convergence`
- Main merge, deploy, and remote push: `0 / 0 / 0`

The instruction archive SHA-256 is
`a6f90dbbd3850761f1c346ff5792e75b6c5771ad3ec7704e893788ab7a1c2120`.

## Contract Recovery

Historical provenance identifies `preconfirmation-asymmetry-decision-engine-v2` as the canonical
contract. The implementation lineage is `c0c9139babb06ead11112aea072a67ef364a9b22`; accepted-decision
ownership lineage includes `f55605189ee0179ab4af7030b94d79d706ed32a8`.

The evidence-backed reuse classification is:

```text
HISTORICAL_PRECONFIRMATION_CONTRACT_ALREADY_CANONICAL_BUT_PROMPT_BYPASSED
```

The invariant remains hard and generic:

- BUY with at least one decisive EARLY or PARTIAL driver requires `pre_confirmation_buy=true`.
- A true flag requires FAVORABLE asymmetry and factual safety other than BLOCKED.
- A true flag requires all six explanation claims; a false flag requires a null explanation.
- HOLD, SELL, and confirmed BUY use a false flag.
- New-buyer stance, holder stance, timing, and price confirmation do not set or clear the flag.

The Stage-2 prompt now states this exact invariant. The schema already represented the flag and
shape relation, so no schema semantic change was needed. The existing hard validator was not
weakened. The old M12BZ GOOGL output remains invalid with exactly
`preconfirmation_buy_flag_missing`.

## Deterministic Gate

- Focused: `115 passed`
- Wider: `208 passed, 4 skipped`
- Full: `4050 passed, 63 skipped, 2 warnings`
- Ruff: PASS
- `git diff --check`: PASS
- Positive and negative flag fixtures: PASS
- BUY + WAIT + HOLDABLE independence: PASS
- Price-confirmation independence: PASS
- Historical GOOGL and 003690 fixtures: PASS
- Candidate auto-repair count: `0`

The prior M12BZ bundle reverified at SHA-256
`bd13d6c9d4adb948bcd400dab53bb93d51ffd00b1d6f84545173d8a8720c5864`, with zero manifest,
size, hash, or secret-scan errors.

## New Generation

Generation:

```text
20260916-uskr22-m12ca-20260916T021457Z-663d69eade2b
```

Frozen packet SHAs remained unchanged:

- US: `2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228`
- KR: `819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597`

The model was `gpt-5.6-sol` at `xhigh`. Planned/started/completed/usable calls were
`16/9/9/9`. Retry, fallback, judge, repair, and selective rerun were all zero. The terminal
generation must not be resumed, stitched, or selectively rerun.

All five US Fundamental Core batches are valid: `14/14`, with zero identity, exact-ref, or core
semantic failures. Four Stage-2 batches returned `12/12` schema-valid candidates. Batches 1-3 are
semantically valid `9/9`. Batch 4 failed for SNDK, TSLA, and TSM with the same error:

```text
freeform_exact_numeric_claim
```

## GOOGL Proof

GOOGL now has:

- Overall direction: BUY
- Directional balance: BUY `6.0` / SELL `4.0`
- Overall maturity: PARTIAL
- `pre_confirmation_buy`: true
- Explanation: all six claims present
- New buyer: WAIT
- Holder: HOLDABLE
- Timing: UNFAVORABLE
- Pricing requirement: BASE_CASE_REQUIRED
- Asymmetry: FAVORABLE
- Confirmation cost: MEDIUM
- Pre-confirmation error cost: MEDIUM
- Price confirmation: `not_reached`
- Stage-2 semantic validation: PASS

This is the requested three-axis independence proof. Price confirmation remained an entry check and
did not become fundamental confirmation.

## Terminal Failure

The call-9 failure is not a model claim defect and not a pre-confirmation regression. SNDK, TSLA,
and TSM have zero frozen-core ownership errors, zero maturity errors, and zero exact numeric claims
inside Stage-2-owned fields. Their four numeric sentences belong to the already validated and
fingerprint-locked Fundamental Core.

Root cause:

```text
validate_preconfirmation_stage2_owned_semantics
  -> _validate_preconfirmation_candidate
  -> exact-number/general prose loop still uses candidate_claims(candidate)
```

Only the unsupported-metric input was narrowed to `stage2_owned_candidate_claims(candidate)`.
Exact-number and other general prose checks still traverse the combined candidate, revalidating the
frozen Core. Classification:

```text
FROZEN_CORE_EXACT_NUMERIC_SCOPE_FALSE_POSITIVE
```

The frozen proof guard stopped before any repair call. No hotfix was applied after observing the
generation.

## Market Context

Kiwoom KOSPI200 2026-09-01 through 2026-09-03 local adapter replays pass, with no completed-session
overwrite, time-layer conflation, or fundamental-ownership leakage. The authenticated live gateway
remains unconfigured, so live read/order/modify/cancel calls are zero.

FRED DGS3/5/10/30, DFII10, and T10YIE parser, same-series comparison, basis-point change,
date ownership, rendering, and time-layer regression all pass. No live provider call was made.

## Safety And Gate

Production DB, assessment, warning, notification, Telegram, scheduler, monitoring, main, deploy,
and remote-push mutations are all zero. Production Assist and production decision gates were not
changed.

```text
TRACK_A_RESULT = FULL22_REPROOF_NEW_HARD_FAILURE
GOOGL_PRECONFIRMATION_CONVERGENCE = PASS
MESSAGE_MODEL_CONTRACT_READINESS = NO
MARKET_CONTEXT_READINESS = LOCAL_PASS_LIVE_KIWOOM_UNAVAILABLE
DEPLOYMENT_READINESS = NO
```

Open P0 is zero because the shadow proof failed closed. Open P1 is one: Stage-2 must apply
claim-language checks only to Stage2-owned prose once frozen-core identity and immutability have
passed.

Next scope:

```text
BOUNDED_STAGE2_FROZEN_CORE_NUMERIC_VALIDATION_SCOPE_REPAIR_AND_NEW_FULL22_REPROOF
```

