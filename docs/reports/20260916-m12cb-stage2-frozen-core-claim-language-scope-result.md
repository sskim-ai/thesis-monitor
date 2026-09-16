# M12CB Stage-2 Frozen-Core Claim-Language Scope Result

## Decision

M12CB closed the intended validator ownership-scope defect. The standalone validator remains
strict, while the trusted Stage-2 path applies exact-number and general claim-language checks only
to Stage-2-owned claims after frozen Fundamental Core identity passes.

Both required proofs pass:

- the immutable M12CA SNDK/TSLA/TSM output replays `3/3` offline;
- SNDK, TSLA, and TSM pass again in the wholly new generation with four frozen-core numeric claims,
  zero Stage-2-owned numeric claims, and zero ownership or semantic errors.

The full22 proof is not clean. A new, independent typed-date ownership violation in `010120`
stopped the immutable generation at call 15. The failure is genuine and fail-closed, so no repair,
retry, or continuation was performed.

## Repository

- Work-instruction commit: `3830959`
- Deterministic implementation: `dcaac603f11edbde150a5d34ee20201fece5e7dc`
- Branch: `codex/20260916-m12cb-stage2-frozen-core-claim-language-scope`
- Reuse classification: `EXISTING_STAGE2_OWNERSHIP_SCOPE_HELPER_INCOMPLETE_APPLICATION`
- Main merge, deploy, remote push: `0 / 0 / 0`

The implementation reuses `stage2_owned_candidate_claims()` as the sole Stage-2 claim inventory.
It adds no ticker exception, numeric allowlist, threshold relaxation, parallel ownership taxonomy,
prompt semantic change, schema semantic change, or canonical semantic-policy change.

## Deterministic Gate

- Focused suite: `115 passed`
- Wider regression reference: `208 passed, 4 skipped`
- Full suite: `4055 passed, 63 skipped, 2 warnings`
- Ruff: PASS
- `git diff --check`: PASS
- Standalone exact-number strictness: PASS
- Trusted frozen-core exact-number fixture: PASS
- Stage-2-owned exact-number rejection: PASS
- Mutated frozen-core rejection: PASS
- Unsupported Stage-2 metric and unknown-ref rejection: PASS
- M12CA batch-4 replay: `3/3 PASS`
- M12CA GOOGL replay: PASS

The M12CA result bundle was reverified at SHA-256
`8e227d7fb643999b6b9b50124c0c51b066ac871e414a1936c8fec32d5419bc99` with 215 payloads,
216 ZIP entries, and zero missing, hash, size, or secret-scan failures.

## New Generation

Generation:

```text
20260916-uskr22-m12cb-20260916T041207Z-dcaac603f11e
```

The model was `gpt-5.6-sol` at `xhigh`. Frozen packet SHAs remained unchanged. Planned, started,
completed, and usable calls were `16 / 15 / 15 / 14`. Retry, fallback, judge, repair, selective
rerun, candidate patching, and cross-generation stitching were all zero.

Proof coverage before the hard stop:

- Fundamental Core: `22/22` valid
- Stage-2 output schema: `20` valid outputs
- Formally accepted Stage-2 semantics: `17`
- Diagnostic Stage-2 semantics: `19/20`
- Final composition: US `14/14`; global full22 not reached
- Exact-ref and fabricated-ref failures: `0 / 0`
- Frozen-core ownership errors: `0`
- Maturity atomic-identity errors: `0`
- Typed-date ownership violations: `1`

KR Stage-2 batch 2 is rejected as a unit. Although `005930` and `012450` pass individual offline
diagnostics, those diagnostics are not accepted or stitched into the proof. KR Stage-2 batch 3
(`047810`, `086280`) was not run.

## Target Scope Proof

SNDK, TSLA, and TSM each pass the new generation's trusted Stage-2 validator. Their copied
Fundamental Core numeric prose no longer triggers `freeform_exact_numeric_claim`, while Stage-2-
owned exact numeric prose remains a hard failure in contrastive tests.

GOOGL also remains stable:

```text
overall BUY / maturity PARTIAL / pre_confirmation_buy=true
new buyer WAIT / holder HOLDABLE / timing UNFAVORABLE
```

This confirms that M12CB did not reopen or couple the pre-confirmation, holder, new-buyer, or timing
contracts.

## Terminal Failure

The failed `010120` maturity row cited only:

```text
decision-evidence:e3e0e73c7b80428e5459
```

That evidence owns `2026-08-12`, but the model emitted `2026-09-15`. The latter is a valid date in
the batch-wide schema enum but is not owned by any evidence ref cited in that same row. The prompt
already states the same-row ownership rule, and the deterministic validator correctly emitted:

```text
maturity_evidence_date_not_owned:수주와 수익성 지속에 대한 높아진 기대는 확인된 부담이다.
```

Classification:

```text
MODEL_OUTPUT_MATURITY_DATE_OWNERSHIP_VIOLATION
```

This is not a validator false positive and not an M12CB scope regression. The batch-global schema
cannot by itself express the row-dependent evidence/date relation; the existing deterministic gate
therefore remains mandatory.

## Safety And Gate

Production DB, assessment, warning, notification, Telegram, scheduler, monitoring, main, deploy,
and remote-push mutations are all zero. Production Assist and production decision gates were not
changed. Kiwoom local adapter and FRED Treasury regressions remain PASS; the live Kiwoom gateway
remains unavailable.

```text
STAGE2_VALIDATION_SCOPE_CONVERGENCE = PASS
TRACK_A_RESULT = FULL22_REPROOF_NEW_HARD_FAILURE
MESSAGE_MODEL_CONTRACT_READINESS = NO
MARKET_CONTEXT_READINESS = LOCAL_PASS_LIVE_KIWOOM_UNAVAILABLE
DEPLOYMENT_READINESS = NO
```

Open P0 is zero because the shadow proof failed closed. Open P1 is one: row-local maturity `as_of`
ownership must be made more reliably model-consumable without weakening the same-row deterministic
validator.

Next scope:

```text
BOUNDED_STAGE2_MATURITY_AS_OF_OWNERSHIP_CONTRACT_REPAIR_AND_NEW_FULL22_REPROOF
```
