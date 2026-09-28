# Sealed Fresh Request Dispatch

REV11 adds an opt-in, unregistered transport boundary. It does not change REV10
analytical gates, source semantics, model policies, or renderers.

## Identity

`FreshRequestDescriptor` freezes a canonical public wire identity, generation,
logical request, role, subject, target period, page/document bounds, timeout,
retry limit, artifact path, and owner/config fingerprints. Nested request data
is immutable canonical JSON text. Credential values are not exported.

`ProviderPlan` rejects duplicate wire identities, cross-generation descriptors,
inconsistent budgets, and noncontiguous page declarations. Admission verifies
the exact accepted REV10 root receipt, mandatory role coverage, unresolved
roles, owner hashes, config hashes, and credential presence. A candidate is not
an executable final provider plan.

## Receipts

`SealedDispatcher` denies requests absent from the admitted whole plan before
transport, applies an overall per-attempt timeout, preserves failed responses,
and retries only the existing transport-transient classes without changing the
request. Authorization/secret failures latch a systemic stop. Independent
requests can continue after ordinary transport or normalization failure.

Plan, start, attempt, raw, normalization, role-binding, and final receipts are
written exclusively. `consume_bound_result` resolves the exact final receipt
hash and checks generation, descriptor, plan, request, raw, normalization, and
role-binding hashes. Retrieval time is distinct from source observation period.

Normalization is supplied by the registered owner in an isolated controller.
The unit test owner is fictional. Existing financial/market/stock owners are
not automatically registered by giving their filename or hash to a plan.
No production endpoint, scheduler, collector, or model route imports this module.

## Exactness Boundary

A finite envelope is not an exact set of requests:

- SEC current/prior accessions, primary documents and exhibits are selected
  from fresh submissions, index and document responses.
- OpenDART statement year/report-code selection follows its fresh filing list.
- Kiwoom page two and later require response-owned continuation keys.
- The native US market owner resolves exchange identity from symbol discovery.

The user's response-binding approval is recorded in the REV11 work instruction
directory. Every child slot, selector, parent set and maximum is frozen before
network access. Only the declared response fields may fill that slot. The
resolved wire and parent receipt hashes are recorded before its first attempt.
No slot can be added or widened after observing a response. Parent artifacts,
selection policy, issuer, filing and cursor ancestry are checked again on use.

The separate KR approval retains global configuration 50 and permits existing
request-local caps within `MAX_KR_REQUEST_PAGES`. This is not a pre-acquisition
guarantee of enough rows. Original consumer normalization, requested-window
completion and continuation state must pass after capture. Unresolved cap
exhaustion is SOURCE_PARTIAL and prohibits model execution.

## Opt-In Whole-Run Controller

`r9_rev11_live` freezes the whole finite provider plan only from a clean,
fully validated local commit and the exact REV10 receipt. It snapshots static
identity and local investment logic, never prior mutable financial packets.
`r9_rev11_collect` routes all provider HTTP through the dispatcher. Native
Kiwoom normalization runs in a separate, network-disabled worker whose private
stdio protocol is never exported. Credential exchanges remain memory-only.

Raw stock pages are replayed through the original native parser. Financial,
Market, macro, night and event owners consume current-generation receipts.
`r9_rev11_replay` verifies source bindings and composes the full graph twice
with network disabled. Capture success alone does not qualify a financial fact
or complete source adapter. Mandatory partial sources stop before AI.
The existing display/source-time owners must also qualify the required US
index/macro/dollar rows and both KR indices plus USD/KRW before issuing complete
source qualification. Honest sector or night-horizon unavailability stays
permitted; a renderable unavailable block is not proof of mandatory coverage.

Only a qualified fresh corpus can reach `r9_rev11_models`. It preserves the
existing signed-in official sol/xhigh transport (1200 seconds, no retry),
Market/Core/A/B contracts and detailed rendering, while using only the new
generation's source inputs. Source and code hashes remain frozen through all
stages. Sender-boundary capture is local and delivery-disabled. No main merge,
push, deploy, scheduler mutation or production database write is part of this
opt-in execution path.
