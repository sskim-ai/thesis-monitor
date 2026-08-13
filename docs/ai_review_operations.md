# Codex Scheduled Daily Review Operations

The daily AI review starts in `shadow` mode. It reads backend-verified local packets and never changes
the official assessment or Telegram message. It does not use `OPENAI_API_KEY`, Responses API, Chat
Completions API, or external web research.

## Schedule

All times are Asia/Seoul.

| Task | Time | Purpose |
| --- | --- | --- |
| US primary | 08:50 | Process the packet finalized after the morning KRX gate. |
| US backup | 09:30 | Reclaim after the primary's 30-minute lease has expired. |
| KR primary | 16:15 | Process the successful Korean close packet. |
| KR backup | 16:55 | Reclaim after the primary's 30-minute lease has expired. |

Every invocation begins with a pending scan. Completed packet and policy combinations are no-ops.
Shadow tasks may catch up an eligible packet from the preceding 24 hours. The scheduling invariant is
`backup_delay > claim_lease + safety_margin`: the current 40-minute delay exceeds the 30-minute lease
by 10 minutes and the configured minimum safety margin is 5 minutes.

Every claim has a UUID and a claim-specific temporary output. Lease expiry permits reclaim but does
not invalidate the worker by itself. Once a backup creates a new claim, the prior worker is fenced and
cannot finalize, even if it later recovers.

## Desktop Requirements

For local-project Scheduled Tasks, verify all four conditions:

1. The Mac mini is powered on and connected to the network.
2. The ChatGPT desktop app is running and signed in to Codex.
3. The scheduled task points to the live local checkout of `sskim-ai/thesis-monitor`.
4. The task is active and has workspace-write access only.

Closing the desktop app is an AI shadow failure, not a deterministic-monitoring failure. Existing
monitoring and Telegram continue independently.

## Manual Checks

```bash
.venv/bin/python -m app.jobs.ai_review health --market us
.venv/bin/python -m app.jobs.ai_review health --market kr
```

A task claims work with:

```bash
.venv/bin/python -m app.jobs.ai_review claim --market us --owner manual-check
```

The claim result contains `claim_id`, packet path, and a claim-specific temporary output path. The
scheduled model reads `knowledge-index.md`, the routed sections of the full Knowledge mirror, and only
canonical packet facts. It writes only the temporary JSON and finalizes it with:

```bash
.venv/bin/python -m app.jobs.ai_review validate --packet-id PACKET_ID --claim-id CLAIM_ID
```

Claim, reclaim, final promotion, and claim cleanup are serialized by a stable per-packet POSIX
`flock` under `data/ai_review/locks`. The lock is held only for short filesystem mutations; Codex
analysis and schema validation run outside it. Lease expiry permits another worker to reclaim the
packet, but an expired worker may still finish while its claim remains current. Once a backup writes
a new claim ID, the older worker cannot promote its claim-specific temporary output or remove the
new claim. This guarantee assumes the configured Mac mini local POSIX filesystem, not a network
filesystem with unknown lock semantics.

Files ending in `.json.tmp` are incomplete and are never considered completed. Every output records
the analysis policy, Knowledge version/checksum, frameworks used, fact references, and numeric claims.

## Security Boundary

Scheduled review may write only under `data/ai_review`. It must not edit `app`, `tests`, `ops`, project
configuration, or the database. External browsing is disabled. Packet facts are allowlisted and user
facts exclude raw parser/provider metadata. Credentials and account identifiers are never packet
fields.

## Promotion Policy

Keep `AI_REVIEW_MODE=shadow` for at least 5 to 10 trading days covering both markets. Review factual
accuracy, omission of material events, modeled-versus-consensus wording, historical-comparability
guardrails, usefulness of next checks, and primary/backup recovery. Assist mode requires an explicit
user decision; it is never enabled automatically.
