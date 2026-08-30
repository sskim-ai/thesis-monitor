# V2 Production Exact Preflight Provenance

The authoritative r4 preflight ran after runtime implementation commit
`6c429fc2f8afc4316b319494ca098c77594d0d2d` was created. The later premerge commit
`ef1bee3464719d63b12b9fad1c91fc1f5e2ce596` changes only `docs/reports/`.

Current HEAD code regenerated every saved base and bounded-repair prompt byte-for-byte:

- prompt files checked: `13`
- prompt SHA matches: `13/13`
- KR accepted artifact revalidation: exact, `7/7 READY`
- US accepted artifact revalidation: exact, `13/13 READY`
- non-report file diff from implementation SHA to premerge SHA: `0`
- worktree during verification: clean

Prompt SHA-256 values:

| Market | Prompt | SHA-256 |
|---|---|---|
| KR | batch-01 | `c27dd5f95263002327c051b34abc2b3f175c26fb963a70bc182791cc988d3679` |
| KR | batch-02 | `d2a6ad9c27a76c29d0a1cdb5c1492e53a6723c32647975dda30ea5c007739ed0` |
| KR | 005930 repair | `e370bf1ed021ced937250af5e0d0d122b4a390cced8cd9d4efaf39016846133d` |
| KR | batch-03 | `a41f91a1cfeb76a4af18e2370c4c69f9f271f19866db842f6bc5a6827b6f7597` |
| US | batch-01 | `23d7ce7c0a9c9eae1cba2657a9e946168b4ad2a24490e8fc688676eb2fee1ebc` |
| US | batch-02 | `b5332731f677432caf477e55afa5951597dbf995c3ae042d03a94e3c10c2ae25` |
| US | MU repair | `4a80edb9e5816f79f6286f1462594423628b2fb77a926d3f5a19db71145a3874` |
| US | batch-03 | `c62be586cf2d8d034a047e06c090125106ae923a69602b5894a51cfa9236e51a` |
| US | SKHY repair | `2c45404adc0407840f5ff012c23ad3fa99202bcf7eff64cb14509e70e2248da3` |
| US | SNDK repair | `d215549cfa3ab691c019d01ae454d516afab9d85f953156334ac0a593976a4b7` |
| US | batch-04 | `9dc8dad6cd235e964f0c084d9beb940180404f6f13bf90a80803c37e0aad1d8a` |
| US | batch-05 | `94803937d13109a4557ed71b71c0cc757c1e3dce1178f202e5d1756f069dd020` |
| US | WULF repair | `ed66d802a0f2d5f1020fcab8fe7217a99a4a3f3a6d1b05bc7bed8d824f4e3b32` |

Therefore the preflight did not depend on an uncommitted or later runtime implementation.
