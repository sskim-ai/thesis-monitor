# Price Structure v3 Validator Ownership

## Canonical Rule

`candidate availability != render obligation`.

`V3 selected render plan = validator source of truth`.

Candidate generation may expose more valid support, resistance, completed Bollinger, provisional
Bollinger, and confluence evidence than a user-facing message should display. Safety,
materiality, overlap deduplication, and the display budget reduce that candidate set before
rendering. Validation applies to the reduced selected plan, not the original candidate inventory.

## Plan States

| State | Meaning | Validation |
| --- | --- | --- |
| `SELECTED_REQUIRED` | The selected fact owns a standalone rendered line. | Missing text or binding fails. |
| `SELECTED_AS_CONFLUENCE` | The selected fact is represented by a confluence annotation. | Missing range or confluence label fails. |
| `OMITTED_BY_MATERIALITY` | A valid candidate was not material enough to display. | No render obligation. |
| `OMITTED_BY_DISPLAY_BUDGET` | A valid candidate exceeded the bounded surface. | No render obligation. |
| `OMITTED_BY_OVERLAP_DEDUP` | Another selected fact owns the overlapping range. | No duplicate standalone obligation. |
| `OMITTED_BY_SAFETY` | The candidate failed a user-visible safety gate. | It must remain omitted. |
| `NOT_AVAILABLE` | No eligible fact exists. | No render obligation. |

Repository-native renderer bindings are the concrete selected plan. A binding emitted by
`render_current_price_structure` is required; an available candidate absent from those bindings is
not reconstructed as required by the fallback validator.

## Strictness

This contract does not disable validation. Removing a selected range, selected dynamic Bollinger
line, selected provisional line, or selected confluence annotation fails the V3 renderer validator.
The notification pipeline continues to abort on real validation failures.

When V3 is off, `fallback_price_context_errors` preserves the legacy dynamic support/resistance
requirements. The selected-plan boundary applies only after a V3 section has passed its own render
validation.

## Incident Control

Run `2026-08-28-kr-run-44-4606feed1396` selected the `000660` near support with daily Bollinger
confluence and omitted a weekly dynamic resistance by materiality. The current runtime correctly
passes that message. Permanent tests retain both sides of the boundary: intentional omission passes,
while a selected fact or confluence removed from rendered text fails.

Completed and provisional Bollinger candidates use the same ownership rule. Candidate existence
alone never creates a user-facing requirement, and no ticker-specific exception is permitted.
