"""R14 fail-closed route tests. Synthetic fixtures are not real use grants."""

import pytest

from app.services.accepted_decision_v2_runtime_service import validate_accepted_v2_stage2_candidate
from app.services.native_accepted_ownership import BackendOwnershipRegistry, FactBoundAcceptedOwnership
from app.services.native_input_admission import BackendAdmissionRegistry
from app.services.unified_snapshot_contract import digest
from tests.native_authority_fixtures import synthetic_registry
from tests.native_economic_fixtures import invocation_for
from tests.test_native_accepted_ownership import downstream
from tests.test_reported_fact_owner import owner_fixture
from tests.test_reported_ownership_stage2 import transport_fixture


@pytest.mark.parametrize("identity,market,kind", [
    ("UNSEEN_US_ROUTE", "US", "common_stock"),
    ("UNSEEN_KR_ROUTE", "KR", "common_stock"),
    ("UNSEEN_ADS_ROUTE", "US", "depositary_receipt"),
])
def test_matching_native_invocation_still_requires_fact_use_grant(identity, market, kind):
    owner, _ = owner_fixture(identity, market=market, security_type=kind)
    admitted = [owner.admit(f) for f in owner.facts if f.field == "revenue"]
    result = owner.compare(*admitted)
    fact = admitted[0].fact
    bundle = synthetic_registry(identity, market=market.lower(), security_type=kind).bundle
    generations = dict(generation_id=fact.execution_generation_id,
                       source_generation_id=fact.source_generation_id)
    bundle = bundle.model_copy(update={**generations,
        "metrics": tuple(m.model_copy(update=generations) for m in bundle.metrics),
        "issuer_context": bundle.issuer_context.model_copy(update=generations)})
    registry = BackendAdmissionRegistry(bundle, expected_bundle_sha256=digest(bundle.model_dump(mode="json")))
    invocation = invocation_for(registry)
    ledger = BackendOwnershipRegistry()
    with pytest.raises(ValueError, match="^FACT_USE_GRANT_MISSING$"):
        ledger.begin_with_reported_interpretation(invocation, model="TEST_ONLY", effort="TEST_ONLY",
            fact_owner=owner, interpretation=result, use_axis="CORE_DIRECTION")
    assert ledger.attempt_states() == ()
    assert result.permitted_core_roles == ()


def test_v1_receipt_cannot_be_relabelled_as_fact_v2_at_actual_stage2():
    ledger, receipt, invocation, core, packet, policy = transport_fixture()
    fields = receipt.model_dump(mode="json")
    fields.update(contract="backend-accepted-economic-ownership-fact-v2",
        reported_source_binding=dict(owner_contract="FORGED_NOT_A_FACT_OWNER", owner_sha256="a" * 64,
            fact_admission_sha256=["b" * 64], raw_source_sha256=["c" * 64],
            economic_policy_version="FORGED_NOT_POLICY", interpretation_result_sha256="d" * 64,
            consumer="CORE", use_axis="CORE_DIRECTION"))
    forged = FactBoundAcceptedOwnership.model_validate(fields)
    result = validate_accepted_v2_stage2_candidate(packet, downstream(core), core, policy.bundle.ownership,
        authority_native_v2=True, accepted_ownership=forged, ownership_registry=ledger,
        backend_invocation=invocation)
    assert not result.valid
    assert result.errors == ("ISSUED_OWNERSHIP_BINDING_MISMATCH",)
