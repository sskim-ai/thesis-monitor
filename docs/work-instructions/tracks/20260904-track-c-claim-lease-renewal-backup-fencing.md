# Track C — Claim Lease Renewal + Backup Fencing

Natural primary outlived its 10-minute static lease and lost ownership to the 08:30 backup.

Implement active lease renewal/heartbeat with fencing tokens.

Heartbeat must continue during blocking model subprocesses.

Fresh healthy primary:
backup SAFE_NOOP / defer.

Dead/stale primary:
backup can reclaim with a new fencing token.

Fallback remains exactly-once and late AI must not send after fallback.
