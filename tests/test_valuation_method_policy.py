import ast
from datetime import date, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.valuation_method_policy import (
    EconomicProperty as P,
    ForwardMethod as F,
    HistoricalMethod as H,
    IssuerCharacteristics,
    MethodApproval,
    PropertyEvidence,
    ShadowAuthority,
    receipt_sha256,
)
from app.services.valuation_method_shadow import BuybackEvidence, InputQualification
from valuation_policy_fixtures import authorize, evidence, fixture, qualify_inputs, run


@pytest.mark.parametrize("method,income,eps,pe,bvps,pbr", [
    (F.NORMALIZED_CYCLE_MARGIN, 800, 8, 15, 106.4, 1.1278),
    (F.BLENDED_NET_MARGIN_60_40, 1040, 10.4, 11.5385, 108.32, 1.1078),
    (F.NORMALIZED_ROE, 800, 8, 15, 106.4, 1.1278),
])
def test_synthetic_method_and_zero_scenario_arithmetic(method, income, eps, pe, bvps, pbr):
    result = run(fixture(method))
    assert result.selection.forward.status == "QUALIFIED_FOR_SHADOW"
    assert result.forward.expected_earnings == pytest.approx(income)
    assert result.forward.forward_eps == pytest.approx(eps)
    assert result.forward.forward_pe == pe
    assert result.forward.confidence == 0.55
    scenario = result.zero_buyback_scenario
    assert scenario.status == "SCENARIO_ONLY"
    assert scenario.forward_bvps_scenario == pytest.approx(bvps)
    assert scenario.forward_pbr_scenario == pbr
    assert scenario.buyback_evidence.state == "UNAVAILABLE"
    assert scenario.assumption_status == "ASSUMED_ZERO"
    assert not scenario.eligible_as_authoritative_evidence
    assert not result.eligible_as_production_authority
    assert result.canonical_modeled_forward_bvps is None
    assert result.canonical_modeled_forward_pbr is None
    assert receipt_sha256(result) == receipt_sha256(run(fixture(method)))


@pytest.mark.parametrize("method", [F.SPECIAL_SCENARIO_METHOD, F.FORWARD_MODEL_INAPPLICABLE])
def test_qualified_inapplicability_does_not_invent_a_number(method):
    result = run(fixture(method, historical=H.INAPPLICABLE))
    assert result.forward.status == "INAPPLICABLE"
    assert result.forward.expected_earnings is None
    assert result.zero_buyback_scenario.status == "INAPPLICABLE"
    assert result.zero_buyback_scenario.forward_pbr_scenario is None
    assert result.historical.position == "unknown"
    assert result.historical.reason_codes == ("HISTORICAL_METHOD_INAPPLICABLE",)
    assert result.independent_sourced_metrics[0].value == 15


@pytest.mark.parametrize("field,value,reason", [
    ("policy_owner", "", "POLICY_OWNER_MISSING"),
    ("approval_version", " ", "APPROVAL_VERSION_MISSING"),
    ("effective_until", date(2025, 12, 31), "METHOD_NOT_EFFECTIVE"),
    ("effective_from", date(2027, 1, 1), "METHOD_NOT_EFFECTIVE"),
])
def test_invalid_approval_even_when_hash_is_reviewed(field, value, reason):
    args = fixture()
    old, history = args["approvals"]
    changed = MethodApproval.model_validate({**old.model_dump(), field: value})
    args["approvals"] = (changed, history)
    result = run(authorize(args))
    assert result.forward.status == "UNRESOLVED"
    assert reason in result.selection.forward.reason_codes
    assert result.selection.historical.status == "QUALIFIED_FOR_SHADOW"
    assert result.independent_sourced_metrics == args["financial_inputs"].sourced_metrics


@pytest.mark.parametrize("field,value", [("security_id", "different-security"),
                                       ("generation", "old-generation"), ("market", "kr")])
def test_method_binding_rejected(field, value):
    args = fixture()
    p, h = args["approvals"]
    changed = MethodApproval.model_validate({**p.model_dump(), "binding": {
        **p.binding.model_dump(), field: value}})
    args["approvals"] = (changed, h)
    result = run(authorize(args))
    assert "METHOD_BINDING_MISMATCH" in result.selection.forward.reason_codes
    assert result.zero_buyback_scenario.forward_pbr_scenario is None


def test_receipt_missing_does_not_default_to_ordinary_margin():
    args = fixture()
    args["approvals"] = ()
    result = run(authorize(args))
    assert result.forward.status == "UNRESOLVED"
    assert result.selection.forward.method == "UNRESOLVED"
    assert "METHOD_APPROVAL_MISSING" in result.selection.forward.reason_codes
    assert result.independent_sourced_metrics[0].value == 15


def test_conflicting_receipts_are_not_first_wins():
    args = fixture()
    args["approvals"] = (*args["approvals"], args["approvals"][0])
    result = run(authorize(args))
    assert "CONFLICTING_APPROVALS" in result.selection.forward.reason_codes


@pytest.mark.parametrize("changes", [
    {"method": "PICK_BY_TICKER"}, {"selection_basis": "TICKER_MAPPING"},
    {"ticker": "MU"}, {"axis": "HISTORICAL_MULTIPLE"},
])
def test_unsupported_method_or_ticker_mapping_cannot_be_approval(changes):
    p = fixture()["approvals"][0]
    with pytest.raises(ValidationError):
        MethodApproval.model_validate({**p.model_dump(), **changes})


def test_generic_semiconductor_does_not_qualify_cycle_normalization():
    args = fixture(F.NORMALIZED_CYCLE_MARGIN)
    c = args["characteristics"]
    c = IssuerCharacteristics.model_validate({**c.model_dump(), "properties": [
        PropertyEvidence(property=P.GENERIC_SEMICONDUCTOR, rationale="Only a generic code",
                         evidence=(evidence(),)).model_dump()]})
    args["characteristics"] = c
    args["approvals"] = tuple(MethodApproval.model_validate({**p.model_dump(),
        "characteristics_sha256": receipt_sha256(c)}) for p in args["approvals"])
    result = run(authorize(args))
    assert result.forward.status == "UNRESOLVED"
    assert any("CYCLE_SENSITIVE_EARNINGS" in r for r in result.selection.forward.reason_codes)


def test_roe_method_does_not_infer_insurer_classification():
    args = fixture(F.NORMALIZED_ROE)
    assert P.REGULATED_INSURER not in {p.property for p in args["characteristics"].properties}
    assert run(args).forward.status == "VALUE"
    args["characteristics"] = None
    result = run(authorize(args))
    assert "ISSUER_CHARACTERISTICS_MISSING" in result.selection.forward.reason_codes
    assert result.forward.status == "UNRESOLVED"


def test_reviewed_hash_is_required_not_just_owner_label():
    args = fixture()
    args["authority"] = ShadowAuthority.model_validate({**args["authority"].model_dump(),
                                                       "method_approval_sha256": ()})
    assert "METHOD_NOT_APPROVED" in run(args).selection.forward.reason_codes


def test_synthetic_cannot_be_promoted_to_live_or_reviewed_domain():
    args = fixture()
    with pytest.raises(ValidationError):
        ShadowAuthority.model_validate({**args["authority"].model_dump(), "purpose": "PRODUCTION"})
    args["authority"] = ShadowAuthority.model_validate({**args["authority"].model_dump(),
        "authority_domain": "REVIEWED_SHADOW_AUTHORITY"})
    result = run(args)
    assert "METHOD_AUTHORITY_DOMAIN_MISMATCH" in result.selection.forward.reason_codes
    assert result.forward.status == "UNRESOLVED"


@pytest.mark.parametrize("field,value", [("reporting_basis", "unqualified-basis"),
                                       ("input_qualification", None)])
def test_input_qualification_is_independent_of_method_approval(field, value):
    args = fixture()
    if field == "input_qualification":
        args[field] = value
    else:
        args["input_qualification"] = InputQualification.model_validate({
            **args["input_qualification"].model_dump(), field: value})
    result = run(authorize(args))
    assert result.selection.forward.status == "QUALIFIED_FOR_SHADOW"
    assert result.forward.status == "UNRESOLVED"
    assert result.forward.forward_pe is None


def test_post_qualification_input_mutation_is_rejected():
    args = fixture()
    args["financial_inputs"] = args["financial_inputs"].model_copy(update={"current_price": 1})
    result = run(args)
    assert "INPUT_DIGEST_MISMATCH" in result.input_reason_codes
    assert result.forward.status == "UNRESOLVED"


@pytest.mark.parametrize("method", [F.NORMALIZED_CYCLE_MARGIN, F.BLENDED_NET_MARGIN_60_40,
                                   F.NORMALIZED_ROE])
def test_identity_permutation_preserves_semantics(method):
    a = run(fixture(method, security="synthetic:MU"))
    b = run(fixture(method, security="synthetic:never-registered-issuer"))
    assert a.forward == b.forward
    assert a.historical == b.historical
    assert a.zero_buyback_scenario.forward_pbr_scenario == b.zero_buyback_scenario.forward_pbr_scenario
    assert a.zero_buyback_scenario.assumptions == b.zero_buyback_scenario.assumptions
    assert receipt_sha256(a) != receipt_sha256(b)


def test_applicability_permutation_changes_only_governed_axis():
    a = run(fixture(F.NORMALIZED_CYCLE_MARGIN))
    b = run(fixture(F.BLENDED_NET_MARGIN_60_40))
    assert a.forward.expected_earnings == 800 and b.forward.expected_earnings == 1040
    assert a.historical == b.historical
    assert a.independent_sourced_metrics == b.independent_sourced_metrics


@pytest.mark.parametrize("method", [F.NORMALIZED_CYCLE_MARGIN, F.BLENDED_NET_MARGIN_60_40,
                                   F.NORMALIZED_ROE])
def test_negative_earnings_not_confused_with_missing_data(method):
    loss = run(fixture(method, loss=True))
    assert loss.forward.status == "NOT_MEANINGFUL"
    assert loss.forward.forward_pe is None
    args = fixture(method)
    missing = run(qualify_inputs(args, quarters=()))
    assert missing.forward.status == "UNRESOLVED"
    assert loss.zero_buyback_scenario.forward_pbr_scenario is None


def test_scenario_toggle_does_not_change_authoritative_or_independent_fields():
    args = fixture()
    before = run(args, scenario=False)
    after = run(args)
    assert before.model_dump(exclude={"zero_buyback_scenario"}) == after.model_dump(
        exclude={"zero_buyback_scenario"})
    assert before.zero_buyback_scenario is None
    assert after.zero_buyback_scenario.forward_pbr_scenario is not None


@pytest.mark.parametrize("state,amount", [("UNAVAILABLE", None), ("VERIFIED_ZERO", 0),
                                        ("VERIFIED_AMOUNT", 20), ("INVALID", None)])
def test_buyback_evidence_and_future_assumption_remain_distinct(state, amount):
    args = fixture()
    observation = BuybackEvidence(state=state, observed_amount=amount,
        observed_period_end=date(2025, 12, 31) if amount is not None else None,
        reason="Explicit synthetic observation state", evidence=(evidence(),) if amount is not None else ())
    result = run(qualify_inputs(args, buybacks=observation))
    scenario = result.zero_buyback_scenario
    assert scenario.buyback_evidence == observation
    assert scenario.assumed_future_buybacks == 0
    assert scenario.assumption_status == "ASSUMED_ZERO"
    if state == "INVALID":
        assert scenario.status == "UNRESOLVED"
        assert scenario.forward_pbr_scenario is None
    else:
        assert scenario.forward_pbr_scenario == 1.1078
    assert result.forward.forward_pe == 11.5385
    assert result.canonical_modeled_forward_pbr is None


@pytest.mark.parametrize("state,amount", [("UNAVAILABLE", 0), ("INVALID", 0),
                                        ("VERIFIED_ZERO", 20), ("VERIFIED_AMOUNT", 0),
                                        ("ASSUMED_ZERO", 0)])
def test_zero_assumption_cannot_be_financial_evidence(state, amount):
    with pytest.raises(ValidationError):
        BuybackEvidence(state=state, observed_amount=amount, reason="test",
                        observed_period_end=date(2025, 12, 31), evidence=(evidence(),))


def test_all_material_scenario_assumptions_are_disclosed():
    scenario = run(fixture()).zero_buyback_scenario
    assumptions = {a.component: a for a in scenario.assumptions}
    assert set(assumptions) == {"forecast_common_income", "forecast_dividends", "forecast_buybacks",
                                "common_shares", "equity_issuance", "other_comprehensive_income"}
    for key in ("forecast_buybacks", "equity_issuance", "other_comprehensive_income"):
        assert assumptions[key].method == "ASSUMED_ZERO" and assumptions[key].value == 0
    assert assumptions["common_shares"].method == "FIXED_CURRENT_COMMON_SHARES"
    assert assumptions["forecast_dividends"].method == "median_3y_payout_ratio"


def test_missing_dividends_and_book_basis_do_not_fabricate_scenario():
    args = fixture()
    quarters = tuple(q.model_copy(update={"dividends": None}) for q in args["financial_inputs"].quarters)
    result = run(qualify_inputs(args, quarters=quarters))
    assert result.zero_buyback_scenario.reason_codes == ("DIVIDEND_INPUT_MISSING",)
    assert result.forward.forward_pe == 11.5385
    assert run(qualify_inputs(args, common_shares=None)).zero_buyback_scenario.reason_codes == (
        "BOOK_BASIS_MISSING",)


def test_price_currency_and_temporal_qualification_fail_closed():
    args = fixture()
    assert "PRICE_FINANCIAL_CURRENCY_MISMATCH" in run(qualify_inputs(
        args, price_currency="KRW")).input_reason_codes
    assert "PRICE_FUTURE_DATA" in run(qualify_inputs(
        args, price_as_of=args["binding"].as_of + timedelta(days=1))).input_reason_codes


def test_input_scope_denial_does_not_spread_from_book_to_income():
    args = fixture()
    args["input_qualification"] = InputQualification.model_validate({
        **args["input_qualification"].model_dump(), "qualified_scopes": ("FORWARD_INCOME",)})
    result = run(authorize(args))
    assert result.forward.forward_pe == 11.5385
    assert result.zero_buyback_scenario.status == "UNRESOLVED"
    assert "INPUT_SCOPE_UNQUALIFIED:BOOK_SCENARIO" in result.zero_buyback_scenario.reason_codes


def test_legacy_entrypoints_do_not_import_shadow_modules():
    root = Path(__file__).resolve().parents[1] / "app"
    new = {"valuation_method_policy.py", "valuation_method_shadow.py"}
    for path in root.rglob("*.py"):
        if path.name in new:
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not any(name[:-3] in (node.module or "") for name in new), str(path)
            elif isinstance(node, ast.Import):
                assert not any(name[:-3] in alias.name for name in new for alias in node.names), str(path)


def test_frozen_types_reject_mutation_and_nonfinite_inputs():
    args = fixture()
    with pytest.raises(ValidationError):
        args["binding"].generation = "mutated"
    with pytest.raises(ValidationError):
        qualify_inputs(args, current_price=float("nan"))


@pytest.mark.parametrize("market", ["us", "kr"])
def test_same_policy_and_evidence_apply_in_supported_market_basis(market):
    result = run(fixture(market=market))
    assert result.forward.forward_pe == 11.5385
    assert result.zero_buyback_scenario.forward_pbr_scenario == 1.1078
    assert result.buyback_evidence.state == "UNAVAILABLE"


def test_zero_earnings_are_not_meaningful_not_missing():
    args = fixture()
    quarters = tuple(q.model_copy(update={"common_income": 0}) for q in args["financial_inputs"].quarters)
    result = run(qualify_inputs(args, quarters=quarters))
    assert result.forward.expected_earnings == 0
    assert result.forward.status == "NOT_MEANINGFUL"
    assert result.zero_buyback_scenario.status == "UNRESOLVED"


def test_qualified_financial_permutation_changes_numbers_by_existing_formula():
    args = fixture()
    quarters = tuple(q.model_copy(update={"common_income": q.common_income * 2})
                     for q in args["financial_inputs"].quarters)
    before, after = run(args), run(qualify_inputs(args, quarters=quarters))
    assert after.forward.expected_earnings == before.forward.expected_earnings * 2
    assert after.forward.forward_eps == before.forward.forward_eps * 2
    assert after.forward.forward_pe == round(120 / after.forward.forward_eps, 4)
    assert before.independent_sourced_metrics == after.independent_sourced_metrics


def test_historical_method_permutation_does_not_control_forward_income():
    normal = run(fixture())
    inapplicable = run(fixture(historical=H.INAPPLICABLE))
    assert normal.forward == inapplicable.forward
    assert inapplicable.historical.position == "unknown"
    assert normal.historical.position != "unknown"


@pytest.mark.parametrize("field", ["security_id", "generation"])
def test_financial_qualification_wrong_identity_or_generation(field):
    args = fixture()
    q = args["input_qualification"]
    args["input_qualification"] = InputQualification.model_validate({**q.model_dump(),
        "binding": {**q.binding.model_dump(), field: "wrong"}})
    result = run(authorize(args))
    assert "INPUT_QUALIFICATION_BINDING_MISMATCH" in result.input_reason_codes
    assert result.forward.status == "UNRESOLVED"


def test_future_characteristic_and_policy_evidence_are_rejected():
    args = fixture()
    p, h = args["approvals"]
    future = evidence().model_copy(update={"available_on": date(2027, 1, 1)})
    args["approvals"] = (MethodApproval.model_validate({**p.model_dump(), "evidence": (future,)}), h)
    assert "METHOD_FUTURE_EVIDENCE" in run(authorize(args)).selection.forward.reason_codes
    c = args["characteristics"]
    args["characteristics"] = IssuerCharacteristics.model_validate({**c.model_dump(),
        "properties": tuple(p.model_copy(update={"evidence": (future,)}) for p in c.properties)})
    assert "CHARACTERISTICS_FUTURE_EVIDENCE" in run(authorize(args)).selection.forward.reason_codes


def test_unapproved_characteristics_and_inputs_remain_unresolved():
    args = fixture()
    args["authority"] = ShadowAuthority.model_validate({**args["authority"].model_dump(),
        "characteristics_sha256": (), "input_qualification_sha256": ()})
    result = run(args)
    assert "CHARACTERISTICS_NOT_REVIEWED" in result.selection.forward.reason_codes
    assert "INPUT_OWNER_NOT_AUTHORIZED" in result.input_reason_codes


def test_nonzero_issuance_and_oci_remain_explicit_forecast_inputs():
    args = fixture()
    quarters = tuple(q.model_copy(update={"equity_issuance": 10, "other_comprehensive_income": -5})
                     for q in args["financial_inputs"].quarters)
    scenario = run(qualify_inputs(args, quarters=quarters)).zero_buyback_scenario
    assert scenario.forecast_equity_scenario == 10837
    assumptions = {a.component: a for a in scenario.assumptions}
    assert assumptions["equity_issuance"].value == 10
    assert assumptions["other_comprehensive_income"].value == -5
    assert assumptions["other_comprehensive_income"].method == "HISTORICAL_MEDIAN_PROJECTION"
