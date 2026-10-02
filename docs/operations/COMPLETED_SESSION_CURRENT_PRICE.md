# Completed-Session Current Price and Storage Gate

REV18 extends only the opt-in fresh source owner. Production dispatch is not
registered or changed. The work instruction was frozen at
`e40233add87258e3a8ee6eaf99eb44d1fb5c49ca` on REV17
`011949824d52e5b4ef84949ce10a4c0c9adbe8c7`.

`CompletedSessionCurrentPriceProjection` owns an exact adjusted daily close.
Its target is the frozen exchange-calendar completed session, not the final
returned row. Receipt, generation, security, exchange, currency, basis, raw
hashes and exact row fingerprint remain bound. Missing, duplicated, conflicting
or invalid target rows are unavailable; no prior-row replacement is permitted.
Unknown row dates fail closed. Later and historical rows retain their original
data and anomaly receipts outside the current-price dependency. No source row
is deleted, repaired, relabeled or made an eligibility override.

The projection feeds the fresh price context, valuation numerator and existing
source-use/materializer/renderer path with the exact session date. Technical
series eligibility is separate and unchanged. A price can be available while
all daily technical facts remain unavailable. There is no new valuation math,
Core direction policy, model prompt, schema, or delivery authority.

## Standing Full-Fresh Storage Policy

Before any new full-fresh generation, plan and record archive-backed cleanup.
Preserve current active worktree/ref, shared Git objects, operating databases,
credentials, scheduler state, all immutable ZIP/SHA files, registered minimal
fixtures and unarchived unique evidence. Preserve active expanded proof until
its own review/closeout, then mark it `NEXT_FULL_FRESH_GC_ELIGIBLE_AFTER_REVIEW`.

Expanded directory deletion requires matching ZIP and sidecar SHA, CRC and
complete internal manifest verification (missing/hash/size/extra all zero),
plus file-by-file correspondence and dependency checks. Reverify immediately
before deletion. Never remove a worktree with a filesystem deletion; clean,
untracked-free, ref-preserved worktrees require `git worktree remove` separately.

Record `storage-gc-plan.json`, `storage-gc-result.json`, exact removed paths and
bytes, skipped reasons and before/after `df -h`. Collection requires 16 GiB free;
models require 10 GiB. Insufficient headroom is a terminal, not permission to
delete unique evidence or lower a safety threshold. Outputs are ZIP plus SHA
in iCloud Drive **Thesis Monitor only**, not its root.
