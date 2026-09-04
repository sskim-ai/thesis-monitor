# 2026-09-04 Holder Decision-Variable Repair

CRCL and HUT used valid business variables that were absent from the holder-variable vocabulary. The generic contract now recognizes reserve/non-interest revenue, funding, cash recovery, project delay, and operation/commissioning language.

The distinction between business logic, price review, and holder management remains intact. A neighboring price-only holder sentence still fails. No mandatory sell instruction and no ticker-specific exception was added.

| Gate | Result |
|---|---|
| Incident false positives repaired | `2/2` |
| Price-only true-positive retained | `PASS` |
| Ticker exceptions | `0` |
