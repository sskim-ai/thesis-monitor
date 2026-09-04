# AI Semantic Reviewer Contract

Date: 2026-09-04 KST

Status: shadow-only; no production mutation.

The reviewer used frozen candidate, frozen structured plan, and the same evidence only. It could not fetch, add facts/numbers, or rewrite. Contract failures: `0`. Verdicts were PASS `18` and advisory WARN `4`. It remains shadow/advisory and is not a universal production veto.

## Advisory findings

- `CRCL` / `UNSUPPORTED_UNKNOWN_CONTEXT`: The cited evidence only states that revenue impact is unknown. The claim adds payment/stablecoin usage expansion as the unresolved driver, which is not present in the subject evidence.
- `RXRX` / `CLAIM_TYPE_SEVERITY_MISMATCH`: The evidence is a thesis-weakening condition, and the text says the platform value assumption weakens. The claim type labels it as a business invalidation condition, which overstates the cited evidence.
- `RXRX` / `UNSUPPORTED_UNKNOWN_CONTEXT`: The cited evidence only states that revenue impact is unknown. The claim adds research achievement and business expansion context that is not stated in the subject evidence.
- `TSM` / `INELIGIBLE_VALUATION_REF_OWNERSHIP`: The valuation caution is supported by the security-basis evidence, which says security identity is unknown and valuation fields are not prose eligible. Citing the raw valuation book fact risks using an ineligible multiple as interpretation support.
- `012450` / `UNSUPPORTED_UNKNOWN_CONTEXT`: The cited evidence only states that FCF impact is unknown. The claim adds a positive order-expansion premise, while the subject evidence provided for orders is an invalidation risk about demand slowdown causing order decline and backlog contraction.
