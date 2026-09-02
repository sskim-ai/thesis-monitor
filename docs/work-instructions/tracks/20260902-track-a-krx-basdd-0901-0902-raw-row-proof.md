# Track A — KRX BAS_DD 09/01 vs 09/02 Raw-Row Proof

Read-only.

Query the same KRX futures daily service for:
- BAS_DD 20260901
- BAS_DD 20260902

For each, capture KOSPI200 202609 NIGHT:
- instrument/contract
- MKT_NM
- O/H/L/C
- volume/change fields
- raw SHA
- normalized fingerprint

Also capture DAY row only as a separate control.
Never compare DAY as NIGHT.
No code changes.
