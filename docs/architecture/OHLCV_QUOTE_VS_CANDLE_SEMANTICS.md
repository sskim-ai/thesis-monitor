# OHLCV Quote vs Candle Semantics

Contract owner: `ohlcv-completed-bar-finality-v1`

## Semantic Owners

- `CURRENT_QUOTE` owns a mutable observed price.
- `COMPLETED_BAR_CLOSE` owns the close used by a historical candle and technical features.

Kiwoom US chart APIs are `usa06012` daily, `usa06013` weekly, and `usa06014` monthly. The adapter
maps `open_pric`, `high_pric`, `low_pric`, and `cur_prc` to normalized O/H/L/C. The official schema
labels `cur_prc` as current price and exposes no separate settled regular close or finality field in
the repository path. Therefore the newest `cur_prc` is retained as current quote evidence and does
not silently own completed close.

If an explicitly sourced settled close becomes available, it owns the candle while the current
quote remains separate. Cross-session substitution, `high=max(high, quote)`, and previous-close
copying are forbidden.

Source: [Kiwoom REST API guide](https://openapi.kiwoom.com/m/guide/apiguide?jobTpCode=15).
