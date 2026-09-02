# US/KR Production-Equivalent Regression

## Cross-Market Result

- US V2 production-equivalent: PASS (`14/14`)
- KR V2 production-equivalent: PASS (`8/8`)
- Dedicated test-sink duplicate: `0`
- Production-recipient send during this repair: `0`
- Production delivery intent during this repair: `0`
- Scheduler timing diff: `0`
- Scheduler ownership diff: `0`

The task performs no new test-sink send. It reuses the immutable prior production-equivalent proof
and verifies that the night-reference change does not alter accepted decisions, stock renderers,
delivery ownership, or schedules.
