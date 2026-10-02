# REV44 In-Flight Semantic Clarification

User clarification received during REV44, before implementation:

- Continue the same run and branch; preserve all earlier evidence and commits.
- Promote only if a Finnhub-owned field-specific definition reproducibly states
  that forwardPE uses analyst estimates for the next fiscal year (or equivalent).
- Then use PROVIDER_FORWARD_HORIZON_FY1,
  QUALIFIED_PROVIDER_NATIVE_FY1_FORWARD_PE, and display label fPER(FY1).
- Otherwise keep PROVIDER_FORWARD_HORIZON_UNSPECIFIED.
- The metric remains an atomic provider-native ratio. Never create implied EPS
  or a FY1 EPS owner.
- No recollection, retry, model call, or message generation for this clarification.
- Record exact documentation provenance and SHA, and run full validation.
