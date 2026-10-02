# REV47 Ten-Minute Execution Clarification

User authorization on 2026-10-02:

> 아냐 그냥 10분으로 해서 진행해. 20분이었던거 바꿀거야

For the current REV47 US14 and conditional KR8 shadow execution, replace the
legacy twenty-minute transport requirement with a frozen ten-minute (600 second)
limit per attempt. Preserve the instruction's maximum two retries of an unchanged
failed logical request, with no rerun of successful requests. US14 permits 16
logical requests (48 attempts maximum); KR8 permits 10 (30 attempts maximum).

Bind the same policy in execution freeze, host qualification, request identity,
and the actual subprocess timeout. Test that path offline before model dispatch.
Legacy callers retain their existing policy unless they explicitly opt in.

Preserve all prior source seals and pre-dispatch failure receipts. The rejected
600/1200 mismatch did not launch the CLI and is not an external model call.
Use a new model-execution namespace, with unchanged frozen source lineage.
No provider recollection is authorized by this timeout amendment.

All REV47 conditional gates remain in force: US success before KR acquisition,
both markets successful before main integration. This amendment does not
authorize deployment, Telegram, scheduler, production database, or broker writes.
