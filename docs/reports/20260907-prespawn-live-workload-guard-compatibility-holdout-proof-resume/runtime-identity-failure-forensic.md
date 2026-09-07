# Runtime Identity Failure Forensic

The repaired pre-spawn guard passed and the model transport completed normally. The first Directional Core context returned four candidates in 127.29 seconds with a valid receipt and complete context preservation.

The run then failed closed before candidate semantic review because the prompt requested runtime generation `20260907-prespawn-guard-resume-20260907T012700Z-1f19aa40aef6`, while the frozen JSON Schema still constrained `packet_id` to source generation `20260907-us-remediation-holdout-20260907T001800Z-57bcd871e06a`.

This is `RUNTIME_GENERATION_SCHEMA_CONST_MISMATCH`, not a guard, transport, timeout, or investment-semantic failure. NVDA, JPM, WMT, and BRK-B are treated as partially exposed. The cohort is retired, A/B/C remain `NOT_RUN`, and no retry or hotfix rerun was performed.
