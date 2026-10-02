# REV31-C1 User State Ownership Clarification

The user's direct response in this task supersedes the broader interpretation
of "official state writes = 0" in the attached instruction:

> Direct DB modification and permission changes remain prohibited. Normal
> internal session, state, log and cache management by the official signed-in
> CLI is authorized. Those internal CLI records are not Thesis Monitor
> production side effects. Thesis Monitor production DB/WAL, scheduler,
> notification state, source corpus, and frozen requests/prompts/schemas/receipts
> must not be modified.

This is not permission to manually edit, copy, chmod, chown, or rewrite the
official state store. A zero direct-write counter does not claim that native
CLI housekeeping was measured as zero. Preserve separate ownership/counters.

The source, model, effort, request identity, call budget, timeout and retry
policy are unchanged. The only preparation-to-execution environment difference
authorized by C1 remains CODEX_SANDBOX after independent target qualification.
