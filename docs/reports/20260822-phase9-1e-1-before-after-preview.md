# Phase 9.1E.1 Before/After Preview

The read-only replay used US run-32 and KR run-29 inputs. Only the working-capital mode changed.

## Selection

- Active universe: `20`
- Inventory candidates: `5`
- Selected Inventory: `3` (`000660`, `005490`, `005930`)
- Suppressed Inventory: `2` (`MU`, `TSLA`), because Phase 9.0E FCF already owns the same current
  decision context
- Trade AR, broad AR and AP selected: `0`

## Message Delta

| Ticker | Added interpretation | Character delta | Quality |
| --- | --- | ---: | --- |
| 000660 | Inventory growth below COGS growth; memory-cycle caution | +87 | minor improvement |
| 005490 | Inventory growth above revenue growth; spread/working-capital follow-up | +82 | minor improvement |
| 005930 | Inventory growth above COGS growth; ASP/mix/demand context | +87 | minor improvement |

Average selected-message delta is `+85.3` characters. The Inventory sentence is placed in the
existing business/earnings section and does not repeat in core, valuation, price, supply or next
checks. No status, warning or valuation delta is created.

Human quality across the five Inventory candidates: `3` minor improvements, `2` no meaningful
change, `0` degraded. Full before/after text and lineage are in the runtime replay JSON.

