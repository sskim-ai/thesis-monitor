# M12W GPT-5.6 Sol Restoration Closeout

## Decision

`M12W_CANARY_FAIL`

The observed Sol runtime returned successfully, but the first context failed a frozen directional
target. The whole generation stopped immediately. Fresh real proof and production remain
`NOT_READY`.

## Repository

- Base: `9e5861a2479aaae3fa473824a6f764435f2bba65`
- Work instruction: `e8441e0543054534566e99c19fbdcd6c0722462c`
- Implementation: `538cb761e1c10754cd74dd66b22d3e2f803561ac`
- Branch: `codex/20260910-gpt56-sol-restoration-m12w`
- Main merge / deployment: `0 / 0`

## Frozen Contract

- Model / effort: `gpt-5.6-sol / xhigh`
- Timeout: `1800s`
- Topology: `4 subjects/context`, `2 contexts`, `3 repetitions`
- Wrapper retry / fallback / split / stitch: `0 / 0 / 0 / 0`
- M12U financial and directional semantic changes: `0 / 0`
- Fictional source, prompt and schema changes: `0`

Generation: `20260910-m12w-fictional-20260910T020309Z-f8b8bd468c5a`

Source lock: `ae98f6b76270399d856cbeb064ac55787c85a8249c96ffc5e5a310d2796be6fa`

## Execution Result

The first context returned a complete parsed output after `407.720583s`. CLI-advertised and
observed runtime identity were both `gpt-5.6-sol / xhigh`. Transport status was PASS, with
timeout `0`, capacity failure `0`, CLI internal retry `0`, wrapper retry `0`, orphan `0`, and
schema-valid rows `4/4`.

Final semantic acceptance was `3/4`. FIC-FIN-01 produced BUY `6.5` against the frozen target
`6.0`, yielding `frozen_ordinal_contract_inconsistent`. FIC-FIN-02, FIC-FIN-03 and FIC-FIN-04
passed their applicable gates. The remaining five contexts were not started. Formal stability,
core balance variance, business delta variance and stance variance remain `NOT_MEASURED`.

This proves only that the observed Sol context completed the transport path. It does not prove
full Sol runtime suitability or semantic stability for the 8x3 cohort.

## Validation

- Focused pytest: `260 PASS`
- Full local pytest: `3255 PASS`, 2 warnings
- Ruff / git diff check: `PASS / PASS`
- Hosted CI run `34427644559`: `3250 PASS`, five known historical portability failures
- New M12W hosted CI failures: `0`

## Safety

Real issuer calls, judge calls, provider fetches, production sends, persistence mutations,
warning mutations, notification writes, monitoring registrations, scheduler mutations, main
merge and deployment are all `0`. All eight monitored schedules remain `PAUSED`. Astra calls in
M12W are `0`.

## Open Items

- P0: `0`
- P1: frozen FIC-FIN-01 directional target mismatch; five inherited hosted-CI portability tests
- P2: none added by M12W

## Next Scope

`BOUNDED_SOL_DIRECTIONAL_CONTRACT_REPAIR`

The next task should diagnose the general directional boundary that produced FIC-FIN-01 BUY 6.5
without changing the threshold automatically or adding ticker-specific exceptions. This generation
must not be resumed, selectively rerun, stitched or used for a real issuer proof.
