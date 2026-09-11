# Track B — Model Transport Instrumentation + Timeout Ownership

Instrument:
process spawn
stdin completion
first/last stdout byte
process exit
parse completion
stdout/stderr byte counts
exit/signal
timeout owner
termination initiator
cleanup status.

Inventory every timeout in CLI/subprocess/parent/outer automation.

Require exactly one authoritative timeout owner.
Outer watchdog must not preempt it.

No blind timeout inflation.
If a bounded increase is justified by canary evidence, maximum 3600 seconds
and only one increase is allowed in this task.

No orphan processes and no secret logging.
