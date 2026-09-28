# REV8 Offline Integration Boundary

The instruction was committed before implementation as
`0ae7d84b441921989432437a52b29f4ef2d26d55`, based on REV7
`3b8ebcfbe07b91e510013cd07236404fc04e71f0`.

## Implemented Locally

- Replay FRED/EIA/ECOS through the existing parsers with original request,
  response hash and receipt time. Provider runtime clocks retain their default.
- Reuse native macro delta arithmetic in a private in-memory database. Only
  observations from the same response can form a pair; no briefing-history
  daily signal or current-period inference is made.
- Replay KOSPI200 probe and D/W/M history from current-run raw receipts in a
  private temporary store, with no operating history read.
- Add an opt-in fresh macro/night input to full-source composition. Legacy
  persisted publication inputs cannot be used with a fresh run seed.
- Add exact artifact-bound issuer descriptors and target-security valuation
  views. Issuer income does not transfer EPS/book/share/multiple authority.
- Rebuild fresh stock graph/registry bindings and run existing Core/A/B input
  probes for all 22 synthetic direct-source subjects.
- Add typed UNKNOWN_LIMIT detailed-plan acceptance and section coverage
  metadata. NORMAL fixtures reach the real Telegram prepare/chunk/send boundary
  with only the external send overridden by a local sink.

## Qualification Limits

These are offline components, not a qualified fresh execution controller.
The all22 fixtures exercise direct domestic, FPI and KR comparison paths;
they do not prove every required owner archetype or a live source response.
The same synthetic FPI path used for SKHY is not its issuer-bridge proof.

An exact current-only SEC fixture raises
`EXPECTED_BUSINESS_QUALITY_OWNER_OUTPUT_MISSING`: the quality owner requires
comparison facts before the existing UNKNOWN_LIMIT consumer can run. Do not
remove that guard, clear mandatory-missing fields, or substitute old financial
facts to force a pass. A source-owned no-direction representation is still
needed before positive UNKNOWN_LIMIT detailed capture can be proven.

Whole-source all22 plus Market replay, real descriptor bridge qualification,
qualified/N-M valuation materialization, full section-owner selection, and the
exact 24-message route remain open. Current unavailable valuation is a safe
denial, not proof that every existing source lacks valuation capability.

`candidate_plan` reports these gaps and cannot dispatch. Terminal:
`R2B_R9_REV8_PREFLIGHT_CONTRACT_GAP`. No final provider plan, live source/model
generation, human-review message bundle, cutover, main merge, push or deployment
is authorized by this receipt. Production side effects remain prohibited.
