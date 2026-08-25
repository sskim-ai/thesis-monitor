# KR Message Quality v2

Replay result: `8/8 PASS`.

Mandatory cases:

- SK hynix: HBM4 and AI-server memory demand lead; expectation remains explicit; participant flow
  stays tactical; exact tuple remains in one `수급` section.
- Hanwha Aerospace: defense exports, backlog, delivery, and margin lead; Inventory is supporting;
  no HBM/ASP ownership leakage.
- Market digest: publication-pending KOSPI/KOSDAQ and breadth are explicit; no domestic market
  direction or participant flow is invented.

Quality deltas from the exact instruction-commit baseline:

- Generic synthesis lines: `10 -> 0`.
- Messages with duplicated generic sections: `5 -> 0`.
- Quality v2 failures: `0` after repair.
- Numeric binding: `123` automatic, `0` rejected.
- Average selected message length: `449.0 -> 445.4` characters.

Decision: `KR_MESSAGE_QUALITY_V2 = PASS`.
