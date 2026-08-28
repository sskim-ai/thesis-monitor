# V3 Render Plan and Validator Contract

`candidate availability != render obligation`.

`V3 selected render plan = validator source of truth`.

| Plan state | Validator behavior |
| --- | --- |
| `SELECTED_REQUIRED` | Exact selected binding must render. |
| `SELECTED_AS_CONFLUENCE` | Selected range and confluence ownership must render. |
| `OMITTED_BY_MATERIALITY` | No missing-render error. |
| `OMITTED_BY_DISPLAY_BUDGET` | No missing-render error. |
| `OMITTED_BY_OVERLAP_DEDUP` | No missing-render error. |
| `OMITTED_BY_SAFETY` | No missing-render error. |
| `NOT_AVAILABLE` | No missing-render error. |

The validator consumes renderer bindings and does not reconstruct selection from all available
support/resistance candidates. V3-off traffic retains the legacy validator. Completed and
provisional Bollinger facts follow the same selected-versus-omitted ownership rule.
