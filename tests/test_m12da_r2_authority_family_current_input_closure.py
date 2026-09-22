from __future__ import annotations

import hashlib
import json
from copy import deepcopy

import pytest

from scripts.m12cq_two_pass_contract import (
    build_pass_a_subject_context,
    build_pass_b_subject_context,
)
from scripts.m12cv_pass_b_capability_contract import (
    build_pass_b_capability_catalog,
    validate_capability_selection,
)
from scripts.m12da_source_use_contract import (
    SourceUse,
    build_source_use_projection,
    build_trusted_source_authority_manifest,
    canonical_sha256,
    freeze_source_use_binding,
    freeze_source_use_input_expectation,
    freeze_security_identity_binding,
    is_use_allowed,
    resolve_archived_sec_security_identity,
    validate_security_identity_binding,
    validate_source_use_current_input,
)


SOURCE_GENERATION = "source-generation"
EXECUTION_GENERATION = "execution-generation"


def _claim(claim_ref: str, parent: str, polarity: str) -> dict[str, object]:
    return {
        "claim_ref": claim_ref,
        "ticker": "RENAMED",
        "claim": {
            "text": "동결된 구조화 근거 주장입니다.",
            "polarity": polarity,
            "reason_role": "FUNDAMENTAL",
            "logical_condition": None,
        },
        "parent_source_refs": [parent],
    }


def _catalog() -> dict[str, object]:
    claims = [
        _claim("claim:bull", "source:business", "BULLISH"),
        _claim("claim:bear", "source:business", "BEARISH"),
        _claim("claim:wc", "canonical:working-capital-relation:new-id", "BEARISH"),
        _claim("claim:expectations", "source:expectations", "BULLISH"),
    ]
    return {
        "ticker": "RENAMED",
        "all_evidence_refs": [
            "source:business",
            "canonical:working-capital-relation:new-id",
            "canonical:working-capital-reported:new-id",
            "source:expectations",
            "canonical:valuation",
            "canonical:price",
            "canonical:security_basis:current",
        ],
        "core_evidence_refs": [
            "source:business",
            "canonical:working-capital-relation:new-id",
            "source:expectations",
            "canonical:valuation",
        ],
        "timing_evidence_refs": ["canonical:price"],
        "valuation_evidence_refs": ["canonical:valuation"],
        "security_valuation_basis_refs": ["canonical:security_basis:current"],
        "positive_quality_refs": [],
        "business_quality_confidence_refs": [],
        "claim_refs": [str(row["claim_ref"]) for row in claims],
        "atomic_claims": claims,
        "entry_catalog": {
            "ticker": "RENAMED",
            "current_price": {
                "value": 90.0,
                "as_of": "2026-09-18",
                "currency": "USD",
                "ref_id": "canonical:price",
            },
            "tactical_candidates": [],
            "unresolved_policy": {"tactical_unresolved_reason": "unavailable"},
        },
    }


def _metadata() -> list[dict[str, object]]:
    return [
        {
            "ref_id": "source:business",
            "category": "thesis",
            "label": "핵심 투자 논리",
            "as_of": "2026-09-18",
            "statement": "동결된 사업 근거",
        },
        {
            "ref_id": "canonical:working-capital-relation:new-id",
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
            "ref_id": "canonical:working-capital-reported:new-id",
            "category": "earnings_quality",
            "label": "working_capital_lineage_input",
            "as_of": "2026-06-30",
            "statement": {
                "relation_id": "working-capital-relation:new-id",
                "semantic_scope": "exact_total_inventory",
            },
        },
        {
            "ref_id": "source:expectations",
            "category": "expectations",
            "label": "시장 기대",
            "as_of": "2026-09-18",
            "statement": {"level": "high", "priced_in": "partly"},
        },
        {
            "ref_id": "canonical:valuation",
            "category": "valuation",
            "label": "valuation",
            "as_of": "2026-09-18",
            "statement": "동결된 밸류에이션 근거",
        },
        {
            "ref_id": "canonical:price",
            "category": "price_structure",
            "label": "price",
            "as_of": "2026-09-18",
            "statement": "동결된 가격 근거",
        },
        {
            "ref_id": "canonical:security_basis:current",
            "category": "quality",
            "label": "security_basis",
            "as_of": "2026-09-18",
            "statement": "동결된 증권 기준",
        },
    ]


def _business_owner(
    catalog: dict[str, object], metadata: list[dict[str, object]]
) -> list[dict[str, object]]:
    row = next(item for item in metadata if item["ref_id"] == "source:business")
    return [
        {
            "ref_id": "source:business",
            "catalog_sha256": canonical_sha256(catalog),
            "source_metadata_sha256": canonical_sha256(row),
            "source_type": "frozen_legacy_business_evidence",
            "source_scope": "exact_source_business_decision_owner",
            "authority_basis": "explicit_frozen_legacy_business_owner",
            "allowed_uses": [
                SourceUse.CONTEXT,
                SourceUse.BUSINESS_CONTEXT,
                SourceUse.PASS_A_ARCHETYPE,
                SourceUse.PASS_A_VALUATION_TIER,
                SourceUse.OVERALL_DIRECTION,
                SourceUse.HOLDER_STANCE,
                SourceUse.NEW_BUYER_EXECUTION_RISK,
            ],
            "prohibited_uses": [SourceUse.VALUATION],
        }
    ]


def _bundle(
    *,
    catalog: dict[str, object] | None = None,
    metadata: list[dict[str, object]] | None = None,
    execution_generation_id: str = EXECUTION_GENERATION,
    owner: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    catalog = deepcopy(catalog or _catalog())
    metadata = deepcopy(metadata or _metadata())
    owners = deepcopy(owner if owner is not None else _business_owner(catalog, metadata))
    manifest = build_trusted_source_authority_manifest(
        ticker="RENAMED",
        source_generation_id=SOURCE_GENERATION,
        catalog=catalog,
        source_metadata=metadata,
        trusted_owner_overrides=owners,
    )
    expectation = freeze_source_use_input_expectation(
        ticker="RENAMED",
        source_generation_id=SOURCE_GENERATION,
        execution_generation_id=execution_generation_id,
        catalog=catalog,
        source_metadata=metadata,
        authority_manifest=manifest,
    )
    projection = build_source_use_projection(
        ticker="RENAMED",
        input_generation_id=SOURCE_GENERATION,
        execution_generation_id=execution_generation_id,
        catalog=catalog,
        authority_manifest=manifest,
        current_input_expectation=expectation,
    )
    binding = freeze_source_use_binding(
        projection=projection,
        authority_manifest=manifest,
        current_input_expectation=expectation,
    )
    return {
        "catalog": catalog,
        "metadata": metadata,
        "manifest": manifest,
        "expectation": expectation,
        "projection": projection,
        "binding": binding,
        "execution_generation_id": execution_generation_id,
    }


def _authority(bundle: dict[str, object], ref_id: str) -> dict[str, object]:
    manifest = bundle["manifest"]
    assert isinstance(manifest, dict)
    return next(row for row in manifest["authority_records"] if row["ref_id"] == ref_id)


@pytest.mark.parametrize(
    ("mutation", "expected_state"),
    [
        ("missing_semantic_scope", "UNRESOLVED_RESTRICTED"),
        ("unknown_relation_contract", "UNRESOLVED_RESTRICTED"),
        ("category_mismatch", "UNRESOLVED_RESTRICTED"),
        ("display_label_variant", "RESOLVED"),
    ],
)
def test_working_capital_family_fails_closed_before_core_fallback(
    mutation: str, expected_state: str
) -> None:
    metadata = _metadata()
    row = next(item for item in metadata if "working-capital-relation" in item["ref_id"])
    if mutation == "missing_semantic_scope":
        row["statement"].pop("semantic_scope")
    elif mutation == "unknown_relation_contract":
        row["statement"]["relation_semantics_contract"] = "unknown-v9"
    elif mutation == "category_mismatch":
        row["category"] = "thesis"
    else:
        row["label"] = "재고-원가 관계"
    bundle = _bundle(metadata=metadata)
    authority = _authority(bundle, "canonical:working-capital-relation:new-id")
    assert authority["authority_state"] == expected_state
    assert authority["source_family"] == "working_capital_relation"
    assert "frozen_core_atomic_parent_owner" not in authority["authority_basis"]
    assert SourceUse.OVERALL_DIRECTION not in authority["allowed_uses"]
    assert not is_use_allowed(
        bundle["projection"],
        binding=bundle["binding"],
        ref_id="claim:wc",
        use=SourceUse.OVERALL_DIRECTION,
    )


def test_expectation_family_ignores_cosmetic_label_and_restricts_unknown_schema() -> None:
    renamed = _metadata()
    next(item for item in renamed if item["ref_id"] == "source:expectations")["label"] = (
        "Market expectations"
    )
    renamed_bundle = _bundle(metadata=renamed)
    renamed_authority = _authority(renamed_bundle, "source:expectations")
    assert renamed_authority["authority_state"] == "RESOLVED"
    assert renamed_authority["authority_basis"] == "structured_expectations_metadata"
    assert SourceUse.OVERALL_DIRECTION not in renamed_authority["allowed_uses"]

    unsupported = deepcopy(renamed)
    next(item for item in unsupported if item["ref_id"] == "source:expectations")["statement"][
        "unknown_version_field"
    ] = True
    unsupported_bundle = _bundle(metadata=unsupported)
    unsupported_authority = _authority(unsupported_bundle, "source:expectations")
    assert unsupported_authority["authority_state"] == "UNRESOLVED_RESTRICTED"
    assert unsupported_authority["allowed_uses"] == [
        SourceUse.CONTEXT,
        SourceUse.EXPECTATIONS_CONTEXT,
    ]


def test_membership_only_is_unresolved_but_exact_legacy_owner_retains_rights() -> None:
    without_owner = _bundle(owner=[])
    authority = _authority(without_owner, "source:business")
    assert authority["authority_state"] == "UNRESOLVED"
    assert authority["authority_basis"] == "explicit_source_owner_required"
    assert SourceUse.OVERALL_DIRECTION not in authority["allowed_uses"]

    with_owner = _bundle()
    authority = _authority(with_owner, "source:business")
    assert authority["authority_state"] == "RESOLVED"
    assert authority["source_family"] == "explicit_legacy_business_owner"
    assert SourceUse.OVERALL_DIRECTION in authority["allowed_uses"]


def test_current_input_binding_rejects_stale_catalog_metadata_subject_and_attempt() -> None:
    bundle = _bundle()
    common = {
        "projection": bundle["projection"],
        "binding": bundle["binding"],
        "expectation": bundle["expectation"],
        "ticker": "RENAMED",
        "source_generation_id": SOURCE_GENERATION,
        "execution_generation_id": EXECUTION_GENERATION,
        "catalog": bundle["catalog"],
        "source_metadata": bundle["metadata"],
    }
    assert validate_source_use_current_input(**common)["status"] == "PASS"

    changed_catalog = deepcopy(bundle["catalog"])
    changed_catalog["atomic_claims"][0]["parent_source_refs"] = ["source:expectations"]
    assert (
        validate_source_use_current_input(**{**common, "catalog": changed_catalog})["status"]
        == "FAIL"
    )
    changed_metadata = deepcopy(bundle["metadata"])
    changed_metadata[0]["statement"] = "changed source bytes"
    assert (
        validate_source_use_current_input(**{**common, "source_metadata": changed_metadata})[
            "status"
        ]
        == "FAIL"
    )
    assert validate_source_use_current_input(**{**common, "ticker": "OTHER"})["status"] == "FAIL"
    assert (
        validate_source_use_current_input(**{**common, "source_generation_id": "stale-source"})[
            "status"
        ]
        == "FAIL"
    )
    assert (
        validate_source_use_current_input(**{**common, "execution_generation_id": "stale-attempt"})[
            "status"
        ]
        == "FAIL"
    )


def test_current_input_identity_is_order_stable_and_authorized_replay_is_explicit() -> None:
    bundle = _bundle()
    assert (
        validate_source_use_current_input(
            bundle["projection"],
            bundle["binding"],
            bundle["expectation"],
            ticker="RENAMED",
            source_generation_id=SOURCE_GENERATION,
            execution_generation_id=EXECUTION_GENERATION,
            catalog=bundle["catalog"],
            source_metadata=list(reversed(bundle["metadata"])),
        )["status"]
        == "PASS"
    )
    replay = _bundle(execution_generation_id="authorized-replay")
    assert replay["expectation"]["source_generation_id"] == SOURCE_GENERATION
    assert replay["expectation"]["execution_generation_id"] == "authorized-replay"
    assert (
        validate_source_use_current_input(
            replay["projection"],
            replay["binding"],
            replay["expectation"],
            ticker="RENAMED",
            source_generation_id=SOURCE_GENERATION,
            execution_generation_id="authorized-replay",
            catalog=replay["catalog"],
            source_metadata=replay["metadata"],
        )["status"]
        == "PASS"
    )


def test_new_self_consistent_permission_pair_cannot_reuse_frozen_expectation() -> None:
    original = _bundle()
    catalog = deepcopy(original["catalog"])
    metadata = deepcopy(original["metadata"])
    broadened_owner = _business_owner(catalog, metadata)
    broadened_owner[0]["allowed_uses"].append(SourceUse.VALUATION)
    changed_manifest = build_trusted_source_authority_manifest(
        ticker="RENAMED",
        source_generation_id=SOURCE_GENERATION,
        catalog=catalog,
        source_metadata=metadata,
        trusted_owner_overrides=broadened_owner,
    )
    changed_projection = build_source_use_projection(
        ticker="RENAMED",
        input_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        catalog=catalog,
        authority_manifest=changed_manifest,
        current_input_expectation=original["expectation"],
    )
    assert changed_projection["status"] == "FAIL"
    assert (
        "current_input_expectation_identity_mismatch:authority_manifest_sha256"
        in (changed_projection["projection_errors"])
    )


def _context(metadata: list[dict[str, object]]) -> dict[str, object]:
    catalog = _catalog()
    return {
        "ticker": "RENAMED",
        "decision_evidence": deepcopy(metadata),
        "evidence_packets": [{"ticker": "RENAMED", "evidence": deepcopy(metadata)}],
        "current_price": deepcopy(catalog["entry_catalog"]["current_price"]),
        "tactical_candidates": [],
        "security_valuation_basis_state": {
            "state": "RESOLVED",
            "new_buyer_price_resolution_use_allowed": True,
            "source_refs": ["canonical:security_basis:current"],
        },
    }


def _pass_a() -> dict[str, object]:
    return {"ticker": "RENAMED", "archetype": "DURABLE_FRANCHISE"}


def _option() -> dict[str, object]:
    return {
        "ticker": "RENAMED",
        "status": "RESOLVED",
        "low": 80.0,
        "high": 100.0,
        "currency": "USD",
        "evidence_refs": ["canonical:valuation"],
        "unresolved_reasons": [],
    }


def _selection() -> dict[str, object]:
    return {
        "decisions": {
            "RENAMED": {
                "overall_direction": "BUY",
                "directional_buy_score": 6.0,
                "decision_confidence": "MEDIUM",
                "decisive_supporting_claim_refs": ["claim:bull"],
                "decisive_contradicting_claim_refs": [],
                "thesis_state": "INTACT",
                "holder_decision": {
                    "holder": "HOLDABLE",
                    "reason_class": "NOT_APPLICABLE",
                    "reason": "핵심 논리를 훼손하는 근거가 없습니다.",
                    "evidence_refs": [],
                },
                "new_buyer_decision": {
                    "new_buyer": "ATTRACTIVE",
                    "reason_class": "ATTRACTIVE_WITHIN_RANGE",
                    "reason": "결정론적 범위 안입니다.",
                    "evidence_refs": ["canonical:valuation"],
                    "tactical_choice": "NOT_APPLICABLE",
                    "re_evaluate_conditions": [],
                },
                "policy_summary": "세 축을 분리해 판단했습니다.",
            }
        }
    }


def test_authoritative_builders_and_direct_final_gate_require_actual_current_input() -> None:
    bundle = _bundle()
    common = {
        "source_use_view": bundle["projection"],
        "source_use_binding": bundle["binding"],
        "source_use_expectation": bundle["expectation"],
        "source_generation_id": SOURCE_GENERATION,
        "execution_generation_id": EXECUTION_GENERATION,
        "require_source_use": True,
    }
    context = _context(bundle["metadata"])
    build_pass_a_subject_context(
        context=context,
        ticker="RENAMED",
        catalog=bundle["catalog"],
        **common,
    )
    build_pass_b_subject_context(
        context=context,
        ticker="RENAMED",
        catalog=bundle["catalog"],
        pass_a=_pass_a(),
        policy_option=_option(),
        **common,
    )
    capability = build_pass_b_capability_catalog(
        context=context,
        catalog=bundle["catalog"],
        pass_a=_pass_a(),
        policy_option=_option(),
        **common,
    )
    final = validate_capability_selection(
        _selection(),
        subjects=("RENAMED",),
        catalogs={"RENAMED": bundle["catalog"]},
        capabilities={"RENAMED": capability},
        source_use_views={"RENAMED": bundle["projection"]},
        source_use_bindings={"RENAMED": bundle["binding"]},
        source_use_expectations={"RENAMED": bundle["expectation"]},
        source_metadata_by_ticker={"RENAMED": bundle["metadata"]},
        source_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        require_source_use=True,
    )
    assert final["status"] == "PASS"

    missing_capability = validate_capability_selection(
        _selection(),
        subjects=("RENAMED",),
        catalogs={"RENAMED": bundle["catalog"]},
        capabilities={},
        source_use_views={"RENAMED": bundle["projection"]},
        source_use_bindings={"RENAMED": bundle["binding"]},
        source_use_expectations={"RENAMED": bundle["expectation"]},
        source_metadata_by_ticker={"RENAMED": bundle["metadata"]},
        source_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        require_source_use=True,
    )
    assert missing_capability["status"] == "FAIL"
    assert "RENAMED:PB_CAPABILITY_MISSING" in missing_capability["errors"]

    changed_context = _context(deepcopy(bundle["metadata"]))
    changed_context["decision_evidence"][0]["statement"] = "changed"
    with pytest.raises(ValueError, match="pass_b_source_use_current_input_invalid"):
        build_pass_b_subject_context(
            context=changed_context,
            ticker="RENAMED",
            catalog=bundle["catalog"],
            pass_a=_pass_a(),
            policy_option=_option(),
            **common,
        )

    changed_catalog = deepcopy(bundle["catalog"])
    changed_catalog["atomic_claims"][0]["parent_source_refs"] = ["source:expectations"]
    with pytest.raises(ValueError, match="pass_b_source_use_current_input_invalid"):
        build_pass_b_subject_context(
            context=context,
            ticker="RENAMED",
            catalog=changed_catalog,
            pass_a=_pass_a(),
            policy_option=_option(),
            **common,
        )
    with pytest.raises(ValueError, match="capability_source_use_current_input_invalid"):
        build_pass_b_capability_catalog(
            context=context,
            catalog=changed_catalog,
            pass_a=_pass_a(),
            policy_option=_option(),
            **common,
        )

    omitted = validate_capability_selection(
        _selection(),
        subjects=("RENAMED",),
        catalogs={"RENAMED": bundle["catalog"]},
        capabilities={"RENAMED": capability},
        source_use_views={"RENAMED": bundle["projection"]},
        source_use_bindings={"RENAMED": bundle["binding"]},
        source_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        require_source_use=True,
    )
    assert omitted["status"] == "FAIL"
    assert any("CURRENT_INPUT_INVALID" in error for error in omitted["errors"])

    omitted_binding = validate_capability_selection(
        _selection(),
        subjects=("RENAMED",),
        catalogs={"RENAMED": bundle["catalog"]},
        capabilities={"RENAMED": capability},
        source_use_views={"RENAMED": bundle["projection"]},
        source_use_expectations={"RENAMED": bundle["expectation"]},
        source_metadata_by_ticker={"RENAMED": bundle["metadata"]},
        source_generation_id=SOURCE_GENERATION,
        execution_generation_id=EXECUTION_GENERATION,
        require_source_use=True,
    )
    assert omitted_binding["status"] == "FAIL"
    assert any("CURRENT_INPUT_INVALID" in error for error in omitted_binding["errors"])


def _sec_identity_resolution(
    *,
    tickers: list[str] | None = None,
    exchanges: list[str] | None = None,
    exhibit_identity: str = "Coupang, Inc. (NYSE: CPNG)",
    expected_submissions_sha256: str | None = None,
) -> tuple[dict[str, object], bytes, bytes]:
    submissions = json.dumps(
        {
            "cik": "0001834584",
            "name": "Coupang, Inc.",
            "tickers": tickers or ["CPNG"],
            "exchanges": exchanges or ["NYSE"],
        },
        sort_keys=True,
    ).encode()
    exhibit = (
        "<html><body>Comparator Corp. (NASDAQ: COMP) "
        + exhibit_identity
        + " today announced results.</body></html>"
    ).encode()
    resolved = resolve_archived_sec_security_identity(
        ticker="CPNG",
        security_type="common-stock",
        submissions_bytes=submissions,
        exhibit_bytes=exhibit,
        expected_submissions_sha256=(
            expected_submissions_sha256 or hashlib.sha256(submissions).hexdigest()
        ),
        expected_exhibit_sha256=hashlib.sha256(exhibit).hexdigest(),
    )
    return resolved, submissions, exhibit


def test_sec_identity_is_source_derived_and_consumed_independently() -> None:
    resolved, _, _ = _sec_identity_resolution()
    assert resolved["status"] == "PASS"
    assert resolved["issuer_id"] == "sec:0001834584"
    assert resolved["venue"] == "nyse"
    assert resolved["security_id"] == "nyse:CPNG:common-stock"
    binding = freeze_security_identity_binding(
        ticker=str(resolved["ticker"]),
        issuer_id=str(resolved["issuer_id"]),
        venue=str(resolved["venue"]),
        security_type=str(resolved["security_type"]),
        official_sources=[
            {
                "provider": "sec_edgar_submissions",
                "document_sha256": resolved["submissions_sha256"],
                "locator": f"tickers[{resolved['ticker_exchange_index']}]",
                "assertion": "aligned ticker and exchange",
            },
            {
                "provider": "sec_edgar_exhibit",
                "document_sha256": resolved["exhibit_sha256"],
                "locator": "issuer_name(exchange:ticker)",
                "assertion": "issuer-owned exchange and ticker occurrence",
            },
        ],
    )
    expected = {
        "venue": str(resolved["venue"]).upper(),
        "issuer_id": resolved["issuer_id"],
        "security_id": resolved["security_id"],
    }
    assert validate_security_identity_binding(binding, expected=expected)["status"] == "PASS"
    wrong = freeze_security_identity_binding(
        ticker="CPNG",
        issuer_id="sec:9999999999",
        venue="NASDAQ",
        security_type="preferred-stock",
        official_sources=binding["official_sources"],
    )
    validation = validate_security_identity_binding(wrong, expected=expected)
    assert validation["status"] == "FAIL"
    assert validation["error_count"] >= 3


@pytest.mark.parametrize(
    "case",
    ["sha_mismatch", "ambiguous_mapping", "exhibit_mismatch"],
)
def test_sec_identity_resolution_fails_closed_on_unavailable_or_conflicting_source(
    case: str,
) -> None:
    if case == "sha_mismatch":
        resolved, _, _ = _sec_identity_resolution(expected_submissions_sha256="0" * 64)
    elif case == "ambiguous_mapping":
        resolved, _, _ = _sec_identity_resolution(
            tickers=["CPNG", "CPNG"],
            exchanges=["NYSE", "NYSE"],
        )
    else:
        resolved, _, _ = _sec_identity_resolution(exhibit_identity="Coupang, Inc. (NASDAQ: CPNG)")
    assert resolved["status"] == "FAIL"
    assert resolved["errors"]
