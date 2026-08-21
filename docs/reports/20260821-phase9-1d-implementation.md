# Phase 9.1D Implementation

## Repository

- Base/main/operating at start: `d0dc76a2446ee5ef9188d1b06dcb241df004c143`
- Branch: `codex/phase-9-1d-selective-working-capital-runtime-shadow-canary`
- Instruction: `docs/work-instructions/20260821-phase-9-1d-selective-working-capital-runtime-shadow-canary.md`
- Instruction commit: `dc4e1cf14faa7cebf78eb8ba5a5e73b6369c991c`
- Implementation commit: `5316113062782b09595a495ec9a903a4973f9df5`

## Implementation

`working-capital-runtime-shadow-canary-v1` adds a detached post-terminal job, immutable attempt
archive, deterministic canary identity, exact delivery SHA verification, idempotent completion,
latency receipt, and independent best-effort dispatch beside the existing cash-flow canary.

The runtime snapshot is dynamically filtered to total Inventory and exact Trade AR before the
unchanged Phase 9.1C selector runs. Broad AR, all AP, advanced ratios, component inventory, contract
assets, and accrued liabilities cannot become candidate relations. Packet financial-period context
suppresses an older static relation when a newer formal filing is already known.

Production AI input, fallback, Telegram, Public Action `0.4.5`, output schema `4`, assessment DB,
warning lifecycle, Phase 9.0E cash-flow selection, and Scheduled Task settings are unchanged.
