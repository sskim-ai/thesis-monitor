# M12CF Symbolic-Only Maturity Provenance Ownership Review

## Result

`M12CF_SYMBOLIC_PROVENANCE_ARCHITECTURE_REVIEW_PASS_BRANCH_A`

M12CF was completed as a local, review-only task. No runtime/model contract was changed, no model
was called, and the terminal M12CE generation was neither resumed nor reused. The selected design
branch is `BRANCH_A_SYMBOLIC_PROVENANCE_IS_VALID_NONDATE_STATE`.

The preferred next implementation candidate is R2: retain the maturity row, permit `as_of = null`,
and add a runtime-owned deterministic provenance status. This requires a controlled contract-version
migration and offline proof in M12CG before any new Full22 generation.

## Source Integrity And Failure Reconstruction

The M12CE result ZIP SHA-256 is
`512c428bbb01c9ae0834cf0d79d01a330095f67553410f854e296bf9d94c07f9`.
Independent manifest verification covered all 112 declared artifacts with zero missing files, hash
mismatches, or size mismatches.

Generation `20260916-uskr22-m12ce-20260916T080425Z-96a562d5cafc` remains terminal at call 8. The
raw MU/RXRX/SKHY Stage-2 output is immutable with SHA-256
`6c8e80898904b44a710c00fdb3d918bf00a6edf757f1e2cc987d8d2fcb79455f`.
SKHY row 2 cited the valid exact ref `canonical:financial_quality:latest` and no fabricated ref or
model-authored date. Materialization correctly failed with
`stage2_materialization_no_concrete_owned_date:SKHY:2` before calls 9-16.

## Population And Ownership

The current US14/KR8 evidence packets contain two symbolic refs, both for SKHY:

- `canonical:earnings:latest`
- `canonical:financial_quality:latest`

Both use intentional symbolic `latest` producer semantics because the eligible financial period is
unknown. The financial-quality state is itself meaningful: it records source/provider/security-basis
limitations. A concrete assessment or observation timestamp exists elsewhere in the packet, but it
does not own the missing financial source period and cannot replace it.

The producer has zero correct concrete source dates for these two refs. This is not a producer date
ownership defect: the canonical state is deliberately nondate. Consequently the audit records zero
`PRODUCER_DATE_OWNERSHIP_GAP` cases.

M12CD historical replay contained 62 maturity rows: zero symbolic-only rows and two symbolic-plus-
concrete SKHY rows. M12CE contained 42 raw rows: 39 single-concrete, two multi-concrete, and one
symbolic-only row. The new row is the first fresh proof of this boundary.

## Consumer Necessity

`driver_maturity.as_of` is used by the same-row ownership and future-date validator and is included
in candidate serialization. The accepted decision plan and renderer consume aggregate maturity,
not the row-level date. No scheduler, monitoring transition, or investment policy uses the scalar
date semantically.

The present mandatory ISO date is therefore a representation constraint, not evidence that a real
consumer needs a fabricated concrete date. Persistence V2 and identity hashes bind the normalized
payload, so a truthful nullable/tagged representation must be introduced through a versioned
migration rather than post-hoc hash preservation.

## Representation Decision

R2 is selected for the next bounded proof:

- `CONCRETE_ONLY`: `as_of = MAX(same-row concrete owned dates)`.
- `CONCRETE_WITH_SYMBOLIC_REFS`: keep the same concrete projection, but expose that unresolved
  symbolic refs also participate. The scalar is only the latest known concrete provenance date,
  never the complete row evidence cutoff.
- `SYMBOLIC_ONLY_NO_CONCRETE_DATE`: `as_of = null`; exact cited refs remain authoritative.

The model must author neither `as_of` nor provenance status. Assessment date, system/current date,
global maximum, nearest sibling date, and file timestamp remain forbidden fallbacks. Unknown,
cross-ticker, future, and tampered provenance remain hard failures.

R1 is rejected because deleting the SKHY row removes a decisive, confirmed limitation about
unverified financial quality. An ephemeral audit showed the remaining candidate still validates and
keeps HOLD/WAIT/REVIEW/MIXED/UNKNOWN top-level labels, but the decisive maturity risk disappears.
R3 is truthful but unnecessarily broader than R2. R4 and R5 are false-owner substitutions. R6 is
unnecessary because a bounded controlled migration is available.

## Identity Impact

R2 is classified as `HASH_CHANGE_WITH_CONTROLLED_CONTRACT_VERSION_MIGRATION`:

- Fundamental Core SHA: unchanged.
- Stage-2 raw model-output hash: unchanged.
- Normalized candidate hash and candidate decision ID: expected to change.
- Accepted evidence fingerprint, accepted decision ID, accepted-plan hash, persisted candidate hash,
  and acceptance receipt ID may change transitively.
- Renderer wording and investment semantics are expected to remain unchanged.
- Historical artifacts remain immutable and readable under their original contract.

## Validation And Safety

- Focused ownership suite: `198 passed, 1 skipped`.
- Full pytest: `4064 passed, 63 skipped, 2 existing warnings`.
- Treasury regression: `69 passed`.
- Kiwoom local regression: `32 passed`.
- Ruff: PASS.
- `git diff --check`: PASS at closure.

Runtime source changes, model calls, retries, fallback/judge/repair calls, selective reruns,
production sends/DB mutations, scheduler resumes, main merges, deployments, and remote pushes are
all zero. Kiwoom remains READ_ONLY and unconfigured; live read/order/modify/cancel counts are
`0/0/0/0`.

## Next Scope

`M12CG_SYMBOLIC_MATURITY_PROVENANCE_REPRESENTATION_MIGRATION_OFFLINE_PROOF`

M12CG should implement and prove the R2 representation with a controlled contract version,
historical compatibility, hash/identity migration, deterministic status ownership, nullable-date
validation, and semantic-preservation replay. It must stop before any model call. A future Full22
proof must begin as a wholly new generation from call 1 only after separate review and approval.
