# Late Packet Validation Ownership Audit

The later packet `2026-09-03-kr-run-54-78ed269de3df` is KR-owned and binds to source monitor run
54. Its IWM/SPY references are present in its own global market fact catalog, including
`market:relative:IWM:SPY`; they are not evidence of a copied US stock candidate.

The validator result at `17:10:56 KST` occurred after deterministic fallback completed at
`17:10:06 KST`. It did not trigger fallback. The defect was archival ownership: the late reject
could overwrite canonical `validation-result.json` even when all delivery rows were terminal.

The repair makes a no-held-row validation receipt late-only. It writes a timestamped immutable
receipt, records terminal count, and changes neither sent rows nor the canonical validation result.
The regression test proves canonical bytes remain unchanged.
