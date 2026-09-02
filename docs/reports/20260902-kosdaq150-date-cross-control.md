# KOSDAQ150 Date Cross-Control

For `BAS_DD=20260901`, the official response contains KOSDAQ150 202609 NIGHT row `A0669000`: O 1440.00 / H 1447.00 / L 1415.50 / C 1432.80, volume 1885, provider change -7.30. Its normalized fingerprint is `02de2670aec86c6dc1f3eef97ca29a9e7297bc9902c441c4af75daa97ce80567`.

The same date also contains a distinct regular DAY control row for the same contract: O 1439.50 / H 1445.30 / L 1396.80 / C 1402.50. It was not compared as NIGHT.

For `BAS_DD=20260902`, the official response contains no rows for any product. With neither a KOSDAQ150 row nor a user-provided Kiwoom KOSDAQ control, product-wide date mapping cannot be proved or contradicted.

`KOSDAQ150_DATE_MAPPING_CONSISTENT = NOT_ENOUGH_EVIDENCE`

`CROSS_CONTRACT_COMPARISON = 0`

`DAY_ROW_COMPARED_AS_NIGHT = 0`
