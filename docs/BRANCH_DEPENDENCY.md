# Branch Dependency Manifest

As of: `2026-08-18`

This manifest separates validated experimental ancestry from the operating baseline. A commit being
present in an experimental branch does not make it operating, deployed, or approved for promotion.

## Current Graph

```text
e925ee0  origin/main and operating main
  |
  +-- 0bf8921  Phase 8.2A KRX implementation
      52d37dd  Phase 8.2A validation docs
      f90f686  Phase 8.2A.1 implementation
      b4c70c8  Phase 8.2A.1 validation docs
      cd28401  Phase 8.2A.2 implementation
      b94f709  Phase 8.2A.2 validation docs
        |
        +-- 82b95cd  Master Workflow v3 docs
            37a7854  Phase 8.3 implementation, tests, and evidence
            ffafccc  Phase 8.3 final validation docs
              |
              +-- codex/phase-8-3-1-broad-peer-provider-research
```

`origin/main...ffafccc` is `0 behind / 9 ahead`. The merge base is
`e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d`. Six commits are KRX ancestry and three are Phase 8.3
commits. Phase 8.3 therefore has a real KRX dependency in Git history even though the peer contract
does not declare KRX as a data provider.

## Branches

| Branch | Base | Unique commits from base | Depends on | Operating eligible |
|---|---|---:|---|---|
| `main` / `origin/main` | operating history | 0 | none | yes, current baseline only |
| `codex/phase-8-2a-krx-market-breadth` | `origin/main` | 6 | operating main | no |
| `codex/phase-8-3-peer-sector-valuation` | KRX final `b94f709` | 3 | KRX experimental ancestry | no |
| `codex/phase-8-3-1-broad-peer-provider-research` | Phase 8.3 final `ffafccc` | this research phase | KRX plus Phase 8.3 ancestry | no |

Existing branches are retained. This phase performs no force push, history rewrite, tag rewrite, or
remote branch deletion.

## Commit Classification

| Commit group | Commits | Classification |
|---|---|---|
| KRX provider and contracts | `0bf8921`, `f90f686`, `cd28401` | KRX-only implementation/tests |
| KRX validation | `52d37dd`, `b4c70c8`, `b94f709` | KRX-only workflow/evidence docs |
| Phase 8.3 workflow | `82b95cd` | workflow/docs; contains KRX lane state |
| Phase 8.3 peer contract | `37a7854` | peer implementation, tests, architecture, and generated evidence |
| Phase 8.3 finalization | `ffafccc` | peer validation and persistent docs; contains KRX lane state |

## Promotion Paths

### Path A: KRX First

After a separate KRX role and promotion approval, promote the validated KRX chain first. A later
Phase 8.3 integration can then retain its natural ancestry, subject to a fresh rebase/merge review and
exact-SHA validation.

```text
main -> approved KRX chain -> reviewed Phase 8.3 chain
```

### Path B: Peer First

If Phase 8.3 is approved before KRX, create a new branch from the then-current `origin/main`. Port the
peer implementation and tests without the six KRX commits. `37a7854` is the implementation source;
the two Phase 8.3 documentation commits must be reconciled rather than blindly copied because they
also describe the KRX lane. Run the complete test and evidence suite on the reconstructed tree before
any promotion.

```text
latest main -> clean Phase 8.3 integration branch
              KRX commits excluded
```

No clean promotion branch is created in Phase 8.3.1 because promotion is not approved and provider
selection is still open. This is a read-only reconstruction plan, not proof that a future selective
cherry-pick is conflict-free.

## Rule

New experimental phases must either start from current operating main or name their experimental
dependency explicitly. A clean branch name alone does not prove a clean ancestry. Before promotion,
record merge base, ahead/behind counts, unique commits, and the feature groups entering main.
