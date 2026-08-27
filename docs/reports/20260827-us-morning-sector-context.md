# 2026-08-27 US Morning Sector Context

## Canonical Sector Set

All rows are production OHLCV facts for `2026-08-26`. XLC is level-only; every other row is current directional.

| Symbol | Sector | Level | Return | State | AI review / digest |
|---|---|---:|---:|---|---|
| SOXX | Semiconductors | 515.40 | +0.2607% | CURRENT_DIRECTIONAL | omitted |
| XLB | Materials | 53.67 | +0.1680% | CURRENT_DIRECTIONAL | omitted |
| XLC | Communication services | 112.61 | n/a | CURRENT_LEVEL_ONLY | omitted safely |
| XLE | Energy | 62.43 | +0.5962% | CURRENT_DIRECTIONAL | omitted |
| XLF | Financials | 58.26 | -0.0857% | CURRENT_DIRECTIONAL | omitted |
| XLI | Industrials | 180.34 | +1.0874% | CURRENT_DIRECTIONAL | material leader omitted |
| XLK | Information technology | 182.84 | +0.6053% | CURRENT_DIRECTIONAL | omitted |
| XLP | Consumer staples | 86.27 | -0.2890% | CURRENT_DIRECTIONAL | omitted |
| XLRE | Real estate | 45.09 | -0.5952% | CURRENT_DIRECTIONAL | omitted |
| XLU | Utilities | 43.51 | +0.4618% | CURRENT_DIRECTIONAL | omitted |
| XLV | Health care | 173.54 | -0.9983% | CURRENT_DIRECTIONAL | material laggard omitted |
| XLY | Consumer discretionary | 117.16 | -0.6698% | CURRENT_DIRECTIONAL | omitted |

The backend-owned ranking identifies XLI as the strongest and XLV as the weakest supported sector row. The AI did not calculate a return or ranking. It also did not promote XLC to directional.

Canonical sector acquisition passed, but propagation to reasoning and delivery was partial: 11 current directional rows were absent. Not all sectors needed prose, yet dropping both leader/laggard context together with all core ETFs created material information loss.

```text
US_SECTOR_CONTEXT_PROPAGATION = PARTIAL
CURRENT_DIRECTIONAL_DROPPED = 11
LEVEL_ONLY_PROMOTED_TO_DIRECTIONAL = 0
SOURCE_UNAVAILABLE_AS_CURRENT = 0
AI_DERIVED_SECTOR_RETURN = 0
AI_DERIVED_SECTOR_RANKING = 0
```
