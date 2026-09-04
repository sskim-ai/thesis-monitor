# Track A — V2 Child Wait / Timeout Ownership

Repair only the orchestration wait contract that interrupted a healthy explicit-V2 child.

Facts to preserve:
- stock_decision V2 child owned a 1800-second command timeout
- outer automation interrupted it with Ctrl-C after about 168.3 seconds
- V2 candidate had not yet persisted
- later backup proved the same V2 path could complete 8/8

Required:
- one authoritative timeout owner
- outer orchestration must not impose a shorter hidden timeout
- active V2 generation/progress keeps the waiter attached
- no arbitrary Ctrl-C while the child is healthy
- bounded cleanup only after child terminal/authorized cancellation
