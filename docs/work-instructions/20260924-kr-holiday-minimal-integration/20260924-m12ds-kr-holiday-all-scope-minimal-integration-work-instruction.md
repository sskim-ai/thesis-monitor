# Thesis Monitor — KR Holiday `--market all` Minimal Integration Work Instruction

**Purpose:** integrate only the proven KR-holiday `--market all` bypass repair into the operating codebase, with no change to the prepared US R5A-R1 live-cutoff path.

## 0. Current SoT

Newest accepted KR holiday proof:

- terminal: `M12DS_KR_HOLIDAY_MESSAGE_SUPPRESSION_PROOF_PASS`
- result ZIP SHA-256:
  `5873dafc178b81d11c9ad87b4ef42338f5171e9b34ceda01b7c447eb28f11efe`
- operating main:
  `2097645892e30d84aba435416f98e7f9545a87fa`
- local repaired final SHA:
  `d6ed77b0c3619257d5559d0351fd62dfa23ade15`

Accepted findings:

1. `--market kr` already performs deterministic KR-holiday safe-noop.
2. `--market all` could bypass the KR holiday guard and let the KR branch continue.
3. The local repair makes `--market all` split correctly:
   - KR holiday branch -> suppress/skip;
   - US branch -> continue normally.
4. Focused/full/Ruff/diff/Knowledge validation passed in the proof result.
5. The repair is not yet present in operating main.

Treat any newer verified result ZIP supplied at execution time as higher-priority SoT.

---

## 1. Scope

Integrate **only** the causal KR holiday suppression repair required for `--market all`.

Do not wholesale-merge the proof branch.

Before changing code, diff:

`2097645892e30d84aba435416f98e7f9545a87fa`
against
`d6ed77b0c3619257d5559d0351fd62dfa23ade15`

Identify exactly which production lines implement the `--market all` KR holiday routing fix.

Expected implementation size is small; the prior proof described it as approximately 11 production lines.

If unrelated changes are present in the proof branch, exclude them.

---

## 2. Required behavior after integration

On an authoritative KRX holiday:

### `--market kr`

Must remain:

`KR holiday -> KR branch safe-noop -> model/message/delivery 0`

### `--market all`

Must become:

`all`
- `KR` -> authoritative KRX holiday gate -> suppressed/no-op
- `US` -> existing US path unchanged and still eligible according to its own calendar/source rules

A KR holiday must **not** suppress an otherwise valid US run.

A KR holiday must **not** be treated as provider failure.

A KR holiday must **not** trigger retry, catch-up, or backfill behavior.

---

## 3. Hard non-regression constraints

Do not change:

- US R5A/R5B source proof code;
- `scripts.m12ds_r6_r5_cutoff_observer`;
- prepared 2026-09-25 R5A-R1 route;
- prepared 2026-09-25 R5A-R1 plan;
- frozen request-array contract;
- US source authority;
- KR canonical universe;
- investment thesis/scoring logic;
- Market/Core/A/B prompt content;
- delivery recipients;
- broker/order behavior;
- schedule cadence;
- Alpha Vantage usage.

Alpha Vantage calls for this task must be:

`0`

The prepared US R5A-R1 worktree must remain byte/commit-identical to its accepted preparation state.

---

## 4. Worktree / branch isolation

Perform this integration in a new worktree/branch based on operating main:

`2097645892e30d84aba435416f98e7f9545a87fa`

Do not edit the existing R5A-R1 boundary-repair/live-cutoff worktree.

Before implementation record:

- operating main SHA;
- new worktree base SHA;
- worktree clean status;
- prepared US R5A-R1 worktree SHA and clean status.

After implementation re-check the prepared US worktree and prove unchanged.

---

## 5. Implementation method

Preferred approach:

1. inspect the exact diff that produced the accepted local proof;
2. isolate the smallest causal production change for `--market all`;
3. re-apply only that change to the new worktree;
4. bring over only the focused tests necessary to permanently lock the behavior;
5. do not copy proof/report-only artifacts into production code.

If an exact clean commit exists containing only this repair and its tests, cherry-pick may be used.

If the commit contains unrelated changes, do not cherry-pick it wholesale; reconstruct the minimal patch.

---

## 6. Required focused tests

At minimum prove:

### Holiday behavior

- known KRX holiday + `--market kr`
  - KR downstream generation = 0
  - KR rendered messages = 0
  - KR delivery intent/send = 0

- known KRX holiday + `--market all`
  - KR branch suppressed
  - US branch still reaches its existing eligible path
  - no KR Market/Core/A/B generation
  - no KR rendered message
  - no KR delivery/send intent

### Open-day regression

- known KRX open day + `--market kr`
  - normal KR eligibility path remains reachable

- known KRX open day + `--market all`
  - KR and US routing remain consistent with pre-repair semantics

### Isolation

- US-only run behavior unchanged
- KR holiday state does not leak into US session state
- holiday skip is not classified as provider error
- no retry/backfill from holiday skip
- no scheduler mutation
- no production DB mutation

No real model call is required.

---

## 7. Required validation

Run:

- focused KR holiday routing tests;
- existing KR holiday/session/source-basis tests;
- US path regression tests;
- full pytest;
- Ruff;
- implementation diff check;
- Investment/Chart Knowledge check;
- secret scan.

Requirements:

- no new unexplained skip/xfail;
- model calls = 0;
- rendered messages = 0;
- send/delivery intent = 0;
- broker actions = 0;
- Alpha Vantage calls = 0;
- scheduler/notification mutation = 0;
- production DB mutation = 0.

Do not report remote CI PASS unless actually pushed and observed.

---

## 8. Promotion rule

This task is an integration proof, not an authorization to deploy automatically.

After tests pass:

1. produce the integration result bundle;
2. record:
   - base SHA;
   - implementation SHA;
   - final local SHA;
   - exact changed production files;
   - exact changed test files;
3. verify operating main itself is still unchanged unless explicit promotion is part of the assigned execution;
4. verify the prepared US R5A-R1 worktree is unchanged.

If promotion to main is explicitly executed within the task, require:

- fast-forward/clean promotion only;
- full validation already PASS;
- no conflict with the 2026-09-25 live-cutoff preparation;
- final main clean;
- no deploy/service restart.

If promotion is not explicitly authorized, stop with the tested local integration ready for promotion.

---

## 9. Required result artifacts

Return ZIP + SHA-256 sidecar containing at minimum:

- `REPORT.md`
- `summary.json`
- source-result identity receipt
- base / implementation / final SHA receipts
- exact minimal patch/diff
- changed-file inventory
- focused test logs
- full pytest log
- Ruff log
- diff/Knowledge logs
- holiday `kr` proof
- holiday `all` proof
- US non-regression proof
- open-KRX-day regression proof
- model/message/delivery counters
- Alpha Vantage call counter = 0
- operating before/after receipt
- prepared US R5A-R1 worktree before/after identity receipt
- secret scan
- bundle manifest.

---

## 10. Acceptance

PASS only if:

1. holiday `--market kr` remains suppressed;
2. holiday `--market all` suppresses KR;
3. holiday `--market all` does **not** suppress eligible US processing;
4. open-day KR behavior remains reachable;
5. US-only behavior is unchanged;
6. no production side effects occur;
7. Alpha Vantage calls = 0;
8. full validation passes;
9. US R5A-R1 live-cutoff worktree/plan/route remains unchanged.

Suggested terminal:

`M12DS_KR_HOLIDAY_ALL_SCOPE_MINIMAL_INTEGRATION_PASS`

Use an existing canonical repository terminal if one already exists.

---

## 11. Next state

After this integration result is accepted:

- KR holiday message-suppression contract can be considered closed at both `kr` and `all` routing scopes, subject to whether the tested local repair has been promoted to operating main.
- The next time-critical priority remains the 2026-09-25 R5A-R1 US actual-cutoff observation.
- Do not let this KR integration task delay or modify that live observation.
