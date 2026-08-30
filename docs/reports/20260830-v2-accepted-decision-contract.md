# V2 Accepted Decision Contract

`candidate_decision -> material disagreement -> final adjudication -> accepted_decision`.
No disagreement uses source `CANDIDATE`; KEEP_V1 and KEEP_V2 use explicit adjudication sources.
Every stage has a deterministic ID and evidence fingerprint. A missing or invalid required
adjudication returns `NOT_READY` and never falls back to the candidate.

Machine artifacts use explicit `candidate_decision`, `accepted_decision`, and `accepted_source`.
The accepted plan is the only authority for rendering, validation, test delivery, and readiness.
