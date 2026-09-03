# Track C — US/KR Regression + Test Sink + Natural-Live Guard

Preserve:
- strict daily-review validation
- directional balance
- accepted_decision_plan ownership
- Treasury 3Y/5Y/10Y/30Y
- night-futures user-facing suppression
- CPNG/HUT technical recovery
- network/runtime repairs

Run US14 and KR8 production-equivalent fixtures if cohorts unchanged.

Use dedicated non-production test sink/recipient per repository release gate.
Production recipient/delivery intent = 0.

Do not redesign timeout policy in this repair.
Only report natural vs production-equivalent timeout parity.

After merge, wait for next ordinary US natural run to prove:
ready packet → network → model → candidate → accepted → balance → delivery.
