# Fib Confluence Render Equivalence

## Policy

`CONFLUENCE_RENDER_EQUIVALENCE_POLICY` makes a deterministic display decision over the already
registered Fib/SR confluence and structural zones:

| State | Rule | Rendering |
| --- | --- | --- |
| `IDENTICAL_DISPLAY_RANGE` | Same display range, or confluence fully contained by an already rendered structural range | suppress the repeated numbers and retain a short auxiliary-confluence label |
| `MATERIAL_RANGE_EXTENSION` | Ranges overlap and the confluence extends outside the rendered structure | render the complete registered confluence range |
| `DISTINCT_RANGE` | No overlap with an already rendered structural range | render the complete registered confluence range separately |

The policy uses raw overlap, raw containment, and existing display strings. It does not introduce
a percentage tolerance or alter raw boundaries. Fib reference-only evidence and ineligible families
remain absent from the short block.

## Safety

Fib/SR is described as structural overlap or auxiliary confirmation. It is never a target, stop,
or certain reversal. Every displayed range retains its v3 zone ID and source references.
