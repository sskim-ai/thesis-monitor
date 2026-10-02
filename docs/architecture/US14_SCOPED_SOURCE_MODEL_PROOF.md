# US14 Scoped Source and Model Proof

REV46 adds an opt-in offline/manual proof path. It is not registered with a
scheduled task, delivery service, or persistence owner.

## Source Ownership

- `one-shot-us14-source-acquisition-v1` derives the exact read set from the
  canonical US14 roster and four existing stock roles: 56 unique reads.
- The previous ALL22 and KR8 contract names, rosters and default serialization
  remain unchanged. Neither accepts an incomplete primary set.
- SKHY declares one `AUXILIARY_ISSUER_ONLY` dependency on 000660. Only the
  existing OpenDART business/financial discovery and document slots are allowed.
  There is no auxiliary stock packet, technical baseline, valuation, event-news
  request, model subject or user message.
- The financial-only owner uses the same reported-comparison selector and
  verified legal issuer bridge. It binds the exact plan, generation, cutoff,
  receipts and official security identity hash. No per-share/valuation rights
  are transferred from 000660 to SKHY.
- `FreshUSSourceRunSeed` binds all 14 primary stock owners plus the separate
  auxiliary issuer result hash. The authority graph records the auxiliary
  result without adding a fifteenth primary subject.
- US market context retains its existing declared macro/FX/night-futures
  inputs; it does not collect a KR index/sector market or other KR stocks.

## Models and Capture

`Us14Execution` verifies the exact US-only source plan and source-only archive
before request construction. Its topology is one Market request and five
requests each for Core, A and B. The provider/model schemas, materializers,
financial policies and current detailed renderer remain the existing owners.

The actual official launch context must be qualified. Model execution is
`gpt-5.6-sol` / `xhigh`, 600 seconds per attempt, at most two retries for a failed
logical request (48 maximum US attempts). A successful logical request cannot
be run again. Each retry has its own attempt directory and namespace; prompt
and schema bytes remain identical. A rejected attempt cannot seed downstream
state. Independent batches continue; downstream batches require their own
validated predecessor. Security/input drift is a systemic stop, not a retry.

Core/A retain valuation isolation. Provider-native forwardPE is governed by the
REV45 user-authorized FY1 product policy, not an invented Finnhub definition.
No implied EPS is calculated. Pass-B NewBuyer/Holder are the only consumers.

`US14_15_MESSAGE_CAPTURE_V1` requires one US market message plus 14 stocks.
All captures use the existing disabled-delivery boundary. The ALL22 24-message
guard is unchanged. The REV46 KR continuation reuses the KR8 KIS valuation and
stock renderer, applies the same bounded attempt policy, and captures the
existing supporting market message as the ninth local message.

## Execution Gates

1. Exact-commit offline full regression, network guard, knowledge and secret
   scans must pass before acquisition.
2. US target session and KST run date are checked at freeze and dispatch.
3. One fresh source generation must pass complete replay and market/source
   qualification before its source-only seal and model calls.
4. Only complete US source/model/message PASS permits the KR completed-session
   gate. An early KR window is a pending terminal, not permission to wait for
   hours, use intraday data, or reuse previous current data.
5. Main integration is conditional on both markets and the combined proof.
   No deployment, restart, scheduler mutation, Telegram send or production
   database write belongs to this proof path.

Synthetic tests are contract evidence only, never live source/model receipts.
Failed live stages are sealed honestly; no prompt/validator hotfix occurs
inside an active generation.
