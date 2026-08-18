# Phase 8.3.1 Workflow Dependency Hardening

Date: `2026-08-18`
Status: `PASS / DEPENDENCY EXPLICIT / NO PROMOTION`

## Graph Audit

| Ref | SHA | Merge base with main | Ahead/behind main | Unique role |
|---|---|---|---|---|
| `origin/main` and operating | `e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d` | self | 0/0 | operating Phase 8.5.x baseline |
| KRX experimental final | `b94f709eb146655a6a2e35377073727aee7cd7ca` | `e925ee0` | 6/0 | Phase 8.2A/A.1/A.2 only |
| Phase 8.3 final | `ffafccc9e71619f2ebc16b0e60b9c2d3d3b75f05` | `e925ee0` | 9/0 | six KRX plus three peer commits |
| Phase 8.3.1 branch at start | `ffafccc9e71619f2ebc16b0e60b9c2d3d3b75f05` | `e925ee0` | 9/0 | provider research branch |

The prior shorthand “Phase 8.3 is experimental” was correct but incomplete: the branch includes all
six KRX experimental commits. This is now explicit in
[the dependency manifest](../BRANCH_DEPENDENCY.md).

## Unique Commit Classification

- KRX-only implementation: `0bf8921`, `f90f686`, `cd28401`.
- KRX-only validation/docs: `52d37dd`, `b4c70c8`, `b94f709`.
- Phase 8.3 workflow/docs: `82b95cd`.
- Phase 8.3 peer implementation/tests/evidence: `37a7854`.
- Phase 8.3 final docs: `ffafccc`.

The Phase 8.3 documentation commits also contain KRX lane statements. They cannot be blindly ported
to a KRX-free integration branch.

## Promotion Paths

| Path | Construction | Boundary |
|---|---|---|
| KRX first | approve/promote KRX chain, then review Phase 8.3 ancestry | natural ancestry may be retained |
| Peer first | new branch from latest main, port peer implementation/tests, reconcile docs | all six KRX commits excluded |

No clean integration branch was created because provider selection and Phase 8.3 promotion are not
approved. A future clean reconstruction must prove conflict-free behavior with full tests; this
phase does not claim that selective cherry-picking has already been validated.

## Workflow State After Hardening

- Phase 8.3 contract: `PASS`.
- Phase 8.3 capability: `STRONG PARTIAL`.
- user-visible peer coverage: `0/20`.
- broad provider: `RESEARCH COMPLETE / SELECTION OPEN`.
- Phase 8.3 operating integration: `NO`.
- KRX operating integration: `NO`.
- Natural AI-assisted delivery: `PARTIAL`.
- Production Assist: `OFF`; AI mode: `shadow`.

## Mutations

The only branch mutation was creation of
`codex/phase-8-3-1-broad-peer-provider-research` from the existing Phase 8.3 final. Existing branches
were retained. Remote deletion, force push, history rewrite, tag rewrite, main merge, and operating
deployment are all `0`.
