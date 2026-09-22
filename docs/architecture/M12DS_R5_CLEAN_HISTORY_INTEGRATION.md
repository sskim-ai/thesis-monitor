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
