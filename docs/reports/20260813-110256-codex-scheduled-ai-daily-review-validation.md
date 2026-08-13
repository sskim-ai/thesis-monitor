# Codex Scheduled AI Daily Review Validation

## Scope

- Base: `90fbcda1b52e6e6411287b2ee60d35ba332a70bf`
- Mode: `shadow`
- DB migration: none
- Public Action schema: `0.4.5`, 20 operationIds
- OpenAI API integration: none
- Custom GPT Instructions/Knowledge: unchanged

## Architecture

```text
deterministic monitor
  -> verified immutable packet
  -> Codex Scheduled Task
  -> thesis-monitor-daily-review skill
  -> strict temporary JSON
  -> local schema and guardrail validator
  -> shadow output and comparison history
```

U.S. packets are generated only after the KRX morning gate is ready or reaches its deadline. Korean
packets are generated after a successful `daily_kr` close run. Packet generation is failure-isolated;
an AI filesystem error cannot stop deterministic Telegram dispatch.

Packets use a source-run content hash in `packet_id`. A retry with identical facts reuses the immutable
packet, while changed facts create a new packet version. The claim scanner selects the newest snapshot
for a source run so an older immutable version cannot be processed after its replacement.

## Packet Contract

The packet contains:

- market regime, material changes, market theses, verified night futures or close FX, and cautions;
- the exact ticker and thesis version;
- current thesis drivers, validation/invalidation signals, expectations, and risks;
- deterministic assessment, material evidence fingerprints, unknowns, and warnings;
- allowlisted earnings, valuation, price, and positioning values;
- the previous assessment for the same ticker and thesis version;
- stable `fact_id` entries used by AI output provenance.

Raw OpenDART facts and parser/provider metadata are omitted. Historical statistics are withheld when
comparability is not verified. Modeled forward values retain modeled provenance.

## Skill And Schedule

The repository skill is `.agents/skills/thesis-monitor-daily-review`. It enforces Fact / Interpretation /
Unknown separation, baseline-versus-delta semantics, business/valuation/price separation, modeled-
versus-consensus wording, no external web research, no code changes, and no hidden chain-of-thought.

Planned local-project schedules, Asia/Seoul:

| Task | Time |
| --- | --- |
| US primary | 08:50 |
| US backup | 09:10 |
| KR primary | 16:15 |
| KR backup | 16:35 |

Scheduled task activation and exact model are pending at report creation. The final completion report
will record the active task state after the pushed commit is deployed to the live checkout.

## Network And Idempotency Fixture

- Primary missed: the backup claimed the pending packet and completed it.
- Primary completed: a later backup scan returned `no_pending_packet`.
- Interrupted claim: a 30-minute lease expired and a backup reclaimed the same packet.
- Partial output: `.json.tmp` was not considered complete.
- Immutable update: the newer packet for the same source run superseded the older packet for claiming.
- Duplicate key: completion is keyed by `packet_id + analysis_policy_version`.

## Shadow Comparison Fixture

| Field | Result |
| --- | --- |
| Deterministic assessment | `no_material_change` |
| AI proposed assessment | `no_material_change` |
| AI interpretation | Verified order evidence supports the demand thesis but does not require a status change. |
| Official assessment mutated | false |
| Telegram mutated | false |

The comparison history preserves deterministic warnings and records guardrail conflicts without changing
the official assessment.

## Guardrails

Validated failures:

- unknown ticker or ticker-set mismatch;
- thesis-version mismatch or no longer current thesis version;
- unknown `fact_id`;
- a number not present in the packet;
- modeled forward EPS described as market/analyst consensus;
- historical percentile/range language when comparability failed;
- raw parser/provider metadata in model output.

The output validator atomically promotes only a valid temporary document, copies it into dated history,
and writes a deterministic-versus-AI comparison record. Rejected output cannot affect the database or
notification queue.

## Validation

- `pytest -q`: 464 passed, one upstream Starlette/httpx deprecation warning
- `ruff check .`: passed
- `git diff --check`: passed
- Skill `quick_validate.py`: passed
- GitHub Actions: pending at report creation

## Operational Boundary

The Mac mini must remain on, network-connected, signed in to Codex, and running the ChatGPT desktop app.
The scheduled tasks use the live local checkout with workspace-write access. They may write only under
`data/ai_review` and may not browse externally. If Codex is unavailable, deterministic monitoring and
Telegram continue unchanged.

Assist mode is not enabled. Promotion requires an explicit user decision after at least 5 to 10 trading
days of U.S. and Korean shadow review.
