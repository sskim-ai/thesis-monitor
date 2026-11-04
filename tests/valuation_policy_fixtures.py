"""Synthetic shadow authority only. Never real issuer classification or approval."""

from datetime import date, timedelta

from app.services.unified_snapshot_contract import digest
from app.services.valuation_method_policy import (
    EconomicProperty as P,
    EvidenceReference,
    ForwardMethod as F,
    HistoricalMethod as H,
    IssuerCharacteristics,
    MethodApproval,
    PropertyEvidence,
    ShadowAuthority,
    ValuationBinding,
    receipt_sha256,
)
from app.services.valuation_method_shadow import (
    BuybackEvidence,
    FinancialInputs,
    InputQualification,
    MultipleObservation,
    Quarter,
    SourcedMetric,
    evaluate_shadow_valuation,
)


DOMAIN = "SYNTHETIC_TEST_AUTHORITY"
PROPERTIES = {
    F.NORMALIZED_CYCLE_MARGIN: (P.CYCLE_SENSITIVE_EARNINGS, P.NORMALIZABLE_CYCLE_FINANCIALS),
    F.BLENDED_NET_MARGIN_60_40: (P.ORDINARY_MARGIN_STATEMENTS,),
    F.NORMALIZED_ROE: (P.EQUITY_EARNINGS_ACCOUNTING_COMPATIBLE,),
    F.SPECIAL_SCENARIO_METHOD: (P.SCENARIO_DEPENDENT, P.ORDINARY_FORWARD_INSUFFICIENT),
    F.FORWARD_MODEL_INAPPLICABLE: (P.ORDINARY_FORWARD_INAPPLICABLE,),
    H.APPLICABLE: (P.COMPARABLE_HISTORICAL_BASIS,),
    H.INAPPLICABLE: (P.ORDINARY_HISTORICAL_INSUFFICIENT,),
}


def evidence(label="synthetic-financial-source"):
    return EvidenceReference(source_id=label, owner="synthetic-fixture-owner",
                             field_scope="explicit-test-only-economic-data",
                             period_end=date(2025, 12, 31), available_on=date(2026, 1, 30),
                             raw_sha256=digest({"SYNTHETIC_NOT_REAL_EVIDENCE": label}))


def fixture(method=F.BLENDED_NET_MARGIN_60_40, *, security="synthetic:unseen-issuer-one",
            historical=H.APPLICABLE, signal="PE_AND_PB", loss=False, market="us"):
    binding = ValuationBinding(security_id=security, market=market,
                               exchange="NASDAQ" if market == "us" else "KRX",
                               security_type="common_stock", generation="synthetic-shadow-generation",
                               as_of=date(2026, 10, 1))
    props = tuple(dict.fromkeys(PROPERTIES[method] + PROPERTIES[historical]))
    characteristics = IssuerCharacteristics(
        authority_domain=DOMAIN, binding=binding, reporting_basis="synthetic-consolidated-common",
        properties=tuple(PropertyEvidence(property=p, rationale="Explicit synthetic characteristic",
                                          evidence=(evidence(str(p)),)) for p in props))
    approvals = tuple(MethodApproval(
        authority_domain=DOMAIN, binding=binding, axis=axis, method=selected,
        historical_signal=signal if selected == H.APPLICABLE else None,
        characteristics_sha256=receipt_sha256(characteristics),
        supporting_properties=PROPERTIES[selected], rationale="Synthetic method review, not issuer fact",
        policy_owner="test-only-economic-policy-owner", approval_version="synthetic-approval-v1",
        effective_from=date(2026, 1, 1), effective_until=date(2026, 12, 31),
        evidence=(evidence("synthetic-policy-review:" + str(selected)),))
        for axis, selected in (("FORWARD_INCOME", method), ("HISTORICAL_MULTIPLE", historical)))
    quarters = []
    for year in range(2022, 2026):
        for kind, month, day in (("Q1", 3, 31), ("H1", 6, 30), ("Q3", 9, 30), ("FY", 12, 31)):
            end = date(year, month, day)
            quarters.append(Quarter(period_end=end, available_on=end + timedelta(days=30),
                                    period_type=kind, revenue=1000,
                                    common_income=-100 if loss else (100 if year < 2025 else 300),
                                    common_equity=10000, dividends=20 if kind == "FY" else None))
    financials = FinancialInputs(
        authority_domain=DOMAIN, binding=binding, currency="USD" if market == "us" else "KRW",
        price_currency="USD" if market == "us" else "KRW", share_basis="ordinary_share",
        reporting_basis=characteristics.reporting_basis, price_as_of=date(2026, 9, 30),
        current_price=120, income_shares=100, common_shares=100, current_equity=10000,
        quarters=tuple(quarters), buybacks=BuybackEvidence(state="UNAVAILABLE",
                                                        reason="NO_SYNTHETIC_BUYBACK_RECORD"),
        evidence=(evidence(),), sourced_metrics=(SourcedMetric(metric="provider_forward_pe", value=15,
        status="qualified_by_separate_test_owner", source_receipt_sha256=evidence().raw_sha256),),
        historical_observations=tuple(MultipleObservation(date=date(2023, 1, 6) + timedelta(days=7*i),
            trailing_pe=12 + i % 10, price_to_book=0.9 + (i % 35) / 100) for i in range(195)),
        trailing_pe=10, current_pbr=1.2)
    qualification = InputQualification(authority_domain=DOMAIN, binding=binding,
        financial_inputs_sha256=receipt_sha256(financials), reporting_basis=financials.reporting_basis,
        qualified_scopes=("FORWARD_INCOME", "HISTORICAL_MULTIPLE", "BOOK_SCENARIO"),
        owner="test-only-financial-owner", qualification_version="synthetic-input-review-v1",
        evidence=(evidence("synthetic-input-review"),))
    args = dict(binding=binding, characteristics=characteristics, approvals=approvals,
                financial_inputs=financials, input_qualification=qualification)
    return authorize(args)


def authorize(args):
    """Test harness explicitly pins reviewed bytes; never called by production code."""
    args = dict(args)
    q = args["input_qualification"]
    c = args["characteristics"]
    args["authority"] = ShadowAuthority(
        authority_domain=DOMAIN, binding=args["binding"], review_owner="offline-test-harness",
        review_version="synthetic-review-v1",
        characteristics_sha256=(receipt_sha256(c),) if c else (),
        method_approval_sha256=tuple(receipt_sha256(p) for p in args["approvals"]),
        input_qualification_sha256=(receipt_sha256(q),) if q else ())
    return args


def qualify_inputs(args, **changes):
    args = dict(args)
    data = args["financial_inputs"].model_dump()
    data.update(changes)
    args["financial_inputs"] = FinancialInputs.model_validate(data)
    old = args["input_qualification"]
    args["input_qualification"] = InputQualification.model_validate({**old.model_dump(),
        "financial_inputs_sha256": receipt_sha256(args["financial_inputs"])})
    return authorize(args)


def run(args, *, scenario=True):
    return evaluate_shadow_valuation(**args, include_zero_buyback_scenario=scenario)
