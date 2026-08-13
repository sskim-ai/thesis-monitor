# Persistent Project Handoff Validation

Date: 2026-08-13 KST

## Objective

Make the full AI-assisted monitoring architecture recoverable from the repository without relying on
the long chat history. The canonical state resolves its deployed commit through `git rev-parse HEAD`
because a committed file cannot embed its own final commit hash.

## Canonical Artifacts

| Artifact | Purpose |
|---|---|
| `docs/PROJECT_HANDOFF.md` | Master purpose, roles, contracts, milestones, gaps, next steps |
| `docs/NEXT_SESSION_PROMPT.md` | Pasteable continuation prompt |
| `docs/project-state.json` | Machine-readable versions and Pilot state |
| `docs/architecture/AI_ASSISTED_MONITORING.md` | End-to-end ownership and safety boundaries |
| `docs/architecture/OHLCV_STRUCTURE_ENGINE.md` | Deterministic structure v2 calculation contract |
| `docs/architecture/MARKET_INTELLIGENCE.md` | Market facts, structure, transmission, and renderer |
| `docs/operations/AI_ASSISTED_PILOT.md` | Schedule, fallback, counting, archive, incident handling |
| `docs/knowledge/README.md` | Dual Knowledge roles, precedence, paths, checksums |

`docs/ai_review_project_handoff.md` remains as a compatibility pointer. Root `README.md` links the
canonical set.

## Decision Record Coverage

Each architecture and operations guide states the problem, decision, reason, rejected alternatives,
and safety constraints. The master handoff additionally records Custom GPT, deterministic backend,
Codex, validator, Telegram, monitoring lifecycle, industry routing, numeric provenance, OHLCV,
market intelligence, Pilot architecture, schedules, known gaps, versions, milestones, and next work.

## Knowledge Validation

- Investment canonical/runtime/upload SHA-256:
  `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart canonical/runtime SHA-256:
  `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`

The documentation does not modify either Knowledge body.

## Security Validation

The documentation contains no credential values, private authenticated URLs, chat identifiers, or
machine-specific absolute paths. It names configuration and audit concepts without embedding secret
content.

## Pilot State

Market-intelligence Pilot v3 starts a fresh state file at KR 0/5 and US 0/5. Old Pilot v1/v2 results
are preserved and not migrated. AI mode remains shadow, single delivery and deterministic fallback
remain active, and Production Assist remains disabled.

## Automated Checks

`tests/test_project_documentation.py` validates artifact existence, JSON state, README navigation,
relative Markdown links, required decision sections, Knowledge file checksums and byte parity, Pilot
version, and absence of machine-specific or secret-like values.

