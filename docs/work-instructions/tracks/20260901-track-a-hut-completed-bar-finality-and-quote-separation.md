# Track A — HUT Completed-Bar Finality + Quote Separation

Focus: HUT `2026-08-31`, where provider raw O/H/L = 79.43/79.99/75.71 and `cur_prc`-derived close = 81.94.

Tasks:
- map raw provider fields and exact semantics
- prove whether cur_prc is quote, regular close, or mixed-session value
- separate CURRENT_QUOTE from COMPLETED_BAR_CLOSE
- implement FINAL / PROVISIONAL / UNCONFIRMED / INVALID bar-finality state
- use settled regular close only when source semantics prove it
- bounded re-probe after session completion
- automatic recovery on later valid FINAL row
- allow safe independent timeframes to remain usable

Never synthesize OHLC.
Never map current quote to completed close heuristically.
