# Korea Night Futures In US Morning

The US morning digest consumes the existing canonical night-futures facts and session mapping. It
does not create aliases or infer a Korean overnight session from the US trade date.

Only safe current overnight directional facts may render. One safe series renders alone; two safe
series render together; no safe series omits the entire section. `PUBLICATION_PENDING`, level-only,
unavailable, or stale facts never produce a directional percentage and are never carried forward.

The immutable run-43 replay had no safe current directional night-futures facts, so omission was
the correct result. Natural proof of the optional section remains independent of the full-message
deployment.
