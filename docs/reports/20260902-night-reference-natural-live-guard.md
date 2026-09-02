# Night Reference Natural Live Guard

This repair is retrospective and production-equivalent proof, not natural live proof.

Next action: wait for the next ordinary US morning cycle and inspect it read-only.

Required natural checks:

- expected reference is the previous valid XKRX business date;
- provider raw `BAS_DD` is preserved and compared explicitly;
- both contract rows pass date, finality, instrument, comparison, and provenance gates;
- the canonical section appears once when ready, or is safely omitted when not ready;
- non-night market content, V2 decisions, stock messages, and exactly-once delivery remain intact.

Prohibited: manual Scheduled Task, historical production resend, forced row readiness, recipient
disclosure, archive rewrite, scheduler change, and Production Assist enablement.
