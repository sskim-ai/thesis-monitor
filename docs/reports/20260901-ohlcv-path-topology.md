# OHLCV Path Topology

## Before

```text
source monitor -> OhlcvClient -> D/W/M -> PriceContext/Price Structure
accepted V2 prepare -> fresh local HTTP -> first ConnectError -> cohort abort
```

The two consumers could observe different execution namespaces and acquisition moments.

## After

```text
source monitor -> bounded OhlcvClient acquisition -> validate -> existing feature engine
               -> freeze packet-owned technical context -> immutable packet
immutable packet -> accepted V2 prepare -> decision evidence -> candidate
```

The decision stage has no local OHLCV HTTP call. Price Structure algorithms and output are
unchanged. `OHLCV_PATH_TOPOLOGY_MAPPED = PASS` and
`V2_DECISION_STAGE_REQUIRES_FRESH_LOCAL_OHLCV_HTTP = 0`.
