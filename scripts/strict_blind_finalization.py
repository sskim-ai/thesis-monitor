"""Post-seal comparison from revalidated native outputs, never caller PASS flags."""
from copy import deepcopy
from tempfile import TemporaryDirectory

from app.services.unified_snapshot_contract import digest
from scripts import strict_blind_contract as blind
from scripts import strict_blind_comparison as comparison
from scripts import strict_blind_monitoring as native
from scripts import newbuyer_b2_v2_shadow as b2


def _by_subject(rows):
    result = {}
    for row in rows:
        blind.require(len(row["subjects"]) == 1, "COMPARISON_SUBJECT_SCOPE")
        ticker = row["subjects"][0]
        blind.require(ticker not in result, "COMPARISON_DUPLICATE_SUBJECT")
        result[ticker] = row
    return result


def materialize(controller):
    controller._guard()
    blind.require(controller.state == "REVEAL_COMPARISON", "COMPARISON_REVEAL_REQUIRED")
    source = controller._value("source")
    package = controller._value("blind_package")
    blind.require(blind.validate_package(package, source), "COMPARISON_SOURCE_PACKAGE_DRIFT")
    blind_rows = _by_subject(controller._value("outputs_BLIND"))
    b2_rows = _by_subject(controller._value("outputs_B2"))
    b2_requests = _by_subject(controller._value("requests_B2"))
    blind.require(set(blind_rows) == set(b2_rows) == set(package["subjects"]) == set(b2_requests),
        "COMPARISON_COHORT_GAP")
    view = dict(source=source, **{"outputs_" + stage: controller._value("outputs_" + stage)
        for stage in native.STAGES})
    left, right, bindings, semantics, comparator = {}, {}, {}, {}, {}
    for market, inputs in source["monitoring_inputs"].items():
        with TemporaryDirectory(prefix="strict-comparison-") as root:
            session = native.NativeSession(root, market=market, generation=controller.generation, source=inputs)
            session.replay("B2", view)
            for ticker in session.execution.prepared:
                subject, audit = blind.project_subject(source["blind_inputs"][ticker], generation=controller.generation)
                left[ticker] = deepcopy(blind_rows[ticker]["output"])
                blind_check = blind.validate_output(left[ticker], subject, audit)
                request, v1 = session.b2_request(ticker)
                expected_payload = b2.provider_payload(request, expected_request_sha256=request["request_sha256"])
                frozen = b2_requests[ticker]
                blind.require(frozen["payload"] == expected_payload and
                    b2_rows[ticker]["canonical_request_sha256"] == digest(frozen), "COMPARISON_B2_REQUEST_DRIFT")
                output = b2_rows[ticker]["output"]
                b2_check = b2.validate_result(output, request, expected_request_sha256=request["request_sha256"])
                row, model_input = output["new_buyer_shadow"], request["provider_request"]["input"]
                accepted = session.execution.brows[ticker]
                # Identity comes from revalidated source, not from an inferred label alias.
                right[ticker] = dict(**{k: subject[k] for k in
                    ("generation", "source_generation_id", "ticker", "security_id")}, subject_sha256=digest(subject),
                    axes={k: dict(judgment=value) for k, value in dict(
                        overall_direction=accepted["overall_direction"], new_buyer=row["new_buyer"],
                        entry_timing=row["timing_context"]["state"], holder=accepted["holder"],
                        active_material_risk=bool(model_input["active_risk_refs"]),
                        valuation_evaluability=model_input["valuation_evaluability"]["evaluability_state"],
                        valuation_state=row["valuation_context"]["state"]).items()})
                hashes = dict(blind_sha256=digest(left[ticker]), monitoring_sha256=digest(right[ticker]))
                bindings[ticker] = dict(status="PASS", **hashes, source_input_sha256=digest(source["blind_inputs"][ticker]),
                    b2_request_sha256=digest(frozen), b2_output_sha256=digest(output),
                    v1_request_sha256=v1["request_sha256"])
                semantics[ticker] = dict(status="PASS" if blind_check["status"] == b2_check["status"] == "PASS" else "FAIL",
                    **hashes, blind=blind_check, native_stages_revalidated=True, b2=b2_check)
                comparator[ticker] = deepcopy(accepted)
    result = comparison.compare(left, right, binding_receipts=bindings, semantic_receipts=semantics,
        authority=controller._value("comparison"), acceptance=controller._value("acceptance"))
    result["revalidation"] = dict(bindings=bindings, semantics=semantics, monitoring=right,
        v1_comparator=comparator, source_sha256=digest(source), economic_labels_modified=False)
    return result


class FrozenComparison:
    def __init__(self, controller):
        self.controller = controller

    def validate(self, result, authority, acceptance):
        return (comparison.validate_comparison(result, authority, acceptance)
            and result == materialize(self.controller))
