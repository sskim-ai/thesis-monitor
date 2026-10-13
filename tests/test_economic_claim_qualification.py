"""Synthetic typed-property fixtures, never accepted real investment judgments."""

from copy import deepcopy
import hashlib
import json

import pytest

from app.services.economic_claim_qualification import (
    BackendQualifiedEconomicPolicy,
    ClaimPolicyBundle,
    EconomicSupport,
    EconomicClaimProposal,
    policy_sha256,
    render_claim,
)
from app.services.native_economic_core import (
    materialize_economic_candidate,
    accept_economic_candidate,
    bound_reference,
)
from app.services.native_accepted_ownership import (
    BackendOwnershipRegistry,
    ClaimBoundAcceptedOwnership,
)
from app.services.unified_snapshot_contract import digest
from tests.native_economic_fixtures import synthetic_economic, invocation_for
from tests.test_native_accepted_ownership import downstream
from app.services.accepted_decision_v2_runtime_service import (
    validate_accepted_v2_candidate_ownership,
)


def claim_fixture(
    identity="UNSEEN_CLAIM_US",
    *,
    market="us",
    security_type="common_stock",
    missing_optional=False,
    mutate_supports=None,
):
    registry, legacy, _, old = synthetic_economic(
        identity, market=market, security_type=security_type
    )
    a, b = [m.metric_ref for m in registry.bundle.metrics]
    rows = []
    for index, (prop, refs, polarity) in enumerate(
        (
            ("BUSINESS_ANCHOR", [a], "POSITIVE"),
            ("BUSINESS_RISK", [b], "NEGATIVE"),
            ("HOLDER_BASIS", [b], "UNCERTAIN"),
            ("COUNTEREVIDENCE", [a, b], "MIXED"),
        )
    ):
        rows.append(
            dict(
                support_ref=f"support-{index}",
                property=prop,
                evidence_refs=refs,
                evidence_bindings=[
                    bound_reference(registry, r).model_dump(mode="json") for r in refs
                ],
                applies_to_supports=["support-0", "support-1", "support-2"]
                if prop == "COUNTEREVIDENCE"
                else [],
                independent_of_supports=[],
                property_owner_ref="synthetic-property-owner",
                economic_lineage="same-economic-lineage",
                polarity=polarity,
                state="AVAILABLE_SUPPORTING",
                temporal_rules=[
                    dict(
                        field="metric_as_of",
                        allowed_states=["UNKNOWN_NOT_PROVIDED"],
                        maximum_age_days=None,
                    )
                ],
                allowed_confidences=["LOW", "MEDIUM"],
            )
        )
    if missing_optional:
        rows.append(
            dict(
                rows[0],
                support_ref="optional-history",
                property="RECURRENCE",
                state="MISSING_OPTIONAL",
            )
        )
    if mutate_supports is not None:
        mutate_supports(rows)
    raw = json.dumps(
        dict(
            security_id=registry.bundle.security_id,
            generation_id=registry.bundle.generation_id,
            source_generation_id=registry.bundle.source_generation_id,
            owner_ref="synthetic-property-owner",
            properties=rows,
            backend_bundle_sha256=digest(registry.bundle.model_dump(mode="json")),
            source_envelope_sha256=registry.bundle.source_envelope_sha256,
        )
    ).encode()
    sha = hashlib.sha256(raw).hexdigest()
    supports = tuple(EconomicSupport(**row, property_source_sha256=sha) for row in rows)
    fields = legacy.bundle.model_dump(mode="json", exclude={"contract", "interpretations"})
    bundle = ClaimPolicyBundle(
        **fields,
        supports=supports,
        rule_sha256=policy_sha256(),
        source_kind="SYNTHETIC_TEST_PROPERTIES",
    )
    policy = BackendQualifiedEconomicPolicy(
        bundle,
        expected_policy_sha256=digest(bundle.model_dump(mode="json")),
        registry=registry,
        property_sources={"support": raw},
        trusted_source_sha256={"support": sha},
    )
    inv = invocation_for(registry, policy=policy)
    proposals = tuple(
        EconomicClaimProposal(
            claim_id=f"claim-{n}",
            requested_role=role,
            security_id=registry.bundle.security_id,
            generation_id=registry.bundle.generation_id,
            source_generation_id=registry.bundle.source_generation_id,
            interpretation_type=kind,
            polarity=polarity,
            uncertainty="LIMITED",
            support_refs=refs,
            policy_sha256=policy_sha256(),
        )
        for n, (role, kind, polarity, refs) in enumerate(
            (
                ("BUY_DRIVER", "BUSINESS_SUPPORT", "POSITIVE", ("support-0", "support-3")),
                ("SELL_DRIVER", "BUSINESS_CAUTION", "NEGATIVE", ("support-1", "support-3")),
                (
                    "DECISIVE_REASON",
                    "BALANCED_SYNTHESIS",
                    "MIXED",
                    ("support-0", "support-1", "support-3"),
                ),
                ("HOLDER_REASON", "HOLDER_REASSESSMENT", "UNCERTAIN", ("support-2", "support-3")),
            )
        )
    )
    by_id = {s.support_ref: s for s in supports}
    claims = [render_claim(p, [by_id[r] for r in p.support_refs]) for p in proposals]
    core = old.model_candidate.candidate.model_copy(
        update=dict(
            buy_drivers=(claims[0],),
            sell_drivers=(claims[1],),
            decisive_reason=claims[2],
            holder_axis=old.model_candidate.candidate.holder_axis.model_copy(
                update={"reason": claims[3]}
            ),
            balance_summary=claims[0].text + " / " + claims[1].text,
        )
    )
    model = dict(
        candidate=core.model_dump(mode="json"),
        interpretation_refs=[p.claim_id for p in proposals],
        economic_claims=[p.model_dump(mode="json") for p in proposals],
    )
    return registry, policy, inv, model


def accept(inv, model):
    bound = materialize_economic_candidate(model, inv.request, invocation=inv)
    return accept_economic_candidate(bound, inv.request, invocation=inv)


@pytest.mark.parametrize(
    "identity,market,kind",
    [
        ("UNSEEN_US", "us", "common_stock"),
        ("UNSEEN_KR", "kr", "common_stock"),
        ("UNSEEN_ADS", "us", "depositary_receipt"),
        ("UNSEEN_FINANCIAL_ROE", "us", "common_stock"),
        ("UNSEEN_CYCLICAL", "us", "common_stock"),
        ("UNSEEN_SOURCE_FORWARD", "us", "common_stock"),
        ("UNSEEN_INCOMPLETE_OPTIONAL", "us", "common_stock"),
    ],
)
def test_same_typed_claim_contract_and_native_acceptance(identity, market, kind):
    _, policy, inv, model = claim_fixture(
        identity, market=market, security_type=kind, missing_optional=True
    )
    result = accept(inv, model)
    assert result.provenance == "TEST_CANDIDATE_NOT_ACCEPTED_MODEL_JUDGMENT"
    assert not result.same_generation_model_judgment
    ledger = BackendOwnershipRegistry()
    with pytest.raises(ValueError, match="V2_ROUTE_REQUIRED"):
        ledger.begin(inv, model="OFFLINE", effort="OFFLINE")
    handle = ledger.begin_claims(inv, model="OFFLINE", effort="OFFLINE")
    receipt = ledger.complete(handle, json.dumps(model).encode())
    assert isinstance(receipt, ClaimBoundAcceptedOwnership)
    assert len(receipt.claim_eligibility_sha256) == 4
    assert (
        ledger.resolve(
            receipt, invocation=inv, candidate=result.candidate, allow_offline_reproof=True
        )
        == result.candidate
    )
    assert (
        validate_accepted_v2_candidate_ownership(
            downstream(result.candidate),
            result.candidate,
            policy.bundle.ownership,
            authority_native_v2=True,
            accepted_ownership=receipt,
            ownership_registry=ledger,
            backend_invocation=inv,
            offline_ownership_reproof=True,
        )
        == ()
    )


@pytest.mark.parametrize(
    "mutation,pattern",
    [
        ("number", "UNSUPPORTED_NUMERIC"),
        ("cause", "UNSUPPORTED_CAUSAL"),
        ("recurrence", "UNSUPPORTED_CAUSAL"),
        ("independence", "CORRELATED_SUPPORT"),
        ("missing_counter", "COUNTEREVIDENCE"),
        ("unadmitted", "UNADMITTED_CLAIM"),
        ("policy", "POLICY_DIGEST"),
        ("confidence", "CONFIDENCE_NOT_AUTHORIZED"),
        ("prose", "UNSUPPORTED_ECONOMIC_NARRATIVE"),
        ("semantic", "REJECT_ECONOMIC_SEMANTICS"),
        ("consumer", "validation error"),
        ("empty", "validation error"),
    ],
)
def test_native_negative_conjunction_no_accepted_cache(mutation, pattern):
    registry, _, inv, model = claim_fixture()
    c = model["economic_claims"][0]
    if mutation == "number":
        c["numeric_assertions"] = [
            dict(evidence_ref=registry.bundle.metrics[0].metric_ref, value=987.654321)
        ]
    elif mutation == "cause":
        c["asserts_causality"] = True
    elif mutation == "recurrence":
        c["asserts_recurrence"] = True
    elif mutation == "independence":
        c["asserts_independent_corroboration"] = True
    elif mutation == "missing_counter":
        c["support_refs"] = ["support-0"]
    elif mutation == "unadmitted":
        c["support_refs"] = ["forged"]
    elif mutation == "policy":
        c["policy_sha256"] = "a" * 64
    elif mutation == "confidence":
        model["candidate"]["confidence"] = "HIGH"
    elif mutation == "prose":
        model["candidate"]["buy_drivers"][0]["text"] = "987.654321 guarantees profit"
    elif mutation == "semantic":
        model["candidate"]["decision"] = "BUY"
    elif mutation == "consumer":
        c["consumer"] = "HOLDER"
    elif mutation == "empty":
        c["support_refs"] = []
    ledger = BackendOwnershipRegistry()
    handle = ledger.begin_claims(inv, model="OFFLINE", effort="OFFLINE")
    with pytest.raises(ValueError, match=pattern):
        ledger.complete(handle, json.dumps(model).encode())
    assert ledger.attempt_states()[0]["status"] == "REJECTED"
    assert not ledger._accepted


def test_request_omission_and_identity_remain_independent_gates():
    registry, policy, _, model = claim_fixture()
    inv = invocation_for(registry, refs=[registry.bundle.metrics[0].metric_ref], policy=policy)
    with pytest.raises(ValueError, match="REJECT_REQUEST_MEMBERSHIP"):
        accept(inv, model)
    _, _, inv, model = claim_fixture()
    bound = materialize_economic_candidate(model, inv.request, invocation=inv)
    wrong = bound.model_copy(update={"source_generation_id": "wrong"})
    with pytest.raises(ValueError, match="IDENTITY_BINDING"):
        accept_economic_candidate(wrong, inv.request, invocation=inv)


def test_valid_looking_direction_requires_inherited_ordinal_support():
    _, _, inv, model = claim_fixture()
    model["candidate"]["decision"] = "BUY"
    model["candidate"]["directional_balance"] = {"buy": 6, "sell": 4}
    with pytest.raises(ValueError, match="ORDINAL_CURRENT_OR_INDEPENDENT_SUPPORT_GAP"):
        accept(inv, model)
    model["candidate"]["decision"] = "HOLD"
    model["candidate"]["directional_balance"] = {"buy": 5.5, "sell": 4.5}
    model["candidate"]["confidence"] = "LOW"
    assert accept(inv, model).candidate.directional_balance.buy == 5.5


def test_new_attempt_does_not_revive_bad_claim_and_public_receipt_is_not_authority():
    _, _, inv, model = claim_fixture()
    ledger = BackendOwnershipRegistry()
    first = ledger.begin_claims(inv, model="OFFLINE", effort="OFFLINE")
    bad = deepcopy(model)
    bad["candidate"]["buy_drivers"][0]["text"] = "unowned"
    with pytest.raises(ValueError):
        ledger.complete(first, json.dumps(bad).encode())
    second = ledger.begin_claims(inv, model="OFFLINE", effort="OFFLINE")
    raw = json.dumps(model).encode()
    receipt = ledger.complete(second, raw)
    assert ledger.complete(second, raw) == receipt
    with pytest.raises(ValueError, match="SUPERSEDED"):
        ledger.complete(first, raw)
    core = accept(inv, model).candidate
    with pytest.raises(ValueError, match="UNISSUED"):
        BackendOwnershipRegistry().resolve(
            receipt, invocation=inv, candidate=core, allow_offline_reproof=True
        )
    with pytest.raises(ValueError, match="NOT_ACCEPTED_MODEL"):
        ledger.resolve(receipt, invocation=inv, candidate=core)
    ledger.revoke(receipt)
    with pytest.raises(ValueError, match="STALE"):
        ledger.resolve(receipt, invocation=inv, candidate=core, allow_offline_reproof=True)


@pytest.mark.parametrize("state", ["AVAILABLE_CONTRADICTORY", "MISSING_REQUIRED"])
def test_model_cannot_omit_backend_required_counterevidence(state):
    def mutate(rows):
        rows.append(
            dict(
                rows[3], support_ref="known-counter", state=state, applies_to_supports=["support-0"]
            )
        )

    _, _, inv, model = claim_fixture(mutate_supports=mutate)
    with pytest.raises(ValueError, match="APPLICABLE_COUNTEREVIDENCE_OR_SUPPORT_OMITTED"):
        accept(inv, model)


@pytest.mark.parametrize(
    "kind,assertion",
    [("CAUSAL_MECHANISM", "asserts_causality"), ("RECURRENCE", "asserts_recurrence")],
)
def test_contradiction_never_supplies_affirmative_assertion(kind, assertion):
    def mutate(rows):
        rows.append(
            dict(
                rows[0],
                support_ref="contradiction",
                property=kind,
                state="AVAILABLE_CONTRADICTORY",
                polarity="NEGATIVE",
                applies_to_supports=["support-0"],
            )
        )

    _, _, inv, model = claim_fixture(mutate_supports=mutate)
    for claim in model["economic_claims"]:
        if "support-0" in claim["support_refs"]:
            claim["support_refs"].append("contradiction")
    model["economic_claims"][0][assertion] = True
    with pytest.raises(ValueError, match="UNSUPPORTED_CAUSAL_OR_RECURRENCE_ASSERTION"):
        accept(inv, model)


def test_negative_anchor_cannot_support_buy_driver():
    def mutate(rows):
        rows[0]["polarity"] = "NEGATIVE"

    _, _, inv, model = claim_fixture(mutate_supports=mutate)
    with pytest.raises(ValueError, match="MATERIAL_ANCHOR_POLARITY_MISMATCH"):
        accept(inv, model)


def test_native_claim_route_cannot_issue_model_owned_receipt():
    _, _, inv, _ = claim_fixture()
    with pytest.raises(ValueError, match="QUALIFIED_CLAIM_OFFLINE_ONLY"):
        BackendOwnershipRegistry(offline_reproof=False).begin_claims(
            inv, model="forged-live", effort="test"
        )


def test_source_properties_bind_exact_admission_and_required_metric_time():
    def altered(rows):
        rows[0]["evidence_bindings"][0]["admission_sha256"] = "a" * 64

    with pytest.raises(ValueError, match="PROPERTY_SOURCE_ADMISSION_BINDING_MISMATCH"):
        claim_fixture(mutate_supports=altered)

    def missing_time(rows):
        rows[0]["temporal_rules"][0]["field"] = "financial_period"

    with pytest.raises(ValueError, match="EXPLICIT_NON_DUPLICATE_METRIC_TEMPORAL_POLICY_REQUIRED"):
        claim_fixture(mutate_supports=missing_time)


def test_correlated_same_refs_do_not_become_independent_by_lineage_label():
    def mutate(rows):
        rows.append(
            dict(
                rows[0],
                support_ref="corroboration",
                property="INDEPENDENT_CORROBORATION",
                economic_lineage="different-label",
                independent_of_supports=["support-0"],
                applies_to_supports=["support-0"],
            )
        )

    _, _, inv, model = claim_fixture(mutate_supports=mutate)
    for claim in model["economic_claims"]:
        if "support-0" in claim["support_refs"]:
            claim["support_refs"].append("corroboration")
    model["economic_claims"][0]["asserts_independent_corroboration"] = True
    with pytest.raises(ValueError, match="CORRELATED_SUPPORT_NOT_INDEPENDENT"):
        accept(inv, model)


@pytest.mark.parametrize("polarity,target", [("NEGATIVE", "support-0"), ("POSITIVE", "support-1")])
def test_other_economic_case_cannot_supply_ordinal_support(polarity, target):
    def mutate(rows):
        rows.append(
            dict(
                rows[0],
                support_ref="current",
                property="CURRENT_CORROBORATION",
                polarity=polarity,
                applies_to_supports=[target],
            )
        )

    _, _, inv, model = claim_fixture(mutate_supports=mutate)
    for claim in model["economic_claims"]:
        claim["support_refs"].append("current")
    model["candidate"]["decision"] = "BUY"
    model["candidate"]["directional_balance"] = {"buy": 6, "sell": 4}
    with pytest.raises(ValueError, match="ORDINAL_CURRENT_OR_INDEPENDENT_SUPPORT_GAP"):
        accept(inv, model)


def test_nested_applicable_required_support_cannot_be_omitted():
    def mutate(rows):
        rows.append(
            dict(
                rows[0],
                support_ref="cause",
                property="CAUSAL_MECHANISM",
                applies_to_supports=["support-0"],
            )
        )
        rows.append(
            dict(
                rows[3],
                support_ref="cause-validation",
                state="MISSING_REQUIRED",
                applies_to_supports=["cause"],
            )
        )

    _, _, inv, model = claim_fixture(mutate_supports=mutate)
    model["economic_claims"][0]["support_refs"].append("cause")
    with pytest.raises(ValueError, match="APPLICABLE_COUNTEREVIDENCE_OR_SUPPORT_OMITTED"):
        accept(inv, model)


def test_standalone_claim_issuance_and_lookup_verify_actual_request():
    _, policy, inv, model = claim_fixture()
    proposal = EconomicClaimProposal.model_validate(model["economic_claims"][0])
    _, receipt, _ = policy.qualify(proposal, request=inv.request, invocation=inv)
    assert policy.resolve_claim(receipt, proposal, request=inv.request, invocation=inv) == receipt
    forged = inv.request.model_copy(update={"prompt": "forged"})
    with pytest.raises(ValueError, match="REQUEST_IDENTITY_BINDING"):
        policy.qualify(proposal, request=forged, invocation=inv)
    with pytest.raises(ValueError, match="REQUEST_IDENTITY_BINDING"):
        policy.resolve_claim(receipt, proposal, request=forged, invocation=inv)


@pytest.mark.parametrize("polarity,target", [("NEGATIVE", "support-0"), ("POSITIVE", "support-1")])
def test_claim_independence_requires_compatible_case_below_six(polarity, target):
    def mutate(rows):
        rows.append(
            dict(
                rows[1],
                support_ref="independent",
                property="INDEPENDENT_CORROBORATION",
                polarity=polarity,
                applies_to_supports=[target],
                independent_of_supports=["support-0"],
                economic_lineage="distinct",
            )
        )

    _, _, inv, model = claim_fixture(mutate_supports=mutate)
    for claim in model["economic_claims"]:
        claim["support_refs"].append("independent")
    model["economic_claims"][0]["asserts_independent_corroboration"] = True
    assert model["candidate"]["directional_balance"]["buy"] == 5
    with pytest.raises(ValueError, match="CORRELATED_SUPPORT_NOT_INDEPENDENT"):
        accept(inv, model)


def test_multiple_drivers_keep_separate_current_support_relationships():
    def mutate(rows):
        rows.append(
            dict(rows[1], support_ref="anchor-two", property="BUSINESS_ANCHOR", polarity="POSITIVE")
        )
        rows[3]["applies_to_supports"].append("anchor-two")
        for anchor in (rows[0], rows[-1]):
            rows.append(
                dict(
                    anchor,
                    support_ref="current-" + anchor["support_ref"],
                    property="CURRENT_CORROBORATION",
                    applies_to_supports=[anchor["support_ref"]],
                )
            )

    registry, policy, inv, model = claim_fixture(mutate_supports=mutate)
    second = deepcopy(model["economic_claims"][0])
    second.update(
        claim_id="claim-second", support_refs=["anchor-two", "support-3", "current-anchor-two"]
    )
    model["economic_claims"].insert(1, second)
    for claim, metric in zip(model["economic_claims"][:2], registry.bundle.metrics, strict=True):
        claim["numeric_assertions"] = [dict(evidence_ref=metric.metric_ref, value=metric.value)]
    for claim in model["economic_claims"]:
        if "support-0" in claim["support_refs"]:
            claim["support_refs"].append("current-support-0")
    by_id = {s.support_ref: s for s in policy.bundle.supports}
    rendered = [
        render_claim(EconomicClaimProposal.model_validate(c), [by_id[r] for r in c["support_refs"]])
        for c in model["economic_claims"]
    ]
    model["interpretation_refs"] = [c["claim_id"] for c in model["economic_claims"]]
    model["candidate"]["buy_drivers"] = [r.model_dump(mode="json") for r in rendered[:2]]
    model["candidate"]["sell_drivers"] = [rendered[2].model_dump(mode="json")]
    model["candidate"]["decisive_reason"] = rendered[3].model_dump(mode="json")
    model["candidate"]["holder_axis"]["reason"] = rendered[4].model_dump(mode="json")
    model["candidate"]["balance_summary"] = " / ".join(r.text for r in rendered[:3])
    model["candidate"]["decision"] = "BUY"
    model["candidate"]["directional_balance"] = {"buy": 6, "sell": 4}
    assert accept(inv, model).candidate.directional_balance.buy == 6
