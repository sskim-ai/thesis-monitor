# 2026-09-04 KR V2 Premature Interrupt Root-Cause Lock

## Locked finding

`SOURCE_FORENSIC_ROOT_CAUSE = OUTER_ORCHESTRATION_PREMATURE_CHILD_INTERRUPT`

The natural KR primary started an explicit V2 child with a command-owned
`1800` second timeout. The outer interactive automation sent Ctrl-C after about
`168.3` seconds while the persisted stage was still model-active and before a
candidate existed. The primary ended with a traceback-only transport result and
without a V2 terminal receipt. A later backup completed the same explicit path
and was deduplicated by the already-terminal delivery state.

This evidence excludes TLS, lease loss, validator failure, and renderer failure
as the first material cause of the incident.

## Repair boundary

- Base: `906b092749511dc42d5799ed335165819efee2ea`
- Work-instruction commit: `5f6043dba8d7e22654e0f3cd74b4d49f52ba9393`
- Runtime implementation: `42374284e1ec16b41823f993ab93c40364c9c95d`
- Timeout-scope correction: `35028fe9a6fd48b1111e84addca161401cbc5fe4`
- CI-isolation test correction: `057208060f5da088ca3c22561edeb13bfc96789e`

No investment judgment, validator threshold, renderer semantic policy, or
ticker-specific exception changed.
