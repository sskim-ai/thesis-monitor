# Free Analyst Adaptive Canary Simulation

- Source packet: `2026-08-25-us-run-37-7e04812311c2`
- Provider recollection: `0`
- Production mutation: `0`
- Candidate eligibility: `14/14`

## Selection

| Slot | Eligible | Selected | Renderer | Runtime quality | Final simulated mode |
| --- | --- | --- | --- | --- | --- |
| Market digest | yes | yes | `CONCISE_HYBRID` | PASS | canary |
| CORZ | yes | yes | `CONCISE_HYBRID` | PASS | canary |
| CRCL | yes | yes | `CONCISE_HYBRID` | PASS | canary |
| Remaining 11 stocks | yes | no | candidate-specific | not selected | current/fallback |

Selection is deterministic and uses message materiality plus stable identity, not ticker
hard-coding. Limits are market `1`, stock `2`, total `3`.

## Safety

Fact mismatch, unsupported numeric, unsupported causality, temporal violations, Trade AR leakage,
hidden arithmetic, external unsourced facts, and material information loss are all `0` for the
selected set. Scoped runtime quality is `PASS`. Open Research, web/news search, and research
sidecar dependencies are `0`.

The two broad-cohort generic synthesis repetitions remain a full-mode P2. They do not pass through
as a material repetition error in the selected three-message canary set, and no threshold changed.
