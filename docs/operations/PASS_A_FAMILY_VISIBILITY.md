# Pass A Family Visibility

Pass A consumes the intersection of existing allowed source uses, explicit source-family visibility,
and its existing stage contract. `scripts/pass_a_evidence_visibility.py` owns a frozen, hashed
`PassAVisibleEvidenceDecision`; the input builder consumes this decision without changing authority.
Optional audit receipts stay outside the model view, including excluded refs and their reasons.

The existing current-source family policy remains authoritative. An explicit family exclusion wins
over generic CONTEXT and over cosmetic category aliases. Approved financial-quality, business and
configured thesis/macro uses retain their existing rights. Claim parents cannot bypass a family
exclusion. The independent final A preflight, Core/B contracts and technical renderer are unchanged.

## Full-Fresh Storage Policy

REV19 supersedes the fixed 16 GiB pre-collection target. After the whole offline gate passes,
verify each superseded archive's SHA sidecar, CRC and exact manifest, preserve registered minimal
fixtures, then remove only matching expanded copies. Retain archives, unique evidence, active and
operating worktrees, refs, shared Git, DB/WAL, secrets and production/scheduler state.

Old completed worktrees additionally require clean status, no untracked content, retained refs,
verified result archives and no fixture dependencies. Remove them only with `git worktree remove`.

Record measured previous full-fresh peak growth when available, otherwise use 2 GiB:
`required = max(12 GiB, 10 GiB + min(last_full_fresh_peak_growth, 4 GiB))`.
Prefer at least 14 GiB where safely achievable; never collect below the hard 12 GiB floor.
The model-stage guard remains 10 GiB. Record both the adaptive requirement and actual free bytes;
do not meet either threshold by deleting unverified or protected evidence.

After sealing the new result, retain the active expanded generation and mark it
`NEXT_FULL_FRESH_GC_ELIGIBLE_AFTER_REVIEW`. Delivery is ZIP plus SHA to iCloud's existing
`Thesis Monitor` folder only, after secret scanning and destination hash/sync verification.
