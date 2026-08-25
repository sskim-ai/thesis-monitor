# Common AI Core v1

## Status

Common AI Core v1 integrates the verified Free Analyst and Adaptive Renderer contracts into the production codebase. Open Research and Event Attribution remain separate and are not imported by the runtime path.

Production flow:

```text
Verified production packet
  -> existing AI review validation
  -> current rendered candidate
  -> natural-packet adapter
  -> Evidence-Locked Free Analyst
  -> synthesis support validation
  -> deterministic Adaptive Renderer
  -> existing hard validators
  -> bounded canary selector
  -> one packet-bound final payload per slot
```

Any unsupported Free Analyst candidate remains ineligible. The slot retains its existing production output or deterministic fallback. No unvalidated prose repair follows a failed candidate.

## Ownership

- Backend canonical facts define what is true.
- Free Analyst selects and connects verified evidence.
- Synthesis validation checks support type and evidence references.
- Adaptive Renderer chooses presentation depth without changing facts.
- Existing hard validators remain authoritative.
- Deterministic fallback guarantees packet completion.

The structured analysis object is a conclusion and provenance contract. It does not store private reasoning or chain-of-thought.

## Control Plane

The authoritative user-visible gate remains `AI_REVIEW_PILOT_ENABLED`. With that setting false, `deliver_validated_ai_review()` returns before candidate preparation or dispatch. The Common AI Core kill switch is independent:

```text
FREE_ANALYST_ADAPTIVE_ENABLED=false
FREE_ANALYST_ADAPTIVE_MODE=current
```

Supported internal modes are `current`, `free_analyst_adaptive_canary`, and `free_analyst_adaptive`. This phase wires only the limited canary mode. Full mode is not armed.

## Isolation

The production dependency graph has no Open Research agent, Event Attribution connector, web/search connector, or research scheduler. Generic typed facts may be shared, but no research side effect is reachable.

The public Action remains `0.4.5`, output schema remains `4`, and no public endpoint or Telegram schema changes.

## Delivery

Canary evaluation is per message. At most one market message and two stock messages may be selected in a run. A scoped runtime-quality receipt evaluates only AI-selected canary messages; non-selected production messages retain their existing ownership. Receipt scope changes completeness identity only. Numeric, semantic, temporal, language, repetition, and causality thresholds are unchanged.

Packet identity, delivery rows, receipt hashes, retry behavior, and exactly-once semantics remain owned by the existing AI-assisted delivery service.

## Market Context Input

`market-context-adapter-v1` supplies one common typed input shape for KR and US verified market
Facts. Market-specific acquisition and semantics remain in their adapters; the Free Analyst and
Adaptive Renderer do not fork by provider. Partial breadth, flow, sector, or size coverage remains
Unknown and cannot block deterministic fallback.

The adapter sidecar is a deterministic view of packet-owned Facts. It does not become a new truth
store, does not alter packet identity, and does not expose internal source hints in the AI packet.
Open Research remains outside the production dependency graph because no qualifying production
research connector is available.
