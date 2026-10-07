# REV59H Harness Convergence

Base: `344425023927e8ac7e047a28ecbce868c2bfbcb5`.

## Anonymous IPC

`qualified_official_launch_context._anonymous_pipe_authority` retains Darwin's
kernel pipe-type and unlink-count checks. Linux uses a FIFO fstat identity,
exact `pipe:[inode]` procfs link, matching procfs stat, and a second fstat.
Linux link count is not an anonymous-pipe predicate. Existing descriptor pinning
and original/pinned descriptor revalidation remain unchanged.

Only a verified anonymous-pipe write-open receives the IPC exemption. Named and
deleted FIFOs, sockets, stale/reused/mismatched descriptors and unresolved paths
remain denied. Regular files and directories never gain IPC authority; they
retain the existing filesystem ownership policy. Truncate/chmod/chown do not
inherit the pipe write-open exemption. This is a parent audit guard, not a claim
of native-child OS isolation or absence of official CLI internal maintenance.

## Optional Night Context

`r2b_r5_market_adapter.project_optional_night` consumes the already sealed and
replayed KRX acquisition. It does not acquire data or change source authority,
the XKRX calendar, previous-business-date mapping, or native numeric eligibility.
The observation clock lies inside the sealed generation window; it need not equal
the request start. It is never replaced with the replay wall clock. The helper
remains inside the existing registered Market adapter code owner.
Request identities, response hashes, date coverage, receipt times, and the native
temporal/finality contract must agree before optional denial is resolved.

Producer observations are preserved and counted separately from eligible current
consumer owners. Each observation is evaluated separately by the existing native
consumer so a dictionary cannot silently discard contradictory current owners.

| Eligible current owners | Result |
|---|---|
| 1 | `AVAILABLE_FINAL` |
| 0, before the native finality boundary | `UNAVAILABLE_BEFORE_FINALITY` |
| 0, after the boundary | `UNAVAILABLE_NO_CURRENT_FINAL_ROW` |
| More than 1 | `INVALID_CONTRADICTORY_OWNERSHIP`, fail closed |

An unplanned/unrequested current slot is still `PLAN_GAP`. A complete optional
denial has `value=null`, explicit coverage and caution, and contributes no night
numeric facts or directional claims. Crossing 06:00 alone does not establish
publication. Stale rows remain preserved source evidence, not current substitutes.
Selected numeric facts retain their actual producer occurrence index.

## Monitoring Ownership

The strict-blind controller remains a seal/dispatch/comparison wrapper.
`strict_blind_monitoring.NativeSession` continues to call the existing native
Market, Core, Pass A, production Pass B/Overall/Holder and B2 builders/validators.
No financial economics, blind prompt/schema/validator, valuation/evaluability,
timing/fundamental separation or provider roles are changed.

Pre-live gates include real Darwin/Linux IPC tests, the five-case guarded native
composition proof, local full tests, Ruff, diff, secrets and architecture drift.
Hosted full CI is deferred by explicit task policy, not claimed as passing.
Even successful fresh blind/AI seals permit only a separate Architecture
Acceptance Review; main integration and production promotion remain unauthorized.
