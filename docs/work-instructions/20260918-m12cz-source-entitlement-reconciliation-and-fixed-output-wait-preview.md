# Thesis Monitor — M12CZ Source Entitlement Reconciliation & Fixed-Output WAIT Preview

## 0. Task and limits

Instruction: `20260918-m12cz-source-entitlement-reconciliation-and-fixed-output-wait-preview.md`

Result: `thesis-monitor-20260918-m12cz-source-entitlement-reconciliation-and-fixed-output-wait-preview-report.zip`

This is a bounded evidence acquisition/reconciliation task plus a document-only presentation replay. M12CY's review is complete. Do not repeat a general 22-subject/66-axis audit, invent another validator framework, or use live inference to discover contract defects.

Authorized outputs:
1. exact source/owner evidence for the disputed working-capital, financial-quality and legacy FCF uses;
2. an adjudication of the expectations-only Overall support question, without generating replacement investment labels;
3. nineteen original-output-preserving WAIT previews and a minimum-change decision.

New A/B/Core/judge/repair/inference calls: **0**. No code or policy implementation is authorized. Ordinary reasoning by the executing assistant is required; the zero-call limit concerns additional model/API/CLI inference jobs.

## 1. Source bindings

Verify the supplied M12CY report and instruction package before work:

- M12CY report SHA: `1b04a3a85f49eeae7967d71bac6040d6fc06d02c4d9cc2b799eb8ac4d5df0b8d` (12 manifest payloads).
- M12CY instruction package SHA: `6a32885e2ac66e3e42c803b58dfc1e49bfe14c2e227885b12ab4036bd69ee67b`.
- M12CX canonical result SHA: `df7d3eef818ae21d479d4dea4bc15f5aeb86b3cde956a981cf9b0e6bfca01488` (239 payloads; formal timeout remains failed).
- M12CX supplemental result SHA: `41e65904e65fcb696a6a44f7348c2d17101e1147497ca256df5b8994bbace6fe` (90 payloads).
- Combined diagnostic file SHA: `34aace744021cc0b4b150dcd47e9c31bb2f48d8ec4a136cc4123c4de64646f4c`.
- Normalized B-row aggregate SHA: `07d90bb018b6347cdd995b468e60950e05dfe1c823f46c1e35a6e759f29ffe27` (not the enriched file-byte hash).
- Original M12CM report SHA: `625606d6df521cf3368c8779ec7f24816ee3a374cdfcc7fac367f984983359cc`.

The previous instruction package contains exact frozen facts and the original source reports. Reuse those exact bytes; do not infer files from filenames. A known extra nested metadata manifest in M12CM is documented, not a new analytical blocker.

Historical analytical implementation: `db92848f9c715807e0e7c55bdd973f9af9a9e095`.

Use read-only `git show`/history to inspect that version, rather than replacing it with current HEAD or checking out another branch. Record current HEAD independently. Chat's remote fetch could not resolve that local-only ref; the next executor's local Git history may resolve it. If not, report that exact missing version and finish other independent work. Do not require a remote push.

## 2. Chat decisions that narrow this task

Keep the entire historical diagnostic output immutable. Neither past monitoring AI nor Chat's former judgments are ground truth.

- Samsung Holder REVIEW is review-pending, not automatically corrected to HOLDABLE.
- SK hynix's source-quality flag is not proof of company impairment, and lack of quality-to-HOLD causation does not by itself justify expectation-only HOLD.
- A cash-flow module's SUPPRESSED flag is not automatically a global prohibition on all independently valid FCF evidence.
- Historical percentile bands are experimental references, not automatically intrinsic value or buy thresholds.
- GOOGL's documented primary WAIT is business-confirmation, not price-wait merely because a valuation range is present.
- No A classification, regime tier, historical valuation formula, BUY/SELL threshold, input quality rule or status policy is changed here.

## 3. Two independent work tracks

**Track S:** retrieve/export the finite missing source and owner records below; adjudicate scope.

**Track P:** replay the 19 existing WAIT outputs into document previews using only frozen data and explicitly marked review annotations.

A missing historical filing or local owner blocks only the conclusion that needs it. It must not stop independent previews or trigger another A/B execution.

## 4. Evidence lanes and bounded historical retrieval

F: exact frozen input and historical model-output lineage; immutable.

R: exact historical source/code records retrieved now to validate F. Keep them outside production stores and outside original model packets.

X: previously packaged Chat corroboration notes. They were not independently obtained by the M12CY executor or supplied as firsthand user evidence. They are not a substitute for source tables.

For R, inspect existing archived filings/caches first. Use readonly DB/snapshot access if needed. Never write production tables, ingestion checkpoints or monitoring state. Do not expose credentials or connection strings.

If missing, this task explicitly permits **targeted read-only historical source retrieval**, not market/fundamental refresh:
- only the relevant prior/current statements already identified by the frozen fact IDs/periods, and the contemporaneous official releases or notes needed to reconcile those statements;
- only the five issuer identities already implicated: MU, 000660, 005490, 005930 and CPNG; these are retrieval targets, not policy code rules;
- resolve exact filing/accession/document identities from the stored lineage first;
- record a finite request manifest with purpose, official endpoint, period, accession/receipt, as-of eligibility and expected use **before** network reads;
- use an existing official-source read client or direct official document read; no new connector/provider, broad crawl or undocumented scraping;
- at most 20 unique historical source payload requests; record every actual request, outcome and retrieved-byte hash. No automatic retry loops or access-control bypasses. If the budget/access is insufficient, name the residual gap and finish independent work;
- no current quotes, estimates, headlines, new portfolio data or market breadth collection;
- a post-cutoff revision is labeled hindsight and cannot retroactively rescue an earlier decision.

A record fetched now can confirm what was publicly reported then, but cannot be silently added to the historical model's knowledge or cited as a ref that the old model selected.

## 5. S1 — working-capital operands and permitted downstream use

Limit the arithmetic/source targets to the already implicated MU, 000660, 005490 and 005930 relations. Resolve exact relation IDs and the four reported/two derived fact IDs from the supplied records.

For each relation obtain:
- current/prior consolidated inventory carrying amounts and balance dates;
- comparable current/prior COGS amounts, with single-quarter versus YTD identified;
- unit/currency, reporting/consolidation basis, restatement version and source columns;
- filing identity, disclosure date, field name and exact evidence locator for every amount.

Recompute using the canonical formula only. Do not substitute an end-date match for flow-period equality or treat missing amounts as zero. Use decimal-safe arithmetic and retain unrounded results and display rounding separately. Nonpositive/invalid denominator conditions follow the existing owner, not an invented rule.

For Samsung the stored signed gap is `35.79975884967539121726114215` percentage points at 2026-06-30, relation `working-capital-relation:4b43f129a5c3b9dbca52fa29`. A difference of growth rates is not itself the sign of either rate, and it is not OCF.

Export exact source/consumer excerpts at the pinned implementation, including the relevant parts of:
- `app/services/working_capital_user_visible_preintegration_service.py`;
- the actual atomic-claim projection owner;
- `scripts/m12cq_two_pass_contract.py`;
- `scripts/m12cv_pass_b_capability_contract.py` and any actual M12CX final consumer.

Identify the owner of `working_capital_only_status_or_valuation_change`. Establish whether and how its scope covers Holder/Overall in the current shadow. Capture governing history and tests when they clarify that scope. Do not decide solely from the prohibition's name.

Trace source restriction -> model-visible claim -> selected parent refs -> capability -> final axis. Show exactly where a restriction is present, dropped, ignored, or intentionally local to a different component. Preserve cautionary use; do not ban all working-capital evidence.

The original Samsung Holder has a sole selected relation ref. Evaluate that actual selection. Do not retroactively supply unselected evidence to justify REVIEW. Other subjects with separately selected CAPEX/dilution risk may have independent support; evaluate permissions per source, not by ticker or parent-list size.

If the restriction covers Holder and is lost, record a confirmed bounded entitlement defect and minimal affected owner. **Do not patch it in M12CZ.** If scope remains unresolved, state the missing contract/history rather than declaring a bug proven.

## 6. S2 — SK hynix source correctness, anomaly policy and selected reasons

Starting from OpenDART receipt `20260814003509` as recorded in the frozen source, verify the actual document identity, consolidated basis, period and single-quarter columns. Do not trust the receipt label alone.

Match recorded revenue `79318746000000` KRW and operating income `60542608000000` KRW to source rows; inspect net profit, tax and nonoperating components only to the extent those same-period statements/notes own them. Do not invent a one-off explanation.

Export exact current-historical predicates from the actual owners (reported paths include `app/services/financial_validation.py`, `app/services/data_coverage_service.py`, `app/services/financial_quality_service.py`). Show which rule, threshold and severity produced:
- `net_income_exceeds_revenue`;
- `unusually_high_or_low_operating_margin`;
- `preliminary_profitability_outlier`.

M12CY describes a 60% margin threshold. Verify the exact versioned predicate and its callers; do not accept the reviewer summary as an executable proof. Trace source `full_statement` versus inherited aggregate preliminary reason, direct fact eligibility versus derived TTM/forward valuation, and any intended taint isolation.

Separate:
1. identity/period/unit or arithmetic error;
2. unusual-but-reported value requiring reconciliation;
3. nonrecurring/unsustainable economic performance;
4. material business impairment.

One does not automatically imply another. Even matching official headlines does not validate all derived values. Propose a narrowly supported change only if needed; do not remove anomaly detection or adjust thresholds to clear this ticker.

### Selected expectations-only support question

The exact selected bearish claim is:
`maturity-claim:3c37cce411c8282169a39768be533807ae6c643f354478d7aa1e5b8c9fed20e4`, parent `decision-evidence:e69aab50953f46aec513`.

Its recorded text is: "HBM4 램프업과 높은 메모리 수익성 지속 기대가 이미 매우 높다."

Inspect the full selected parent and governing Overall policy. Does this establish independently meaningful business/cycle risk or only expectations/price reflection? Do not relabel an expectation as business evidence just because it is inside a bearish Core claim.

Report policy acceptance separately from source truth and causal attribution. It remains NOT_CLOSED unless justified by the already selected evidence and approved policy. Do not force BUY, reconstruct hidden model weights, or claim confidence caused HOLD. Apply the same interpretive distinction to Samsung's high-expectation contribution where relevant; do not expand into a new 22-name calibration run.

## 7. S3 — CPNG legacy FCF entitlement

Trace selected parent `decision-evidence:c6b338c45aaae1f1cb71` and its margin/FCF claim. The stored narrative includes a TTM FCF contraction and mixes a narrative as-of with older price/chart dates.

Determine:
- original publication/source, factual event dates and provenance of the exact FCF number;
- TTM period endpoints, currency/unit, FCF definition and current/prior comparable values;
- whether margin deterioration has independent, adequately selected support;
- whether `cash_flow_user_visible = SUPPRESSED` / `ai_enabled=false` is a display/feature gate, global source entitlement, or another policy;
- whether the legacy path is an independently permitted source or an unverified bypass.

Do not conclude either "SUPPRESSED means FCF is false/forbidden everywhere" or "registered legacy thesis means FCF is verified". Both require owner/source proof. Do not silently convert management-adjusted FCF to OCF-minus-CAPEX, add mismatched periods, update the narrative date, or remove a legitimate source merely to enforce a module flag.

If provenance is absent, isolate the unverified metric without rewriting the historical output. Propose source binding or narrower prose based on actually independently selected facts; implement neither here.

## 8. Exact evidence export, not another summary-only audit

For each owner finding include a short source excerpt with path, pinned commit, line range and byte SHA. Include the read-only command used and relevant caller/test/history evidence. For each financial amount include the actual machine row or table excerpt with source identity and period.

Provide `finding -> source locator -> governing rule -> observation -> conclusion -> remaining uncertainty`. An earlier PASS marker, registered ref, reviewer statement or current default-branch file is not a substitute for the required evidence.

Keep exports targeted. No repository-wide audit, new contract framework, full historical-backtest project or bulk formatting.

## 9. P — nineteen fixed-output WAIT previews

Use all and only the existing 19 WAIT rows. Keep original labels, scores, reasons, evidence refs, archetype/tier and all raw numeric fields unchanged. No A/B call.

Create document previews that separate:
1. original long-term/holder/new-buyer labels (with review flags outside the labels);
2. the actual waiting condition;
3. historical conditional valuation reference, when present;
4. tactical support, only when selected and separately labeled;
5. existing re-evaluation conditions;
6. unresolved data/basis and the frozen as-of date.

PRICE_WAIT / BUSINESS_CONFIRMATION_WAIT / VALUATION_INPUT_UNRESOLVED / MIXED_WAIT are document tags only, not new runtime enums. Derive them from the actual reason and documented predicates, not merely the presence of a band. GOOGL's primary tag is business-confirmation; no buy-on-rise or price-wait predicate is inferred from a band above current price.

Five numeric ranges and fourteen unresolved cases retain their original identity. Refer to them as conditional historical-method references, not certified intrinsic value. No new percentile tier, fair-price formula, discount, EPS, technical level, checkpoint date or threshold.

For disputed Samsung/CPNG/SK findings, preserve the current label and display an audit annotation such as "근거 사용 범위 확인 중". REVIEW PENDING is not a new investment stance or a corrected accepted result.

Clearly distinguish copied model conditions from reviewer-proposed, nonnumeric wording. New reviewer suggestions must be labeled proposals and cannot be counted as original model evidence or release triggers. Do not suppress inconvenient original facts while calling the message unchanged.

Create a source-binding table proving every displayed number and source-based statement came from its stated lane. No ordinary renderer or production schema edit is needed: generate MD/JSON previews outside the runtime tree.

## 10. Minimum-change decision, not automatic repair

For each named finding select:
- KEEP_AS_IS;
- PRESENTATION_ONLY;
- CONFIRMED_SOURCE_ENTITLEMENT_DEFECT_REPAIR_PROPOSAL;
- SOURCE_DATA_RECONCILIATION_REQUIRED;
- POLICY_APPLICATION_REQUIRES_CHAT;
- DEFER_EXACT_MISSING_ARTIFACT.

Name the smallest existing owner and expected input/output scope. State whether evidence/claim semantics or A inputs would change. Frozen-A reuse is not automatic when source semantics change. Pure wording previews require no inference. Any later B or A+B proof must be separately authorized.

LS/POSCO archetype and broad historical-multiple method policy remain parked review questions; do not open another A-classification workstream here. Do not expand this task to every review disagreement.

## 11. Required artifacts and completion

Required deliverables:
- `SOURCE_RECONCILIATION_DECISION.md` with confirmed findings versus remaining gaps;
- `source-binding-and-retrieval-manifest.json` (F/R/X lanes, cutoff and retrieval times);
- `historical-owner-evidence-index.json` and targeted exact code/history exports;
- `working-capital-operands-and-entitlement.json` for the four named relations;
- `financial-quality-source-and-predicate-reconciliation.json`;
- `expectation-only-overall-support-review.json`;
- `cpng-fcf-source-and-suppression-scope.json`;
- `WAIT_PREVIEW_19.md` and machine source/display binding table;
- `original-output-immutability-check.json`;
- `MINIMUM_CHANGE_DECISION.md` and a finite residual-gap ledger;
- safety counters, program completion, artifact manifest and ZIP SHA sidecar.

Do not run the entire pytest suite or re-certify provider/schema/old Full22 proofs for this document-only task. Targeted audit-helper arithmetic/hash checks are appropriate, but report their true scope. Preserve M12CY's original classifications and record Chat corrections as a separate overlay.

Complete when all named targets have either source-backed findings or precise missing-artifact records, all 19 previews are source-bound and input-preserving, and the next minimal decisions are explicit. A missing filing is a bounded gap, not permission to fabricate or restart inference.

Terminal choices:
- `M12CZ_SOURCE_RECONCILIATION_AND_WAIT_PREVIEW_READY_FOR_CHAT_DECISION`;
- `M12CZ_COMPLETE_WITH_NAMED_SOURCE_GAPS`;
- `M12CZ_REQUIRED_FROZEN_SOURCE_BINDING_FAILED`.

None means investment accuracy, canonical M12CX PASS, production integration or deployment authorization. The 22-name development set is already revealed, not a blind holdout.

## 12. Hard safety and stopping boundary

- Additional model/provider-inference/CLI inference jobs: 0.
- A/B/Core output reruns or repairs: 0.
- Current-market or fundamental refresh/ingestion: 0.
- Targeted historical-source reads: only the logged finite scope in section 4.
- Production/shadow decision policy, prompts, schemas, validators, materializers and configuration edits: 0.
- Original source/accepted-output/valuation-band rewrites: 0.
- Broker operations, production writes/intents/sends, scheduler changes, merge, push and deploy: 0.

Frozen KRX night-futures/Treasury paths are out of scope; Kiwoom screenshots remain comparison fixtures, not a gateway requirement. Do not revisit transport-timeout design or formatting debt.

Return to Chat with the dossier and previews. Do not automatically start a code repair, A/B run or deployment.
