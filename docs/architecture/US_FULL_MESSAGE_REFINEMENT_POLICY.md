# US Full Message Refinement Policy

Full-message refinement is bounded by deterministic ownership:

1. Build the exact index, market-internal, optional night-futures, optional macro, and next-check
   layout from canonical facts.
2. Validate numeric refs, temporal roles, section order, and message length.
3. Send the production-equivalent candidate only to the dedicated non-production sink.
4. Compare rendered, outbound, and received payload hashes.
5. Refine only a demonstrated formatting or semantic defect; never loosen a validator.

The 2026-08-28 proof required one bounded repair: a legacy stored plan's SOXX/SPY relative fact was
rejected as macro evidence. The final test message passed on its first external test-sink send.
Production recipients, tasks, DB, assessments, and Production Assist are outside this loop.
