# R5-R2 CI-Portable Provenance

Contract: `m12ds-r5-r2-ci-portable-provenance-tests-v1`.

The test/lint checkout retrieves published history with `fetch-depth: 0`. The
reviewed clean root must actually resolve and be an ancestor; missing history
does not authorize bypassing the unchanged R5-R1 guard. No private refs, deployment
steps, workflow permissions, test commands or lint commands are added.

`M12DS_R5_PORTABLE_HISTORICAL_BASELINES.json` records only reviewed identities and
fingerprints. Its byte hash is independently pinned by the direct test owner.
Tests verify the actual clean-root tree, ancestry and both root file hashes.
Private historical commit identifiers are metadata, never required Git objects.

The runner's 14 historically protected methods retain normalized AST fingerprints.
The `pass_a` validation/materialization tail has a separate fingerprint. The
original exclusions (`invoke` and the first `pass_a` statement), inherited method
identity assertions and schema-ownership assertion remain. Negative controls
mutate every protected method and the tail; unrelated comments and originally
excluded implementation surfaces remain outside this semantic check.

Transport remains exact-byte checked, including a one-byte negative control.
Malformed, wrong-root, wrong-tree, hash, fingerprint, owner and path attestations
fail closed. The reviewed runner hash ends in `7365e`; the intake baseline JSON
omits the final `e`, while its prose and contract JSON match the verified clean
root's complete SHA-256. No baseline source bytes were inferred or changed.

M12W mutation coverage now uses the existing real isolated Git fixture: reviewed
root, attestation, unchanged descendant, and committed mutated descendant. Its
explicit file-level archive mode must accept unchanged content and reject exactly
the protected renderer path after mutation. No aggregate-label substitution or
stubbed guard result is used.

Production code, model/source/render contracts and accepted payloads are unchanged.
Reports and populated evidence remain outside Git.
Candidate freeze requires actual clean-clone focused/full tests, Actions-equivalent
regressions, publication audit and exact zero-model replay before remote CI.

## Approved Workflow-Only Guard Extension

After the R5-R2 local full suite exposed four historical scope failures, the user
explicitly approved a bounded guard extension. The original eight-path clean and
legacy modes are retained. Only `.github/workflows/test.yml` gets a separate
`REVIEWED_CI_HISTORY_DEPTH` receipt. It verifies the reviewed clean-root ancestry,
tree and parent, the original workflow hash, and the exact two-line transformation.

- Before: `b0932124732f0234db8ad76b1e356b044c8c4bc0892645c6f514ef7575515d5d`
- After: `f1502fd11213551c9f552c43ea4eb65df913104e1fd8241fc03a53d0fd03be31`

The working bytes must be exactly the approved after image. HEAD may contain only
the reviewed before image during precommit validation or the approved after image
after commit; an unreviewed HEAD cannot be hidden by restoring working bytes.
Unknown paths, other depth values, permissions, job edits, additional whitespace,
wrong root ancestry/identity/bytes and other mutations remain rejected. No generic
workflow exemption, private history dependency or runtime behavior change is added.
