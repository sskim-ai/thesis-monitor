# Open Research Production Integration Proposal

No integration is performed. A future design may trigger research only for a material price move, new official event, thesis-sensitive event, large gap/reversal, unusual breadth, sector shock, new warning, or explicit user `why` request.

`normal packet -> trigger? -> no: existing Free Analyst / yes: Open Research -> attribution sidecar -> Free Analyst -> Adaptive Renderer -> hard validators -> deterministic fallback`

Proposed independent kill switch: `OPEN_RESEARCH_ENABLED=false`. It disables research without disabling the existing Free Analyst. A failed/partial search remains nonfatal and must fall back to the immutable non-research path.
