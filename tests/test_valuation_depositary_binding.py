"""Synthetic shadow-basis proof, never real depositary authority."""
from datetime import date

import pytest
from pydantic import ValidationError

from app.services.valuation_method_policy import (
    DepositaryRatioEvidence,
    DepositaryValuationBinding,
    ForwardMethod,
    IssuerCharacteristics,
    MethodApproval,
    ShadowAuthority,
    ValuationBinding,
    receipt_sha256,
    select_shadow_methods,
)
from app.services.valuation_method_shadow import FinancialInputs, InputQualification
from valuation_policy_fixtures import evidence, fixture, run


def depositary(**changes):
    claim = DepositaryRatioEvidence(
        listed_security_id="synthetic:new-ads", underlying_security_id="synthetic:underlying",
        generation="synthetic-shadow-generation", ordinary_shares_per_listed_share="5",
        listed_currency="USD", reporting_currency="USD", effective_from=date(2026, 1, 30),
        effective_until=date(2026, 10, 1), evidence=(evidence("synthetic-depositary-contract"),),
    )
    data = dict(security_id=claim.listed_security_id, underlying_security_id=claim.underlying_security_id,
        market="us", exchange="TEST", security_type="ADS", generation=claim.generation,
        as_of=date(2026, 10, 1), listed_currency="USD", reporting_currency="USD", ratio_claims=(claim,))
    data.update(changes)
    return DepositaryValuationBinding.model_validate(data)


def rebind(args, binding):
    args = dict(args)
    args["binding"] = binding
    characteristics = IssuerCharacteristics.model_validate({
        **args["characteristics"].model_dump(), "binding": binding})
    approvals = tuple(MethodApproval.model_validate({**a.model_dump(), "binding": binding,
        "characteristics_sha256": receipt_sha256(characteristics)}) for a in args["approvals"])
    financials = FinancialInputs.model_validate({**args["financial_inputs"].model_dump(), "binding": binding})
    qualification = InputQualification.model_validate({**args["input_qualification"].model_dump(),
        "binding": binding, "financial_inputs_sha256": receipt_sha256(financials)})
    authority = ShadowAuthority.model_validate({**args["authority"].model_dump(), "binding": binding,
        "characteristics_sha256": (receipt_sha256(characteristics),),
        "method_approval_sha256": tuple(receipt_sha256(a) for a in approvals),
        "input_qualification_sha256": (receipt_sha256(qualification),)})
    args.update(characteristics=characteristics, approvals=approvals, financial_inputs=financials,
                input_qualification=qualification, authority=authority)
    return args


def test_common_stock_original_serialization_is_unchanged():
    b = fixture()["binding"]
    assert ValuationBinding.model_validate(b.model_dump()).model_dump() == b.model_dump()
    assert set(b.model_dump()) == {"security_id", "market", "exchange", "security_type", "generation", "as_of"}


@pytest.mark.parametrize("kind", ["ADS", "DEPOSITARY_RECEIPT"])
def test_depositary_keeps_explicit_five_to_one_ratio_and_basis(kind):
    b = depositary(security_type=kind)
    assert b.ratio_claims[0].ordinary_shares_per_listed_share == 5
    assert b.price_share_basis != b.reporting_share_basis
    assert DepositaryValuationBinding.model_validate_json(b.model_dump_json()) == b


@pytest.mark.parametrize("field,value,reason", [
    ("underlying_security_id", "synthetic:wrong", "underlying_mismatch"),
    ("security_id", "synthetic:wrong", "listing_mismatch"),
    ("generation", "old-generation", "generation_mismatch"),
    ("reporting_currency", "KRW", "currency_mismatch"),
    ("listed_currency", "KRW", "currency_mismatch"),
    ("as_of", date(2026, 10, 2), "ratio_not_effective"),
    ("as_of", date(2026, 1, 1), "ratio_not_effective"),
])
def test_wrong_depositary_binding_rejected(field, value, reason):
    with pytest.raises(ValidationError, match=reason):
        depositary(**{field: value})


def test_missing_ratio_cannot_default_to_one():
    with pytest.raises(ValidationError):
        depositary(ratio_claims=())


@pytest.mark.parametrize("ratio", ["0", "-1", "NaN", "Infinity"])
def test_invalid_ratio_rejected(ratio):
    claim = depositary().ratio_claims[0].model_dump()
    with pytest.raises(ValidationError):
        DepositaryRatioEvidence.model_validate({**claim, "ordinary_shares_per_listed_share": ratio})


def test_conflicting_official_ratio_claims_fail_closed():
    first = depositary().ratio_claims[0]
    second = DepositaryRatioEvidence.model_validate({**first.model_dump(), "ordinary_shares_per_listed_share": "3"})
    with pytest.raises(ValidationError, match="conflicting_ratios"):
        depositary(ratio_claims=(first, second))


def test_future_evidence_does_not_qualify_historical_binding():
    first = depositary().ratio_claims[0]
    future = evidence().model_copy(update={"available_on": date(2026, 10, 2)})
    claim = DepositaryRatioEvidence.model_validate({**first.model_dump(), "evidence": (future,)})
    with pytest.raises(ValidationError, match="future_evidence"):
        depositary(ratio_claims=(claim,))


@pytest.mark.parametrize("market", ["us", "kr"])
@pytest.mark.parametrize("method", list(ForwardMethod)[:-1])
def test_unseen_subject_method_qualification_is_property_based(market, method):
    a = fixture(method, market=market, security="synthetic:new-P-one")
    b = fixture(method, market=market, security="synthetic:new-P-two")
    left, right = run(a), run(b)
    assert left.selection.forward.status == right.selection.forward.status == "QUALIFIED_FOR_SHADOW"
    assert left.forward == right.forward
    assert left.historical == right.historical


def test_depositary_method_can_qualify_without_fabricating_converted_financials():
    args = rebind(fixture(), depositary())
    selection = select_shadow_methods(args["binding"], args["characteristics"], args["approvals"], args["authority"])
    assert selection.forward.status == "QUALIFIED_FOR_SHADOW"
    result = run(args)
    assert "DEPOSITARY_FINANCIAL_CONVERSION_NOT_QUALIFIED" in result.input_reason_codes
    assert result.forward.forward_eps is None
    assert result.zero_buyback_scenario.forward_pbr_scenario is None
    assert result.independent_sourced_metrics == args["financial_inputs"].sourced_metrics
    assert run(args, scenario=False).forward == result.forward


def test_cross_generation_depositary_approval_is_rejected_by_existing_selector():
    args = rebind(fixture(), depositary())
    claim = DepositaryRatioEvidence.model_validate({
        **args["binding"].ratio_claims[0].model_dump(), "generation": "other-generation"})
    changed = depositary(generation="other-generation", ratio_claims=(claim,))
    selected = select_shadow_methods(changed, args["characteristics"], args["approvals"], args["authority"])
    assert selected.forward.status == "UNRESOLVED"
    assert "METHOD_BINDING_MISMATCH" in selected.forward.reason_codes
