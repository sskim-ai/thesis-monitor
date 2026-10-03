# Provider-Wire Constant Typing

REV54 repairs the REV53 HTTP 400 at
`properties.new_buyer_shadow.anyOf[0].properties.contract`. The sealed request
used a `const` without an explicit type; the old dialect scanner accepted it.
This was a request-schema failure, not a model investment judgment.

## Ownership

`m12cs_r1_provider_schema.py` owns provider representation. Local B2 schemas,
validators, prompts, business gates, valuation permissions and timing ownership
are unchanged. The default-OFF shadow adapter remains separate from production.

JSON-native scalar constants receive explicit types. Booleans are distinct from
integers; nonfinite numbers and Python-only values fail closed. An explicit
compatible type is retained; a conflicting type raises
`provider_const_type_mismatch`. Additional constraints must be provably compatible
or are rejected for review, never silently discarded.

Object constants become closed objects with every key required and recursively
typed children. Primitive array constants become typed finite item sets with
exact length bounds. Array order and exact membership/multiplicity remain owned
by the unchanged local semantic schema. Local validation is mandatory after wire
validation; the wire schema alone is deliberately not an exact-array certificate.
Complex or heterogeneous arrays require a separate supported lowering design.

Empty arrays need an explicit primitive item type or one of the exact B2 ref-array
paths enumerated by `EMPTY_REF_ARRAY_PATHS`. Unrelated fields do not inherit this
rule. Schema traversal visits `properties`, `$defs`, `items` and `anyOf`, not
arbitrary literal payloads.

The projection receipt records primitive typing, object/array lowering and
owned-empty-ref paths. Existing unique-item removal and shared string-enum
definitions retain their local semantic owners.

## Offline Qualification

The scanner rejects untyped constants, incompatible constant types, unclosed
objects and untyped array items, including nested branches and definitions.
The exact old CORZ schema is a portable regression fixture. An offline PASS is
not proof of live provider acceptance. Official documentation describes a
supported subset and requires closed object properties; the exact missing-type
requirement here is additionally evidenced by the preserved REV53 response.

Reference: [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

## Next Proof

`newbuyer_b2_shadow_failure.request_schema_rejection` classifies structured
HTTP 400 `invalid_json_schema` error events as
`REQUEST_SCHEMA_PROVIDER_REJECTED`, nonretryable. It does not inspect investment
prose or equate authentication, timeout, throttling, server errors or generated
output-validation failures with an invalid request schema.

The REV55 task-local controller is frozen, not executed, in the REV54 result
package. It requires separate execution authorization, exact inputs and runtime
identity, then one accepted CORZ smoke before the remaining 21 subjects.
Model, effort, timeout, retries and physical cap remain sol/xhigh, 600 seconds,
two retries per logical request and 30 caller-controlled CLI attempts overall.
