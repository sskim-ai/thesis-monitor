# Strict-Blind Clean-Start Controller

REV59A repairs task orchestration only. `scripts/strict_blind_controller.py` is
opt-in and has no production imports, provider client, CLI launch, delivery or
persistence entry point. Existing source, investment, B2, and blind economic
contracts are unchanged. It must not be confused with a completed live blind run.

## Ownership

REV59C binds an explicit request scope and market into the plan, canonical
envelope, detached authorization, and output seal. Only the registered `MARKET`
stage is `MARKET_SCOPED`; its native US/KR contract requires `subjects=[]`.
Its payload's uppercase market must match the envelope. US and KR native
capture contracts and their committed code hashes are frozen independently of
the unchanged native payload. A fake Market ticker is rejected. Every other
stage remains `SUBJECT_SCOPED`, requiring nonempty exact subjects. No default
scope or empty-subject compatibility fallback exists.

- Canonical requests use the existing UTF-8 sorted JSON serializer. Identity
  includes payload SHA, serialization version, logical ID, generation, stage,
  subjects/batch, exact context refs and prompt/schema/policy hashes. Tuple and
  list representations authorize identically; changed bytes do not.
- A clean root has no failed-ledger dependency. Resume is a separate mode that
  verifies the journal chain, frozen code, sealed artifacts and latest genuine
  retryable receipt. It cannot resume a semantic rejection or incomplete attempt.
- Each stage's exact request set is sealed after its prerequisites. Fixed order,
  complete accepted output sets, immutable artifact hashes and the causal state
  machine forbid backward execution, selective resampling and early reveal.
- Native host qualification remains `qualified_official_launch_context`. Both
  unchanged and predeclared native-allowed transitions work. Its existing
  `(600 seconds, 10 calls, 2 retries)` qualification is scoped to **one logical
  request**, which the controller further limits to three physical attempts.
  Separate predeclared stage caps, including BLIND/B2 caps of 30, are enforced
  across requests. No native policy table or retry taxonomy was relaxed.
- A dispatch authorization binds the immutable stage request set, exact request,
  native host receipt, execution limits and prerequisite seal hashes. Clean-start
  authorizations never cite an old failure. Request bytes are not rewritten.
- Predeclared domain projection adapters can seal their native provider payload
  directly. The controller binds that projection and its input lineage rather
  than wrapping or rewording the existing model input. An executable regression
  uses the unchanged B2 v2 builder and checks byte-for-byte provider-payload parity.

## Isolation

The private controller journal is not a model workspace. Blind views contain
only the allowlist-validated source package and presealed blind authorities.
AI views contain same-generation source/owner/upstream artifacts; the blind seal
API exposes existence and hash, never its content. Context payloads must equal
their declared view. Dependency closure is checked, separate materialized roots
cannot overlap, and symlink destinations are refused.

This is a **declared-input and orchestration boundary**, not an OS sandbox.
A future live runner must independently qualify separate processes/sessions and
their filesystem/tool surfaces. Trusted frozen source-only exporters, economic
builders and validators remain responsible for their own semantics. Synthetic
fixtures are not evidence of their economic correctness or of live host access.

## Freeze And Attempts

Before source admission, seal rubric, schema/prompt, comparison, acceptance,
controller policies, execution plan and source DAG. These are opaque authorities:
the controller cannot reinterpret their economic meanings. Freeze adapter code
before this boundary. Unexpected post-start harness defects require a new repair
revision, never a result-dependent continuation exception.

The strict-run marker is written at the admission immediately preceding the
first future external source call. Offline simulation uses a distinct marker and
cannot dispatch with an external-execution flag. The controller exposes no live
network operation; integration must call admission before the frozen source owner.

Attempts persist authorization, raw bytes and a raw-capture hash receipt before
parsing, provider-schema validation and local semantic validation. Existing
transport/response-form failures alone may retry. A schema-valid semantic failure
is terminal even if a callback incorrectly calls it a response-form failure.
Accepted output seals bind request, raw and validation receipts.
Transport, schema and semantic callbacks must belong to predeclared frozen code;
their exact source/qualified-function identities are attached to authorization.
Even another preexisting callback cannot replace one during a same-request retry.
Source-only and comparison validator code is subject to the same frozen-owner check.

## Offline Proof

`python -B -m scripts.strict_blind_offline_proof NEW_DIRECTORY` exercises the
complete state chain using invented subjects and values. The host evidence is
explicitly synthetic. No official state, source provider or model is accessed.
The test suite includes all 20 required control classes and additional identity,
retry, raw-first, causal-order, view and mutation checks. The proof is not an
automatic authorization to run the next REV59 or to promote production.

`python -B -m scripts.strict_blind_native_market_proof NEW_DIRECTORY` adds the
actual US14/KR8 capture paths, native prompt/schema and native semantic validator
to a complete synthetic lifecycle. Both Market requests preserve native bytes,
authorize detached tuple/list representations, persist simulated raw bytes
before validation, and seal both outputs before Core can start. Source, response
and host fixtures are invented; no live auth, market, or economic qualification
is claimed. Existing host, retry, resume, isolation and reveal negatives still run.
