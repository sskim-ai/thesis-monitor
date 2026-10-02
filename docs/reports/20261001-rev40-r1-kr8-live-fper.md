# REV40-R1 KR8 Live FY1 Integration Closeout

Terminal: `R2B_R9_REV40_R1_SOURCE_ONLY_SEAL_GAP`.
End-to-end readiness: **NO**. Local shadow scope only.

## Identity

- Instruction-first commit: `526833a4739180fdbb913ebb4f4752a9dd47ce10`.
- Base: `8fcb75412d4763df46e946285bf636778e043a73`.
- Exact tested implementation: `f4ac42985fd1824160926e5c2dde269935479cea`.
- Fresh generation: `rev40-r1-kr8-20261001T082129Z`.
- Main and operating remain `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`.
- No merge, remote push, deployment or restart.

## Observed Results

| Gate | Result |
| --- | --- |
| Focused regression | 496 passed, 1 skipped |
| Full regression | 7,696 passed, 63 skipped, 0 failures/errors |
| Ruff, diff, Investment Knowledge, Chart Knowledge | PASS |
| Fresh KR source requests | 171 attempted logical requests, all PASS |
| KR source packets and equal offline replay | 8/8, PASS |
| KIS authentication / data requests | 1 / 65 |
| KIS typed states and equal offline replay | 8/8, PASS |
| FY1 EPS / current-price FY1 fPER qualified | 7/8 / 7/8 |
| 003690 | Typed unavailable research estimate; not zero |
| Source-only export seal | FAIL before model invocation |
| Market / Core / A / B model calls | 0 / 0 / 0 / 0 |
| Exact stock sender payloads | 0/8, not generated |
| US-only provider / model / message | 0 / 0 / 0 |
| Telegram / production mutation | 0 / 0 |

KIS reads comprised eight estimate requests, eight identity requests, seven
unadjusted completed-session price requests, and 42 exact-security corporate
action requests. No transport retries, fallback or judge calls occurred.

## P1 Export Identity Mismatch

The frozen report-side `model_run.py:source_seal` attempted to read
`whole['seed']['run_id']`. The accepted full-source seed contract serializes
its parent generation as `whole['seed']['parent_run_id']`. A `KeyError` stopped
execution before source-only sealing, valuation visibility checks or models.

The actual parent identity matches both the fresh provider plan and KIS
generation. This was not a provider, credential, disk or financial arithmetic
failure. The report-side export preflight had not been tested against the real
serialized seed layout. The frozen controller and failure record were retained;
no in-run hotfix, identity replacement or selective rerun was performed.

Bounded next repair: bind export identity to the existing typed full-source
contract, add actual serialized-seed coverage, freeze the repaired controller,
and pass source-only sealing plus valuation visibility before model dispatch.
NewBuyer/Holder use and exact message integration remain unproven.

## Storage And Preservation

The user permitted testing without meeting 12 GiB. This KR-only task uses the
instruction's 10 GiB floor; the default all22 12 GiB guard is unchanged.
The final collection had more than 13 GiB available.

51 archive-backed paths were removed, with 4,695,186,506 summed path bytes.
Observed free space changed from 8.125 to 13.383 GiB. The net free-space change
is not equated to deletion sizes because concurrent host allocations differ.
Archive ZIP/SHA pairs, local refs, shared git, registered fixtures, REV11,
REV39 and production/configuration/authentication state were preserved.

## Evidence Delivery

Local report directory:
`/Users/sskim/Documents/Codex/Reports/20261001-r2b-r9-rev40-r1-kr8-live-fper`.

Six deliverables: result, source-only-status and human-review ZIPs with SHA
sidecars. The source-only and human-review artifacts explicitly disclose that
no qualified blind export or model messages were produced. Fresh source
evidence and detailed failure receipts are retained in the result archive.
Upload destination is only iCloud Drive / Thesis Monitor. Per-file server
upload status is recorded separately; local copy alone is not upload proof.
