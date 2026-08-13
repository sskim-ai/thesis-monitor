# Knowledge Parity and Atomic Claim Validation

## Repository

- Base: `ead834c795a9f6f27114d62c36dc2229ed058410`
- Branch: `main`
- DB migration: none
- Public Action schema: unchanged (`0.4.5`, 20 operationIds)
- AI review mode: `shadow`
- GitHub Actions: pending at report creation

## Knowledge Before / After

| Copy | Before SHA-256 | Before lines / bytes | After SHA-256 | After lines / bytes |
|---|---|---:|---|---:|
| Current Custom GPT attachment | `9c769f6be1ea6d17b858a14b35a7b2cd63201c0dc8066f7b05368d9bab967176` | 942 / 16,599 | same | 942 / 16,599 |
| `docs/custom_gpt_knowledge_ko.md` | `4af4e4f41ef65e1a1b5c7d8dece08a72a89f06f1774493947718fddb3d762c8c` | 648 / 29,251 | `9c769f6be1ea6d17b858a14b35a7b2cd63201c0dc8066f7b05368d9bab967176` | 942 / 16,599 |
| Codex runtime mirror | `4af4e4f41ef65e1a1b5c7d8dece08a72a89f06f1774493947718fddb3d762c8c` | 648 / 29,251 | `9c769f6be1ea6d17b858a14b35a7b2cd63201c0dc8066f7b05368d9bab967176` | 942 / 16,599 |

The canonical source was the conversation attachment `1-thesis_monitor_analysis_knowledge_v2.md`. Its bytes were copied without Markdown formatting, line-ending normalization, BOM removal, or trailing-newline changes. The local attachment path is not stored in the repository.

The manifest keeps Knowledge version `2026-08-13` and records this as mirror correction `canonical-parity-correction-2026-08-13`. It now includes SHA-256, line count, byte count, and source role. New packets and Shadow outputs use the corrected SHA; historical outputs are retained.

## Semantic Difference

The canonical document is the v2.0 guide with sections 0-26. It contains the data hierarchy, Fact/Interpretation/Unknown rules, Action/API usage, financial formulas, industry valuation, earnings quality, expectations, OHLCV, reward/risk, thesis state, macro/FOMC transmission, provisional earnings, valuation comparability, ADR, portfolio scoring, and answer template.

The former repository copy was a later 18-section reorganization. It added repository-specific detail including KRX night-futures timing, KR-close FX and supply field semantics, monitoring data-quality states, and newer Action wording. Those additions caused the canonical mismatch and were not copied into the canonical mirror.

Repository-only AI runtime rules that remain necessary are now explicit in `daily-review-policy.md`: US 07:50 evaluation and KRX gate, KR 16:05 close result, night futures as price context, KR-close FX and supply as backend facts, and backend ownership of provider retry/freshness/schedules. The routing index now points to headings that actually exist in the canonical v2.0 document.

## Mirror Validation

`scripts/sync_custom_gpt_knowledge.py` accepts an explicit canonical source, writes both mirrors atomically, refreshes the manifest, and verifies byte equality. Its `--check` mode enforces the repository invariant without requiring remote Custom GPT access. CI tests verify:

- docs bytes equal runtime bytes
- both hashes equal manifest SHA
- line and byte counts equal the manifest
- canonical import preserves BOM, CRLF, and missing trailing newline in a fixture
- routed core headings exist
- new packet provenance uses the corrected Knowledge identity

## Atomic Claim Lock

- Lock type: POSIX `fcntl.flock(..., LOCK_EX)`
- Stable path: `data/ai_review/locks/<sha256(packet_id)>.lock`
- Serialized mutations: claim, reclaim, final promotion, history write, and current-claim cleanup
- Outside the lock: packet scan, Codex reasoning, schema validation, numeric validation, and guardrail checks
- Claim writes: temporary file, file `fsync`, atomic replace

The lock file is stable and is not deleted after each operation. This avoids path replacement races. The guarantee targets the current Mac mini local POSIX filesystem and does not claim network-filesystem semantics.

## Fencing Interleavings

### Finalizer A wins the lock

`A validates → A locks → A rechecks active claim → A promotes → A cleans its claim → unlock → B locks → final exists → B no-op`

Result: A remains the only final output; B cannot reclaim or overwrite it.

### Backup B wins the lock

`B locks → expired A is replaced by claim B → unlock → A locks → active claim is B → A rejected`

Result: A receives `stale_claim_output`; A's claim-specific temp is never promoted and A cannot delete B's claim.

Lease expiry alone still does not invalidate A. If no worker reclaims, active claim ID remains A and A may finalize. Once B reclaims, A is permanently fenced.

## Network Recovery

- Claim lease: 30 minutes
- US tasks: 08:50 primary, 09:30 backup
- KR tasks: 16:15 primary, 16:55 backup
- Backup delay: 40 minutes
- Safety margin over lease: 10 minutes

All four Scheduled Tasks were ACTIVE at validation time, used GPT-5.6 Sol with high reasoning, and targeted `/Users/sskim/Codex/thesis-monitor`.

## Validation

- Start baseline: `473 passed`, Ruff pass, diff check pass
- Focused Knowledge/claim/health tests: `29 passed`
- Full suite after implementation: `477 passed`
- Ruff: pass
- `git diff --check`: pass
- Knowledge checksum: pass (`9c769f...`, 942 lines, 16,599 bytes)
- Skill validation: pass

Shadow isolation remains intact: no official `ThesisAssessment`, `NotificationDelivery`, or Telegram behavior is changed.

## Remaining Gaps

- Structured-industry-first routing remains a later phase.
- Prose-level numeric provenance strengthening remains a later phase.
- Production assist and Telegram AI narrative remain disabled.
