# Fresh Shadow Prerequisites

REV58A is an offline prerequisite repair. It does not collect sources, invoke a
model, enable B2 v2, replace an assessment or authorize delivery. The operating
checkout and production scheduler remain untouched.

## Retry Ownership

`Us14Execution.invoke` is shared by `Rev46Kr8Execution`. Each physical attempt
first persists raw response bytes and a hash-bound raw receipt. Wire and internal
response-form schemas are checked next; the unchanged stage owner then evaluates
local semantics. The final attempt receipt records both statuses independently.

- `TRANSPORT_OR_RESPONSE_FORM_FAILURE`: only the existing transport allowlist
  or malformed/missing/schema-invalid responses may use the existing retry cap.
- `LOCAL_SEMANTIC_VALIDATION_FAILURE`: a schema-valid response rejected by local
  validation stops that logical request without another sample.
- `SYSTEMIC_FAILURE`: an existing systemic failure, prelaunch failure or unexpected
  controller exception stops immediately. It is never reclassified as retryable.

Raw responses, semantic receipts and per-attempt receipts survive rejection.
Rejected partial in-memory stage state is rolled back. Independent batch sweep
behavior is unchanged. Model, effort, schemas, prompts, 600-second timeout, batch
topology and maximum two response retries are unchanged.

## Source-Only Coverage

`scripts/newbuyer_b2_v2_coverage.py` exposes explicit `SourceOwners`, `seal_inputs`
and `compose` APIs. The caller supplies a cohort, per-subject source generations,
collection receipt hashes, assembled source packets, security master records,
native valuation receipts, business quality receipts and, for KIS, the source
plan, source view and raw-bound availability observation. An issuer business
bridge supplies its separately selected business projection. It grants no
security-valuation transfer rights.

No Core, A, B, Overall, Holder, blind-label or historical report-path argument is
accepted. Source generations, security identities, packet/owner hashes, source
time, decision versions and field eligibility are verified before composition.
The selected business-quality owner is independently replayed. Source input seals
bind bytes but never manufacture a financial verdict.

`newbuyer_coverage_cells.py` contains the unchanged reviewed category decisions.
`newbuyer_coverage_dataflow.json` pins the reviewed producer code. A changed
producer cannot silently inherit a non-consumption proof. `PRODUCER_SEMANTICS`
proves only `PROVEN_NOT_APPLICABLE`, never a current QUALIFIED/DENIED state.

The consumer receipt remains `REV56COfflineCoverageReproofV1`. New source-seal
metadata is separate from category semantics. Legacy model references are not
coverage inputs. Census and metric evaluability use the unchanged REV56C/REV56D
functions and are produced only after complete cohort coverage. Incomplete input
either fails explicit validation or returns incomplete coverage with no census.

Normal-empty KIS observations retain request-bound negative identity, not
provider-returned positive identity. The existing availability/scope owner alone
may narrow prerequisites; malformed empty payloads cannot do so. Metric denials
never propagate to independently qualified metrics.

## Future Explicit Orchestration

The next separately authorized fresh run must preserve this order:

1. Seal the bounded source/model execution plan before acquisition.
2. Complete fresh acquisition and seal its exact source corpus.
3. Replay current stock/native/KIS/business owners for each new source generation.
4. Call `seal_inputs`, then `compose`; require the exact 22-subject cohort complete.
5. Preserve the coverage, census and pre-model metric/evaluability receipts.
6. Prepare and run the unchanged US/KR Market/Core/A/B controllers with the
   repaired retry boundary; seal their accepted authority before B2 construction.
7. Build opt-in B2 v2 requests from those new authorities and the same coverage.

Coverage generation is not imported by production and does not automatically
start this sequence. A fresh run remains a separate task. Source provider pacing,
conditional slots and budgets remain owned by the existing sealed source plan.
An unavailable source is not recollected adaptively in response to model output.

Historical replay validates semantic compatibility only; historical packets or
receipts must never be relabeled as a current generation.
