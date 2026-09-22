from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.cross_market_decision_engine_service import _compact
from scripts.m12da_source_use_contract import (
    SourceUse,
    build_source_use_projection,
    freeze_source_use_binding,
    freeze_source_use_input_expectation,
    validate_source_use_current_input,
)
from scripts.m12dk_current_source_authority import (
    build_current_source_authority,
    freeze_current_source_binding,
)
from scripts.m12dj_source_authority_preflight import preflight_current_pass_a_subject


TICKER = "RENAMED_ISSUER"
PERIOD = "2026-06-30"
ASOF = "2026-09-21"


def earnings_fact():
    q = {
        "decision_version": "financial-quality-taint-v2",
        "state": "verified_usable",
        "provider": "sec_companyfacts",
        "source_type": "full_statement",
        "source_period": PERIOD,
        "dependency_periods": [PERIOD],
        "dependency_fields": ["earnings.latest_revenue"],
        "lineage_verification_status": "verified",
        "prose_eligible": True,
        "denial_reason": None,
        "quality_reason_codes": [],
    }
    return {
        "fact_id": "earnings:" + PERIOD,
        "fact_type": "earnings",
        "as_of_date": PERIOD,
        "fields": {
            "period": PERIOD,
            "period_type": "Q2",
            "financial_period_required": True,
            "revenue": {"value": 100, "currency": "USD"},
        },
        "financial_quality": {
            "decision_version": "financial-quality-taint-v2",
            "fields": {"latest_revenue": q},
            "source_snapshot": {
                "provider": "sec_companyfacts",
                "source_type": "full_statement",
                "period": PERIOD,
                "period_type": "Q2",
                "filing_date": "2026-08-01",
            },
        },
        "field_quality": {"fields.revenue.value": deepcopy(q)},
        "prose_eligible": True,
        "interpretation_eligible": True,
    }


def inputs(paths=("stock.thesis.core_thesis",), *, mutate_fact=None, ticker=TICKER):
    fact = earnings_fact()
    if mutate_fact:
        mutate_fact(fact)
    thesis = {
        "core_thesis": "Recurring demand supports the business frame.",
        "macro_exposures": [
            {
                "factor": "demand",
                "direction": "positive",
                "weight": 2,
                "channel": "demand",
                "horizon": "long term",
                "condition": "Orders translate to revenue",
                "review_required": False,
            }
        ],
        "strengthen_signals": ["Orders expand"],
        "weaken_signals": ["Orders contract"],
        "invalidation_signals": ["Business assumptions fail"],
        "market_expectations": {"level": "high", "priced_in": "partly"},
    }
    stock = {"ticker": ticker, "thesis": thesis, "fact_catalog": [fact]}
    packet = {
        "market": "us",
        "packet_id": "frozen-source-packet",
        "assessment_date": ASOF,
        "stocks": [stock],
    }
    rows = []
    for i, path in enumerate(paths):
        category, statement, asof = "thesis", "Context only", ASOF
        ref = f"decision-evidence:renamed-{i}"
        condition = None
        if path.startswith("stock.thesis."):
            key = path.split(".")[-1]
            value = thesis[key]
            statement = _compact(value[0] if isinstance(value, list) else value)
            category = {
                "macro_exposures": "macro",
                "weaken_signals": "risks",
                "invalidation_signals": "risks",
                "market_expectations": "expectations",
            }.get(key, "thesis")
            if key.endswith("signals"):
                condition = {
                    "contract": "source-owned-logical-condition-v1",
                    "subject": ticker,
                    "generation_id": packet["packet_id"],
                }
        elif path.startswith("stock.fact_catalog."):
            fid = path.removeprefix("stock.fact_catalog.")
            ref = "canonical:" + fid
            if fid.startswith("earnings:"):
                category, statement, asof = "earnings", _compact(fact["fields"]), PERIOD
            elif fid.startswith("working-capital-relation:"):
                category, statement = (
                    "earnings_quality",
                    _compact(
                        {
                            "relation_semantics_contract": "working-capital-relation-semantics-v1",
                            "relation_id": "relation:renamed",
                            "semantic_scope": "exact_total_inventory",
                        }
                    ),
                )
            elif fid.startswith(("working-capital-derived:", "working-capital-reported:")):
                category, statement = (
                    "earnings_quality",
                    _compact(
                        {
                            "relation_id": "relation:renamed",
                            "semantic_scope": "exact_total_inventory",
                        }
                    ),
                )
            elif fid.startswith(("financial_quality:", "security_identity:", "security_basis:")):
                category, statement = "quality", "Quality context"
            else:
                category = "price_structure"
        rows.append(
            {
                "ref_id": ref,
                "source_ref": path,
                "category": category,
                "statement": statement,
                "as_of": asof,
                "label": "cosmetic label",
                "logical_condition": condition,
            }
        )
    refs = [r["ref_id"] for r in rows]
    catalog = {
        "ticker": ticker,
        "all_evidence_refs": refs,
        "core_evidence_refs": refs,
        "timing_evidence_refs": [],
        "valuation_evidence_refs": [],
        "positive_quality_refs": [],
        "material_disclosure_failure_refs": [],
        "claim_refs": ["claim:renamed"],
        "atomic_claims": [
            {
                "ticker": ticker,
                "claim_ref": "claim:renamed",
                "claim": {"text": "Demand supports the business frame.", "polarity": "BULLISH"},
                "parent_source_refs": refs,
            }
        ],
    }
    ep = {"ticker": ticker, "evidence": rows}
    return {
        "ticker": ticker,
        "source_generation_id": "source-frozen",
        "source_packet": packet,
        "evidence_packet": ep,
        "catalog": catalog,
        "source_metadata": deepcopy(rows),
        "frozen_binding": freeze_current_source_binding(
            source_generation_id="source-frozen", source_packet=packet, evidence_packet=ep
        ),
    }


def run(data):
    original = deepcopy(data)
    result = build_current_source_authority(**data)
    authority = result["authority"]
    ex = freeze_source_use_input_expectation(
        ticker=data["ticker"],
        source_generation_id="source-frozen",
        execution_generation_id="execution-new",
        catalog=data["catalog"],
        source_metadata=data["source_metadata"],
        authority_manifest=authority,
    )
    proj = build_source_use_projection(
        ticker=data["ticker"],
        input_generation_id="source-frozen",
        execution_generation_id="execution-new",
        catalog=data["catalog"],
        authority_manifest=authority,
        current_input_expectation=ex,
    )
    bound = freeze_source_use_binding(
        projection=proj, authority_manifest=authority, current_input_expectation=ex
    )
    val = validate_source_use_current_input(
        proj,
        bound,
        ex,
        ticker=data["ticker"],
        source_generation_id="source-frozen",
        execution_generation_id="execution-new",
        catalog=data["catalog"],
        source_metadata=data["source_metadata"],
    )
    assert val["status"] == "PASS"
    assert data == original
    result["projection"] = proj
    result["gate"] = preflight_current_pass_a_subject(
        ticker=data["ticker"],
        source_generation_id="source-frozen",
        execution_generation_id="execution-new",
        catalog=data["catalog"],
        source_packet={"ticker": data["ticker"], "decision_evidence": data["source_metadata"]},
        authority=authority,
        projection=proj,
        binding=bound,
        expectation=ex,
    )
    return result


@pytest.mark.parametrize("path", ["stock.thesis.core_thesis", "stock.thesis.macro_exposures"])
def test_definitions_authorize_archetype_tier_but_never_current_direction(path):
    result = run(inputs((path,)))
    uses = result["projection"]["claim_records"]["claim:renamed"]["allowed_uses"]
    assert SourceUse.PASS_A_ARCHETYPE in uses and SourceUse.PASS_A_VALUATION_TIER in uses
    assert not set(uses) & {
        SourceUse.OVERALL_DIRECTION,
        SourceUse.HOLDER_STANCE,
        SourceUse.NEW_BUYER_EXECUTION_RISK,
    }
    assert result["gate"]["receipt"]["status"] == "PASS"


@pytest.mark.parametrize("key", ["strengthen_signals", "weaken_signals", "invalidation_signals"])
def test_condition_existence_is_not_observation(key):
    result = run(inputs(("stock.thesis." + key,)))
    assert result["projection"]["claim_records"]["claim:renamed"]["allowed_uses"] == [
        "BUSINESS_CONTEXT",
        "CONTEXT",
    ]
    assert result["gate"]["model_context"] is None


def test_verified_earnings_uses_and_field_binding():
    result = run(inputs(("stock.fact_catalog.earnings:" + PERIOD,)))
    uses = result["projection"]["claim_records"]["claim:renamed"]["allowed_uses"]
    assert SourceUse.OVERALL_DIRECTION in uses and SourceUse.PASS_A_ARCHETYPE in uses
    assert result["family_receipts"][0]["earnings_lineage"]["supported_field_paths"] == [
        "fields.revenue.value"
    ]
    assert result["gate"]["receipt"]["status"] == "PASS"


@pytest.mark.parametrize(
    "change",
    [
        "denied",
        "critical",
        "unverified",
        "missing_provider",
        "unknown_provider",
        "unknown_type",
        "unknown_version",
        "wrong_period",
        "missing_dependency",
        "wrong_field_owner",
        "missing_field_proof",
        "extra_metric",
        "future_filing",
        "missing_period",
        "not_eligible",
    ],
)
def test_bad_earnings_lineage_never_elevated(change):
    def mutate(f):
        q = f["field_quality"]["fields.revenue.value"]
        if change == "denied":
            q.update(state="denied", prose_eligible=False)
        elif change == "critical":
            q["quality_reason_codes"] = ["financial_hard_error"]
        elif change == "unverified":
            q["lineage_verification_status"] = "unverified"
        elif change == "missing_provider":
            q.pop("provider")
        elif change == "unknown_provider":
            q["provider"] = "unknown_provider"
        elif change == "unknown_type":
            q["source_type"] = "future_unapproved_type"
        elif change == "unknown_version":
            q["decision_version"] = "financial-quality-taint-v99"
        elif change == "wrong_period":
            q["source_period"] = "2025-06-30"
        elif change == "missing_dependency":
            q["dependency_periods"] = []
        elif change == "wrong_field_owner":
            q["dependency_fields"] = ["earnings.latest_operating_income"]
        elif change == "missing_field_proof":
            f["field_quality"] = {}
        elif change == "extra_metric":
            f["fields"]["unsupported_metric"] = 9
        elif change == "future_filing":
            f["financial_quality"]["source_snapshot"]["filing_date"] = "2027-01-01"
        elif change == "missing_period":
            f["fields"]["financial_period_required"] = False
        elif change == "not_eligible":
            f["interpretation_eligible"] = False
        f["financial_quality"]["fields"]["latest_revenue"] = deepcopy(q)

    result = run(inputs(("stock.fact_catalog.earnings:" + PERIOD,), mutate_fact=mutate))
    assert result["family_receipts"][0]["earnings_lineage"]["status"] == "FAIL"
    assert (
        SourceUse.PASS_A_ARCHETYPE
        not in result["projection"]["claim_records"]["claim:renamed"]["allowed_uses"]
    )


def test_caution_usable_preserved_as_caution_not_verified():
    def mutate(f):
        for q in (
            f["field_quality"]["fields.revenue.value"],
            f["financial_quality"]["fields"]["latest_revenue"],
        ):
            q.update(
                state="caution_usable",
                provider="sec_foreign_filing",
                source_type="preliminary_earnings",
            )
        f["financial_quality"]["source_snapshot"].update(
            provider="sec_foreign_filing", source_type="preliminary_earnings"
        )

    result = run(inputs(("stock.fact_catalog.earnings:" + PERIOD,), mutate_fact=mutate))
    assert result["family_receipts"][0]["earnings_lineage"]["status"] == "PASS"
    assert result["family_receipts"][0]["earnings_lineage"]["caution_usable"] is True


@pytest.mark.parametrize(
    "path",
    [
        "stock.fact_catalog.working-capital-derived:x",
        "stock.fact_catalog.working-capital-relation:x",
        "stock.fact_catalog.working-capital-reported:x",
        "stock.thesis.market_expectations",
        "stock.market_transmission",
        "stock.fact_catalog.market:x",
        "stock.fact_catalog.security_identity:current",
        "stock.fact_catalog.security_basis:current",
        "stock.fact_catalog.financial_quality:current",
    ],
)
def test_restricted_family_context_preserved(path):
    result = run(inputs((path,)))
    uses = result["projection"]["claim_records"]["claim:renamed"]["allowed_uses"]
    assert SourceUse.CONTEXT in uses
    assert not set(uses) & {
        SourceUse.OVERALL_DIRECTION,
        SourceUse.PASS_A_ARCHETYPE,
        SourceUse.PASS_A_VALUATION_TIER,
    }


@pytest.mark.parametrize(
    "path",
    [
        "stock.fact_catalog.chart:x",
        "stock.fact_catalog.positioning:x",
        "stock.fact_catalog.price:current",
        "stock.fact_catalog.v3-zone:x",
        "stock.fact_catalog.valuation:current",
        "stock.current_price_context",
        "stock.technical_context",
        "technical_feature:x",
    ],
)
def test_price_technical_valuation_never_decisive(path):
    result = run(inputs((path,)))
    assert result["pass_a_visibility_exclusions"]
    assert result["gate"]["model_context"] is None


def test_unknown_family_same_text_and_cosmetic_label_cannot_create_permission():
    data = inputs(("unknown.source",))
    data["source_metadata"][0]["statement"] = data["source_packet"]["stocks"][0]["thesis"][
        "core_thesis"
    ]
    data["source_metadata"][0]["label"] = "trusted official business authority"
    data["evidence_packet"]["evidence"] = deepcopy(data["source_metadata"])
    data["frozen_binding"] = freeze_current_source_binding(
        source_generation_id="source-frozen",
        source_packet=data["source_packet"],
        evidence_packet=data["evidence_packet"],
    )
    result = run(data)
    assert result["projection"]["claim_records"]["claim:renamed"]["allowed_uses"] == ["CONTEXT"]


@pytest.mark.parametrize("target", ["ticker", "generation", "metadata", "stock", "receipt"])
def test_wrong_frozen_identity_or_digest_rejected(target):
    data = inputs()
    if target == "ticker":
        data["ticker"] = "WRONG"
    elif target == "generation":
        data["source_generation_id"] = "WRONG"
    elif target == "metadata":
        data["source_metadata"][0]["statement"] = "Changed after freeze"
    elif target == "stock":
        data["source_packet"]["stocks"][0]["ticker"] = "WRONG"
    else:
        data["frozen_binding"]["binding_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        build_current_source_authority(**data)


def test_parent_intersection_does_not_drop_restrictions():
    result = run(inputs(("stock.thesis.core_thesis", "stock.fact_catalog.earnings:" + PERIOD)))
    uses = result["projection"]["claim_records"]["claim:renamed"]["allowed_uses"]
    assert SourceUse.PASS_A_ARCHETYPE in uses and SourceUse.OVERALL_DIRECTION not in uses
    result = run(
        inputs(
            (
                "stock.fact_catalog.earnings:" + PERIOD,
                "stock.fact_catalog.working-capital-relation:x",
            )
        )
    )
    uses = result["projection"]["claim_records"]["claim:renamed"]["allowed_uses"]
    assert uses == ["CONTEXT"]
    assert len(result["projection"]["claim_records"]["claim:renamed"]["parent_source_refs"]) == 2


def test_labels_do_not_change_permission_under_new_exact_binding():
    data = inputs()
    before = run(data)["projection"]["claim_records"]["claim:renamed"]["allowed_uses"]
    data["source_metadata"][0]["label"] = "arbitrary renamed label"
    data["evidence_packet"]["evidence"] = deepcopy(data["source_metadata"])
    data["frozen_binding"] = freeze_current_source_binding(
        source_generation_id="source-frozen",
        source_packet=data["source_packet"],
        evidence_packet=data["evidence_packet"],
    )
    assert run(data)["projection"]["claim_records"]["claim:renamed"]["allowed_uses"] == before


@pytest.mark.parametrize(
    "remove",
    [
        None,
        "source_row_identity",
        "financial_lineage_contract",
        "statement_basis_state",
        "amount_period_start",
    ],
)
def test_opendart_requires_exact_statement_occurrence_lineage(remove):
    def mutate(f):
        q = f["field_quality"]["fields.revenue.value"]
        q.update(
            provider="opendart",
            source_type="formal",
            financial_lineage_contract="financial-lineage-v2",
            statement_basis_contract="financial-statement-basis-v1",
            statement_basis_state="verified_consolidated",
            source_filing_identifier="synthetic-filing",
            source_row_identity="synthetic-filing:row",
            amount_period_start="2026-04-01",
            amount_period_end=PERIOD,
            amount_period_type="single_quarter",
        )
        if remove:
            q.pop(remove)
        f["financial_quality"]["fields"]["latest_revenue"] = deepcopy(q)
        f["financial_quality"]["source_snapshot"].update(
            provider="opendart", source_type="full_statement"
        )

    result = run(inputs(("stock.fact_catalog.earnings:" + PERIOD,), mutate_fact=mutate))
    assert result["family_receipts"][0]["earnings_lineage"]["status"] == (
        "PASS" if remove is None else "FAIL"
    )


def test_one_denied_field_does_not_hide_inside_usable_earnings_envelope():
    def mutate(f):
        q = deepcopy(f["field_quality"]["fields.revenue.value"])
        q.update(
            state="denied",
            prose_eligible=False,
            dependency_fields=["earnings.latest_operating_income"],
        )
        f["fields"]["operating_income"] = {"value": 10, "currency": "USD"}
        f["field_quality"]["fields.operating_income.value"] = q
        f["financial_quality"]["fields"]["latest_operating_income"] = deepcopy(q)

    result = run(inputs(("stock.fact_catalog.earnings:" + PERIOD,), mutate_fact=mutate))
    lineage = result["family_receipts"][0]["earnings_lineage"]
    assert lineage["status"] == "FAIL"
    assert lineage["supported_field_paths"] == ["fields.revenue.value"]
    assert result["gate"]["model_context"] is None


def test_source_metadata_unknown_version_is_not_accepted():
    data = inputs()
    data["source_metadata"][0]["contract"] = "unapproved-v99"
    data["evidence_packet"]["evidence"] = deepcopy(data["source_metadata"])
    data["frozen_binding"] = freeze_current_source_binding(
        source_generation_id="source-frozen",
        source_packet=data["source_packet"],
        evidence_packet=data["evidence_packet"],
    )
    assert run(data)["gate"]["model_context"] is None
