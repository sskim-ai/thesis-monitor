# OHLCV Acquisition Topology

Contract: `ohlcv-acquisition-topology-v2`

## Ownership

```text
source monitor
  -> OhlcvClient
  -> local official OHLCV analyst service
  -> D/W/M bar validation
  -> existing feature engine
  -> packet-owned technical context
  -> immutable review packet
  -> accepted V2 decision runtime
```

The source monitor owns network acquisition. The accepted V2 decision runtime consumes the
packet-owned artifact and does not open a second local HTTP dependency. Price Structure keeps its
existing semantic contract; it may share the acquisition result but is not redefined by this
contract.

## Incident Topology

Run 49 used a second `httpx.AsyncClient` call from `accepted_decision_v2_runtime.prepare_context`.
The source monitor had already completed all 14 subjects, while that later process namespace could
not connect to loopback. The first `ConnectError` aborted the cohort before candidate generation.

## Repaired Topology

- Acquire each configured timeframe through `OhlcvClient`.
- Retry only retryable transport, timeout, protocol, and 5xx failures within configured bounds.
- Validate bar ordering, uniqueness, OHLC relations, volume, future bars, identity, currency, and
  adjustment basis.
- Compute the existing feature packet once and freeze its raw/feature fingerprints.
- Serialize the technical context into the internal review packet.
- Let each subject fail closed as `PARTIAL_SAFE`, `UNAVAILABLE`, or `INVALID` without aborting peers.
- Never fetch OHLCV while preparing an accepted V2 decision context.

Public schema 4, Telegram rendering, Price Structure algorithms, valuation algorithms, and delivery
schedules are unchanged.
