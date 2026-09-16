# Thesis Monitor — M12CG-R3 Native Delivery Offline Proof & Finalization Ownership Trace

**Work-instruction revision: R3-REV2 (2026-09-16).** Same task M12CG-R3; this is not R4 and does not change any runtime/model contract version. This revision supersedes the earlier R3 instruction for execution. The required repository base, safety restrictions, source bundles and existing proof obligations remain unchanged. Changes clarify completion boundaries and prevent serial re-auditing or scope growth; they do not authorize new runtime work or waive a gate.

## 0. Decision and bounded authorization

This is an **offline execution-proof and exact ownership-diagnostic task** after M12CG-R2, not another symbolic repair, a new receipt architecture, a numeric-policy repair, a Full22 run or deployment.

Work instruction: `20260916-m12cg-r3-native-delivery-offline-proof-and-finalization-ownership-trace-revised.md`.

Result bundle: `thesis-monitor-20260916-m12cg-r3-native-delivery-offline-proof-and-finalization-ownership-trace-report.zip` and matching `.sha256`.

Chat decisions:

1. Accept R2's targeted result `M12CG_R2_GUARD_REPAIR_PASS_OFFLINE_CLOSURE_PENDING`. Freeze the presence guard; do not relabel R2 or prior results as complete migration PASS.
2. Explicitly authorize execution of the **existing native delivery path using an isolated, in-process test transport sink and temporary state**, with real network and production actions blocked. This was already allowed in R2 section 9; there is no additional user-approval prerequisite for the bounded test defined here.
3. Preserve actual native ownership. The orchestration sidecar is not automatically a trusted acceptance receipt. Do not invent a bridge to `canonical_acceptance_receipt_service`, a new ledger, a new dedupe key or a new trust policy.
4. Obtain an exact numeric ownership trace for the two existing GOOGL/HUT finalization failures. **Diagnosis is authorized; application runtime repair is not.** All-subject final acceptance remains a required closure gate, not an optional goal.
5. Correct only test/audit harness and reporting defects, including fail-open aggregation and untyped negative-test assertions.
6. Application source/config behavior changes **0**; external model calls **0**; Full22 generations **0**; production sends/intents/mutations **0**. Return results to Chat even if all offline checks pass.

A real runtime, trust, identity or numeric ownership defect must produce a minimal reproducer and a separate bounded repair proposal. STOP means no unauthorized repair and no dependent PASS claim; it does not by itself cancel other safe, independent diagnostics. Finish the independent workstreams below within this same authorized execution when isolation and source integrity remain valid.

## 1. Sources and mandatory preflight

The package contains eight unmodified result ZIPs and their original sidecars under `sources/`, plus a source index, previous R2 instruction and Chat review. Review artifacts are indexes and analysis, not replacement evidence owners. Never rely on a stale `/tmp` or `/Users/...` path; bind by original SHA and package-relative path.

| Phase | Result ZIP SHA-256 | Declared payloads |
|---|---|---:|
| M12CB | `86d9a40debc253b1a2a155fe260962f701274bc7a75d17bf3c744ab3871bcddb` | 262 |
| M12CC | `7b4a09d651fc47d400831ddff603d4ce8b8cd2310674a31e07cd0b2b2fa728fd` | 114 |
| M12CD | `89d51179aca722ce38b282c51d3fedb34ea6446df8c6c6ea71bb8e5cf74951ff` | 89 |
| M12CE | `512c428bbb01c9ae0834cf0d79d01a330095f67553410f854e296bf9d94c07f9` | 112 |
| M12CF | `4375203ad1268fae87b79c88c00607e25849651e32961a87b0b73c537e8a1846` | 46 |
| M12CG | `ad8a75edb25d88220cb59d61919a9ba7c86278362b4bac2d30193092e14d06e8` | 42 |
| M12CG-R1 | `55b2c890fedad3b5b09e5995862637d040f69db882745bfdddfa30d1d38c191f` | 86 |
| M12CG-R2 | `58dbbca3dda5d90d734167c0273de9b7b086de4d47bc43beb5e4f28a6e2cc279` | 173 |

Run `python verify_package.py` from the extracted package. It performs byte verification only, not repository/model execution. Independently confirm source SHA, ZIP CRC, path safety, no duplicates, every manifest hash/size and no extras other than the manifest itself. Missing or corrupt required sources => `M12CG_R3_SOURCE_OR_BASE_FAILURE` before executing a proof.

Historical outputs/generation verdicts remain immutable. Imported scripts are references until inspected for network/model/production paths; never execute an old Full22 script to recover evidence. Preserve source hashes and transformation logs for all ephemeral controls.

## 2. Exact base and frozen contracts

| Role | Value |
|---|---|
| Repository | `sskim-ai/thesis-monitor` |
| Required base / R2 final docs | `f15f299c668787171742aa1beda22415cc4e7537` |
| R2 guard implementation | `50dcec1a56a81db1ebc7e23a322e69f9b028323a` |
| R2 audit implementation | `4cb2cf5fe048b82b5722c8ac45d93d6baccd7263` |
| R2 instruction Git commit | `a141e2711beedf43b1046369b4e821b2544abbdc` |
| R2 instruction content SHA-256 | `368cf3f109c656f15455434261005f1d581c75e81e2e813faafd88cec9f53c07` |
| Before-guard runtime | `b7e541b6a3c54567018f937f32d6f92be09a7e4e` |
| Exact pre-M12CG control | `912b1ce6c46f0caf801b2c620b42d904b489c4e7` |
| Last supplied origin-main observation | `9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479` |

The origin entry is historical observation, not a new remote check. Record any current repository observation separately; do not fetch/merge/push merely to update a label. Distinguish 40-character Git commits from 64-character content digests.

Create an isolated clean local worktree/branch from the required base; suggested branch `codex/20260916-m12cg-r3-native-delivery-offline-proof`. Verify ancestry and application/config hashes. Do not reset others' worktrees or alter the operating checkout. Unexpected runtime divergence => STOP.

Frozen contracts:

- raw Stage-2: `v2-accepted-stage2-model-output-v2`;
- normalization: `stage2-maturity-as-of-deterministic-v2`;
- accepted output: `v2-accepted-production-output-v2`;
- artifact: `v2-accepted-production-artifact-v2`, legacy v1 explicitly dispatched;
- model authors neither `as_of` nor `provenance_status`, including null/correct values;
- concrete-only and mixed: existing same-row ticker-local concrete MAX;
- valid symbolic-only: JSON null with `SYMBOLIC_ONLY_NO_CONCRETE_DATE`;
- scalar meaning: `LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE`, never an absolute full-row cutoff;
- required nullable producer keys must exist and explicitly contain JSON null. Missing/invalid provenance is not symbolic success.

No version bump, producer-policy change, placeholder eligibility promotion, fallback date, field rewriting, or symbol/ticker-specific production exception.

## 3. Closure ledger and precise denominators

Carry forward closed findings instead of restarting earlier design audits:

- R2 changes one application classifier with three presence checks. Required missing metadata is rejected; valid explicit null and concrete/mixed behavior are preserved.
- Historical inventory: 62 rows / 20 snapshot candidates / 7 batches, including one original negative candidate. R2 ephemeral normalized candidates are valid; this does not make the original 010120 output valid.
- Fresh M12CE available outputs: 42 rows / 9 subjects / 3 Stage-2 batches, not a completed Full22. Original M12CE remains terminal at call 8.
- Chat compared all 46 submitted before/after payload file pairs byte-for-byte: 27 historical (7 batches + 20 candidates), 19 fresh (3 batches + 9 candidates + 7 artifacts). No differences.
- Fresh raw and normalized candidate semantics match after removing only the two runtime fields; all 9 raw candidate excerpts match the original M12CE batch bytes structurally.
- R2 guard probe reports 14 G fixture IDs / 47 observations. Its P/N matrix has **35 fixture IDs**, not 35 exhaustive variants: 34 reported PASS, N17 partial. Do not conflate IDs, variants, node IDs, candidates, rows and batches.
- Successful R2 finalizations: 7; legacy/R2 paired finalization/renderer comparisons: 6; GOOGL/HUT downstream failures: 2. The SKHY symbolic row has no old accepted baseline.
- R2 native artifact test covers a reduced ephemeral CORZ packet; the harness explicitly rebound its source-packet hash. It is not an untouched original full-packet operational proof.
- Actual delivery route and test transport sink were not executed. State roundtrip PASS does not imply delivery continuity or no duplicate intent.

Preserve the 010120 original `2026-09-15` versus same-row owned `2026-08-12` negative. Keep original/ephemeral/new-contract verdicts separate. Do not modify old source files or restore an obsolete blocker.

### 3.1 Three fixed workstreams; no new feature redesign

The entry/holder-axis design, approved provenance representation, concrete MAX policy and repaired presence guard are **frozen at their previously demonstrated scopes**, not declarations of complete 22-subject acceptance. Carry their evidence forward. A downstream numeric rejection or an unexecuted delivery test does not by itself reopen them.

| ID | Existing open workstream | Completion required in R3 | What completion does not imply |
|---|---|---|---|
| W1 | GOOGL/HUT finalization ownership trace (section 9) | Both failures have exact text/token/JSON pointer/ref/registry/predicate inputs, source and caller ownership, classification, and a minimal reproducer. A demonstrably wrong harness invocation may be corrected through existing APIs. | A complete diagnosis is not accepted-plan PASS; any required runtime repair remains separately authorized. |
| W2 | Native delivery/binding/continuity offline proof (sections 4–8) | Execute the applicable D01–D14 cases through the existing owner and isolated sink. Otherwise identify the exact unsupported call path, missing authority or isolation dependency with executable evidence. | Diagnostic completeness about a missing path is not operational proof or permission to build a bridge. |
| W3 | Proof-harness correctness (section 10) | Repair aggregation, variant coverage and expected-exception handling; prove negative and all-pass controls; regenerate reports from executed child results. | Green aggregate/unit tests cannot substitute for W1/W2 execution or close unproven variants. |

Map every planned test or diagnostic to W1, W2 or W3 before running it; sections 1–2 and 11–12 remain shared integrity, neutrality and safety guards. Keep the original detailed obligations, including N17 and applicable D14 cases. Do not add a fourth workstream, new product feature, broad refactor, new receipt/ledger policy or a fresh architecture survey inside R3.

Reuse verified code/history evidence and compatible test fixtures rather than repeating a closed discovery phase. Regression execution is still required where prescribed; reuse is not permission to skip full/focused suites or substitute old results for a newly measured boundary. Reopen a closed finding only when a reproducible counterexample on the exact frozen runtime directly contradicts its stated scope. Then mark only the affected finding `CONTESTED_BY_NEW_EVIDENCE`, preserve its historical result, and return the evidence to Chat without unauthorized application changes.

### 3.2 Completion layers and honest status carry-forward

Report these layers independently in the existing closure ledger, program completion and result MD; do not add another parallel reporting framework:

| Layer | Required distinction |
|---|---|
| `closed_design_and_repairs` | List the already-closed design/repair findings, source SHA and proven scope as `CARRIED_FORWARD_VERIFIED_AT_STATED_SCOPE`; do not call the whole entry/holder feature fully integrated. |
| `offline_acceptance_integration` | Actual Stage-2, finalized-plan and comparable-renderer counts/identities; retain 9/7/6 as the observed starting evidence, not hardcoded targets. Keep GOOGL/HUT failures explicit until validly resolved. |
| `offline_operational_proof` | Executed native binding, sink, state, continuity and duplicate-event guarantees, plus precise NOT_PROVEN dependencies. |
| `fresh_full22_proof` | `NOT_RUN_IN_R3`; no inherited/offline row is a new model proof. |
| `deployment_authorization` | `NOT_AUTHORIZED`; independent of every other layer. |

For each layer record `status`, `evidence_origin` (prior verified / newly executed), input and runtime hashes, measured denominator, and blockers. `FAIL` means an executed requirement was violated; `NOT_RUN` means it was not executed; `NOT_PROVEN` means evidence is insufficient; `BLOCKED_BY_DEPENDENCY` identifies the missing predecessor. An expected negative rejection or a successfully reproduced defect is not a successful production behavior. No skipped/missing layer may aggregate to PASS. The existing terminal codes in section 16 stay unchanged.

### 3.3 Dependency-aware stopping and one consolidated decision packet

Establish a small W1/W2/W3 dependency matrix at preflight. After a blocker, stop its dependent acceptance/proof steps and any unauthorized fix, but complete other authorized, safe, independent diagnostics in the same execution. For example, delivery isolation failure must not prevent the local numeric trace or pure aggregation tests; a GOOGL/HUT rejection must not prevent an independently valid batch from exercising the sink. Never relabel a rejected whole batch as successful by selecting only a passing subject.

A common source-integrity/base failure, failed safety isolation, or another shared dependency does stop all affected execution. Mark downstream tests blocked with that dependency; do not count each blocked test as a separate runtime defect. This rule changes no formal Full22 first-hard-failure policy: no model generation runs here.

The final `complete-blocker-ledger.json` must group findings by demonstrated causal owner, not by the number of downstream failed assertions. Each open item needs its W1/W2/W3 mapping, category (`RUNTIME`, `HARNESS`, `COVERAGE`, `ARCHITECTURE`, or shared `SOURCE_OR_ISOLATION`), exact gate/fixture, input hashes, minimal reproducer, confirmed facts versus hypotheses, affected completion layer, completed independent work, and the smallest missing repair or measurement. State why the missing step could not be completed under this authorization; do not return only “another audit is needed.” Genuine uncertainty remains NOT_PROVEN with a precise missing observation; do not invent a cause to complete the report.

Unrelated improvements are `OUT_OF_SCOPE_BACKLOG`, not new R3 acceptance requirements. A newly demonstrated safety/identity problem that actually violates an existing W1/W2 requirement remains a blocker even if repair is out of scope. Never hide it as backlog, waive it, or broaden the patch. Return one consolidated proposal covering the concrete unmet dependencies, for Chat prioritization; no automatic R4, proof rerun or deployment. This is not a promise that no further defect can be found.

## 4. Isolation and test-sink authorization

This task **must attempt the supported existing operational route**, not repeat only a parser/state test. Before calling it, establish executable isolation:

1. Use temporary settings and paths confined to a fresh test root; never read production credentials or mutate persistent user data. No operating scheduler or real send configuration changes.
2. Block network egress for every path that could contact models, broker gateways, market providers, Telegram/email or other remote transports. A deliberate connection attempt must fail the isolation guard without reaching the network.
3. Replace only external transport/provider I/O with an in-process capture sink or existing test double. The sink records attempted test messages/requests and returns controlled success/failure. No real recipient identifiers or tokens.
4. Keep canonical artifact acceptance, hashes, versions, claim/packet binding, dedupe, orchestration and state-transition logic real. Do not replace those functions with always-success stubs.
5. Provide an eligible positive control that demonstrably reaches the sink. An always-suppressed route cannot prove dedupe or invalid-input protection.
6. Count test sink invocations, test logical intents and test state transitions separately from production sends/intents (always zero). Offline repeated invocations for idempotency are allowed and are not model retries.
7. If the supported path cannot be isolated without application changes or a missing dependency, stop that workstream with `M12CG_R3_NATIVE_ROUTE_ISOLATION_DEPENDENCY`, exact call site and minimal missing requirement. Do not claim lack of user authorization; permission for the isolated test is explicit.

No network exception, live dry-run endpoint, broker credential, real Telegram send or production ledger access is authorized. Creating a test transport double is allowed; creating a new production ledger/bridge is not.

## 5. Trace the actual operational owner first

Inspect current canonical callers and Git history before adding a harness adapter. Known search targets:

- `app/jobs/accepted_decision_v2_runtime.py::validate_output` and any actual invoking job/claim owner;
- `parse_accepted_v2_production_artifact` / `load_accepted_v2_production_artifact`;
- `app/services/ai_assisted_delivery_service.py::_load_delivery_accepted_v2` and its actual caller;
- actual delivery orchestration, split-message handling, success/failure handler, lock/claim/intent/duplicate checks;
- `advance_accepted_v2_state` / state loader/writer and when they are called;
- native orchestration sidecar `v2-accepted-production-receipt-v1` versus any genuine trusted finalization receipt.

Produce an exact file/symbol/line/source-hash call graph from entrypoint to transport and state update. Follow dynamic/imported callers; absence of one direct service reference does not prove absence of an upstream authority. Trace only the selected existing route, without redesigning unrelated legacy routes.

Identify the existing logical delivery event key, scope, store, issuer, concurrency behavior and state transition rules. Distinguish candidate/plan hashes, packet/claim IDs, event IDs, transport message IDs and post-delivery accepted state. Determine which component, if any, actually enforces dedupe. No naming-based assumptions.

Classify the route:

- `EXISTING_NATIVE_OPERATIONAL_OWNER_SUPPORTED`: execute it under section 4.
- `EXISTING_UPSTREAM_OWNER_REQUIRED`: include that already-existing owner in the isolated test; a loader-only call is insufficient.
- `MISSING_REQUIRED_NATIVE_INTENT_OR_TRUST_OWNER`: return `M12CG_R3_REQUIRED_NATIVE_INTEGRATION_DESIGN_DECISION`. Do not manufacture a new owner or mark absence as not applicable.
- `UNRESOLVED_NATIVE_ROUTE`: give exact missing evidence; remain NOT_PROVEN.

A service-specific `CanonicalAcceptanceReceiptV1` test may be not applicable to the accepted-v2 route only with explicit requirement-to-actual-owner mapping. That does not waive artifact integrity, trust, version isolation, persistence or duplicate-intent obligations.

## 6. Source-faithful fixtures and scope

Use matched immutable source context/Core/raw/packet/claim snapshots to build **ephemeral outputs under the frozen runtime**. Export full input packet and resulting artifacts with hashes and exact transformations. Replay is offline evidence only, never a fresh generation or historical verdict rewrite.

Prefer the existing complete M12CE batches whose candidates actually finalize, including concrete cases and the MU/RXRX/SKHY batch with the symbolic limitation. Keep original batch membership and order. The GOOGL/HUT/IBM batch has a known finalization failure and must not be relabeled a successful whole batch by selecting IBM alone.

Where native fixture execution requires test-scoped path/recipient/settings translation, separate transport scope from evidence identity. Do not silently rewrite packet/claim/source hashes or accepted identities to make a loader accept mismatched data. An officially supported canonical subset projection or synthetic generic fixture is allowed only when fully labeled and regenerated consistently through existing APIs. It does not prove original whole-batch coverage.

For same-version repetition, metadata-only v1→v2 transition and legacy coexistence use genuine versioned control artifacts and established compatibility paths. Never label an R2 payload v1 or remove semantic fields to construct a fake baseline. SKHY symbolic-only has no valid old normalization; do not invent its old accepted artifact.

Keep valid source evidence and semantic fields unchanged. The test may temporarily inject invalid metadata/content into separately labeled negative copies only. No changes to financial facts, cited refs, decision axes, decisive claims, BusinessDelta or maturity meaning to pass acceptance.

## 7. Native delivery, continuity and binding matrix

Define expected behavior **before execution** from the actual canonical policy and the existing logical event scope. Do not define a new dedupe policy in a test. If that policy is absent or ambiguous, return the architecture decision rather than inventing expected values.

Required cases, with each actual boundary and denominator reported:

| ID | Offline case | Required evidence |
|---|---|---|
| D01 | Eligible matched concrete artifact | Actual route reaches capture sink; correct block/source/claim; real post-success state transition |
| D02 | Eligible symbolic-only SKHY limitation | Null/status preserved; exact five rows/decisive meaning retained upstream; correct rendered content and canonical state |
| D03 | Mixed provenance fixture | M12CD concrete MAX retained; mixed status not discarded; same semantic outcome |
| D04 | Repeat same logical event/key after success | Existing dedupe/idempotency rule observed; capture sink/intent/state counts demonstrate no unintended duplicate for that event |
| D05 | New independent authorized test event | Canonical route does not always suppress; distinguish legitimate new daily/event delivery from a duplicate |
| D06 | Transport failure before success | Existing failure handling observed; no false successful delivery/accepted-state advancement |
| D07 | Failure then re-entry under same event | Existing replay/recovery policy, correct count/binding; no invented retry policy |
| D08 | Metadata-only version change within same logical event | Existing continuity/key policy handles version/hash differences without an unintended duplicate or semantic delta |
| D09 | Legacy/new artifact coexistence | No incorrect overwrite or cross-version authorization; proper version dispatch and preserved legacy bytes |
| D10 | Wrong packet/claim/market/date/subject/source hash | Actual consumer gate rejects/safely suppresses according to existing policy; no invalid block reaches sink or state |
| D11 | Modified candidate/accepted-plan/block/status/version | Trace actual authoritative protection, not only a schema parse; exact rejection/suppression and stage; no whole-plan/default rewrite |
| D12 | Missing/swapped/forged diagnostic sidecar | Demonstrate actual disposition; cannot authorize invalid artifact or override authoritative verdict |
| D13 | Genuine authoritative receipt/artifact swap, where that owner exists | Existing authority rejects mismatch; not matching a diagnostic sidecar as a substitute |
| D14 | Chunked/partial send, crash window or overlapping claim, if supported by selected route | Exercise existing handling; report actual guarantees/limits rather than inventing exactly-once guarantees |

D14's individual variants may be NOT_APPLICABLE only with source/caller evidence that the selected route does not use that mechanism. Concurrency/crash ambiguity relevant to the intended route is an open dependency, not a silent exemption. Do not add recovery logic here.

For every test capture: input/packet/claim/artifact hashes; existing logical event key and key owner; route entrypoint; enabled test-only settings; acceptance boundary; before/after state/ledger/receipt; sink count/content hash; result and exception/gate; retry/re-entry semantics where applicable. Export event traces and full payloads, not just counters.

A same-version frozen-timestamp state equality test proves only state determinism. A distinct daily event may legitimately send unchanged analysis; do not impose "never send identical text" as a new policy. Zero production activity proves safety, not that an unexecuted test route has zero duplicate intents.

## 8. Receipt/sidecar applicability without a fictitious bridge

R2's native proof calls a loader that checks packet/claim/scope/source-packet hash and compares blocks to rendered accepted plans. Its orchestration sidecar carries status metadata, not automatically a cryptographic or canonical trust attestation. A source-packet hash is not itself a signature over arbitrary accepted-plan mutations.

Trace model validators, trusted creation paths, artifact content/plan identity checks and any existing upstream gate before concluding which mutations the real route rejects. Do not infer that the loader excerpt alone proves the entire artifact's semantic integrity, and do not invent a trust defect from that excerpt without the full path.

Split N17 into explicit applicable obligations:

- N17A parser/version/date/status tamper;
- N17B packet/claim/scope binding;
- N17C actual authoritative payload/receipt identity binding;
- N17D diagnostic sidecar cannot elevate an invalid artifact;
- N17E persistence/continuity/operational duplicate control.

If a sidecar is purely diagnostic, a swap may have **no effect** rather than cause rejection; that is a valid result only when the true authority remains enforced. Mark service-specific receipt tests not applicable with the equivalent native-owner evidence; never mark all N17 PASS based only on loader tamper cases. If no applicable native authority exists for a required property, stop with a concrete integration/identity gap.

Use exact expected exception classes/codes or documented safe-suppression states. `except Exception: PASS` is forbidden. Inject an unrelated exception in a harness-only control and show the test does not pass. No runtime error renaming or trusted-issuer bypass.

## 9. GOOGL/HUT exact finalization ownership trace

The known error `adjudication_introduced_unregistered_numeric` remains unresolved at token/owner level. R1 established the same rejection on exact pre-M12CG code; R2 preserves it. That rules out claiming this presence guard introduced the observed rejection, but does not establish the rejection's semantic cause.

For both candidates preserve and bind:

- original batch/raw/context/Core/packet/prior-state hashes;
- Stage-2 validation result and subsequent failing finalization call/stack;
- exact candidate/adjudication/accepted-plan text and JSON pointer evaluated by the numeric validator;
- matched token substring, normalized numeric value/unit, regex or parser owner, and every compared registered value/metric/evidence ref;
- the same-row/claim source ownership, exact evidence statement and canonical registered numeric representation;
- whether the text/value was authored by frozen Core, Stage-2, deterministic composition, existing adjudication adapter or the harness;
- input to the rejecting predicate and its evaluated result, captured by observer-only instrumentation.

Run the same immutable input on the current frozen runtime and the exact pre-M12CG control if needed to trace the owner; reuse verified baseline artifacts as context but do not substitute error-name parity for the trace. Read Git history of the real validator and callers before suggesting a change. Do not search public prices or use external model reasoning to replace source evidence.

Classify each failure, allowing multiple evidence-backed causes:

- `GENUINE_MODEL_AUTHORED_UNREGISTERED_NUMERIC`;
- `FROZEN_CORE_REVALIDATION_SCOPE_FALSE_POSITIVE`;
- `DETERMINISTIC_COMPOSITION_OWNERSHIP_MISMATCH`;
- `CANONICAL_NUMERIC_REGISTRY_PROJECTION_GAP`;
- `HARNESS_CONTEXT_OR_IDENTITY_MISMATCH`;
- `UNRESOLVED_NUMERIC_OWNERSHIP`.

Do not preselect a false-positive explanation because an earlier numeric issue was fixed. Do not reopen M12CB's Stage-2 scope repair, preconfirmation BUY, price-confirmation isolation or numeric strictness merely because the error also involves a number.

If the fault is strictly a proof-harness misuse of an existing API, an evidence-backed harness correction is in scope: preserve the old invocation/error and demonstrate unchanged raw evidence/semantics under the proper existing owner. If a production validator, registry, composition or source policy must change, **STOP before fixing runtime** with the narrow caller/contract-specific proposal and required regression fixtures. Never strip a number, add an arbitrary registered value/ref, rewrite a candidate, widen a regex, suppress an error, force an adjudication or ask a repair model.

Successful diagnosis does not make the candidate accepted. Report accepted-plan coverage separately and keep all-subject acceptance blocked while either required candidate fails. A genuine historical model violation remains a negative fixture; changing positive-inventory expectations requires an explicit later Chat decision.

## 10. Complete the proof-harness contract

R2's reporting improved but direct isolated execution of its bundled helpers exposed these counterexamples:

- `aggregate_fixture_rows([])` returns PASS;
- missing assertion status, literal `SKIPPED` and `NOT_RUN` can return PASS;
- `matching_nodes` plus `test_ok` can accept one passing match while another required pattern has no executed node;
- native negative wrapper treats any exception as rejection success;
- 35 original IDs are labeled `fixture_variant_count`, obscuring actual parameter coverage.

These findings concern test/audit code, not a new application guard defect. Preserve original evidence. Fix the existing harness without starting a parallel acceptance/validation owner.

Required behavior:

1. Supply explicit expected fixture IDs and variant/node manifests. No empty inventory may close a nonempty required gate.
2. Missing ID, duplicate ID, missing status, unknown status, null row, missing/zero denominator, no evidence, skipped/not-run/unmeasured child => never parent PASS. Preserve NOT_APPLICABLE only with an approved owner-specific disposition and equivalent evidence where required.
3. Match exact node IDs including parameter IDs, or expand an explicitly enumerated declared pattern and verify **each required match/variant**. One test cannot stand in for an absent sibling. Verify collection inventory separately from JUnit execution.
4. Each fixture has expected predicate/gate, observed runtime result, assertion outcome, source/runtime SHA, node/record ID and actual scope. Do not fill `observed_result` from the final assertion label.
5. For compound requirements track subvariants. In particular a test of concrete null rejection is not proof of mixed null rejection; another state's forged status is not every possible status/date pair. Reuse proven tests, add only missing intended assertions, and distinguish fixture-ID readiness from variant readiness.
6. Aggregate directly from children, not hardcoded final status or `forced` success. A conservative pending disposition may remain while its dependency is genuinely unexecuted, but readiness must become data-driven when results exist.
7. Negative success requires the intended class/code or documented safe-suppression gate. File-not-found, TypeError, AssertionError, transport setup failures and unrelated exceptions cannot stand in for validator protection.
8. Unit-test the aggregator with missing/empty/skipped/unknown/conflicting/duplicate inputs, absent parameter variants and unrelated exceptions. Include an all-pass positive control. Record concrete expected vs actual results.

The previously implemented N16 decisive-row deletion and N22 polarity controls stay; do not replace them with aggregate label equality. No full-suite result may silently satisfy an individual migration assertion.

## 11. Valid-input neutrality and preserved proof

No application edits are authorized. Verify all application/config file hashes unchanged at start/end and compile the exact diff path list. Test settings/monkeypatches must not persist beyond isolated fixture contexts.

Reuse the verified historical 62 and fresh 42 normalized baseline payloads and source map. Compare actual new outputs from every re-exercised canonical path to the frozen R2 baseline at the correct scope: complete normalized candidate, claims/refs/row order, Core hashes, accepted plan semantics, renderer, identities and state. No invented zero for an unexecuted boundary.

For model-facing parity, keep the reported three fresh-batch hash comparison scoped to those builders. Export actual before/after prompt/schema/catalog bytes where re-exercised, so an independent reviewer can check equality. Do not claim historical builder byte coverage solely from normalized payload equality. Do not invoke a model for schema verification.

If an apparent valid-input difference comes only from harness clock/serialization/path setup, explain and reproduce it with identical legitimate inputs; do not normalize away authoritative data. A real application semantic/identity change or materialization failure outside the pending scope => STOP, no opportunistic runtime repair.

## 12. Market and successful-contract freeze

Do not reopen the presence guard, symbolic R2 policy, concrete MAX semantics, frozen-core numeric scope, standalone numeric strictness, preconfirmation BUY, BUY/WAIT/HOLDABLE independence, maturity atomic polarity/eligibility, Fundamental Core batch identity/immutability, exact-ref fidelity, typed primitives, post-confirmation HOLD, expectation/valuation separation, BusinessDelta or Persistence V2 authority.

Treasury: provider FRED; nominal DGS3/DGS5/DGS10/DGS30; real DFII10; breakeven T10YIE; historical renderer `4407cd11a78579e11681b503b2d4e72ee3c3d60f`; daily/per-series as-of/bp-change semantics unchanged.

Kiwoom: historical `28f4f70700046f98d5d899ee491d3e5f45922e9a`; KOSPI200 2026-09-01/02/03 replay and local LeadingMarket adapter preserved; KOSDAQ150 actual historical fixture UNVERIFIED. Last gateway status unconfigured/unavailable, READ_ONLY only. Config names `KIWOOM_GATEWAY_URL`, `KIWOOM_GATEWAY_API_KEY`, `KIWOOM_GATEWAY_TIMEOUT_SECONDS`; never print secrets. No gateway configuration, new connector, live read/order/modify/cancel in this task.

No merge to main, remote push, deployment, scheduler start/resume/change, operating checkout change, production database write or real send/intent. Test sink activity is permitted and must be visibly counted separately.

## 13. Execution sequence

1. Verify package/eight source bundles, repository base and clean isolation. Freeze runtime hashes.
2. Carry forward the closure ledger and five completion layers; define the W1/W2/W3 dependency matrix. Correct the prior sink-authorization explanation without rewriting R2. Preserve previously closed design/repair scope.
3. Trace the actual native operational/intent/trust owner and establish section 4's isolation guards.
4. Define expected event scopes/behaviors and granular fixture coverage before running tests.
5. Fix only harness aggregation, coverage and negative-exception handling; execute W3 counterexamples and all-pass controls. Keep subsequent measurements granular.
6. Capture W1 GOOGL/HUT exact numeric token/claim/ref/validator ownership and classify the cause. No runtime numeric fix; do not leave this local diagnosis pending behind delivery work.
7. Execute W2 through the existing native operational route using matched artifact fixtures and the capture sink; record positive, negative, repeat, migration and failure traces. Steps 6–7 may be reordered where justified by real dependencies; safe independent work must not be abandoned after the other stream is blocked.
8. Reconcile the five completion layers, W1/W2/W3 statuses and all-subject acceptance separately. Generate one causally grouped blocker/dependency ledger, not a succession of new task proposals.
9. Run relevant focused/full/frozen suites, Ruff and `git diff --check`. R2 bundled baseline: 4120 full passes/63 skips, focused210/1, Treasury79, Kiwoom70. Explain legitimate selection/count changes; no test deletion or skip inflation.
10. Freeze audit implementation and final docs commits separately; generate granular reports/full payloads, manifest and ZIP SHA. STOP for Chat.

Normal local red/green harness tests are allowed. A runtime integration/guard/identity/numeric defect is not permission to expand the task. Apply section 3.3: complete safe independent non-mutating diagnostics after a scoped stop, but stop all affected execution on a shared safety/source/base failure. Never call models to obtain new evidence.

## 14. Required artifacts

Include full reproducible scripts with source/repo/output-root arguments, no stale-path-only inputs. At minimum:

- `source-and-base-integrity.json`;
- `runtime-freeze-and-diff.json`;
- `closure-ledger-and-authorization-correction.json`, including the frozen findings, five completion layers, W1/W2/W3 mapping and dependency matrix;
- `native-route-owner-call-graph.json` plus full relevant source/caller excerpts;
- `logical-event-key-and-intent-owner-contract.json`;
- `test-isolation-and-network-denial-proof.json`;
- `native-fixture-source-and-transformation-manifest.json`;
- `native-delivery-case-matrix.json` (D01–D14 with granular applicable variants);
- `native-sink-event-traces.jsonl`, state/ledger snapshots and authoritative payloads;
- `same-event-idempotency-and-new-event-positive-control.json`;
- `failure-reentry-and-applicable-crash-concurrency-proof.json`;
- `cross-version-continuity-and-authority-isolation.json`;
- `n17-service-specific-to-native-obligation-matrix.json`;
- `googl-hut-numeric-token-claim-ref-owner-trace.json` with actual rejected predicate inputs;
- `prechange-current-finalization-control.json`;
- `numeric-cause-classification-and-bounded-repair-proposal.md`;
- `fixture-id-and-variant-manifest.json`, collected/executed node IDs and exact assertions;
- `aggregation-counterexamples-before-after.json`;
- `native-negative-expected-exception-matrix.json`;
- `valid-input-semantic-byte-hash-parity.json` and actual compared files;
- `model-facing-byte-proof.json` plus any compared prompt/schema/catalog files;
- `coverage-and-denominator-matrix.json`;
- `focused-full-frozen-test-results.json`, commands/exit codes/logs/JUnit;
- `safety-counters.json`;
- `complete-blocker-ledger.json`, grouping causal blockers and dependent unexecuted checks, with minimal reproducers and a single bounded follow-on proposal;
- `program-completion.json`, result MD and next bounded proposal;
- `artifact-manifest.json` (relative path, size, SHA; explicit self-exclusion), external ZIP SHA sidecar.

No aggregate-only receipt/delivery proof. Export before/after raw copies for each negative transformation with JSON pointers and hashes. Reduced/synthetic controls must be labeled. Do not include credentials. All original artifacts and historical terminal verdicts remain unchanged.

## 15. Program completion and measurement integrity

Required fields include:

`top_level_result`, `required_base_sha`, `frozen_guard_runtime_sha`, `instruction_git_sha`, `instruction_content_sha256`, `audit_implementation_sha`, `final_local_sha`, `runtime_changed_files`, `runtime_source_change_count`, `source_bundle_count_verified`, `prior_sink_authorization_correction`, `native_route_classification`, `logical_event_key_owner`, `native_intent_owner`, `test_isolation_result`, `network_attempts_blocked`, `actual_native_delivery_route_executed`, `test_sink_invocation_count`, `test_logical_intent_count`, `test_state_transition_count`, `native_authoritative_binding_result`, `diagnostic_sidecar_disposition`, `same_event_duplicate_result`, `new_event_positive_control_result`, `cross_version_continuity_result`, `failure_reentry_result`, `applicable_crash_concurrency_result`, `native_n17_subobligation_results`, `googl_numeric_cause`, `hut_numeric_cause`, `numeric_trace_complete_count`, `numeric_runtime_repair_required`, `stage2_valid_subject_count`, `finalized_subject_count`, `failed_finalization_subject_count`, `accepted_plan_coverage_complete`, `fixture_id_required_count`, `fixture_variant_required_count`, `fixture_variant_proven_count`, `missing_node_or_variant_count`, `unknown_status_count`, `unexpected_exception_count`, `aggregation_counterexample_result`, `valid_input_semantic_change_count`, `valid_input_hash_change_count`, `model_facing_byte_comparison_denominator`, `model_facing_byte_delta_count`, `native_offline_proof_status`, `offline_migration_compatibility_status`, `complete_blocker_set`, `new_full22_authorized=false`, `message_model_contract_readiness`, `deployment_readiness=NO`.

Model calls/Full22/retry/fallback/judge/repair-model/schema-repair-model/selective-model-rerun/per-ticker-retry = 0. Production sends/intents/DB writes, main merges, deployments, remote pushes, scheduler changes/resumes and Kiwoom live read/order/modify/cancel = 0. Do not confuse nonzero authorized offline sink activity with production send counts.

Every measured zero has a scope/denominator. Unavailable, skipped or blocked results remain NOT_PROVEN/NOT_RUN with a dependency. A complete numeric trace is not a passing finalization. A test assertion that reproduces a defect can pass while the operational property fails; record both.

Add `instruction_revision=R3-REV2`, `completion_layers`, `workstream_statuses`, `closed_finding_reopen_events`, `causal_blocker_count`, `dependent_blocked_check_count`, `independent_work_completed`, and `out_of_scope_backlog`. Keep these inside the existing artifacts, generated from granular evidence, not a second acceptance system. An unchanged frozen finding is carried forward, not marked as freshly re-proven. The opening result summary must state: what was already closed; what R3 actually executed/closed; what remains and at which layer; and whether another bounded repair or missing measurement is required. Never summarize an unexecuted delivery test as “entry/holder judgment failed.”

## 16. Terminal results and later authorization

- `M12CG_R3_NATIVE_DELIVERY_OFFLINE_PROOF_PASS_FINALIZATION_GAP_REMAINS`: native owner/sink/binding/continuity/dedupe obligations and harness requirements proven, numeric cause traced, but all-subject finalization remains unresolved. No whole-migration PASS.
- `M12CG_R3_REQUIRED_NATIVE_INTEGRATION_DESIGN_DECISION`: a required native authority/intent/trust edge does not exist or needs application change. Exact owner/caller/counterexample required; no new bridge here.
- `M12CG_R3_FINALIZATION_OWNER_REPAIR_REQUIRED`: exact numeric/composition/registry application repair required; no repair implemented in this task.
- `M12CG_R3_OFFLINE_PROOF_NOT_CLOSED`: remaining isolation/harness/coverage/ownership dependency with measured partial results. Do not rerun broad inconclusive audits without a specific missing path.
- `M12CG_R3_OWNER_SCOPED_OFFLINE_CLOSURE_PASS`: only if all applicable native and all-subject acceptance/compatibility requirements are genuinely closed using existing canonical behavior plus authorized harness corrections, no hidden waiver or runtime change. Still no model/deployment authorization.

All results return to Chat with `new_full22_authorized=false`. The guard remains closed unless direct contrary runtime evidence appears; do not regress to symbolic date fabrication or row removal. A completed W1 diagnosis may be recorded alongside a remaining application repair; it cannot close offline acceptance. A W2/W3 PASS must not be reset to FAIL solely because W1 remains open. Overall readiness still stays blocked whenever a required layer is not proven. Preserve existing terminal outcomes rather than inventing another “whole feature failed” status.

Subsequent sequence: offline closure or separately approved repair → Chat → separately authorized entirely new US14/KR8 Full22 from call 1, no reuse/stitch/retry/fallback/judge/repair/selective/per-ticker rerun → Chat → Kiwoom read-only gateway verification → Chat → current US/KR market plus monitored-stock message smoke → independent human judgment using collected facts before consulting AI verdict → AI comparison → separate deploy/automation decision.

No PASS authorizes main merge, deploy, scheduler resume or real send. Architecture and scope decisions remain in Chat; Work/Codex executes this bounded task only.
