# Korea Night Futures In US Morning

The US morning digest consumes the existing canonical night-futures facts and session mapping. It
does not create aliases or infer a Korean overnight session from the US trade date.

Only safe current overnight directional facts may render. One safe series renders alone; two safe
series render together; no safe series omits the entire section. `PUBLICATION_PENDING`, level-only,
unavailable, or stale facts never produce a directional percentage and are never carried forward.

The immutable run-43 replay had no safe current directional night-futures facts, so omission was
the correct result. Natural proof of the optional section remains independent of the full-message
deployment.

## Canonical Summary Projection

`night_futures_gate` is the sole owner of both user-visible night-futures rows and the compact
`market_summary.items` projection. Raw or legacy summary strings are removed before projection.
Only gate-approved rows may be projected, with these stable identities:

| Series | Fact ID | Field |
| --- | --- | --- |
| KOSPI200 | `market:night_futures:1` | `fields.change_pct` |
| KOSDAQ150 | `market:night_futures:2` | `fields.change_pct` |

The projected value, session, and state must match the canonical sidecar exactly. An unavailable,
stale, or not-ready gate therefore produces neither a compact summary number nor a rendered
section. Historical display fixtures must be explicitly labeled and cannot establish natural
runtime proof.
