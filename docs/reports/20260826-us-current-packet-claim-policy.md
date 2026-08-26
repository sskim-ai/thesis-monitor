# 2026-08-26 US Current Packet Claim Policy

Implementation SHA: `505a3a2487eb0ba7db8bd64f787eac8e5b17942d`

For US claims, the service now computes the expected completed regular session with the existing `us_market_session(now)` contract and reads packet identity from:

```text
market_context.adapter_context.session_context.latest_completed_regular_session_date
```

`adapter_context.session_date` is a compatibility fallback. A packet with missing or different session identity is not claimable as current.

If no current-session packet is available, the result is:

```text
status = no_pending_packet
reason = wait_current_packet
```

The AI job's existing polling loop continues without creating a claim file. When the current packet appears, only that packet can be claimed. Claim metadata records `target_session` for auditability. KR claim behavior is unchanged.

Regression coverage proves stale-only wait, current appearance, lease reclaim, primary/backup concurrency, stale finalizer fencing, and deterministic fallback ownership. Grace and validator thresholds were not changed.
