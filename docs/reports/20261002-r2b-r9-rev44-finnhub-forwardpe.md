# REV44: Finnhub Atomic Forward P/E Owner

## Outcome

`R2B_R9_REV44_FINNHUB_PROVIDER_NATIVE_FORWARDPE_OWNER_PASS_READY_FOR_FRESH_US_INTEGRATION`

This closes local owner integration under the explicit UNSPECIFIED-horizon
policy. It is not a fresh live proof or production enablement.

- Instruction commit: `38b6ef01fc0da3237fd1fb5a03fae53599c4b309`.
- Base: `0a0d68b9f9b1b62c61839ba3b7f91fba808a38b8`.
- Tested implementation: `deccb0f99957028d949b5c528b87f4a1c4440ab5`.
- Branch: `codex/r2b-r9-rev44-finnhub-forwardpe-owner`.
- Operating/main unchanged: `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`.

## Semantic Boundary

The sealed `metric.forwardPE` value is consumed as an atomic Finnhub ratio.
Captured official Basic Financials HTML, linked Swagger, official OpenAPI and
browser navigation do not establish its exact FY1/NTM horizon. The user's
follow-up confirmed only the ratio was visible. Absence of exposed calculation
parameters does not prove FY1: a provider can publish a precomputed NTM ratio.

Actual snapshots therefore retain `PROVIDER_FORWARD_HORIZON_UNSPECIFIED`,
`provider_horizon=null`, `estimate_basis=null` and `Finnhub Forward P/E`.
The conditional FY1 mapping has only synthetic test coverage; its reviewed
official-definition pin remains empty. No `fPER(FY1)` activation, implied EPS,
new FY1 EPS owner, ADR conversion or repricing occurred.

Only qualified refs may enter deterministic Valuation display and Pass-B
NewBuyer/Holder context. Overall/Core/Pass-A use remains excluded.

## Sealed Replay Coverage

Historical evidence, not current data:

- Exact-horizon qualified: 0/14.
- Unspecified-horizon qualified: 2/14 (GOOGL, IBM).
- ADR/identity blocked: 10/14.
- Missing value after eligible identity: 2/14.
- Existing PER/PBR owners: canonical JSON parity for all 22 subjects.

Two original offline replays and follow-up exact-code checks match matrix hash
`a1398db09c3f64f7f6ecd60adc284efef8c81113f5d530702a9731a7d9ebf829`.
Original raw bodies, source timestamps, receipts and generation IDs were retained.

## Validation

- Focused: 207 passed.
- Bounded audit-matrix repair check: 26 passed.
- Full pytest: 7917 passed, 63 skipped, 0 failures, 0 errors.
- Ruff, diff check, Investment Knowledge, Chart Knowledge: PASS.
- Test network guard enabled; production DB not used.

One earlier full run was interrupted for context state/fact-ID binding
hardening. The next full run exposed a legacy audit control that still looked
for `fPER` after the atomic `FORWARD_PE` row was introduced. That control now
checks qualified UNSPECIFIED ownership and rejects horizon promotion, EPS
ownership and Core/Pass-A use. Both earlier receipts remain in the private
bundle; neither is reported as a successful full run. The full suite then
passed on the exact implementation above.

## Safety and Handoff

New stock-provider calls 0; external model calls 0; full messages 0; Telegram 0.
Production DB/WAL, scheduler and notification state unchanged. No REV44 push,
main merge, deploy or restart. REV43 was separately preserved remotely as
required by the work instruction, without raw artifacts.

Private report bundle:
`thesis-monitor-20261002-r2b-r9-rev44-finnhub-provider-native-forwardpe-owner-report.zip`
plus SHA-256 sidecar. Official capture hashes, source matrix, failure continuity,
exact final SHA, secret scan and integrity receipts are in that bundle. Delivery
is limited to iCloud Drive / Thesis Monitor; the cloud delivery receipt is kept
beside the local bundle.

REV45 requires a separate task. It was not started.
