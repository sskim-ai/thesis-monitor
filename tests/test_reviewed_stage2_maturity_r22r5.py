"""Native maturity mechanics stay TEST_ONLY; production authority stays denied."""
import json
import subprocess
import sys

import pytest

from app.services import reviewed_fixture_authority as owner
from app.services.accepted_decision_v2_runtime_service import (
    accepted_v2_fundamental_core_prompt,
    AcceptedV2ProductionContext,
    build_accepted_v2_production_context,
    materialize_accepted_v2_stage2_output,
    parse_accepted_v2_production_batch_output,
    validate_accepted_v2_production_output,
)
from app.services.fixture_context_authority import reject_test_only_production
from app.services.reviewed_stage2_maturity_fixture import (
    build_reviewed_maturity_fixture,
    materialize_reviewed_stage2_fixture,
    ReviewedMaturityFixtureContext,
)
from tests.test_preconfirmation_decision_v2_service import (
    _reviewed_stage2_materialization_fixture as _stage2_materialization_fixture,
)


def test_native_maturity_positive_is_marked_and_never_production_acceptance():
    context, _, raw = _stage2_materialization_fixture()
    output = materialize_reviewed_stage2_fixture(context, raw)
    assert output.candidates[0].driver_maturity[0].as_of == "2026-08-30"
    assert output.provenance == "TEST_ONLY" and output.production_eligible is False
    assert materialize_reviewed_stage2_fixture(context, raw) == output
    for consume in (
        lambda: materialize_accepted_v2_stage2_output(context, raw),
        lambda: validate_accepted_v2_production_output(context, output),
        lambda: accepted_v2_fundamental_core_prompt(context),
    ):
        with pytest.raises(ValueError, match="reviewed_fixture_consumer_forbidden"):
            consume()
    for value in (context, output, json.loads(output.model_dump_json())):
        with pytest.raises(ValueError, match="production_test_only_fixture_forbidden"):
            reject_test_only_production(value)
    with pytest.raises(ValueError):
        parse_accepted_v2_production_batch_output(output.model_dump(mode="json"))


@pytest.mark.parametrize("change", ("ticker", "period", "statement", "source", "claim", "packet"))
def test_caller_cannot_sign_unreviewed_materialization_input(change):
    context, _, _ = _stage2_materialization_fixture()
    packet = context.evidence_packets[0]
    raw = dict(packet_id="packet-v2", market="us", assessment_date="2026-08-30", stocks=[{"ticker":"TEST"}])
    claim = "claim-stage2-materialization"
    if change == "ticker":
        packet = packet.model_copy(update={"ticker":"UNISSUED"})
    elif change in {"period", "statement", "source"}:
        key, value = {"period":("as_of","2026-08-29"), "statement":("statement","Unadmitted 987.654321"), "source":("source_ref","issuer.filing")}[change]
        packet = packet.model_copy(update={"evidence":(packet.evidence[0].model_copy(update={key:value}), *packet.evidence[1:])})
    elif change == "claim":
        claim = "unissued-claim"
    else:
        raw["packet_id"] = "unissued-packet"
    with pytest.raises(ValueError, match="reviewed_maturity_unapproved_recipe"):
        build_reviewed_maturity_fixture(packet=raw, claim_id=claim, evidence_packets=(packet,))


@pytest.mark.parametrize("change", ("receipt", "purpose", "generation", "membership", "date", "pid"))
def test_changed_context_fails_before_native_materialization(change):
    context, _, raw = _stage2_materialization_fixture()
    if change in {"receipt", "purpose", "pid"}:
        key, value = {"receipt":("receipt_id","0"*64), "purpose":("purpose","FROZEN_CORE_SCHEMA_SEMANTICS"), "pid":("owner_pid",-1)}[change]
        context = context.model_copy(update={"backend_seal":context.backend_seal.model_copy(update={key:value})})
    elif change == "generation":
        context = context.model_copy(update={"packet_id":"other"})
    elif change == "date":
        context = context.model_copy(update={"assessment_date":"2026-08-31"})
    else:
        item = context.evidence_ownership[0].model_copy(update={"core_ref_ids":("unissued",)})
        context = context.model_copy(update={"evidence_ownership":(item,)})
    with pytest.raises(ValueError, match="reviewed_fixture_"):
        materialize_reviewed_stage2_fixture(context, raw)


def test_revocation_and_new_issue_do_not_revive_old_materialization_receipt():
    context, _, raw = _stage2_materialization_fixture()
    owner.revoke_reviewed_fixture(context)
    with pytest.raises(ValueError, match="reviewed_fixture_unissued_revoked_or_changed"):
        materialize_reviewed_stage2_fixture(context, raw)
    fresh, _, _ = _stage2_materialization_fixture()
    assert fresh.backend_seal.receipt_id != context.backend_seal.receipt_id
    assert materialize_reviewed_stage2_fixture(fresh, raw).provenance == "TEST_ONLY"
    with pytest.raises(ValueError, match="reviewed_fixture_unissued_revoked_or_changed"):
        materialize_reviewed_stage2_fixture(context, raw)


def test_negative_reaches_native_provenance_gate():
    context, _, raw = _stage2_materialization_fixture()
    raw["candidates"][0]["driver_maturity"][0]["as_of"] = "2026-08-30"
    with pytest.raises(ValueError, match="stage2_model_authored_as_of_forbidden"):
        materialize_reviewed_stage2_fixture(context, raw)


def test_stripped_markers_and_base_revalidation_do_not_create_production_authority():
    context, _, raw = _stage2_materialization_fixture()
    output = materialize_reviewed_stage2_fixture(context, raw)
    bare = output.model_dump(mode="json", exclude={"provenance", "production_eligible"})
    parsed = parse_accepted_v2_production_batch_output(json.loads(json.dumps(bare)))
    stripped = AcceptedV2ProductionContext.model_validate(context.model_dump(
        mode="json", exclude={"provenance", "fixture_use", "backend_seal"},
    ))
    with pytest.raises(ValueError, match="legacy_context_backend_seal_required"):
        validate_accepted_v2_production_output(stripped, parsed)
    rebuilt = build_accepted_v2_production_context(
        packet={"packet_id": context.packet_id, "market": context.market,
                "assessment_date": context.assessment_date, "stocks": [{"ticker": "TEST"}]},
        claim_id=context.claim_id, evidence_packets=context.evidence_packets,
    )
    assert not rebuilt.evidence_ownership[0].core_ref_ids
    with pytest.raises(ValueError, match="v2_production_candidate_ownership_invalid:TEST:noncore_ref_in_fundamental_core"):
        validate_accepted_v2_production_output(rebuilt, parsed)


def test_serialized_receipt_cannot_acquire_authority_in_another_process():
    context, _, raw = _stage2_materialization_fixture()
    code = '''
import json, sys
from app.services.reviewed_stage2_maturity_fixture import (
    ReviewedMaturityFixtureContext, materialize_reviewed_stage2_fixture,
)
value = json.load(sys.stdin)
context = ReviewedMaturityFixtureContext.model_validate(value["context"])
try:
    materialize_reviewed_stage2_fixture(context, value["raw"])
except ValueError as exc:
    assert "reviewed_fixture_" in str(exc), str(exc)
    print("DENIED_WITHOUT_ISSUANCE")
else:
    raise AssertionError("serialized receipt acquired ownership")
'''
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        input=json.dumps({"context": context.model_dump(mode="json"), "raw": raw}),
        text=True, capture_output=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "DENIED_WITHOUT_ISSUANCE"
    assert isinstance(context, ReviewedMaturityFixtureContext)
