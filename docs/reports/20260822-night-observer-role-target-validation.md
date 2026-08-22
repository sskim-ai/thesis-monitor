# Night Observer Role-target Validation

The 08:45 and 09:15 roles now call the same canonical NIGHT session resolver as
production. Saturday 2026-08-22 resolves NIGHT BAS_DD 2026-08-22 and preceding
XKRX business date 2026-08-21; no wall-clock trading-day gate intervenes.

Session basis, preceding DAY pairing, instrument/contract/maturity matching,
provider cross-check, telemetry record shape, and 08:20 production deadline are
unchanged. A terminal 08:45 result suppresses 09:15. A nonterminal 08:45 result
allows 09:15; the horizon result then suppresses later dates for the same target.

Provider-call bound: zero for invalid, duplicate, or terminal target; one per
eligible observer slot otherwise. No observer was manually run.

