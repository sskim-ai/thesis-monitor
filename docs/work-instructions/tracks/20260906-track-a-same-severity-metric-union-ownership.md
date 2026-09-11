# Track A — Same-Severity Selected-Evidence Metric Union

Repair IBM's false reject generically.

Allow metric ownership to be the UNION of claim-selected evidence only when:
- same subject
- same generation
- same claim scope
- same semantic severity
- same checkpoint kind
- same time scope

Never use packet-wide evidence.
Never union across strengthening/invalidation severity.

GOOGL-style unowned strengthening must remain fail-closed.

