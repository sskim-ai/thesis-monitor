# Track C — Approved Secondary OHLCV Recovery

Tasks:
- inventory existing repository-approved secondary OHLCV sources
- map identity/session/currency/adjustment semantics
- do not introduce an unapproved or paid provider automatically
- recover only exact bad rows when all comparability checks pass
- preserve primary bad specimen and secondary recovery provenance
- reject security/date/adjustment/scale mismatches
- no cross-provider averaging
- no whole-series swap for a single bad row unless systemic defect is proven

Apply controls to both CPNG historical row and HUT completed-bar close.
