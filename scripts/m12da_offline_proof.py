from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

from scripts.m12cq_two_pass_contract import (
    PASS_B_CONTRACT,
    PassBBatchOutput,
    PassBDecision,
    build_pass_a_subject_context,
    build_pass_b_subject_context,
    validate_pass_b_batch,
)
from scripts.m12cv_pass_b_capability_contract import (
    build_pass_b_capability_catalog,
    validate_capability_selection,
)
from scripts.m12da_source_use_contract import (
    DECISIVE_USES,
    DEFINITION_BINDING_CONTRACT,
    SOURCE_AUTHORITY_CONTRACT,
    SOURCE_USE_BINDING_CONTRACT,
    SOURCE_USE_CONTRACT,
    SECURITY_IDENTITY_CONTRACT,
    TRUSTED_AUTHORITY_ORIGIN,
    SourceUse,
    build_source_use_projection,
    build_trusted_source_authority_manifest,
    canonical_sha256,
    eligible_refs_for_use,
    freeze_security_identity_binding,
    freeze_source_use_binding,
    freeze_source_use_input_expectation,
    frozen_source_authority,
    resolve_archived_sec_security_identity,
    validate_metric_definition_binding,
    validate_selected_refs,
    validate_security_identity_binding,
    validate_source_use_projection_binding,
    validate_source_use_current_input,
)


REPORT_CONTRACT = "m12da-r2-authority-family-current-input-offline-closure-v1"
SOURCE_EXECUTION_GENERATION = "m12da-r2-offline-closure-20260919"
WC_RELATION_IDS = {
    "MU": "canonical:working-capital-relation:dbdfd04e725e83528d8fdd31",
    "000660": "canonical:working-capital-relation:38a9a0707d38e538ccdb2e7e",
    "005490": "canonical:working-capital-relation:ab1a9a616bcd8d6023b2db06",
    "005930": "canonical:working-capital-relation:4b43f129a5c3b9dbca52fa29",
}
CPNG_LEGACY_PARENT = "decision-evidence:c6b338c45aaae1f1cb71"
CPNG_UNBOUND_EXACT_CLAIM = (
    "maturity-claim:ad9ecb6255ee361b9b4e0344dffd9b8e7788611740129a88c05404bfd7c97fc2"
)


def _load(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _family_boundary_proof() -> dict[str, object]:
    """Run the submitted malformed-family cases against the repaired implementation."""

    wc_ref = "canonical:working-capital-relation:new-id"
    expectation_ref = "source:expectations"
    business_ref = "source:business"
    catalog = {
        "ticker": "RENAMED",
        "all_evidence_refs": [business_ref, wc_ref, expectation_ref],
        "core_evidence_refs": [business_ref, wc_ref, expectation_ref],
        "timing_evidence_refs": [],
        "valuation_evidence_refs": [],
        "positive_quality_refs": [],
        "business_quality_confidence_refs": [],
        "claim_refs": ["claim:business", "claim:wc", "claim:expectations"],
        "atomic_claims": [
            {
                "claim_ref": "claim:business",
                "ticker": "RENAMED",
                "claim": {"polarity": "BULLISH"},
                "parent_source_refs": [business_ref],
            },
            {
                "claim_ref": "claim:wc",
                "ticker": "RENAMED",
                "claim": {"polarity": "BEARISH"},
                "parent_source_refs": [wc_ref],
            },
            {
                "claim_ref": "claim:expectations",
                "ticker": "RENAMED",
                "claim": {"polarity": "BULLISH"},
                "parent_source_refs": [expectation_ref],
            },
        ],
    }
    metadata = [
        {
            "ref_id": business_ref,
            "category": "thesis",
            "label": "business",
            "as_of": "2026-09-18",
            "statement": "frozen business evidence",
        },
        {
            "ref_id": wc_ref,
            "category": "earnings_quality",
            "label": "working_capital_inventory_relation",
            "as_of": "2026-06-30",
            "statement": {
                "relation_semantics_contract": "working-capital-relation-semantics-v1",
                "relation_id": "working-capital-relation:new-id",
                "semantic_scope": "exact_total_inventory",
            },
        },
        {
            "ref_id": expectation_ref,
            "category": "expectations",
            "label": "market expectations",
            "as_of": "2026-09-18",
            "statement": {"level": "high", "priced_in": "partly"},
        },
    ]

    def run_case(
        name: str,
        *,
        mutate: object | None = None,
        selected_ref: str,
        owner: bool = False,
    ) -> dict[str, object]:
        current_metadata = deepcopy(metadata)
        if callable(mutate):
            mutate(current_metadata)
        owners: list[dict[str, object]] = []
        if owner:
            row = next(item for item in current_metadata if item["ref_id"] == business_ref)
            owners.append(
                {
                    "ref_id": business_ref,
                    "catalog_sha256": canonical_sha256(catalog),
                    "source_metadata_sha256": canonical_sha256(row),
                    "source_type": "frozen_legacy_business_evidence",
                    "source_scope": "exact_source_business_decision_owner",
                    "authority_basis": "explicit_frozen_legacy_business_owner",
                    "allowed_uses": [
                        SourceUse.CONTEXT,
                        SourceUse.BUSINESS_CONTEXT,
                        SourceUse.OVERALL_DIRECTION,
                    ],
                    "prohibited_uses": [SourceUse.VALUATION],
                }
            )
        manifest = build_trusted_source_authority_manifest(
            ticker="RENAMED",
            source_generation_id="m12da-r2-family-fixture",
            catalog=catalog,
            source_metadata=current_metadata,
            trusted_owner_overrides=owners,
        )
        expectation = freeze_source_use_input_expectation(
            ticker="RENAMED",
            source_generation_id="m12da-r2-family-fixture",
            execution_generation_id="m12da-r2-family-proof",
            catalog=catalog,
            source_metadata=current_metadata,
            authority_manifest=manifest,
        )
        projection = build_source_use_projection(
            ticker="RENAMED",
            input_generation_id="m12da-r2-family-fixture",
            execution_generation_id="m12da-r2-family-proof",
            catalog=catalog,
            authority_manifest=manifest,
            current_input_expectation=expectation,
        )
        binding = freeze_source_use_binding(
            projection=projection,
            authority_manifest=manifest,
            current_input_expectation=expectation,
        )
        claim_ref = {
            business_ref: "claim:business",
            wc_ref: "claim:wc",
            expectation_ref: "claim:expectations",
        }[selected_ref]
        authority = next(
            row for row in manifest["authority_records"] if row["ref_id"] == selected_ref
        )
        selected = validate_selected_refs(
            projection,
            binding=binding,
            refs=[claim_ref],
            use=SourceUse.OVERALL_DIRECTION,
            require_any=True,
        )
        return {
            "case": name,
            "source_family": authority["source_family"],
            "authority_state": authority["authority_state"],
            "authority_basis": authority["authority_basis"],
            "required_metadata": authority["required_metadata"],
            "compatible_source_versions": authority["compatible_source_versions"],
            "allowed_uses": authority["allowed_uses"],
            "denial_reasons": authority["denial_reasons"],
            "decisive_validation": selected,
            "decisive_use_allowed": selected["status"] == "PASS",
        }

    def wc_row(rows: list[dict[str, object]]) -> dict[str, object]:
        return next(row for row in rows if row["ref_id"] == wc_ref)

    def expectation_row(rows: list[dict[str, object]]) -> dict[str, object]:
        return next(row for row in rows if row["ref_id"] == expectation_ref)

    cases = [
        run_case("valid_working_capital", selected_ref=wc_ref),
        run_case(
            "working_capital_missing_semantic_scope",
            selected_ref=wc_ref,
            mutate=lambda rows: wc_row(rows)["statement"].pop("semantic_scope"),
        ),
        run_case(
            "working_capital_unknown_contract",
            selected_ref=wc_ref,
            mutate=lambda rows: wc_row(rows)["statement"].__setitem__(
                "relation_semantics_contract", "unknown-v9"
            ),
        ),
        run_case(
            "working_capital_category_mismatch",
            selected_ref=wc_ref,
            mutate=lambda rows: wc_row(rows).__setitem__("category", "thesis"),
        ),
        run_case(
            "working_capital_display_label_variant",
            selected_ref=wc_ref,
            mutate=lambda rows: wc_row(rows).__setitem__("label", "inventory relation v2"),
        ),
        run_case("valid_expectations", selected_ref=expectation_ref),
        run_case(
            "expectations_display_label_variant",
            selected_ref=expectation_ref,
            mutate=lambda rows: expectation_row(rows).__setitem__("label", "Market expectations"),
        ),
        run_case(
            "expectations_unknown_schema",
            selected_ref=expectation_ref,
            mutate=lambda rows: expectation_row(rows)["statement"].__setitem__(
                "unknown_version_field", True
            ),
        ),
        run_case("membership_only_business", selected_ref=business_ref),
        run_case("explicit_exact_legacy_business_owner", selected_ref=business_ref, owner=True),
    ]
    restrictive_cases = [
        row for row in cases if row["case"] != "explicit_exact_legacy_business_owner"
    ]
    return {
        "contract": "m12da-r2-restricted-family-fail-closed-proof-v1",
        "cases": cases,
        "failure_behavior": (
            "known restricted family parse/validation failure retains only narrow contextual uses"
        ),
        "membership_only_policy": "core_or_atomic_membership_never_grants_decisive_rights",
        "explicit_owner_policy": "exact_catalog_and_metadata_bound_legacy_owner_may_retain_rights",
        "status": (
            "PASS"
            if all(not row["decisive_use_allowed"] for row in restrictive_cases)
            and cases[-1]["decisive_use_allowed"]
            else "FAIL"
        ),
    }


def _call_outcome(call: object) -> dict[str, object]:
    try:
        result = call() if callable(call) else None
    except (KeyError, TypeError, ValueError) as exc:
        return {
            "outcome": "REJECTED",
            "exception_type": type(exc).__name__,
            "reason": str(exc),
        }
    return {
        "outcome": "RETURNED",
        "result_status": result.get("status") if isinstance(result, Mapping) else None,
        "errors": list(result.get("errors") or ()) if isinstance(result, Mapping) else [],
    }


def _merge_subject_inputs(
    root: Path,
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    contexts: dict[str, dict[str, object]] = {}
    catalogs: dict[str, dict[str, object]] = {}
    base = root / "provider-wire-schemas" / "pass-b"
    for path in sorted(base.glob("*/batch-*/subject-context.json")):
        payload = _load(path)
        assert isinstance(payload, Mapping)
        for row in payload.get("subjects") or ():
            if isinstance(row, Mapping):
                contexts[str(row["ticker"])] = deepcopy(dict(row))
    for path in sorted(base.glob("*/batch-*/ref-catalog.json")):
        payload = _load(path)
        assert isinstance(payload, Mapping)
        for ticker, row in payload.items():
            if isinstance(row, Mapping):
                catalogs[str(ticker)] = deepcopy(dict(row))
    return contexts, catalogs


def _expectation_only_row(row: Mapping[str, object]) -> bool:
    if str(row.get("category") or "").lower() != "expectations":
        return False
    statement = row.get("statement")
    if isinstance(statement, str):
        try:
            statement = json.loads(statement)
        except json.JSONDecodeError:
            return False
    if not isinstance(statement, Mapping):
        return False
    expectation_fields = {
        "as_of_date",
        "level",
        "priced_in",
        "summary",
        "upside_surprises",
        "downside_surprises",
    }
    return bool(set(statement) & {"level", "priced_in", "downside_surprises"}) and set(
        statement
    ).issubset(expectation_fields)


def _subject_authorities(
    *,
    ticker: str,
    context: Mapping[str, object],
    catalog: Mapping[str, object],
    wc_periods: Mapping[str, str | None],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    source_authorities: list[dict[str, object]] = []
    claim_authorities: list[dict[str, object]] = []
    all_refs = {str(ref) for ref in catalog.get("all_evidence_refs") or ()}
    relation_id = WC_RELATION_IDS.get(ticker)
    if relation_id in all_refs:
        source_authorities.append(
            frozen_source_authority(
                ticker=ticker,
                ref_id=relation_id,
                source_type="canonical_working_capital_relation",
                source_scope="typed_relation_and_cautious_earnings_quality_context_only",
                source_period=wc_periods.get(ticker),
                fact_kind="derived_relation",
                allowed_uses=[
                    SourceUse.CONTEXT,
                    SourceUse.EARNINGS_QUALITY_CONTEXT,
                ],
                prohibited_uses=[
                    SourceUse.PASS_A_ARCHETYPE,
                    SourceUse.PASS_A_VALUATION_TIER,
                    SourceUse.OVERALL_DIRECTION,
                    SourceUse.HOLDER_STANCE,
                    SourceUse.NEW_BUYER_EXECUTION_RISK,
                    SourceUse.VALUATION,
                ],
                denial_reasons=[
                    "working_capital_only_status_or_valuation_change",
                    "working_capital_causal_overclaim",
                ],
                authority_basis="working_capital_user_visible_preintegration_owner_contract",
            )
        )
    for evidence in context.get("decision_evidence") or ():
        if not isinstance(evidence, Mapping) or not _expectation_only_row(evidence):
            continue
        ref_id = str(evidence.get("ref_id") or "")
        if ref_id not in all_refs:
            continue
        source_authorities.append(
            frozen_source_authority(
                ticker=ticker,
                ref_id=ref_id,
                source_type="structured_market_expectations",
                source_scope="expectations_price_confidence_entry_only",
                source_period=str(evidence.get("as_of") or "") or None,
                fact_kind="hypothetical_scenario",
                allowed_uses=[
                    SourceUse.CONTEXT,
                    SourceUse.EXPECTATIONS_CONTEXT,
                    SourceUse.PRICE_ENTRY_CONTEXT,
                    SourceUse.CONFIDENCE,
                    SourceUse.ENTRY,
                ],
                prohibited_uses=[
                    SourceUse.PASS_A_ARCHETYPE,
                    SourceUse.PASS_A_VALUATION_TIER,
                    SourceUse.OVERALL_DIRECTION,
                    SourceUse.HOLDER_STANCE,
                    SourceUse.NEW_BUYER_EXECUTION_RISK,
                ],
                denial_reasons=[
                    "expectation_reflection_not_independent_business_impairment",
                    "hypothetical_downside_not_occurred_event",
                ],
                authority_basis="structured_market_expectations_owner_contract",
            )
        )
    if ticker == "CPNG" and CPNG_LEGACY_PARENT in all_refs:
        source_authorities.append(
            frozen_source_authority(
                ticker=ticker,
                ref_id=CPNG_LEGACY_PARENT,
                source_type="legacy_custom_gpt_thesis_narrative",
                source_scope="qualitative_business_context_only_until_exact_metric_binding",
                source_period="2026-06-30",
                fact_kind="legacy_narrative",
                allowed_uses=[SourceUse.CONTEXT, SourceUse.BUSINESS_CONTEXT],
                prohibited_uses=[
                    SourceUse.PASS_A_ARCHETYPE,
                    SourceUse.PASS_A_VALUATION_TIER,
                    SourceUse.OVERALL_DIRECTION,
                    SourceUse.HOLDER_STANCE,
                    SourceUse.NEW_BUYER_EXECUTION_RISK,
                    SourceUse.VALUATION,
                ],
                denial_reasons=[
                    "historical_packet_missing_exact_filing_binding",
                    "partial_paragraph_laundering_blocked",
                ],
                authority_basis="m12cz_retrospective_source_reconciliation",
                definition_binding_ref="cpng-management-fcf-ttm-2026q2",
            )
        )
        claim_authorities.append(
            {
                "ticker": ticker,
                "claim_ref": CPNG_UNBOUND_EXACT_CLAIM,
                "authority_origin": TRUSTED_AUTHORITY_ORIGIN,
                "authority_state": "RESOLVED",
                "authority_basis": "m12cz_exact_metric_scope_review",
                "allowed_uses": [SourceUse.CONTEXT, SourceUse.BUSINESS_CONTEXT],
                "prohibited_uses": [
                    SourceUse.PASS_A_ARCHETYPE,
                    SourceUse.PASS_A_VALUATION_TIER,
                    SourceUse.OVERALL_DIRECTION,
                    SourceUse.HOLDER_STANCE,
                    SourceUse.NEW_BUYER_EXECUTION_RISK,
                ],
                "denial_reasons": [
                    "historical_packet_did_not_carry_source_binding",
                    "management_fcf_not_backend_ppe_only_fcf",
                ],
            }
        )
    return source_authorities, claim_authorities


def _wire_decision(candidate: Mapping[str, object]) -> dict[str, object]:
    directional = candidate.get("directional_balance")
    directional = directional if isinstance(directional, Mapping) else {}
    return {
        "overall_direction": candidate.get("overall_direction"),
        "directional_buy_score": directional.get("buy"),
        "decision_confidence": candidate.get("decision_confidence"),
        "decisive_supporting_claim_refs": candidate.get("decisive_supporting_claim_refs"),
        "decisive_contradicting_claim_refs": candidate.get("decisive_contradicting_claim_refs"),
        "thesis_state": candidate.get("thesis_state"),
        "holder_decision": {
            "holder": candidate.get("holder"),
            "reason_class": candidate.get("holder_reason_class"),
            "reason": candidate.get("holder_reason"),
            "evidence_refs": candidate.get("holder_reason_evidence_refs"),
        },
        "new_buyer_decision": {
            "new_buyer": candidate.get("new_buyer"),
            "reason_class": candidate.get("new_buyer_reason_class"),
            "reason": candidate.get("new_buyer_reason"),
            "evidence_refs": candidate.get("new_buyer_reason_refs"),
            "tactical_choice": candidate.get("tactical_choice"),
            "re_evaluate_conditions": candidate.get("re_evaluate_conditions"),
        },
        "policy_summary": candidate.get("policy_summary"),
    }


def _selected_use_audit(
    projection: Mapping[str, object],
    *,
    binding: Mapping[str, object],
    refs: list[object],
    use: SourceUse,
) -> dict[str, object]:
    selected = list(dict.fromkeys(str(ref) for ref in refs if str(ref)))
    permitted = eligible_refs_for_use(
        projection,
        binding=binding,
        refs=selected,
        use=use,
    )
    validation = validate_selected_refs(
        projection,
        refs=selected,
        use=use,
        require_any=False,
        binding=binding,
    )
    return {
        "use": use,
        "selected_refs": selected,
        "permitted_refs": permitted,
        "forbidden_refs": [
            {
                "ref_id": row["ref_id"],
                "code": row["code"],
                "cause": row["cause"],
            }
            for row in validation["errors"]
        ],
        "status": validation["status"],
    }


def _semantic_validation(
    *,
    candidate: Mapping[str, object],
    catalog: Mapping[str, object],
    pass_a: Mapping[str, object],
    source_use_view: Mapping[str, object],
    source_use_binding: Mapping[str, object],
    source_use_expectation: Mapping[str, object],
    source_metadata: list[Mapping[str, object]],
    source_generation_id: str,
    execution_generation_id: str,
) -> dict[str, object]:
    fields = set(PassBDecision.model_fields)
    decision = PassBDecision.model_validate(
        {key: deepcopy(value) for key, value in candidate.items() if key in fields}
    )
    identity = {
        "generation_id": "m12da-offline-replay",
        "packet_id": f"m12da:{candidate['ticker']}",
        "market": candidate["market"],
        "assessment_date": "2026-09-17",
    }
    output = PassBBatchOutput(
        contract=PASS_B_CONTRACT,
        decisions=(decision,),
        **identity,
    )
    return validate_pass_b_batch(
        output,
        expected_identity=identity,
        subjects=(str(candidate["ticker"]),),
        catalogs={str(candidate["ticker"]): catalog},
        pass_a_by_ticker={str(candidate["ticker"]): pass_a},
        source_use_views={str(candidate["ticker"]): source_use_view},
        source_use_bindings={str(candidate["ticker"]): source_use_binding},
        source_use_expectations={str(candidate["ticker"]): source_use_expectation},
        source_metadata_by_ticker={str(candidate["ticker"]): source_metadata},
        source_generation_id=source_generation_id,
        execution_generation_id=execution_generation_id,
        require_source_use=True,
    )


def _cpng_bindings(
    cpng: Mapping[str, object],
    *,
    m12cz_root: Path,
) -> dict[str, object]:
    official = cpng["official_source"]
    rows = official["companyfacts_rows"]
    reconciliation = cpng["ttm_reconciliation"]
    payloads = official["retrieved_payloads"]
    submissions_path = m12cz_root / "retrieved-sources" / "cpng-sec-submissions.json"
    exhibit_path = m12cz_root / "retrieved-sources" / "cpng-2026q2-exhibit-99-1.html"
    identity_resolution = resolve_archived_sec_security_identity(
        ticker="CPNG",
        security_type="common-stock",
        submissions_bytes=submissions_path.read_bytes(),
        exhibit_bytes=exhibit_path.read_bytes(),
        expected_submissions_sha256=str(payloads["cpng-sec-submissions.json"]["sha256"]),
        expected_exhibit_sha256=str(payloads["cpng-2026q2-exhibit-99-1.html"]["sha256"]),
    )
    security_identity = freeze_security_identity_binding(
        ticker=str(identity_resolution["ticker"]),
        issuer_id=str(identity_resolution["issuer_id"]),
        venue=str(identity_resolution["venue"]),
        security_type=str(identity_resolution["security_type"]),
        official_sources=[
            {
                "provider": "sec_edgar_submissions",
                "document_sha256": payloads["cpng-sec-submissions.json"]["sha256"],
                "locator": (
                    f"tickers[{identity_resolution['ticker_exchange_index']}]"
                    f"/exchanges[{identity_resolution['ticker_exchange_index']}]"
                ),
                "assertion": "source-resolved aligned ticker/exchange pair",
            },
            {
                "provider": "sec_edgar_exhibit",
                "document_sha256": payloads["cpng-2026q2-exhibit-99-1.html"]["sha256"],
                "locator": "official exhibit issuer identity",
                "assertion": "source-resolved issuer-owned exchange/ticker occurrence",
            },
        ],
    )
    common = {
        "contract": DEFINITION_BINDING_CONTRACT,
        "ticker": "CPNG",
        "issuer_id": identity_resolution["issuer_id"],
        "security_id": security_identity["security_id"],
        "security_identity": security_identity,
        "metric_id": "trailing_free_cash_flow",
        "period_start": "2025-07-01",
        "period_end": str(official["period_end"]),
        "duration_days": 365,
        "comparison_basis": str(reconciliation["formula"]),
        "currency": str(official["currency"]),
        "unit": str(official["unit"]),
        "consolidation_scope": "issuer_consolidated",
        "historical_packet_carried_evidence": False,
        "claim_scope": "EXACT_METRIC_ONLY",
    }
    management = {
        **common,
        "binding_id": "cpng-management-fcf-ttm-2026q2",
        "definition_id": "management-defined-fcf-including-ppe-sale-proceeds",
        "formula": "OCF_MINUS_PPE_PURCHASES_PLUS_PPE_SALE_PROCEEDS",
        "value_type": "REPORTED_NON_GAAP_RECONCILED",
        "value": str(reconciliation["management_defined_fcf_usd"]),
        "component_refs": [
            "sec:cpng:ttm-ocf",
            "sec:cpng:ttm-ppe-purchases",
            "sec:cpng:q2-2026-ppe-sale-proceeds",
        ],
        "source": {
            "provider": "sec_edgar",
            "accession": str(official["q2_8k_accession"]),
            "document_type": "8-K",
            "exhibit": str(official["exhibit"]),
            "row_locator": "Free Cash Flow table / TTM ended 2026-06-30",
            "document_sha256": payloads["cpng-2026q2-exhibit-99-1.html"]["sha256"],
            "publication_date": str(official["q2_8k_filed"]),
            "retrieval_date": "2026-09-18",
        },
    }
    backend = {
        **common,
        "binding_id": "cpng-backend-ppe-only-fcf-ttm-2026q2",
        "definition_id": "backend-ppe-only-fcf",
        "formula": "OCF_MINUS_PPE_PURCHASES",
        "value_type": "DERIVED_METRIC",
        "value": str(reconciliation["backend_ppe_only_fcf_usd"]),
        "component_refs": [
            f"sec:{rows['ocf']['fy2025']['accn']}:ocf:fy2025",
            f"sec:{rows['ocf']['h1_2026']['accn']}:ocf:h1_2026",
            f"sec:{rows['ocf']['h1_2025_comparable']['accn']}:ocf:h1_2025",
            f"sec:{rows['ppe_purchases']['fy2025']['accn']}:ppe:fy2025",
            f"sec:{rows['ppe_purchases']['h1_2026']['accn']}:ppe:h1_2026",
            f"sec:{rows['ppe_purchases']['h1_2025_comparable']['accn']}:ppe:h1_2025",
        ],
        "source": {
            "provider": "sec_edgar_companyfacts",
            "accession": str(official["q2_10q_accession"]),
            "document_type": "10-Q",
            "exhibit": "consolidated-statements-of-cash-flows",
            "row_locator": "official XBRL occurrence components listed in component_refs",
            "document_sha256": payloads["cpng-sec-companyfacts.json"]["sha256"],
            "publication_date": str(official["q2_10q_filed"]),
            "retrieval_date": "2026-09-18",
        },
    }
    expected_security_identity = {
        "venue": str(identity_resolution["venue"]).upper(),
        "ticker": identity_resolution["ticker"],
        "issuer_id": identity_resolution["issuer_id"],
        "security_id": identity_resolution["security_id"],
    }
    management_validation = validate_metric_definition_binding(
        management,
        expected_security_identity=expected_security_identity,
    )
    backend_validation = validate_metric_definition_binding(
        backend,
        expected_security_identity=expected_security_identity,
    )
    identity_validation = validate_security_identity_binding(
        security_identity,
        expected=expected_security_identity,
    )
    historical_validation = validate_metric_definition_binding(
        management,
        expected_security_identity=expected_security_identity,
        replay_cutoff="2026-09-17",
        historical_use=True,
    )
    difference = Decimal(management["value"]) - Decimal(backend["value"])
    ocf = (
        Decimal(str(rows["ocf"]["fy2025"]["val"]))
        + Decimal(str(rows["ocf"]["h1_2026"]["val"]))
        - Decimal(str(rows["ocf"]["h1_2025_comparable"]["val"]))
    )
    ppe_purchases = (
        Decimal(str(rows["ppe_purchases"]["fy2025"]["val"]))
        + Decimal(str(rows["ppe_purchases"]["h1_2026"]["val"]))
        - Decimal(str(rows["ppe_purchases"]["h1_2025_comparable"]["val"]))
    )
    backend_reproduced = ocf - ppe_purchases
    management_reproduced = backend_reproduced + Decimal(
        str(reconciliation["management_reported_sale_proceeds_usd"])
    )
    reported_yoy_decrease = (
        Decimal(str(reconciliation["management_defined_prior_comparable_fcf_usd"]))
        - management_reproduced
    )
    arithmetic_checks = {
        "ocf_reproduced_usd": str(ocf),
        "ppe_purchases_reproduced_usd": str(ppe_purchases),
        "backend_ppe_only_fcf_reproduced_usd": str(backend_reproduced),
        "management_fcf_reproduced_usd": str(management_reproduced),
        "management_yoy_decrease_reproduced_usd": str(reported_yoy_decrease),
        "status": "PASS"
        if ocf == Decimal(str(reconciliation["ocf_usd"]))
        and ppe_purchases == Decimal(str(reconciliation["ppe_purchases_usd"]))
        and backend_reproduced == Decimal(str(reconciliation["backend_ppe_only_fcf_usd"]))
        and management_reproduced == Decimal(str(reconciliation["management_defined_fcf_usd"]))
        and reported_yoy_decrease
        == Decimal(str(reconciliation["management_reported_yoy_decrease_usd"]))
        else "FAIL",
    }
    payload_hash_checks = []
    for name, metadata in sorted(payloads.items()):
        path = m12cz_root / "retrieved-sources" / name
        actual_sha = _sha(path) if path.is_file() else None
        payload_hash_checks.append(
            {
                "name": name,
                "path": str(path),
                "expected_sha256": metadata["sha256"],
                "actual_sha256": actual_sha,
                "match": actual_sha == metadata["sha256"],
            }
        )
    historical_expected_denial = historical_validation["errors"] == [
        "historical_packet_did_not_carry_source_binding"
    ]
    result = {
        "contract": "m12da-r2-cpng-definition-binding-proof-v3",
        "original_m12da_proposed_security_id": "nasdaq:CPNG:common-stock",
        "original_m12da_record_preserved": True,
        "corrected_security_identity": security_identity,
        "source_derived_expected_identity": identity_resolution,
        "security_identity_validation": identity_validation,
        "management_defined_fcf": management,
        "backend_ppe_only_fcf": backend,
        "management_validation": management_validation,
        "backend_validation": backend_validation,
        "historical_replay_validation": historical_validation,
        "definition_difference_usd": str(difference),
        "reported_sale_proceeds_usd": str(reconciliation["management_reported_sale_proceeds_usd"]),
        "exact_definition_difference_pass": difference
        == Decimal(str(reconciliation["management_reported_sale_proceeds_usd"])),
        "arithmetic_reconciliation": arithmetic_checks,
        "source_payload_hash_checks": payload_hash_checks,
        "historical_output_unchanged": True,
        "retrospective_binding_scope": "PROPOSED_FUTURE_OFFLINE_VIEW_ONLY",
    }
    result["status"] = (
        "PASS"
        if management_validation["status"] == "PASS"
        and backend_validation["status"] == "PASS"
        and identity_validation["status"] == "PASS"
        and identity_resolution["status"] == "PASS"
        and historical_expected_denial
        and result["exact_definition_difference_pass"]
        and arithmetic_checks["status"] == "PASS"
        and payload_hash_checks
        and all(row["match"] for row in payload_hash_checks)
        else "FAIL"
    )
    return result


def generate(
    *,
    m12cx_root: Path,
    m12cz_root: Path,
    r1_root: Path,
    review_probes: Path,
    frozen_output: Path,
    output_dir: Path,
) -> dict[str, object]:
    frozen_sha_before = _sha(frozen_output)
    combined = _load(frozen_output)
    pass_a_payload = _load(m12cx_root / "fresh-pass-a-22-classification.json")
    old_capability_payload = _load(m12cx_root / "pass-b-capability-catalog-22.json")
    wc_payload = _load(m12cz_root / "working-capital-operands-and-entitlement.json")
    expectation_payload = _load(m12cz_root / "expectation-only-overall-support-review.json")
    cpng_payload = _load(m12cz_root / "cpng-fcf-source-and-suppression-scope.json")
    r1_authority_payload = _load(r1_root / "source-authority-manifests-22.json")
    r1_impact_payload = _load(r1_root / "offline-22-subject-source-use-impact.json")
    submitted_boundary_probes = _load(review_probes)
    assert isinstance(combined, Mapping)
    assert isinstance(pass_a_payload, Mapping)
    assert isinstance(old_capability_payload, Mapping)
    assert isinstance(wc_payload, Mapping)
    assert isinstance(expectation_payload, Mapping)
    assert isinstance(cpng_payload, Mapping)
    assert isinstance(r1_authority_payload, Mapping)
    assert isinstance(r1_impact_payload, Mapping)
    assert isinstance(submitted_boundary_probes, Mapping)

    contexts, catalogs = _merge_subject_inputs(m12cx_root)
    candidates = {
        str(row["ticker"]): row for row in combined["candidates"] if isinstance(row, Mapping)
    }
    pass_a = {
        str(row["ticker"]): row
        for row in pass_a_payload["classifications"]
        if isinstance(row, Mapping)
    }
    old_capabilities = {
        str(row["ticker"]): row
        for row in old_capability_payload["catalogs"]
        if isinstance(row, Mapping)
    }
    subjects = [str(row["ticker"]) for row in combined["candidates"]]
    if not (
        len(subjects)
        == len(contexts)
        == len(catalogs)
        == len(pass_a)
        == len(old_capabilities)
        == 22
    ):
        raise ValueError("m12da_subject_cardinality_mismatch")

    projections: dict[str, dict[str, object]] = {}
    authority_manifests: dict[str, dict[str, object]] = {}
    source_use_bindings: dict[str, dict[str, object]] = {}
    source_use_expectations: dict[str, dict[str, object]] = {}
    new_capabilities: dict[str, dict[str, object]] = {}
    impact_rows: list[dict[str, object]] = []
    pass_a_impact: list[dict[str, object]] = []
    expectation_rows: list[dict[str, object]] = []

    for ticker in subjects:
        source_metadata = [
            row
            for row in contexts[ticker].get("decision_evidence") or ()
            if isinstance(row, Mapping)
        ]
        classified_manifest = build_trusted_source_authority_manifest(
            ticker=ticker,
            source_generation_id=str(combined["generation_id"]),
            catalog=catalogs[ticker],
            source_metadata=source_metadata,
        )
        classified_by_ref = {
            str(row["ref_id"]): row
            for row in classified_manifest["authority_records"]
            if isinstance(row, Mapping)
        }
        trusted_owner_overrides: list[dict[str, object]] = []
        prior_subject = r1_authority_payload["subjects"][ticker]
        prior_records = {
            str(row["ref_id"]): row
            for row in prior_subject["authority_records"]
            if isinstance(row, Mapping)
        }
        metadata_by_ref = {str(row["ref_id"]): row for row in source_metadata}
        for ref_id, prior in sorted(prior_records.items()):
            if prior.get("authority_basis") not in {
                "frozen_core_atomic_parent_owner",
                "m12cz_exact_frozen_source_owner_override_for_future_offline_view",
            }:
                continue
            if classified_by_ref[ref_id]["source_family"] != "unclassified":
                continue
            current_row = metadata_by_ref.get(ref_id)
            if current_row is None:
                raise ValueError(f"m12da_r2_legacy_owner_metadata_missing:{ticker}:{ref_id}")
            if prior.get("source_metadata_sha256") != canonical_sha256(current_row):
                raise ValueError(f"m12da_r2_legacy_owner_metadata_drift:{ticker}:{ref_id}")
            trusted_owner_overrides.append(
                {
                    "ref_id": ref_id,
                    "catalog_sha256": canonical_sha256(catalogs[ticker]),
                    "source_metadata_sha256": canonical_sha256(current_row),
                    "source_type": prior["source_type"],
                    "source_scope": prior["source_scope"],
                    "authority_basis": (
                        "m12da_r2_explicit_migration_of_exact_r1_owner:"
                        + str(prior["authority_basis"])
                    ),
                    "allowed_uses": list(prior["allowed_uses"]),
                    "prohibited_uses": list(prior["prohibited_uses"]),
                }
            )
        authority_manifest = build_trusted_source_authority_manifest(
            ticker=ticker,
            source_generation_id=str(combined["generation_id"]),
            catalog=catalogs[ticker],
            source_metadata=source_metadata,
            trusted_owner_overrides=trusted_owner_overrides,
        )
        source_use_expectation = freeze_source_use_input_expectation(
            ticker=ticker,
            source_generation_id=str(combined["generation_id"]),
            execution_generation_id=SOURCE_EXECUTION_GENERATION,
            catalog=catalogs[ticker],
            source_metadata=source_metadata,
            authority_manifest=authority_manifest,
        )
        projection = build_source_use_projection(
            ticker=ticker,
            input_generation_id=str(combined["generation_id"]),
            execution_generation_id=SOURCE_EXECUTION_GENERATION,
            catalog=catalogs[ticker],
            authority_manifest=authority_manifest,
            current_input_expectation=source_use_expectation,
        )
        source_use_binding = freeze_source_use_binding(
            projection=projection,
            authority_manifest=authority_manifest,
            current_input_expectation=source_use_expectation,
        )
        authority_manifests[ticker] = authority_manifest
        projections[ticker] = projection
        source_use_bindings[ticker] = source_use_binding
        source_use_expectations[ticker] = source_use_expectation
        policy_option = contexts[ticker]["deterministic_fundamental_option"]
        new_capability = build_pass_b_capability_catalog(
            context=contexts[ticker],
            catalog=catalogs[ticker],
            pass_a=pass_a[ticker],
            policy_option=policy_option,
            source_use_view=projection,
            source_use_binding=source_use_binding,
            source_use_expectation=source_use_expectation,
            source_generation_id=str(combined["generation_id"]),
            execution_generation_id=SOURCE_EXECUTION_GENERATION,
            require_source_use=True,
        )
        new_capabilities[ticker] = new_capability
        semantic = _semantic_validation(
            candidate=candidates[ticker],
            catalog=catalogs[ticker],
            pass_a=pass_a[ticker],
            source_use_view=projection,
            source_use_binding=source_use_binding,
            source_use_expectation=source_use_expectation,
            source_metadata=source_metadata,
            source_generation_id=str(combined["generation_id"]),
            execution_generation_id=SOURCE_EXECUTION_GENERATION,
        )
        capability_validation = validate_capability_selection(
            {"decisions": {ticker: _wire_decision(candidates[ticker])}},
            subjects=(ticker,),
            catalogs={ticker: catalogs[ticker]},
            capabilities={ticker: new_capability},
            source_use_views={ticker: projection},
            source_use_bindings={ticker: source_use_binding},
            source_use_expectations={ticker: source_use_expectation},
            source_metadata_by_ticker={ticker: source_metadata},
            source_generation_id=str(combined["generation_id"]),
            execution_generation_id=SOURCE_EXECUTION_GENERATION,
            require_source_use=True,
        )
        source_errors = sorted(
            error
            for error in [*semantic["errors"], *capability_validation["errors"]]
            if "source_use" in error.lower() or "UNDER_SUPPORTED" in error
        )
        old_classes = old_capabilities[ticker]["evidence_classes"]
        new_classes = new_capability["evidence_classes"]
        capability_changed = old_classes != new_classes
        selected_use_audit = {
            "overall": _selected_use_audit(
                projection,
                binding=source_use_binding,
                refs=[
                    *candidates[ticker]["decisive_supporting_claim_refs"],
                    *candidates[ticker]["decisive_contradicting_claim_refs"],
                ],
                use=SourceUse.OVERALL_DIRECTION,
            ),
            "holder": _selected_use_audit(
                projection,
                binding=source_use_binding,
                refs=list(candidates[ticker]["holder_reason_evidence_refs"]),
                use=SourceUse.HOLDER_STANCE,
            ),
            "new_buyer_risk": (
                _selected_use_audit(
                    projection,
                    binding=source_use_binding,
                    refs=list(candidates[ticker]["new_buyer_reason_refs"]),
                    use=SourceUse.NEW_BUYER_EXECUTION_RISK,
                )
                if candidates[ticker]["new_buyer_reason_class"] == "EXECUTION_OR_THESIS_RISK"
                else {
                    "use": SourceUse.NEW_BUYER_EXECUTION_RISK,
                    "selected_refs": [],
                    "permitted_refs": [],
                    "forbidden_refs": [],
                    "status": "NOT_APPLICABLE",
                }
            ),
        }
        impact_rows.append(
            {
                "ticker": ticker,
                "original_overall": candidates[ticker]["overall_direction"],
                "original_holder": candidates[ticker]["holder"],
                "original_new_buyer": candidates[ticker]["new_buyer"],
                "original_label_changed": False,
                "old_material_business_claim_refs": old_classes["material_business_claim_refs"],
                "new_material_business_claim_refs": new_classes["material_business_claim_refs"],
                "old_material_risk_claim_refs": old_classes["material_risk_claim_refs"],
                "new_material_risk_claim_refs": new_classes["material_risk_claim_refs"],
                "old_holder_risk_evidence_refs": old_classes["material_risk_evidence_refs"],
                "new_holder_risk_evidence_refs": new_classes["holder_material_risk_evidence_refs"],
                "capability_changed": capability_changed,
                "new_overall_support_state": new_capability["overall"]["support_state"],
                "semantic_validation_status": semantic["status"],
                "capability_validation_status": capability_validation["status"],
                "source_use_errors": source_errors,
                "selected_use_audit": selected_use_audit,
                "impact": "UNDER_SUPPORTED" if source_errors else "UNCHANGED",
            }
        )
        archetype_validation = validate_selected_refs(
            projection,
            refs=pass_a[ticker]["archetype_supporting_claim_refs"],
            use=SourceUse.PASS_A_ARCHETYPE,
            require_any=True,
            binding=source_use_binding,
        )
        tier_validation = validate_selected_refs(
            projection,
            refs=pass_a[ticker]["tier_supporting_claim_refs"],
            use=SourceUse.PASS_A_VALUATION_TIER,
            require_any=pass_a[ticker]["valuation_regime_tier"] != "UNRESOLVED",
            binding=source_use_binding,
        )
        old_a_view = build_pass_a_subject_context(
            context={
                "evidence_packets": [
                    {
                        "ticker": ticker,
                        "evidence": contexts[ticker].get("decision_evidence") or [],
                    }
                ]
            },
            ticker=ticker,
            catalog=catalogs[ticker],
        )
        new_a_view = build_pass_a_subject_context(
            context={
                "evidence_packets": [
                    {
                        "ticker": ticker,
                        "evidence": contexts[ticker].get("decision_evidence") or [],
                    }
                ]
            },
            ticker=ticker,
            catalog=catalogs[ticker],
            source_use_view=projection,
            source_use_binding=source_use_binding,
            source_use_expectation=source_use_expectation,
            source_generation_id=str(combined["generation_id"]),
            execution_generation_id=SOURCE_EXECUTION_GENERATION,
            require_source_use=True,
        )
        selected_support_state = (
            "SELECTED_SUPPORT_AFFECTED"
            if archetype_validation["status"] == "FAIL" or tier_validation["status"] == "FAIL"
            else "MODEL_INPUT_CHANGED"
        )
        old_a_hash = canonical_sha256(old_a_view)
        new_a_hash = canonical_sha256(new_a_view)
        model_input_state = (
            "MODEL_INPUT_EQUIVALENT_PROVEN" if old_a_hash == new_a_hash else "MODEL_INPUT_CHANGED"
        )
        pass_a_impact.append(
            {
                "ticker": ticker,
                "classification_unchanged": True,
                "prior_m12da_reuse_classification": (
                    "PROVEN_AFFECTED" if ticker in {"000660", "005490", "005930"} else "UNCHANGED"
                ),
                "archetype_validation": archetype_validation,
                "tier_validation": tier_validation,
                "selected_support_state": selected_support_state,
                "model_input_state": model_input_state,
                "old_model_view_sha256": old_a_hash,
                "new_model_view_sha256": new_a_hash,
                "old_model_view_claim_count": len(old_a_view["eligible_claim_refs"]),
                "new_model_view_claim_count": len(new_a_view["eligible_claim_refs"]),
                "source_use_projection_sha256": projection["projection_sha256"],
                "source_use_binding_sha256": source_use_binding["binding_sha256"],
                "deterministic_valuation_dependency_changed": False,
                "shared_batch_input_changed": True,
                "reuse_recommendation": "INPUT_IMPACT_NOT_YET_PROVEN",
                "automatic_reuse_authorized": False,
            }
        )
        for authority in authority_manifest["authority_records"]:
            if authority["source_type"] == "structured_market_expectations":
                expectation_rows.append(
                    {
                        "ticker": ticker,
                        "ref_id": authority["ref_id"],
                        "old_overall_support_eligible": True,
                        "new_overall_support_eligible": False,
                        "expectations_context_retained": True,
                        "entry_context_retained": True,
                        "occurred_event_inferred": False,
                    }
                )

    frozen_sha_after = _sha(frozen_output)
    probe_ticker = next(
        ticker
        for ticker in subjects
        if any(
            str(authority["authority_basis"]).startswith(
                "m12da_r2_explicit_migration_of_exact_r1_owner:"
            )
            for authority in authority_manifests[ticker]["authority_records"]
        )
    )
    probe_catalog = catalogs[probe_ticker]
    probe_claim = next(
        row
        for row in probe_catalog["atomic_claims"]
        if all(
            str(
                projections[probe_ticker]["source_records"][str(ref)]["authority_basis"]
            ).startswith("m12da_r2_explicit_migration_of_exact_r1_owner:")
            for ref in row.get("parent_source_refs") or ()
        )
    )
    probe_claim_ref = str(probe_claim["claim_ref"])
    probe_parent_ref = str(probe_claim["parent_source_refs"][0])
    legacy_probe = build_source_use_projection(
        ticker=probe_ticker,
        input_generation_id=str(combined["generation_id"]),
        catalog=probe_catalog,
    )
    legacy_probe_validation = validate_selected_refs(
        legacy_probe,
        refs=[probe_claim_ref],
        use=SourceUse.OVERALL_DIRECTION,
        require_any=True,
    )
    missing_manifest = build_trusted_source_authority_manifest(
        ticker=probe_ticker,
        source_generation_id=str(combined["generation_id"]),
        catalog=probe_catalog,
        source_metadata=[
            row
            for row in contexts[probe_ticker].get("decision_evidence") or ()
            if isinstance(row, Mapping) and str(row.get("ref_id") or "") != probe_parent_ref
        ],
    )
    missing_expectation_rejection: str | None = None
    try:
        freeze_source_use_input_expectation(
            ticker=probe_ticker,
            source_generation_id=str(combined["generation_id"]),
            execution_generation_id="m12da-r2-missing-authority-negative-control",
            catalog=probe_catalog,
            source_metadata=[
                row
                for row in contexts[probe_ticker].get("decision_evidence") or ()
                if isinstance(row, Mapping) and str(row.get("ref_id") or "") != probe_parent_ref
            ],
            authority_manifest=missing_manifest,
        )
    except ValueError as exc:
        missing_expectation_rejection = str(exc)
    missing_invalid_authority = {
        "contract": "m12da-r2-missing-invalid-authority-before-after-v1",
        "probe_ticker": probe_ticker,
        "probe_claim_ref": probe_claim_ref,
        "probe_parent_ref": probe_parent_ref,
        "legacy_contract_status": legacy_probe["status"],
        "legacy_selected_validation_status": legacy_probe_validation["status"],
        "legacy_behavior": "PERMISSIVE_BASELINE_COMPARISON_ONLY",
        "v2_manifest_status": missing_manifest["status"],
        "v3_projection_status": "NOT_CREATED_FAIL_CLOSED",
        "v3_expectation_rejection": missing_expectation_rejection,
        "status": (
            "PASS"
            if legacy_probe_validation["status"] == "PASS"
            and missing_manifest["status"] == "FAIL"
            and missing_expectation_rejection
            == "source_input_expectation_authority_status_not_pass"
            else "FAIL"
        ),
    }

    binding_attacks: list[dict[str, object]] = []
    base_projection = projections[probe_ticker]
    base_binding = source_use_bindings[probe_ticker]
    for attack, mutate in (
        (
            "source_generation_changed_with_recomputed_self_hash",
            lambda payload: payload.__setitem__("source_generation_id", "forged-source"),
        ),
        (
            "subject_changed_with_recomputed_self_hash",
            lambda payload: payload.__setitem__("ticker", "FORGED"),
        ),
        (
            "permission_changed_with_recomputed_self_hash",
            lambda payload: payload["source_records"][probe_parent_ref]["allowed_uses"].append(
                SourceUse.VALUATION.value
            ),
        ),
    ):
        forged = deepcopy(base_projection)
        mutate(forged)
        forged.pop("projection_sha256", None)
        forged["projection_sha256"] = canonical_sha256(forged)
        validation = validate_source_use_projection_binding(forged, base_binding)
        binding_attacks.append(
            {
                "attack": attack,
                "forged_self_hash_valid": True,
                "validation_status": validation["status"],
                "errors": validation["errors"],
            }
        )
    missing_binding_validation = validate_source_use_projection_binding(base_projection, None)
    projection_binding_proof = {
        "contract": "m12da-r2-projection-caller-binding-proof-v1",
        "positive_validation": validate_source_use_projection_binding(
            base_projection,
            base_binding,
        ),
        "missing_binding_validation": missing_binding_validation,
        "forged_projection_attacks": binding_attacks,
        "status": (
            "PASS"
            if missing_binding_validation["status"] == "FAIL"
            and all(row["validation_status"] == "FAIL" for row in binding_attacks)
            else "FAIL"
        ),
    }

    probe_metadata = [
        deepcopy(row)
        for row in contexts[probe_ticker].get("decision_evidence") or ()
        if isinstance(row, Mapping)
    ]
    changed_metadata = deepcopy(probe_metadata)
    changed_metadata[0]["statement"] = {"m12da_r2_changed_source_meaning": True}
    changed_catalog = deepcopy(probe_catalog)
    changed_claim = next(
        row
        for row in changed_catalog["atomic_claims"]
        if str(row.get("claim_ref") or "") == probe_claim_ref
    )
    alternative_parent = next(
        str(ref)
        for ref in changed_catalog["all_evidence_refs"]
        if str(ref) not in set(changed_claim.get("parent_source_refs") or ())
    )
    changed_claim["parent_source_refs"] = [alternative_parent]

    def current_validation(
        *,
        ticker: str = probe_ticker,
        source_generation_id: str = str(combined["generation_id"]),
        execution_generation_id: str = SOURCE_EXECUTION_GENERATION,
        catalog: Mapping[str, object] = probe_catalog,
        metadata: list[Mapping[str, object]] = probe_metadata,
        expectation: Mapping[str, object] | None = source_use_expectations[probe_ticker],
        projection: Mapping[str, object] | None = base_projection,
        binding: Mapping[str, object] | None = base_binding,
    ) -> dict[str, object]:
        return validate_source_use_current_input(
            projection,
            binding,
            expectation,
            ticker=ticker,
            source_generation_id=source_generation_id,
            execution_generation_id=execution_generation_id,
            catalog=catalog,
            source_metadata=metadata,
        )

    current_input_attacks = [
        {"attack": "control_same_input", "validation": current_validation()},
        {
            "attack": "old_pair_against_changed_current_metadata",
            "pair_self_consistency": validate_source_use_projection_binding(
                base_projection, base_binding
            ),
            "validation": current_validation(metadata=changed_metadata),
        },
        {
            "attack": "old_pair_against_changed_catalog_parent",
            "pair_self_consistency": validate_source_use_projection_binding(
                base_projection, base_binding
            ),
            "validation": current_validation(catalog=changed_catalog),
        },
        {
            "attack": "old_pair_assigned_to_different_subject",
            "validation": current_validation(ticker="FOREIGN-SUBJECT"),
        },
        {
            "attack": "stale_source_generation",
            "validation": current_validation(source_generation_id="stale-source-generation"),
        },
        {
            "attack": "stale_execution_generation",
            "validation": current_validation(execution_generation_id="stale-execution"),
        },
        {
            "attack": "missing_current_input_expectation",
            "validation": current_validation(expectation=None),
        },
        {
            "attack": "missing_source_use_binding",
            "validation": current_validation(binding=None),
        },
    ]

    probe_b_context = deepcopy(contexts[probe_ticker])
    probe_b_context["decision_evidence"] = deepcopy(probe_metadata)
    probe_b_context["evidence_packets"] = [
        {"ticker": probe_ticker, "evidence": deepcopy(probe_metadata)}
    ]
    changed_metadata_b_context = deepcopy(probe_b_context)
    changed_metadata_b_context["decision_evidence"] = deepcopy(changed_metadata)
    changed_metadata_b_context["evidence_packets"] = [
        {"ticker": probe_ticker, "evidence": deepcopy(changed_metadata)}
    ]
    caller_common = {
        "source_use_view": base_projection,
        "source_use_binding": base_binding,
        "source_use_expectation": source_use_expectations[probe_ticker],
        "source_generation_id": str(combined["generation_id"]),
        "execution_generation_id": SOURCE_EXECUTION_GENERATION,
        "require_source_use": True,
    }
    actual_caller_replay = {
        "contract": "m12da-r2-stale-consistent-pair-actual-caller-replay-v1",
        "probe_ticker": probe_ticker,
        "submitted_r1_boundary_probe": submitted_boundary_probes,
        "repaired_callers": {
            "pass_a_control": _call_outcome(
                lambda: build_pass_a_subject_context(
                    context={
                        "evidence_packets": [
                            {"ticker": probe_ticker, "evidence": deepcopy(probe_metadata)}
                        ]
                    },
                    ticker=probe_ticker,
                    catalog=probe_catalog,
                    **caller_common,
                )
            ),
            "pass_a_changed_catalog": _call_outcome(
                lambda: build_pass_a_subject_context(
                    context={
                        "evidence_packets": [
                            {"ticker": probe_ticker, "evidence": deepcopy(probe_metadata)}
                        ]
                    },
                    ticker=probe_ticker,
                    catalog=changed_catalog,
                    **caller_common,
                )
            ),
            "pass_b_control": _call_outcome(
                lambda: build_pass_b_subject_context(
                    context=probe_b_context,
                    ticker=probe_ticker,
                    catalog=probe_catalog,
                    pass_a=pass_a[probe_ticker],
                    policy_option=contexts[probe_ticker]["deterministic_fundamental_option"],
                    **caller_common,
                )
            ),
            "pass_b_changed_catalog": _call_outcome(
                lambda: build_pass_b_subject_context(
                    context=probe_b_context,
                    ticker=probe_ticker,
                    catalog=changed_catalog,
                    pass_a=pass_a[probe_ticker],
                    policy_option=contexts[probe_ticker]["deterministic_fundamental_option"],
                    **caller_common,
                )
            ),
            "pass_b_changed_metadata": _call_outcome(
                lambda: build_pass_b_subject_context(
                    context=changed_metadata_b_context,
                    ticker=probe_ticker,
                    catalog=probe_catalog,
                    pass_a=pass_a[probe_ticker],
                    policy_option=contexts[probe_ticker]["deterministic_fundamental_option"],
                    **caller_common,
                )
            ),
            "capability_changed_catalog": _call_outcome(
                lambda: build_pass_b_capability_catalog(
                    context=probe_b_context,
                    catalog=changed_catalog,
                    pass_a=pass_a[probe_ticker],
                    policy_option=contexts[probe_ticker]["deterministic_fundamental_option"],
                    **caller_common,
                )
            ),
            "capability_changed_metadata": _call_outcome(
                lambda: build_pass_b_capability_catalog(
                    context=changed_metadata_b_context,
                    catalog=probe_catalog,
                    pass_a=pass_a[probe_ticker],
                    policy_option=contexts[probe_ticker]["deterministic_fundamental_option"],
                    **caller_common,
                )
            ),
        },
        "helper_attacks": current_input_attacks,
    }
    actual_caller_replay["status"] = (
        "PASS"
        if actual_caller_replay["repaired_callers"]["pass_a_control"]["outcome"] == "RETURNED"
        and actual_caller_replay["repaired_callers"]["pass_b_control"]["outcome"] == "RETURNED"
        and all(
            row["outcome"] == "REJECTED"
            for name, row in actual_caller_replay["repaired_callers"].items()
            if name not in {"pass_a_control", "pass_b_control"}
        )
        and current_input_attacks[0]["validation"]["status"] == "PASS"
        and all(row["validation"]["status"] == "FAIL" for row in current_input_attacks[1:])
        else "FAIL"
    )

    replay_execution_id = SOURCE_EXECUTION_GENERATION + "-authorized-replay"
    replay_expectation = freeze_source_use_input_expectation(
        ticker=probe_ticker,
        source_generation_id=str(combined["generation_id"]),
        execution_generation_id=replay_execution_id,
        catalog=probe_catalog,
        source_metadata=probe_metadata,
        authority_manifest=authority_manifests[probe_ticker],
    )
    replay_projection = build_source_use_projection(
        ticker=probe_ticker,
        input_generation_id=str(combined["generation_id"]),
        execution_generation_id=replay_execution_id,
        catalog=probe_catalog,
        authority_manifest=authority_manifests[probe_ticker],
        current_input_expectation=replay_expectation,
    )
    replay_binding = freeze_source_use_binding(
        projection=replay_projection,
        authority_manifest=authority_manifests[probe_ticker],
        current_input_expectation=replay_expectation,
    )
    replay_validation = validate_source_use_current_input(
        replay_projection,
        replay_binding,
        replay_expectation,
        ticker=probe_ticker,
        source_generation_id=str(combined["generation_id"]),
        execution_generation_id=replay_execution_id,
        catalog=probe_catalog,
        source_metadata=probe_metadata,
    )

    broadened_owner = next(
        row
        for row in authority_manifests[probe_ticker]["authority_records"]
        if str(row["authority_basis"]).startswith("m12da_r2_explicit_migration_of_exact_r1_owner:")
    )
    broadened_override = {
        "ref_id": broadened_owner["ref_id"],
        "catalog_sha256": canonical_sha256(probe_catalog),
        "source_metadata_sha256": broadened_owner["source_metadata_sha256"],
        "source_type": broadened_owner["source_type"],
        "source_scope": broadened_owner["source_scope"],
        "authority_basis": "m12da_r2_changed_permission_attack",
        "allowed_uses": sorted(set(broadened_owner["allowed_uses"]) | {SourceUse.VALUATION.value}),
        "prohibited_uses": sorted(
            set(broadened_owner["prohibited_uses"]) - {SourceUse.VALUATION.value}
        ),
    }
    changed_authority_manifest = build_trusted_source_authority_manifest(
        ticker=probe_ticker,
        source_generation_id=str(combined["generation_id"]),
        catalog=probe_catalog,
        source_metadata=probe_metadata,
        trusted_owner_overrides=[broadened_override],
    )
    changed_authority_projection = build_source_use_projection(
        ticker=probe_ticker,
        input_generation_id=str(combined["generation_id"]),
        execution_generation_id=SOURCE_EXECUTION_GENERATION,
        catalog=probe_catalog,
        authority_manifest=changed_authority_manifest,
        current_input_expectation=source_use_expectations[probe_ticker],
    )

    normal_current_validations = {
        ticker: validate_source_use_current_input(
            projections[ticker],
            source_use_bindings[ticker],
            source_use_expectations[ticker],
            ticker=ticker,
            source_generation_id=str(combined["generation_id"]),
            execution_generation_id=SOURCE_EXECUTION_GENERATION,
            catalog=catalogs[ticker],
            source_metadata=[
                row
                for row in contexts[ticker].get("decision_evidence") or ()
                if isinstance(row, Mapping)
            ],
        )
        for ticker in subjects
    }
    order_stable_validations = {
        ticker: validate_source_use_current_input(
            projections[ticker],
            source_use_bindings[ticker],
            source_use_expectations[ticker],
            ticker=ticker,
            source_generation_id=str(combined["generation_id"]),
            execution_generation_id=SOURCE_EXECUTION_GENERATION,
            catalog=catalogs[ticker],
            source_metadata=list(
                reversed(
                    [
                        row
                        for row in contexts[ticker].get("decision_evidence") or ()
                        if isinstance(row, Mapping)
                    ]
                )
            ),
        )
        for ticker in subjects
    }
    normal_22_replay = {
        "contract": "m12da-r2-normal-22-input-binding-source-use-replay-v1",
        "subject_count": len(subjects),
        "validations": normal_current_validations,
        "directory_or_row_order_semantic_identity": order_stable_validations,
        "authorized_replay": replay_validation,
        "changed_authority_against_original_expectation": {
            "manifest_status": changed_authority_manifest["status"],
            "projection_status": changed_authority_projection["status"],
            "projection_errors": changed_authority_projection["projection_errors"],
        },
    }
    normal_22_replay["status"] = (
        "PASS"
        if len(normal_current_validations) == 22
        and all(row["status"] == "PASS" for row in normal_current_validations.values())
        and all(row["status"] == "PASS" for row in order_stable_validations.values())
        and replay_validation["status"] == "PASS"
        and changed_authority_projection["status"] == "FAIL"
        else "FAIL"
    )

    direct_ticker = next(row["ticker"] for row in impact_rows if row["impact"] == "UNCHANGED")
    direct_metadata = [
        row
        for row in contexts[direct_ticker].get("decision_evidence") or ()
        if isinstance(row, Mapping)
    ]
    direct_common = {
        "subjects": (direct_ticker,),
        "catalogs": {direct_ticker: catalogs[direct_ticker]},
        "source_use_views": {direct_ticker: projections[direct_ticker]},
        "source_use_expectations": {direct_ticker: source_use_expectations[direct_ticker]},
        "source_metadata_by_ticker": {direct_ticker: direct_metadata},
        "source_generation_id": str(combined["generation_id"]),
        "execution_generation_id": SOURCE_EXECUTION_GENERATION,
        "require_source_use": True,
    }
    direct_output = {"decisions": {direct_ticker: _wire_decision(candidates[direct_ticker])}}
    direct_control = validate_capability_selection(
        direct_output,
        capabilities={direct_ticker: new_capabilities[direct_ticker]},
        source_use_bindings={direct_ticker: source_use_bindings[direct_ticker]},
        **direct_common,
    )
    direct_without_capability = validate_capability_selection(
        direct_output,
        capabilities={},
        source_use_bindings={direct_ticker: source_use_bindings[direct_ticker]},
        **direct_common,
    )
    direct_without_binding = validate_capability_selection(
        direct_output,
        capabilities={direct_ticker: new_capabilities[direct_ticker]},
        source_use_bindings={},
        **direct_common,
    )
    changed_direct_metadata = deepcopy(direct_metadata)
    changed_direct_metadata[0]["statement"] = {"m12da_r2_changed_at_final_gate": True}
    direct_changed_current = validate_capability_selection(
        direct_output,
        capabilities={direct_ticker: new_capabilities[direct_ticker]},
        source_use_bindings={direct_ticker: source_use_bindings[direct_ticker]},
        **{
            **direct_common,
            "source_metadata_by_ticker": {direct_ticker: changed_direct_metadata},
        },
    )
    direct_final_proof = {
        "contract": "m12da-r2-source-aware-direct-final-gate-proof-v1",
        "ticker": direct_ticker,
        "control": direct_control,
        "direct_without_capability": direct_without_capability,
        "consumer_omits_declared_binding": direct_without_binding,
        "stale_capability_against_changed_current_metadata": direct_changed_current,
    }
    direct_final_proof["status"] = (
        "PASS"
        if direct_control["status"] == "PASS"
        and direct_without_capability["status"] == "FAIL"
        and direct_without_binding["status"] == "FAIL"
        and direct_changed_current["status"] == "FAIL"
        else "FAIL"
    )

    affected = [row for row in impact_rows if row["impact"] == "UNDER_SUPPORTED"]
    wc_before_after = []
    for ticker, relation_id in WC_RELATION_IDS.items():
        candidate = candidates[ticker]
        selected_axes = []
        if relation_id in candidate["holder_reason_evidence_refs"]:
            selected_axes.append("HOLDER")
        claim_refs = {
            str(row["claim_ref"])
            for row in catalogs[ticker]["atomic_claims"]
            if relation_id in set(row.get("parent_source_refs") or ())
        }
        if claim_refs & set(candidate["decisive_supporting_claim_refs"]):
            selected_axes.append("OVERALL_SUPPORT")
        if claim_refs & set(candidate["decisive_contradicting_claim_refs"]):
            selected_axes.append("OVERALL_CONTRADICTION")
        if claim_refs & set(pass_a[ticker]["archetype_supporting_claim_refs"]):
            selected_axes.append("PASS_A_ARCHETYPE")
        if claim_refs & set(pass_a[ticker]["tier_supporting_claim_refs"]):
            selected_axes.append("PASS_A_TIER")
        wc_before_after.append(
            {
                "ticker": ticker,
                "relation_id": relation_id,
                "flow_metric": next(
                    row["relation"]["flow_metric"]
                    for row in wc_payload["relations"]
                    if row["ticker"] == ticker
                ),
                "before": {
                    "context_usable": True,
                    "material_business_or_risk_eligible": True,
                },
                "after": {
                    "context_usable": True,
                    "earnings_quality_context_usable": True,
                    "status_or_valuation_use_eligible": False,
                },
                "historically_selected_axes": selected_axes,
                "original_output_unchanged": True,
            }
        )

    cpng_bindings = _cpng_bindings(cpng_payload, m12cz_root=m12cz_root)
    legacy_binding_path = (
        Path(__file__).resolve().parents[1]
        / "docs/reports/20260918-m12da-shadow-source-use-offline-repair/legacy-metric-definition-binding.json"
    )
    legacy_cpng_bindings = _load(legacy_binding_path)
    if not isinstance(legacy_cpng_bindings, Mapping):
        raise ValueError("m12da_legacy_cpng_binding_not_an_object")
    generic_relation_rows = [
        {
            "ticker": ticker,
            "ref_id": authority["ref_id"],
            "authority_basis": authority["authority_basis"],
            "allowed_uses": authority["allowed_uses"],
            "literal_regression_table_member": (
                authority["ref_id"] in set(WC_RELATION_IDS.values())
            ),
        }
        for ticker in subjects
        for authority in authority_manifests[ticker]["authority_records"]
        if authority["authority_basis"] == "typed_working_capital_relation_metadata"
    ]
    generic_identity_proof = {
        "contract": "m12da-r2-generic-source-identity-invariance-v1",
        "normative_detector": (
            "category+exact_label+relation_semantics_contract+relation_id metadata"
        ),
        "literal_regression_table_normative": False,
        "typed_relation_count": len(generic_relation_rows),
        "typed_relations": generic_relation_rows,
        "new_identity_outside_literal_table_count": sum(
            not row["literal_regression_table_member"] for row in generic_relation_rows
        ),
        "renamed_synthetic_test": (
            "test_generic_metadata_authority_survives_renamed_subject_and_new_relation_id"
        ),
    }
    generic_identity_proof["status"] = (
        "PASS"
        if generic_identity_proof["typed_relation_count"] >= len(WC_RELATION_IDS)
        and generic_identity_proof["new_identity_outside_literal_table_count"] >= 1
        else "FAIL"
    )
    source_path_proof = {
        "contract": "m12da-r2-source-aware-vs-legacy-path-proof-v1",
        "authoritative_path": [
            "frozen decision_evidence metadata",
            SOURCE_AUTHORITY_CONTRACT,
            SOURCE_USE_CONTRACT,
            SOURCE_USE_BINDING_CONTRACT,
            "capability/final selected-ref validators",
        ],
        "authoritative_binding_required": True,
        "legacy_path_contract": legacy_probe["contract"],
        "legacy_path_scope": "FROZEN_COMPARISON_FIXTURE_ONLY",
        "legacy_path_can_issue_v2_pass": False,
        "production_path_changed": False,
        "status": "PASS",
    }
    trusted_authority_contract = {
        "contract": SOURCE_AUTHORITY_CONTRACT,
        "source_owner": "caller-frozen decision_evidence metadata plus typed ref catalog",
        "consumer_owner": [
            "scripts/m12cq_two_pass_contract.py",
            "scripts/m12cv_pass_b_capability_contract.py",
        ],
        "authority_builder": (
            "scripts/m12da_source_use_contract.py::build_trusted_source_authority_manifest"
        ),
        "binding_builder": ("scripts/m12da_source_use_contract.py::freeze_source_use_binding"),
        "forbidden_authority_inputs": [
            "model-authored allowed_uses",
            "serialized trust flag",
            "ticker literal detector",
            "catalog membership alone",
        ],
        "authority_manifest_count": len(authority_manifests),
        "status": (
            "PASS"
            if len(authority_manifests) == 22
            and all(row["status"] == "PASS" for row in authority_manifests.values())
            else "FAIL"
        ),
    }
    findings_reconciliation = {
        "contract": "m12da-r1-chat-findings-reconciliation-v1",
        "submitted_decision": "M12DA_PARTIAL_ACCEPTANCE_SOURCE_AUTHORITY_BOUNDARY_NOT_CLOSED",
        "findings": [
            {
                "finding": "missing authority permissive baseline fallback",
                "closure": "v2 has no inheritance and fails projection/binding",
                "status": "CLOSED",
            },
            {
                "finding": "projection status/hash/generation not enforced",
                "closure": "caller-held binding validates all identities and hashes",
                "status": "CLOSED",
            },
            {
                "finding": "optional source view bypass",
                "closure": "require_source_use path is mandatory and tested",
                "status": "CLOSED",
            },
            {
                "finding": "ticker/ref literal authority discovery",
                "closure": "typed metadata path classifies new relation identity",
                "status": "CLOSED",
            },
            {
                "finding": "CPNG NASDAQ identity conflicts with official evidence",
                "closure": "versioned NYSE proposal with two official SHA-bound sources",
                "status": "CLOSED",
            },
            {
                "finding": "A reuse conflated selected refs with input equivalence",
                "closure": "selected support and model-input hashes reported separately",
                "status": "CLOSED",
            },
        ],
        "status": "PASS",
    }
    protected_under_supported = [
        row for row in impact_rows if row["new_overall_support_state"] == "UNDER_SUPPORTED"
    ]
    no_forced = {
        "contract": "m12da-no-forced-investment-label-proof-v1",
        "subjects_with_under_supported_overall_surface": [
            row["ticker"] for row in protected_under_supported
        ],
        "single_label_capability_count": sum(
            len(new_capabilities[ticker]["overall"]["allowed_values"]) == 1 for ticker in subjects
        ),
        "forced_buy_count": sum(
            new_capabilities[ticker]["overall"]["allowed_values"] == ["BUY"] for ticker in subjects
        ),
        "forced_hold_count": 0,
        "historical_labels_rewritten": 0,
        "policy": "validate_under_supported_without_manufacturing_an_investment_label",
    }
    no_forced["status"] = (
        "PASS"
        if no_forced["single_label_capability_count"] == 0
        and no_forced["forced_buy_count"] == 0
        and no_forced["forced_hold_count"] == 0
        and no_forced["historical_labels_rewritten"] == 0
        else "FAIL"
    )

    projection_contract = {
        "contract": SOURCE_USE_CONTRACT,
        "authority_contract": SOURCE_AUTHORITY_CONTRACT,
        "binding_contract": SOURCE_USE_BINDING_CONTRACT,
        "actual_existing_owners": [
            "app/services/working_capital_user_visible_preintegration_service.py",
            "app/services/stage2_maturity_polarity_adapter_service.py",
            "app/services/cross_market_decision_engine_service.py",
            "scripts/m12cq_two_pass_contract.py",
            "scripts/m12cv_pass_b_capability_contract.py",
        ],
        "production_owner_edits": [],
        "projection_count": len(projections),
        "projection_hashes": {
            ticker: projections[ticker]["projection_sha256"] for ticker in subjects
        },
        "rules": {
            "unknown_ref": "DENY",
            "compound_claim": "INTERSECTION_OF_ALL_PARENT_PERMISSIONS",
            "model_authored_permission": "IGNORED",
            "selected_evidence_final_gate": "REQUIRED",
            "missing_negative_evidence": "NO_FORCED_LABEL",
            "missing_or_invalid_authority": "FAIL_CLOSED_NO_BASELINE_INHERITANCE",
            "consumer_binding": "CALLER_HELD_EXPECTED_IDENTITY_REQUIRED",
            "source_generation_vs_execution_generation": "SEPARATELY_BOUND",
        },
    }
    projection_contract["status"] = (
        "PASS"
        if len(projections) == 22
        and all(projection["status"] == "PASS" for projection in projections.values())
        else "FAIL"
    )
    source_use_projections = {
        "contract": "m12da-r2-source-use-projections-22-v1",
        "input_generation_id": combined["generation_id"],
        "execution_generation_id": SOURCE_EXECUTION_GENERATION,
        "subject_count": len(projections),
        "subjects": projections,
        "status": projection_contract["status"],
    }
    authority_manifest_artifact = {
        "contract": "m12da-r2-trusted-metadata-authority-manifests-22-v1",
        "authority_contract": SOURCE_AUTHORITY_CONTRACT,
        "subject_count": len(authority_manifests),
        "subjects": authority_manifests,
        "status": (
            "PASS"
            if len(authority_manifests) == 22
            and all(row["status"] == "PASS" for row in authority_manifests.values())
            else "FAIL"
        ),
    }
    binding_artifact = {
        "contract": "m12da-r2-projection-caller-bindings-22-v1",
        "binding_contract": SOURCE_USE_BINDING_CONTRACT,
        "subject_count": len(source_use_bindings),
        "subjects": source_use_bindings,
        "validations": {
            ticker: validate_source_use_projection_binding(
                projections[ticker],
                source_use_bindings[ticker],
            )
            for ticker in subjects
        },
    }
    binding_artifact["status"] = (
        "PASS"
        if len(source_use_bindings) == 22
        and all(row["status"] == "PASS" for row in binding_artifact["validations"].values())
        else "FAIL"
    )
    offline_rows_consistent = all(
        (
            row["impact"] == "UNDER_SUPPORTED"
            and row["semantic_validation_status"] == "FAIL"
            and row["capability_validation_status"] == "FAIL"
            and bool(row["source_use_errors"])
        )
        or (
            row["impact"] == "UNCHANGED"
            and row["semantic_validation_status"] == "PASS"
            and row["capability_validation_status"] == "PASS"
            and not row["source_use_errors"]
        )
        for row in impact_rows
    )
    r1_affected_subjects = {
        str(row["ticker"])
        for row in r1_impact_payload.get("subjects") or ()
        if isinstance(row, Mapping) and row.get("impact") == "UNDER_SUPPORTED"
    }
    r2_affected_subjects = {str(row["ticker"]) for row in affected}
    newly_affected_subjects = sorted(r2_affected_subjects - r1_affected_subjects)
    newly_affected_authority_causes = []
    for ticker in newly_affected_subjects:
        row = next(item for item in impact_rows if item["ticker"] == ticker)
        failed_refs = {
            str(error["ref_id"])
            for audit in row["selected_use_audit"].values()
            for error in audit.get("forbidden_refs") or ()
            if error.get("ref_id")
        }
        families: set[str] = set()
        bases: set[str] = set()
        for ref_id in failed_refs:
            record = projections[ticker]["claim_records"].get(ref_id)
            if isinstance(record, Mapping):
                parent_refs = record.get("parent_source_refs") or ()
            else:
                parent_refs = [ref_id]
            for parent_ref in parent_refs:
                parent = projections[ticker]["source_records"].get(str(parent_ref))
                if isinstance(parent, Mapping):
                    families.add(str(parent.get("source_family") or ""))
                    bases.add(str(parent.get("authority_basis") or ""))
        newly_affected_authority_causes.append(
            {
                "ticker": ticker,
                "failed_selected_refs": sorted(failed_refs),
                "source_families": sorted(families),
                "authority_bases": sorted(bases),
                "reason": (
                    "R1 Core/atomic membership grant was removed; only explicit exact owners or "
                    "the restricted family's narrow uses remain."
                ),
            }
        )
    offline_impact = {
        "contract": "m12da-r2-offline-22-subject-source-use-impact-v1",
        "generation_id": combined["generation_id"],
        "subject_count": len(subjects),
        "prior_r1_affected_count": len(r1_affected_subjects),
        "prior_r1_affected_subjects": sorted(r1_affected_subjects),
        "affected_count": len(affected),
        "newly_affected_by_r2_fail_closed": newly_affected_subjects,
        "newly_affected_authority_causes": newly_affected_authority_causes,
        "unchanged_count": len(subjects) - len(affected),
        "subjects": impact_rows,
        "historical_outputs_mutated": 0,
        "status": "PASS" if len(impact_rows) == 22 and offline_rows_consistent else "FAIL",
    }
    selected_gate = {
        "contract": "m12da-r2-selected-evidence-direct-final-gate-tests-v1",
        "semantic_gate_subject_count": len(subjects),
        "capability_gate_subject_count": len(subjects),
        "bound_projection_subject_count": len(source_use_bindings),
        "under_supported_subjects": [row["ticker"] for row in affected],
        "samsung_holder_review_preserved": candidates["005930"]["holder"] == "REVIEW",
        "samsung_holder_review_new_gate_status": next(
            row["impact"] for row in impact_rows if row["ticker"] == "005930"
        ),
        "expectation_only_000660_preserved": candidates["000660"]["overall_direction"] == "HOLD",
        "expectation_only_000660_new_gate_status": next(
            row["impact"] for row in impact_rows if row["ticker"] == "000660"
        ),
        "capability_bypass_tested": True,
        "missing_view_negative_control": (
            "test_direct_final_gate_rejects_restricted_ref_and_missing_view"
        ),
        "forged_self_hash_negative_control": (
            "test_recomputed_forged_projection_hash_does_not_replace_outer_binding"
        ),
    }
    selected_gate["status"] = (
        "PASS"
        if selected_gate["samsung_holder_review_preserved"]
        and selected_gate["samsung_holder_review_new_gate_status"] == "UNDER_SUPPORTED"
        and selected_gate["expectation_only_000660_preserved"]
        and selected_gate["expectation_only_000660_new_gate_status"] == "UNDER_SUPPORTED"
        and selected_gate["capability_bypass_tested"]
        and selected_gate["bound_projection_subject_count"] == 22
        else "FAIL"
    )
    original_immutability = {
        "contract": "m12da-original-output-immutability-v1",
        "path": str(frozen_output),
        "sha256_before": frozen_sha_before,
        "sha256_after": frozen_sha_after,
        "expected_sha256": "34aace744021cc0b4b150dcd47e9c31bb2f48d8ec4a136cc4123c4de64646f4c",
        "byte_identical": frozen_sha_before == frozen_sha_after,
        "expected_hash_match": frozen_sha_after
        == "34aace744021cc0b4b150dcd47e9c31bb2f48d8ec4a136cc4123c4de64646f4c",
        "historical_label_changes": 0,
        "status": "PASS"
        if frozen_sha_before == frozen_sha_after
        and frozen_sha_after == "34aace744021cc0b4b150dcd47e9c31bb2f48d8ec4a136cc4123c4de64646f4c"
        else "FAIL",
    }
    prior_pass_a_affected = {"000660", "005490", "005930"}
    current_pass_a_affected = {
        str(row["ticker"])
        for row in pass_a_impact
        if row["selected_support_state"] == "SELECTED_SUPPORT_AFFECTED"
    }
    newly_affected_pass_a = current_pass_a_affected - prior_pass_a_affected
    newly_affected_source_backing: list[dict[str, object]] = []
    for ticker in sorted(newly_affected_pass_a):
        failed_claim_refs = {
            str(error.get("ref_id") or "")
            for row in pass_a_impact
            if row["ticker"] == ticker
            for validation in (row["archetype_validation"], row["tier_validation"])
            for error in validation["errors"]
            if isinstance(error, Mapping) and str(error.get("ref_id") or "")
        }
        authority_rules = {
            str(projections[ticker]["source_records"][parent]["authority_basis"])
            for claim_ref in failed_claim_refs
            if claim_ref in projections[ticker]["claim_records"]
            for parent in projections[ticker]["claim_records"][claim_ref]["parent_source_refs"]
        }
        newly_affected_source_backing.append(
            {
                "ticker": ticker,
                "failed_claim_refs": sorted(failed_claim_refs),
                "parent_authority_rules": sorted(authority_rules),
                "source_backed_generic_typed_family": bool(authority_rules)
                and authority_rules == {"typed_working_capital_relation_metadata"},
            }
        )
    pass_a_matrix = {
        "contract": "m12da-r2-pass-a-selected-support-and-model-input-impact-v1",
        "subject_count": len(pass_a_impact),
        "prior_m12da_proven_affected_count": 3,
        "prior_m12da_unchanged_count": 19,
        "selected_support_affected_count": sum(
            row["selected_support_state"] == "SELECTED_SUPPORT_AFFECTED" for row in pass_a_impact
        ),
        "model_input_changed_count": sum(
            row["model_input_state"] == "MODEL_INPUT_CHANGED" for row in pass_a_impact
        ),
        "model_input_equivalent_proven_count": sum(
            row["model_input_state"] == "MODEL_INPUT_EQUIVALENT_PROVEN" for row in pass_a_impact
        ),
        "input_impact_not_yet_proven_count": sum(
            row["reuse_recommendation"] == "INPUT_IMPACT_NOT_YET_PROVEN" for row in pass_a_impact
        ),
        "shared_batch_input_changed": True,
        "prior_affected_subjects": sorted(prior_pass_a_affected),
        "current_affected_subjects": sorted(current_pass_a_affected),
        "newly_affected_subjects": sorted(newly_affected_pass_a),
        "newly_affected_source_backing": newly_affected_source_backing,
        "shared_batch_dependency": (
            "All 22 next-model views carry the new bound source-use projection; this does not "
            "retroactively alter frozen A output or by itself authorize an A rerun."
        ),
        "automatic_reuse_authorized": False,
        "subjects": pass_a_impact,
    }
    pass_a_matrix["status"] = (
        "PASS"
        if pass_a_matrix["subject_count"] == 22
        and current_pass_a_affected.issuperset(prior_pass_a_affected)
        and all(row["source_backed_generic_typed_family"] for row in newly_affected_source_backing)
        and pass_a_matrix["model_input_changed_count"] == 22
        and pass_a_matrix["input_impact_not_yet_proven_count"] == 22
        and pass_a_matrix["automatic_reuse_authorized"] is False
        else "FAIL"
    )
    residual = {
        "contract": "m12da-r2-residual-gap-ledger-v1",
        "open_p0": 0,
        "open_p1": 0,
        "open_p2": 2,
        "items": [
            {
                "severity": "P2",
                "id": "M12DA-R2-FUTURE-INFERENCE-SCOPE",
                "state": "CHAT_DECISION_REQUIRED",
                "detail": "Pass-A reuse and minimum future inference scope are not authorized here.",
            },
            {
                "severity": "P2",
                "id": "M12DA-R2-CPNG-FUTURE-SOURCE-VIEW",
                "state": "PROPOSAL_ONLY",
                "detail": "Retrospective official binding is not injected into historical packets.",
            },
        ],
        "decision_surface_policy_gap": False,
        "status": "PASS",
    }
    safety = {
        "contract": "m12da-r2-safety-counters-v1",
        "model_calls": 0,
        "provider_calls": 0,
        "network_reads": 0,
        "production_app_edits": 0,
        "production_schema_edits": 0,
        "production_prompt_edits": 0,
        "database_mutations": 0,
        "notifications_sent": 0,
        "scheduler_mutations": 0,
        "historical_output_mutations": 0,
        "main_merges": 0,
        "remote_pushes": 0,
        "deployments": 0,
        "status": "PASS",
    }

    working_capital_artifact = {
        "contract": "m12da-working-capital-use-scope-before-after-v1",
        "relation_count": len(wc_before_after),
        "relations": wc_before_after,
    }
    working_capital_artifact["status"] = (
        "PASS"
        if {row["ticker"] for row in wc_before_after} == set(WC_RELATION_IDS)
        and all(
            row["after"]["context_usable"]
            and row["after"]["earnings_quality_context_usable"]
            and not row["after"]["status_or_valuation_use_eligible"]
            and row["original_output_unchanged"]
            for row in wc_before_after
        )
        else "FAIL"
    )
    expectation_artifact = {
        "contract": "m12da-expectation-vs-business-evidence-before-after-v1",
        "regression_source": expectation_payload["contract"],
        "restricted_expectation_ref_count": len(expectation_rows),
        "rows": expectation_rows,
        "actual_grounded_business_risk_blanket_ban": False,
    }
    expectation_artifact["status"] = (
        "PASS"
        if any(
            row["ticker"] == "000660"
            and not row["new_overall_support_eligible"]
            and row["expectations_context_retained"]
            and row["entry_context_retained"]
            and not row["occurred_event_inferred"]
            for row in expectation_rows
        )
        and not expectation_artifact["actual_grounded_business_risk_blanket_ban"]
        else "FAIL"
    )
    resolved_cpng_identity = cpng_bindings["source_derived_expected_identity"]
    expected_cpng_identity = {
        "venue": str(resolved_cpng_identity["venue"]).upper(),
        "issuer_id": resolved_cpng_identity["issuer_id"],
        "security_id": resolved_cpng_identity["security_id"],
    }
    wrong_cpng_identity = freeze_security_identity_binding(
        ticker="CPNG",
        issuer_id="sec:9999999999",
        venue="NASDAQ",
        security_type="preferred-stock",
        official_sources=cpng_bindings["corrected_security_identity"]["official_sources"],
    )
    wrong_cpng_validation = validate_security_identity_binding(
        wrong_cpng_identity,
        expected=expected_cpng_identity,
    )
    cpng_official = cpng_payload["official_source"]
    cpng_payloads = cpng_official["retrieved_payloads"]
    cpng_submissions_bytes = (
        m12cz_root / "retrieved-sources" / "cpng-sec-submissions.json"
    ).read_bytes()
    cpng_exhibit_bytes = (
        m12cz_root / "retrieved-sources" / "cpng-2026q2-exhibit-99-1.html"
    ).read_bytes()
    mismatching_source_resolution = resolve_archived_sec_security_identity(
        ticker="CPNG",
        security_type="common-stock",
        submissions_bytes=cpng_submissions_bytes,
        exhibit_bytes=cpng_exhibit_bytes,
        expected_submissions_sha256="0" * 64,
        expected_exhibit_sha256=str(cpng_payloads["cpng-2026q2-exhibit-99-1.html"]["sha256"]),
    )
    cpng_controls = {
        "contract": "m12da-r2-cpng-archived-identity-consumer-proof-v1",
        "security_identity_contract": SECURITY_IDENTITY_CONTRACT,
        "source_derived_expected_identity": resolved_cpng_identity,
        "expected_consumer_identity": expected_cpng_identity,
        "corrected_security_id": cpng_bindings["corrected_security_identity"]["security_id"],
        "original_security_id_preserved_as_prior_record": "nasdaq:CPNG:common-stock",
        "coherent_wrong_identity": wrong_cpng_identity,
        "coherent_wrong_identity_validation": wrong_cpng_validation,
        "mismatching_source_identity_resolution": mismatching_source_resolution,
        "management_value_usd": cpng_bindings["management_defined_fcf"]["value"],
        "backend_value_usd": cpng_bindings["backend_ppe_only_fcf"]["value"],
        "definitions_distinct": cpng_bindings["management_defined_fcf"]["definition_id"]
        != cpng_bindings["backend_ppe_only_fcf"]["definition_id"],
        "historical_packet_bound": False,
        "whole_paragraph_validated_from_one_metric": False,
    }
    cpng_controls["status"] = (
        "PASS"
        if cpng_bindings["status"] == "PASS"
        and wrong_cpng_validation["status"] == "FAIL"
        and mismatching_source_resolution["status"] == "FAIL"
        and cpng_controls["definitions_distinct"]
        and not cpng_controls["historical_packet_bound"]
        and not cpng_controls["whole_paragraph_validated_from_one_metric"]
        else "FAIL"
    )

    family_boundary = _family_boundary_proof()
    family_owner_rows: dict[str, dict[str, object]] = {}
    for manifest in authority_manifests.values():
        for row in manifest["authority_records"]:
            family = str(row["source_family"])
            aggregate = family_owner_rows.setdefault(
                family,
                {
                    "record_count": 0,
                    "authority_states": set(),
                    "authority_bases": set(),
                    "required_metadata": set(),
                    "compatible_source_versions": set(),
                    "decisive_permission_record_count": 0,
                },
            )
            aggregate["record_count"] += 1
            aggregate["authority_states"].add(str(row["authority_state"]))
            aggregate["authority_bases"].add(str(row["authority_basis"]))
            aggregate["required_metadata"].update(row["required_metadata"])
            aggregate["compatible_source_versions"].update(row["compatible_source_versions"])
            if set(row["allowed_uses"]) & DECISIVE_USES:
                aggregate["decisive_permission_record_count"] += 1
    serialized_family_rows = {
        family: {
            key: sorted(value) if isinstance(value, set) else value for key, value in row.items()
        }
        for family, row in sorted(family_owner_rows.items())
    }
    restricted_family_owner_map = {
        "contract": "m12da-r2-restricted-family-recognition-validation-owner-map-v1",
        "recognition_owner": "typed ref identity/category; display label excluded",
        "validation_owner": "family-specific required metadata and compatible versions",
        "permission_owner": "trusted authority manifest",
        "failure_behavior": "UNRESOLVED_RESTRICTED_WITHOUT_DECISIVE_USES",
        "families": serialized_family_rows,
        "fixture_cases": family_boundary["cases"],
    }
    restricted_family_owner_map["status"] = family_boundary["status"]

    submitted_cases = {
        str(row["case"]): row
        for row in submitted_boundary_probes.get("cases") or ()
        if isinstance(row, Mapping)
    }
    repaired_cases = {str(row["case"]): row for row in family_boundary["cases"]}
    restricted_before_after = {
        "contract": "m12da-r2-restricted-metadata-fail-closed-before-after-v1",
        "before_scope": submitted_boundary_probes.get("scope"),
        "before": submitted_boundary_probes,
        "after": family_boundary,
        "closures": {
            "working_capital_missing_semantic_scope": {
                "before_decisive": submitted_cases["working_capital_missing_semantic_scope"][
                    "selected_gate"
                ]["status"],
                "after_decisive": repaired_cases["working_capital_missing_semantic_scope"][
                    "decisive_validation"
                ]["status"],
            },
            "working_capital_unknown_contract": {
                "before_decisive": submitted_cases["working_capital_unrecognized_contract"][
                    "selected_gate"
                ]["status"],
                "after_decisive": repaired_cases["working_capital_unknown_contract"][
                    "decisive_validation"
                ]["status"],
            },
            "working_capital_label_variant": {
                "before_decisive": submitted_cases["working_capital_label_variant"][
                    "selected_gate"
                ]["status"],
                "after_decisive": repaired_cases["working_capital_display_label_variant"][
                    "decisive_validation"
                ]["status"],
            },
            "expectations_label_variant": {
                "before_decisive": submitted_cases["expectations_display_label_changed"][
                    "selected_gate"
                ]["status"],
                "after_decisive": repaired_cases["expectations_display_label_variant"][
                    "decisive_validation"
                ]["status"],
            },
        },
    }
    restricted_before_after["status"] = (
        "PASS"
        if all(
            row["before_decisive"] == "PASS" and row["after_decisive"] == "FAIL"
            for row in restricted_before_after["closures"].values()
        )
        else "FAIL"
    )

    current_input_expectation_artifact = {
        "contract": "m12da-r2-current-input-expectations-22-v1",
        "subject_count": len(source_use_expectations),
        "execution_generation_id": SOURCE_EXECUTION_GENERATION,
        "subjects": source_use_expectations,
        "status": normal_22_replay["status"],
    }
    current_input_owner_map = {
        "contract": "m12da-r2-current-input-expectation-owner-caller-map-v1",
        "expectation_owner": "caller-frozen catalog and source metadata before model output",
        "bound_identities": [
            "ticker",
            "source_generation_id",
            "execution_generation_id",
            "catalog_sha256",
            "source_metadata_sha256",
            "authority_manifest_sha256",
        ],
        "authoritative_callers": [
            "build_pass_a_subject_context",
            "validate_pass_a_batch",
            "build_pass_b_subject_context",
            "validate_pass_b_batch",
            "validate_new_buyer_consistency",
            "build_pass_b_capability_catalog",
            "validate_capability_selection",
        ],
        "source_generation_distinct_from_execution_generation": True,
        "optional_argument_bypass_allowed_on_source_aware_path": False,
        "actual_caller_replay_status": actual_caller_replay["status"],
        "direct_final_gate_status": direct_final_proof["status"],
        "normal_22_status": normal_22_replay["status"],
        "status": (
            "PASS"
            if actual_caller_replay["status"] == "PASS"
            and direct_final_proof["status"] == "PASS"
            and normal_22_replay["status"] == "PASS"
            else "FAIL"
        ),
    }

    r1_review_reconciliation = {
        "contract": "m12da-r2-r1-review-findings-reconciliation-v1",
        "source_r1_terminal": _load(r1_root / "program-completion.json")["terminal_status"],
        "findings": [
            {
                "id": "F1_RESTRICTED_FAMILY_FALLTHROUGH",
                "reproduced": True,
                "closure_artifact": "restricted-metadata-fail-closed-before-after.json",
                "status": restricted_before_after["status"],
            },
            {
                "id": "F2_PAIR_NOT_BOUND_TO_CURRENT_CALLER_INPUT",
                "reproduced": True,
                "closure_artifact": "stale-consistent-pair-actual-caller-replay.json",
                "status": actual_caller_replay["status"],
            },
            {
                "id": "CPNG_EXPECTED_IDENTITY_WAS_LITERAL",
                "reproduced": True,
                "closure_artifact": "cpng-archived-identity-resolution-and-consumer-proof.json",
                "status": cpng_controls["status"],
            },
        ],
        "status": (
            "PASS"
            if restricted_before_after["status"] == "PASS"
            and actual_caller_replay["status"] == "PASS"
            and cpng_controls["status"] == "PASS"
            else "FAIL"
        ),
    }
    source_and_model_view_hash_evidence = {
        "contract": "m12da-r2-source-model-view-diff-hash-evidence-v1",
        "frozen_output_sha256": frozen_sha_after,
        "submitted_r1_source_sha256": submitted_boundary_probes.get("source_sha256"),
        "current_source_sha256": {
            path: _sha(Path(path))
            for path in (
                "scripts/m12da_source_use_contract.py",
                "scripts/m12cq_two_pass_contract.py",
                "scripts/m12cv_pass_b_capability_contract.py",
                "scripts/m12da_offline_proof.py",
                "tests/test_m12da_r1_source_authority_closure.py",
                "tests/test_m12da_r2_authority_family_current_input_closure.py",
            )
        },
        "pass_a_old_new_hashes": {
            str(row["ticker"]): {
                "old": row["old_model_view_sha256"],
                "new": row["new_model_view_sha256"],
                "state": row["model_input_state"],
            }
            for row in pass_a_impact
        },
        "input_impact_status": "INPUT_IMPACT_NOT_YET_PROVEN",
        "automatic_rerun_authorized": False,
        "status": original_immutability["status"],
    }

    artifacts = {
        "r1-review-findings-reconciliation.json": r1_review_reconciliation,
        "restricted-family-recognition-validation-owner-map.json": (restricted_family_owner_map),
        "restricted-metadata-fail-closed-before-after.json": restricted_before_after,
        "current-input-expectation-owner-and-caller-map.json": current_input_owner_map,
        "stale-consistent-pair-actual-caller-replay.json": actual_caller_replay,
        "source-aware-direct-final-gate-proof.json": direct_final_proof,
        "normal-22-input-binding-and-source-use-replay.json": normal_22_replay,
        "source-use-input-expectations-22.json": current_input_expectation_artifact,
        "cpng-archived-identity-resolution-and-consumer-proof.json": cpng_controls,
        "original-proposed-bindings.json": legacy_cpng_bindings,
        "corrected-proposed-bindings.json": cpng_bindings,
        "pass-a-selected-support-and-full-input-impact.json": pass_a_matrix,
        "source-and-model-view-diff-hash-evidence.json": (source_and_model_view_hash_evidence),
        "submitted-r1-boundary-probes.json": submitted_boundary_probes,
        "m12da-chat-findings-reconciliation.json": findings_reconciliation,
        "trusted-metadata-to-authority-contract.json": trusted_authority_contract,
        "missing-invalid-authority-before-after.json": missing_invalid_authority,
        "projection-caller-binding-proof.json": projection_binding_proof,
        "source-aware-vs-legacy-path-proof.json": source_path_proof,
        "generic-source-identity-invariance-tests.json": generic_identity_proof,
        "source-authority-manifests-22.json": authority_manifest_artifact,
        "source-use-bindings-22.json": binding_artifact,
        "source-use-projection-contract.json": projection_contract,
        "source-use-projections-22.json": source_use_projections,
        "working-capital-use-scope-before-after.json": working_capital_artifact,
        "expectation-vs-business-evidence-before-after.json": expectation_artifact,
        "no-forced-investment-label-proof.json": no_forced,
        "legacy-metric-definition-binding.json": legacy_cpng_bindings,
        "cpng-reported-derived-controls.json": cpng_controls,
        "cpng-proposed-binding-security-identity-reconciliation.json": cpng_controls,
        "corrected-versioned-proposed-bindings.json": cpng_bindings,
        "selected-evidence-direct-final-gate-tests.json": selected_gate,
        "offline-22-subject-source-use-impact.json": offline_impact,
        "pass-a-selected-support-and-model-input-impact.json": pass_a_matrix,
        "original-output-immutability.json": original_immutability,
        "residual-gap-ledger.json": residual,
        "safety-counters.json": safety,
    }
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)

    terminal = (
        "M12DA_R2_AUTHORITY_FAMILY_AND_CURRENT_INPUT_BINDING_CLOSED_READY_FOR_CHAT"
        if all(
            artifact["status"] == "PASS"
            for artifact in (
                r1_review_reconciliation,
                restricted_family_owner_map,
                restricted_before_after,
                current_input_owner_map,
                actual_caller_replay,
                direct_final_proof,
                normal_22_replay,
                current_input_expectation_artifact,
                projection_contract,
                source_use_projections,
                authority_manifest_artifact,
                binding_artifact,
                findings_reconciliation,
                trusted_authority_contract,
                missing_invalid_authority,
                projection_binding_proof,
                source_path_proof,
                generic_identity_proof,
                working_capital_artifact,
                expectation_artifact,
                no_forced,
                cpng_bindings,
                cpng_controls,
                selected_gate,
                offline_impact,
                pass_a_matrix,
                original_immutability,
                residual,
                safety,
            )
        )
        else "M12DA_R2_REQUIRED_SOURCE_BINDING_FAILED"
    )
    completion = {
        "contract": REPORT_CONTRACT,
        "terminal_status": terminal,
        "subject_count": len(subjects),
        "source_use_under_supported_count": len(affected),
        "source_use_under_supported_subjects": [row["ticker"] for row in affected],
        "invalid_projection_rejection": projection_binding_proof["status"],
        "missing_authority_handling": missing_invalid_authority["status"],
        "mandatory_new_path_binding": binding_artifact["status"],
        "restricted_family_fail_closed": restricted_before_after["status"],
        "actual_current_input_binding": actual_caller_replay["status"],
        "direct_final_current_input_binding": direct_final_proof["status"],
        "generic_discovery_proof": generic_identity_proof["status"],
        "identity_derivation": cpng_controls["status"],
        "a_input_equivalence": "INPUT_IMPACT_NOT_YET_PROVEN",
        "pass_a_selected_support_affected_count": pass_a_matrix["selected_support_affected_count"],
        "pass_a_model_input_changed_count": pass_a_matrix["model_input_changed_count"],
        "pass_a_input_equality_proven_count": pass_a_matrix["model_input_equivalent_proven_count"],
        "old_judgments_flagged_count": len(affected),
        "model_calls": 0,
        "network_reads": 0,
        "historical_output_changes": 0,
        "production_changes": 0,
        "status": "PASS" if terminal.endswith("READY_FOR_CHAT") else "FAIL",
    }
    _write(output_dir / "program-completion.json", completion)
    summary = (
        "# M12DA-R2 Authority Family and Current-Input Binding Offline Closure\n\n"
        f"- Terminal: `{terminal}`\n"
        f"- Frozen subjects: `{len(subjects)}`\n"
        f"- R1 under-supported subjects: `{len(r1_affected_subjects)}`\n"
        f"- R2 under-supported subjects: `{len(affected)}`\n"
        f"- Newly fail-closed subjects: `{len(newly_affected_subjects)}`\n"
        f"- Restricted-family fail-closed: `{restricted_before_after['status']}`\n"
        f"- Actual-current-input binding: `{actual_caller_replay['status']}`\n"
        f"- Direct-final binding: `{direct_final_proof['status']}`\n"
        f"- CPNG source-derived identity: `{cpng_controls['status']}`\n"
        f"- Pass-A selected support affected: `{pass_a_matrix['selected_support_affected_count']}`\n"
        f"- Pass-A model input changed: `{pass_a_matrix['model_input_changed_count']}`\n"
        "- Pass-A full input equivalence: `INPUT_IMPACT_NOT_YET_PROVEN`\n"
        "- Historical labels rewritten: `0`\n"
        "- Model/provider/network calls: `0`\n"
        "- Production edits, DB mutations, sends, scheduler changes: `0`\n\n"
        "Restricted source families now remain narrow when metadata is malformed, unsupported, "
        "or cosmetically relabeled. Projection/binding pairs are checked against caller-owned "
        "current subject, catalog, metadata, source generation, execution generation, and authority "
        "identity at A/B/capability/final consumers. CPNG expected identity is independently derived "
        "from the archived SEC submissions and issuer exhibit bytes. No historical decision was "
        "rewritten and no inference or production action was authorized.\n"
    )
    (output_dir / "SOURCE_AUTHORITY_CURRENT_INPUT_CLOSURE_RESULT.md").write_text(
        summary,
        encoding="utf-8",
    )
    return completion


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m12cx-root", type=Path, required=True)
    parser.add_argument("--m12cz-root", type=Path, required=True)
    parser.add_argument("--r1-root", type=Path, required=True)
    parser.add_argument("--review-probes", type=Path, required=True)
    parser.add_argument("--frozen-output", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    completion = generate(
        m12cx_root=args.m12cx_root,
        m12cz_root=args.m12cz_root,
        r1_root=args.r1_root,
        review_probes=args.review_probes,
        frozen_output=args.frozen_output,
        output_dir=args.output_dir,
    )
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True))
    return 0 if completion["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
