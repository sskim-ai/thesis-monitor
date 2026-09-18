# Thesis Monitor — M12CY Calibration Policy Acceptance & WAIT Actionability Review

## 0. Task identity and authorized outcome

Work instruction:
`20260918-m12cy-calibration-policy-acceptance-wait-actionability-review.md`

Suggested result:
`thesis-monitor-20260918-m12cy-calibration-policy-acceptance-wait-actionability-review-report.zip`

This is a **read-only, no-new-inference review of the existing 22-subject diagnostic results**, with explicit fact-versus-inference adjudication and document-only message prototypes.

The user asks both:
1. proceed with policy acceptance / WAIT actionability review; and
2. verify whether the Samsung inventory/cash-conversion rationale and SK hynix expectation/financial-quality rationale are actually justified.

Do not assume either the current monitor or the prior Chat judgment is correct. The deliverable is a bounded decision dossier, not another code-repair or model-execution task.

Hard scope:
- New Pass-A, Pass-B, Core, judge, repair or other external model/API/CLI inference calls: **0**.
- Frozen analytical data/source refresh: **0**.
- Application, shadow decision policy, prompt, schema, validator, materializer and configuration edits: **0**.
- Source packets, historical outputs and accepted artifacts rewritten: **0**.
- Production writes/intents/sends, broker reads/orders/modifications/cancellations, scheduler changes, merge, push, deploy: **0**.
- Read-only source/history inspection and temporary audit/report-generation helpers are allowed.
- Ordinary reasoning by the executing assistant is needed; "model calls 0" prohibits launching additional inference jobs, not writing the review.
- No full pytest/provider-schema/112-rule reproof is required for a document-only review. Do not recertify prior passes.
- No automatic next execution. Return the evidence and minimum-change decision to Chat.

## 1. Exact source lineage and evidentiary boundary

### Main M12CX result
`thesis-monitor-20260918-m12cx-new-buyer-risk-wait-axis-independence-pass-b-closure-report.zip`

SHA-256:
`df7d3eef818ae21d479d4dea4bc15f5aeb86b3cde956a981cf9b0e6bfca01488`

239 declared payloads. Formal terminal remains M12CX_PASS_B_FAILED / MODEL_TIMEOUT:attempts=1.

### Supplemental M12CX result
`thesis-monitor-20260918-m12cx-user-requested-supplemental-batch4-retry-batches5-8-report.zip`

SHA-256:
`41e65904e65fcb696a6a44f7348c2d17101e1147497ca256df5b8994bbace6fe`

90 declared payloads. Successful batch-4 retry plus batches 5–8; supplemental diagnostic evidence, not retroactive canonical PASS.

### Combined diagnostic output
Within supplemental source:
`cross-run-offline-validation/combined-fresh-a-m12cx-b-22-subject-results.json`

File-byte SHA-256:
`34aace744021cc0b4b150dcd47e9c31bb2f48d8ec4a136cc4123c4de64646f4c`

Normalized Pass-B array canonical aggregate SHA-256:
`07d90bb018b6347cdd995b468e60950e05dfe1c823f46c1e35a6e759f29ffe27`

The two hashes have different owners; file bytes and normalized row-array identity are not interchangeable.

### Frozen facts
M12CM report:
`thesis-monitor-20260917-m12cm-fresh-current-v4-production-equivalent-smoke-blind-handoff-report.zip`
SHA-256:
`625606d6df521cf3368c8779ec7f24816ee3a374cdfcc7fac367f984983359cc`

Assessment: 2026-09-17. This is the frozen experiment input, not today's investment recommendation.
The 27 supplied facts-only files are exact bytes copied from this report. Their original freeze manifest is included.
The original M12CM outer manifest declares 68 payloads; it additionally contains an undeclared nested `source-package-integrity/artifact-manifest.json`. This source packaging limitation is recorded. Do not claim zero original extras; do not make this unrelated metadata file a new blocker when all reviewed facts have exact declared hashes.

### Implementation/source inspection
The main/supplemental M12CX diagnostic lineage reports implementation:
`db92848f9c715807e0e7c55bdd973f9af9a9e095`.

Inspect that version's owners using existing Git history/source exports where available. Read-only `git show` is preferred to changing the working checkout. Do not substitute whatever happens to be current HEAD and call it the historical implementation. If a required historical owner is inaccessible, mark that specific conclusion unproven and give the exact missing artifact; finish all independent review work.

Formal experiment counts remain: A reused by authorization; B requests 9 including the initial batch-4 timeout and a separate retry; successful outputs 8 batches / 22 subjects. Do not report global retry 0, uninterrupted fresh E2E PASS, or new production readiness.

## 2. Review epistemology: two evidence lanes

### F — Frozen-run evidence
Use the original facts, source limits, Core/claim projections, capability catalogs, raw B output and combined result to answer what the model was entitled to infer **at that run**.

Trace:
source fact + allowed scope -> Core claim -> Pass-A classification -> candidate eligibility -> B selected refs/reason -> final axis/message.

A ref being registered or a claim being BEARISH does not prove economic materiality or unrestricted downstream use.

### X — External corroboration, separately marked
The user also asked whether the explanation is actually correct. Chat has supplied primary-source corroboration notes collected on 2026-09-18, separate from the frozen inputs.

Use these notes to challenge/confirm source interpretation, not to silently enrich F.
- Original publication date and check date must both be recorded.
- Company earnings releases are company-reported and may be preliminary; do not call them reviewed statements.
- External corroboration of rounded headlines does not clear every denied field, TTM estimate or downstream valuation.
- A statement not found is NOT_PROVEN, not false.
- No new provider refresh or broad web crawl in this task. Use supplied primary notes and existing archived filings/caches first.
- If exact official inventory operands or quality-threshold explanations remain unavailable, produce the precise retrieval specification for a later separately authorized check; do not invent numbers.

No updated external price, target, or trading instruction is requested.

## 3. Mandatory focused adjudication A — Samsung Electronics (005930)

This name is a snapshot regression case, not a ticker-specific policy rule.

### Observed frozen facts
The exact source has:
- relation `working-capital-relation:4b43f129a5c3b9dbca52fa29`
- comparison_basis = year_over_year_growth_rate_percentage_points
- lhs = inventory_growth; rhs = cogs_growth
- signed gap = +35.79975884967539 percentage points
- balance_date = 2026-06-30
- semantic_scope = exact_total_inventory
- cash_flow_alignment_state = NOT_PRESENT
- separate cash_flow_user_visible: SUPPRESSED, ai_enabled=false, selection_reason=initial_market_or_source_scope_excluded.

Its `working_capital_user_visible.prohibited_claims` includes:
- working_capital_causal_overclaim
- dso_inventory_days_dpo_ccc
- working_capital_only_status_or_valuation_change.

Original B Holder:
- REVIEW / BALANCE_SHEET_RISK
- sole `holder_decision.evidence_refs` entry:
  `canonical:working-capital-relation:4b43f129a5c3b9dbca52fa29`
- reason says inventory growth substantially outpaces cost growth and cash conversion warrants review.

The selected Core claim converts the relation into bearish working-capital/cash-conversion risk. Preserve its exact text and ref; do not edit it to resolve the question.

### Required distinctions
Answer separately:
1. Is the **stored growth-rate gap** present? (Yes is directly checkable.)
2. Are the four reported operands and comparison periods independently re-computable from supplied/archived data?
3. Does the gap prove absolute inventory rose? A difference of growth rates alone does not prove the sign of either growth rate.
4. Does it prove operating cash flow deteriorated? NOT_PRESENT/suppressed cash-flow context is not evidence of cash-flow deterioration or improvement.
5. Does the source authorize using this relation alone for a Holder status change?
6. Does `status` in the original source prohibition include the present Holder status or only a narrower legacy consumer? Inspect the actual canonical owner/history; do not infer the full rule solely from its name.
7. Is there separate, independently selected evidence adequate to justify REVIEW? Do not rescue an output by citing unselected future facts after the event.

### Accounting/source checks
Seek only existing archived operands first:
- current/prior inventory carrying amounts, dates and consolidated scope;
- current/prior comparable COGS flow periods (single quarter vs YTD explicitly);
- unit/currency, restatement, source-column and filing identity;
- total inventory vs components, group vs DS/memory scope;
- source-lineage validity independently of an upstream PASS tag.

If available, recompute gap with exact decimal arithmetic. If absent, report `STORED_RELATION_PRESENT_OPERAND_REPROOF_NOT_AVAILABLE`.

Distinguish inventories (a balance at a date) from COGS (a flow over a period). Do not invent inventory days/DSO/DPO/CCC, or turn the aggregate group signal into a specific HBM demand problem.

Separate hypotheses requiring evidence: demand-backed work in progress, product mix/ramp-up, stockbuilding, impaired sell-through, write-downs, FX/consolidation changes. Do not assert any hypothesis occurred without source proof.

### Provisional Chat position to test, not target
A cautious monitoring note is supportable from the stored relation. Confirmed cash-flow deterioration, thesis impairment, or automatic Holder REVIEW is not established by that relation alone. There is a concrete **source-use restriction versus selected reason** question requiring owner confirmation.

Do not force HOLDABLE or BUY as the expected output. Do not remove working-capital controls.

## 4. Mandatory focused adjudication B — SK hynix ordinary share (000660)

Keep this distinct from SKHY's traded-security/depositary valuation basis.

### Observed frozen facts
`canonical:financial_quality:2026-06-30`:
- state = denied
- reason_codes:
  net_income_exceeds_revenue
  preliminary_profitability_outlier
  unusually_high_or_low_operating_margin
- decision_version = financial-quality-taint-v2.

This is an **internal eligibility/quality decision**, not a finding that the company has fraudulent or unreliable financial reporting.

Frozen headline earnings include:
- revenue: KRW 79,318,746,000,000
- operating income: KRW 60,542,608,000,000
- computed operating margin: approximately 76.328%.
The supplied source lineage identifies OpenDART receipt `20260814003509`, consolidated CIS, single-quarter rows ending 2026-06-30. Verify metadata as recorded; do not claim the live filing was re-fetched.

Runtime business quality is CONFIDENCE_ONLY with directional_use_allowed=false.

Actual B:
- HOLD / WAIT / HOLDABLE
- confidence LOW
- sole decisive contradicting claim is the high-expectations claim
  `maturity-claim:3c37cce411c8282169a39768be533807ae6c643f354478d7aa1e5b8c9fed20e4`.
- The denied-quality claim is present in the available Core but is **not** selected in decisive_contradicting_claim_refs.
- The summary nevertheless mentions financial-quality limitations.

Therefore do not state as proven that the quality flag mechanically caused HOLD. Distinguish summary association, selected-ref support and demonstrated runtime causation.

### Supplied external corroboration (lane X)
Official SK hynix Q2 2026 release, published 2026-07-29, reports:
- revenue KRW 79.3187 trillion
- operating profit KRW 60.5426 trillion
- net profit KRW 93.9226 trillion
- operating margin 76%, net margin 118%.
These rounded revenue/profit figures corroborate the unusual scale; the release is explicitly preliminary, not completion of a formal statement reconciliation.

The central question is whether the quality rule is confusing **unusual-but-reported performance** with data corruption. Do not assume outlier detection is wrong everywhere or disable it.

### Required adjudication
Trace the actual anomaly predicate and taint propagation:
- threshold/rule owner and historical purpose;
- observation vs hard identity/period/unit impossibility;
- latest quarter vs cumulative columns and same basis;
- reported earnings correctness vs recurring-earnings quality;
- whether one-time/non-operating items explain net profit exceeding revenue (NOT_PROVEN unless archived notes support it);
- whether an unverified "preliminary" warning persisted into a full-statement source;
- fields genuinely tainted, and fields denied only by cascading generic thresholds.

A large margin or net income above revenue is a reconciliation signal, not by itself a company-thesis impairment fact. Official headline corroboration does not make extrapolation of those profits economically justified.

For the axis decision, determine whether HOLD is supported by an independently material business/cycle fact, or only current expectations, valuation and epistemic limits under the user's approved policy. Preserve legitimate business risk. Do not turn absence of adverse proof into mandatory BUY.

## 5. Complete 22-subject policy acceptance matrix

Review all 22 subjects and all 3 axes (66 axis entries). This is an evidence review, not new investment output generation.

Required columns:
- subject and market;
- original three-axis labels, score, confidence, thesis state (unchanged);
- Pass-A archetype/tier and exact supporting refs;
- relevant capability alternatives/exclusions; identify any deterministic forced label versus actual model choice;
- selected decisive/axis refs and exact source facts;
- original source use restrictions, quality and economic scope;
- factual support status;
- inference level (observation / derived relation / conditional risk / confirmed impairment / action);
- policy application result;
- missing evidence and precise minimal next action.

Use separate classifications, not one undifferentiated FAIL:
Factual status:
`VERIFIED_WITHIN_FROZEN_INPUT | SOURCE_OPERANDS_NOT_REPROVEN | EXTERNAL_CORROBORATION_ONLY | SOURCE_CONTRADICTION | UNRESOLVED`.
Policy review:
`SUPPORTED | REASONABLE_JUDGMENT_DIFFERENCE | UNDER_SUPPORTED | SOURCE_SCOPE_CONFLICT_REQUIRES_OWNER_CONFIRMATION | POLICY_DECISION_REQUIRED`.
Presentation:
`CLEAR | MISLEADING_OR_AMBIGUOUS | INCOMPLETE_ACTION_CONDITION`.

A valid reference is not automatically sufficient for a material downgrade. Conversely, disagreement with prior Chat labels is not automatically an error.

### Additional priority cases, within the same bounded review
- Samsung/SK hynix ordinary share/SKHY: business quality vs instrument basis, source scope and selected evidence.
- TSM: genuine overseas-fab business costs versus valuation-only caution.
- CRCL, HUT, RXRX, WRD, WULF: optionality vs realized economics, material cash/financing risk, evidence needed for WAIT/AVOID and HOLDABLE/REVIEW.
- LS Electric and POSCO Holdings: evidence behind EXECUTION_DEPENDENT_GROWTH classification; established operations vs growth initiative. Do not reclassify by name/market cap.
- GOOGL/MU: long-term direction vs current entry conditions; method/tier and conditional range interpretation.
- Other subjects: complete the 66-row record without turning every row into a separate research project.

No hidden model weights or causal attribution may be inferred from prose or scores. Use observable selections, schemas, constraints and reason fields only.

## 6. General policy principles to assess, not automatically encode

- Company thesis and current entry attractiveness remain separate. Size/name alone cannot guarantee BUY.
- A verified company may still deserve HOLD/REVIEW when actual competitive, cycle, financial or execution evidence supports it.
- For execution-dependent businesses, "no collapse confirmed" is not automatically sufficient positive evidence of attractive expected economics. Yet missing data alone is not automatic SELL.
- Distinguish data unavailable, internal source anomaly, non-recurring earnings, actual disclosure failure and business impairment.
- Review archetype choice as a consequential economic decision because it determines method eligibility; structural PASS alone does not validate its economics.
- Source-level scope restrictions must not vanish merely because evidence was converted into an atomic Core claim or marked material in a capability catalog.

Preserve all existing policy unless a later Chat decision authorizes a specific modification.

## 7. WAIT actionability: document prototypes, not a schema migration

Do not create mandatory new runtime enums in this task. First map existing reason classes and runtime fields into clear message sections.

Use these descriptive categories:
- PRICE_WAIT
- BUSINESS_CONFIRMATION_WAIT
- VALUATION_INPUT_UNRESOLVED
- MIXED_WAIT.

They are review labels only.

Every prototype must separate:
1. long-term company thesis;
2. primary reason to wait;
3. conditional fundamental valuation reference, if legitimately available;
4. tactical support, separately labelled;
5. what price and/or business evidence would permit reconsideration;
6. unresolved inputs and as-of/period limitations.

### Mandatory cases
- GOOGL: frozen price 345.20 USD versus historical-tier range about 558.69–600.39 USD, WAIT for execution risk. Do not imply buying after price rises to the lower bound. This is not a target-price instruction.
- MU: price-based WAIT, show original historical P/B candidate and its assumptions without presenting it as objectively proven intrinsic value.
- Samsung/SK hynix ordinary share: do not promote a working-capital warning/internal outlier label into a confirmed thesis deterioration statement.
- One execution-dependent growth subject: no safe scenario price -> honest unresolved; exact required scenario inputs, no arbitrary pullback.
- One depositary/basis-unresolved subject: separate company thesis from current-security price inability.

Draft at least 6 document-only messages. Preserve original labels, numbers and refs in the "current-output-preserving" version. Where the label itself is under-supported, mark it **REVIEW PENDING** and show an alternative wording only as an explicitly proposed scenario, not a corrected accepted output.

Do not invent future EPS, multiples, targets, percentile choices, technical levels, or checkpoint dates/thresholds.

## 8. Price-range economic acceptance

For every currently resolved WAIT price range (5) and unresolved WAIT (14), distinguish:
- numeric/source correctness;
- method suitability;
- tier support;
- actionability and width/sensitivity;
- current business conditions.

Historical percentile ranges are descriptive reference constructs, not automatically fair value.
The existing CONSERVATIVE/BASE/PREMIUM mapping is an experimental policy assumption. Do not sanctify it because it was deterministic or earlier Chat selected it.

Check metric basis, loss/peak-cycle distortion, book relevance and normalization before endorsing a range for user action. No new price bands in M12CY.

For unresolved entries, classify the gap as missing source, unusable basis, method-policy not suitable, or choice unresolved. Do not force 22/22 numeric coverage. A missing price must not become a fabricated discount or a hidden investment label.

## 9. Three required top-level deliverables

### A. `POLICY_ACCEPTANCE_REVIEW.md` plus machine appendix
- 22 subjects / 66 axes, evidence-linked.
- Focused Samsung and SK hynix findings first.
- Confirmed finding vs hypothesis vs unproven causation clearly separated.
- Working-capital and quality-flag source restrictions included.
- A concise root-cause ledger, no one-ticket-per-label proliferation.

### B. `WAIT_MESSAGE_PROTOTYPES.md`
- At least 6 messages spanning price, business, unresolved basis and mixed WAIT.
- Current-output-preserving wording separated from policy-change proposals.
- No implied buy-on-rise or technical-support-as-fair-value mistakes.

### C. `MINIMUM_CHANGE_DECISION.md`
For each issue choose:
- KEEP_AS_IS
- PRESENTATION_ONLY
- SOURCE_VALIDATION_REQUIRED
- B_POLICY_REPAIR_PROPOSAL
- A_CLASSIFICATION_OR_TIER_REVIEW
- ACCEPT_REASONABLE_DIFFERENCE
- DEFER_WITH_SPECIFIC_MISSING_EVIDENCE.

State the existing owner/path and minimal affected contract, whether future model calls would be needed, and which stage can remain frozen. Do not implement.

If a concrete source/consumer bug is found, evidence and a bounded proposal are enough; finish independent rows instead of aborting the entire review. No automatic new validator framework, transport redesign, schema rewrite or policy retune.

Machine appendix:
- source-input-binding.json
- samsung-skhynix-fact-inference-adjudication.json
- policy-acceptance-matrix-22.json (three axes per subject)
- source-restriction-propagation-review.json
- waiting-condition-and-range-review.json
- minimal-change-ledger.json
- review-limitations.json
- safety-counters.json
- program-completion.json
- artifact-manifest.json and result ZIP SHA sidecar.

## 10. Completion criteria and stopping conditions

Complete this review when:
- 22 subjects / 66 axes accounted for; no missing row passed implicitly;
- Samsung arithmetic, causal inference and source-scope questions separately adjudicated;
- SK quality flag, official corroboration, recurring-economics question and label reasoning separately adjudicated;
- external corroboration never blended into frozen-run input;
- all proposed changes have evidence and narrow owners;
- unresolved evidence is explicitly tracked, not manufactured;
- message prototypes are honest about price/business/data waiting conditions;
- no model/provider/production action occurred.

Terminal options:
`M12CY_POLICY_REVIEW_COMPLETE_READY_FOR_CHAT_DECISION`
`M12CY_REVIEW_COMPLETE_WITH_BOUNDED_SOURCE_GAPS`
`M12CY_REQUIRED_FROZEN_SOURCE_BINDING_FAILED`.

Review completion is not investment accuracy, a canonical M12CX PASS, production integration approval, or a new holdout score.
The 22-subject set and prior labels are already revealed and development-exposed; do not claim blindness or use agreement as optimization/acceptance.

After Chat selects changes:
- presentation only -> document/renderer replay can precede any inference;
- B-only policy change -> frozen A + bounded B proof, if A inputs/semantics remain valid;
- source or A semantics change -> explicitly re-evaluate affected lineage, not automatic reuse;
- generalization and operational reliability are later separately scoped decisions.
Do not run any of these follow-up tasks now.
