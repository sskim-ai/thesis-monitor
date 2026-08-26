# 2026-08-26 US Summary Item Temporal Binding

The temporal decision object now carries:

```text
series_code
observation_date
prior_observation_date
temporal_role
cadence_basis
today_signal_eligible
important_change_eligible
structured_state
reason
```

The digest selector accepts only direction-bearing observations whose temporal contract permits important-change use. Relative facts additionally require same observation date, same temporal role, and eligible source facts. RSP cannot form a relative return without a canonical return. XLE:XLF can form one because both source returns share the 2026-08-25 session.

Focused controls covered current/previous sessions, weekends, holidays, legacy rehydration, current level-only, official release date labels, stale WTI, and same-session sector dispersion.

`SUMMARY_ITEM_WITHOUT_TEMPORAL_BINDING = 0`.
