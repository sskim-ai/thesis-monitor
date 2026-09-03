# Codex Shadow Decision Experiment Source Lock

## Identity

- Packet: `2026-09-03-us-run-53-055ae8ea01f6`
- Cohort: `14` US/foreign stocks
- Packet file SHA-256: `969b52387ca9eee504f922fced85f629aaf85bffaf43234514b2ffa2ea5ac7d1`
- Canonical packet SHA-256: `1434a5c8cc7e197d348299aacaa38366cb989867ec5fd1b43eebfc70b6b1e9fc`
- Base SHA: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Work-instruction commit: `3281e59e33c1ae5ba85c78f8a26433fed0efb502`
- Fresh fact collection: `0`
- Post-run-53 fact leakage: `0`

## Blind Boundary

Phase 1 received only packet-owned evidence, the generic decision contract, and verified price maps. The manual comparator and prior accepted decision were absent from generation. The manual comparator was loaded only after the frozen candidate, accepted artifact, and combined preview hashes all revalidated.

| Ticker | Evidence fingerprint | Price-map fingerprint | Contamination scan |
| --- | --- | --- | --- |
| CORZ | b3e0620200cbcc2f... | 23cd19bd6321f4b2... | clean |
| CPNG | 4e5ec6d9dd20e3d7... | c1256ea5dee31652... | clean |
| CRCL | 24e05bfd98e7b20e... | 5af7742f40d9375b... | clean |
| GOOGL | 46c26d00e2b87c3f... | 64ef08619cb3e498... | clean |
| HUT | b8261e2fa61dd3cc... | de92dadff4e68569... | clean |
| IBM | 5fdffdbbb336cc6d... | 74481f0d5de2f53b... | clean |
| MU | ab1dd37739519cb1... | 2e3085db34468bf5... | clean |
| RXRX | e4395ca1fb599ea9... | 4d92ccd87eaa46fd... | clean |
| SKHY | b2b8b74db322a138... | f2778ce2e7fa8c2e... | clean |
| SNDK | 9f548fbd751a9229... | a5c6d19c09292be3... | clean |
| TSLA | 5bcd4aef26ecffb6... | a8c88bb57296a0a7... | clean |
| TSM | 7348e948acd62584... | a616f6de8259c10c... | clean |
| WRD | fe1b02502ea42b92... | ee0a24684b44f60e... | clean |
| WULF | b78e92fb7bd157bd... | cd6f179a366e1262... | clean |

## Freeze Verification

| Artifact | Status | SHA-256 |
| --- | --- | --- |
| shadow-candidates.json | PASS | 249079a79abba30d08d020d69732a92ede55c62f4641f1ff05690d8e89f682f5 |
| shadow-accepted.json | PASS | fcbdb4712c54efd0b512bc5788129feb48e6fc98a9423106a1ebddce60b816fb |
| 20260903-us14-shadow-decision-message-preview.md | PASS | 6ba07b9cc0e404514a38240191f2e2ba63b92c3d6a0e3d313dd4339932003b93 |
