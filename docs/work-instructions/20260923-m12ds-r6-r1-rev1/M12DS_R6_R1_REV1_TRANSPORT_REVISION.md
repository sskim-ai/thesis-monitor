# M12DS-R6-R1-REV1 Transport Policy Revision

This revision changes **only the execution transport policy** from the previous
R6-R1 work instruction.

New user-approved standing policy:

- timeout: **600 seconds / 10 minutes per attempt**
- retries: **up to 2 retries after the first attempt**
- maximum attempts: **3 per logical request**
- every retry must be **byte-identical**
- retry only typed transient transport/process failures
- never retry schema, semantic, source-use, policy, security, or identity failures
- no source refresh or prompt/schema change between attempts
- no fourth attempt
- no offline response substitution

All source-diagnostic, KR price-basis, macro-freshness, night-futures, message-capture,
validation, and no-main-merge requirements from R6-R1 remain unchanged.
