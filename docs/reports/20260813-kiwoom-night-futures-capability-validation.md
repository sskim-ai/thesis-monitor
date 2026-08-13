# Kiwoom Night Futures Capability Validation

## Scope

This is a capability gate, not a production-provider rollout. No account, HTS ID,
certificate, password, API secret, or token was read, stored, logged, or committed.

## Official Contract Evidence

- OpenAPI+ service: https://www.kiwoom.com/h/customer/download/VOpenApiInfoView
- OpenAPI+ guide: https://download.kiwoom.com/web/openapi/kiwoom_openapi_plus_devguide_ver_1.7.pdf
- REST service: https://openapi.kiwoom.com/intro
- OpenAPI+ is a Windows OCX service. Its current public product list includes stocks,
  KOSPI200 futures, and KOSPI200 options.
- The guide exposes KOSPI200 futures discovery and generic futures realtime FIDs, but it
  does not define current KRX night-session identity, closing-auction delivery, or a safe
  final-close rule.
- Kiwoom REST currently lists domestic and US stocks, not domestic derivatives.

## Product Decision

- KOSPI200: `partial` - OpenAPI+ documents KOSPI200 futures discovery and generic futures realtime FIDs, but not current KRX night-session identity or final-close semantics.
- KOSDAQ150: `unsupported` - The current official OpenAPI+ product list is limited to stocks, KOSPI200 futures, and KOSPI200 options; KOSDAQ150 futures are not listed.

## Gateway Contract

The probe accepts one normalized, credential-free gateway response at
`/v1/night-futures/capabilities`. A product is `supported` only when symbol discovery,
front-month identity, realtime subscription, explicit night-session ticks, closing-phase
ticks, final-close semantics, session identity, contract identity, and a persisted final
observation are all verified.

Architecture:

`Kiwoom OpenAPI+ Windows gateway -> normalized capability/final close -> shadow validation`

`KRX official daily data -> same-product/same-contract/same-session reconciliation`

## Production Decision

- Status: `not_enabled`
- Primary enabled: `false`
- Reason: Kiwoom gateway URL is not configured.

The production provider registry and Daily Digest source priority were not changed. KRX
remains the only production night-futures source until an authenticated live probe and
multi-session shadow reconciliation succeed independently for each product.

## Remaining Live Evidence

- Actual night-session subscription and ticks
- 05:50-06:00 closing-phase delivery
- Provider-defined final close and session-final event
- Persisted close availability before 07:50 KST
- Same-contract KRX reconciliation over multiple sessions, including rollover
