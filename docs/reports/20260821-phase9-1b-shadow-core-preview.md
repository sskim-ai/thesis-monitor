# Phase 9.1B Shadow Core Preview

- **KR memory inventory** `000660`: `ELIGIBLE`; Fact `working-capital-reported:b742cc7afdc66afa6d7e1135`; balance date `2026-06-30`; semantic `ifrs-full:Inventories`; relation `working-capital-relation:60a7f3631777af552b12d80e`.
- **US platform broad AR** `GOOGL`: `ELIGIBLE`; Fact `working-capital-reported:173c00a08ebaaa117ff3753e`; balance date `2026-06-30`; semantic `us-gaap:AccountsReceivableNetCurrent`; relation `working-capital-relation:b92bed4bd89180e676f6b36d`.
- **non-calendar memory inventory** `MU`: `ELIGIBLE`; Fact `working-capital-reported:2a5dd10bfd88a91b65bcc777`; balance date `2026-05-28`; semantic `us-gaap:InventoryNet`; relation `working-capital-relation:dbdfd04e725e83528d8fdd31`.
- **foreign issuer inventory** `TSM`: `ELIGIBLE`; Fact `working-capital-reported:9d0e87e9dd05c663bd0cf8dc`; balance date `2024-12-31`; semantic `ifrs-full:Inventories`; relation `working-capital-relation:305f55539aa61a8d6b2f9b55`.
- **HPC broad AR** `CORZ`: `ELIGIBLE`; Fact `working-capital-reported:89da109262e582429a35247c`; balance date `2025-03-31`; semantic `us-gaap:AccountsReceivableNetCurrent`; relation `working-capital-relation:2042e08a6f1ef9ae53c96805`.
- **biotech broad AP context-only** `RXRX`: `ELIGIBLE`; Fact `working-capital-reported:441c0c58aaeba638409c7223`; balance date `2026-06-30`; semantic `us-gaap:AccountsPayableCurrent`; relation `working-capital-relation:84ce5ec88196baf7f8065bb2`.
- **insurance negative control** `003690`: `NOT_APPLICABLE`; Fact `None`; balance date `None`; semantic `None`; relation `NOT_APPLICABLE`.

These are sanitized audit-only snapshots. Source occurrence IDs and canonical Fact IDs are preserved in the JSON; raw provider payloads and credentials are excluded. No production or AI consumer imports this preview.
