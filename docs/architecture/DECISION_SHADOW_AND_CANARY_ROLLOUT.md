# Decision Shadow and Canary Rollout

```text
SHADOW -> TEST_SINK_READY -> operator review -> optional BOUNDED_CANARY
```

Current-date decisions and ten immutable historical checkpoints per stock run in archive-only mode. Historical replay does not receive future outcomes. Full historical D/W/M features and forward-return diagnostics remain `PARTIAL_SAFE` until raw point-in-time bars are archived.

The dedicated test sink must differ from production, preserve exact payload hashes, and create zero production intents. Passing this phase does not enable production canary automatically.
