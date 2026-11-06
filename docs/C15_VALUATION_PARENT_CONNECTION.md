# C15: dated references and remaining live capture contracts

The new `dated_market_component_reference.read_dated_component` is default OFF.
It calls the original `market_component_execution.cold_component`, checks the
original aggregate bytes, session, generation and value digest, and supplies a
dated source-inspection view. It does not issue an economic Owner, restore a live
handoff, supply missing publications/night inputs or construct a Full Parent.
`render_reference` emits a deterministic NO-SEND source preview, not an AI or
investment message. A source reference PASS is not a sealed Market context PASS.

## Kiwoom: explicit valuation Source purpose

Do not change `registered_identity_source_parent.PURPOSE` or its `valuation=False`
receipt. Do not pass that capability into an economic or valuation consumer.

The minimum next implementation is a separate, default-off
`issue_valuation_source_parent` with a versioned Source-only purpose:

1. Require the original current registration/discovery capability and exact KR
   identity set. `KRX` alone is not KOSPI. Use
   `provider_native_valuation_acquisition.routing_markets` with receipt-bound
   official listing rows, not ticker digits or a name guess.
2. Compile with original `provider_native_valuation_acquisition.add_slots`,
   `canonical_source_plan.kiwoom_request`, `FreshRequestDescriptor`,
   `sealed_chart_slots.chart_slots` and original response bindings. Include auth
   in the physical cap. KR8 with two five-page listing bounds and eight basics
   needs at most 19 physical slots including auth, within C15's 24; this count is
   only conditional on legitimate routing and not a live admitted plan.
3. Extend `pending_source_parent.state` with an exact new-purpose branch that
   revalidates the current registration capability, code pins, expiry and
   one-dispatch lifetime. Keep identity-only validation unchanged.
4. Extend `market_component_execution.prepare_capture` with a distinct valuation
   capture mode, not `identity_only=True`. Bind the actual Parent, original
   `ParticipatingSession`, `CurrentScopedDispatcher`, private Worker PID and
   `SealedSourceTransport`. No direct child network, original policy A remains.
5. Add only that exact purpose to `scripts/current_scoped_source_worker.py`'s
   pending handoff and command checks. Permit only auth, ka10099 and ka10001 from
   the frozen descriptors; preserve command receipts and response continuations.
6. After Worker completion, feed actual bound receipts through
   `provider_native_valuation_acquisition.replay_native` and
   `provider_native_valuation_snapshot.derive_provider_snapshots`, then independent
   Cold. The Source purpose itself grants no PER/PBR, EPS, direction or Native use.

Minimum tests: old identity capability still denied valuation; expired/cross-PID
or JSON Parent rejected; no routing inference; listing conflict denied; exact
continuation parent/cursor; hard 24 including auth; STOP/401/403/429 propagation;
child direct HTTP denied; receipt/raw/code tamper; aliases need original reviewed
Owner; Source success with semantic denial; original PER/PBR replay in new Cold.

## KIS: separate raw estimates from full qualification

`scripts.kr8_kis_integration.build_plan` is a full integration: auth 1, estimates 8,
identity 8, then conditional price/action reads. `qualify_estimates` also requires
the identity artifacts, current DART inventory, original documentation, controls
and scale. Calling only the first nine requests cannot satisfy that full Owner.

Implement a separate estimate-Source compiler using the original
`kis_estimate_capability_probe` request/auth routines. It must retain the original
account lock, spacing, return-code/continuation checks and exact raw receipts.
Compile eight exact estimate requests plus optional auth, with retries zero.
Source-only acceptance must explicitly deny qualified FY1/FPER. Qualify those
only when the original `kis_output3_protocol_owner` / `kis_current_fy1_owner` /
`kis_exact_action_guard` parent set is legitimately available; do not substitute
old inventory or omit the shares/action guard.

Minimum tests: exact 9 ceiling including auth; source-only receipt cannot enter
`vnext_kis_research.owner_snapshots`; missing current identity/inventory denied;
estimate date differs from capture date; FY1 period and units preserved; invalid
denominator or action family denied; empty response distinct from zero EPS;
restart Cold preserves original generation and source hashes.

## Finnhub: preserve the original manual capture Owner without DB writes

`add_slots` already compiles profile2 + metric for US14 as 28 optional reads,
retries zero. It cannot be dispatched by `CurrentScopedRequestPlan`, which is
explicitly Kiwoom-only. Do not widen that private Worker to arbitrary hosts.

The existing alternate original path is `vnext_public_capture.PublicTransport`
and `vnext_legacy_reuse.native_valuation_inputs`; both currently depend on SQL
`source_capture` / `research_run` via ResearchStore. C15 forbids unapproved new DB
writes, so this is a storage/receipt connection gap, not a missing user approval
for the already-approved 28 GETs and not a Finnhub outage.

Minimum connection: extract a capture storage interface (`find_capture`,
`record_capture`, `list_captures`, `run_started_at`) with unchanged ResearchStore
semantics and an exclusive file-only archive implementation. Keep
`PublicTransport`'s official host/GET scope, frozen request matching, counters
before I/O, provider-specific hard STOP, secret redaction and TLS verification.
Prove the original account lock/participation scope before live GETs. Build native
inputs from actual original receipt bytes and call the existing atomic Owner;
the storage backend issues no financial permission.

Minimum tests: SQL/file canonical input equality using synthetic fixtures only;
cache lookup never changes acquisition birth; old run cannot become current;
secrets absent from URL/receipt output; changed profile/metric/raw denied;
zero retries and cap28; 401/403/429 stop provider; exact identity/class/currency;
ADS refusal; no metric date or FY1 horizon invented; independent process replay.

## Full Market context remains separate

Use `market_component_handoff.required_original_parents` and the original
`canonical_market_projection.project_sealed_market_context` contract. A real seed,
authority graph, publication PIT, optional denials and US night provenance are
still needed. Production additionally requires `ProductionSourceRunBinding`.
Never relabel PENDING as PRODUCTION_MONITORING. KR query-time ka20001/ka20009
responses are not automatically completed-session roles. Preserve the four
missing role verdicts and concentration warnings. No recapture is authorized by
this design document. No next generation starts automatically.
