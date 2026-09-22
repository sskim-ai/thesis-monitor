# R5 Clean-History Integration Boundary

The 2026-09-22 follow-up authorization supersedes the original R5 requirement to
publish the exact historical commit. The accepted code reference remains
`ac2fa4aa6fe8e34af6b06b66829537eb0818ebe6`; the integration lineage starts directly
from `9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479` and has a new commit identity.

Application code, reusable scripts, and tests are copied byte-for-byte from the
accepted code reference. Historical generated reports, populated model requests,
outputs, receipts, logs, and instruction bundles are not imported into the new
lineage. Original branches and local evidence remain preserved. Generic prompt
builders and synthetic regression fixtures remain part of the reviewed code.

Publication requires code-content equality, a reachable-history artifact audit,
frozen source and Core/A/B validation, exact production-renderer reproduction of
all 24 accepted messages, official night-futures E2E parity, local validation,
and remote CI. Private proof receipts and results remain outside Git. A change
of Git identity is not evidence of a new model generation.

R5 does not authorize deployment, message delivery, recipient changes, scheduler
changes, production persistence, broker actions, or onboarding implementation.
The existing P2 price-as-of, US market coverage, and wording items are unchanged.

This document specifies the integration boundary; completion and exact-SHA
validation are recorded in the separate local R5 closeout report.

## R5-R1 Provenance Migration

`m12ds-r5-r1-clean-history-provenance-v1` preserves legacy pin ancestry and adds
an explicit reviewed clean-root mode. The compact provenance JSON binds the
published root, its tree and parent, original review identities, path owners and
the eight reviewed byte hashes. The guard independently pins the expected
attestation; editing the JSON cannot authorize different protected bytes.

Clean mode verifies root ancestry and root, HEAD and working-tree file bytes. It
never reads private historical commit blobs. A failed clean attestation cannot
fall back to legacy approval. Receipts distinguish verified clean-root ancestry
from historical ancestry and never claim the latter when it is absent.

A checkout must contain the published clean root and its descendants to perform
this audit. Missing history fails closed; a shallow checkout is not an implicit
approval. Direct tests use isolated real Git graphs without private objects so
CI checkout depth does not weaken or skip the proof. A separate full clean clone
of the candidate verifies the actual reviewed root before publication.
