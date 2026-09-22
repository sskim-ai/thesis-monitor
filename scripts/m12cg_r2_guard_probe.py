from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2ProductionContext,
    materialize_accepted_v2_stage2_output,
)
from app.services.cross_market_decision_engine_service import DecisionEvidenceRef
from app.services.decision_canary_service import canonical_sha256
from app.services.evidence_maturity_pricing_service import (
    concrete_evidence_date,
    project_maturity_provenance,
    symbolic_maturity_evidence_kind,
)
from app.services.preconfirmation_decision_v2_service import (
    validate_preconfirmation_candidate,
)


FINANCIAL_REF = "canonical:financial_quality:latest"
EARNINGS_REF = "canonical:earnings:latest"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def pretty_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def subset_context(
    context: AcceptedV2ProductionContext,
    subjects: tuple[str, ...],
) -> AcceptedV2ProductionContext:
    selected = set(subjects)
    return context.model_copy(
        update={
            "selected_subjects": subjects,
            "evidence_packets": tuple(
                row for row in context.evidence_packets if row.ticker in selected
            ),
            "evidence_ownership": tuple(
                row for row in context.evidence_ownership if row.ticker in selected
            ),
            "prior_accepted": tuple(
                row for row in context.prior_accepted if row.ticker in selected
            ),
        }
    )


def subset_raw(raw: dict[str, object], ticker: str) -> dict[str, object]:
    payload = deepcopy(raw)
    for field_name in ("fundamental_cores", "candidates", "adjudications"):
        rows = payload.get(field_name)
        if isinstance(rows, list):
            payload[field_name] = [
                row
                for row in rows
                if isinstance(row, dict) and str(row.get("ticker")) == ticker
            ]
    return payload


def mutate_context_statement(
    context_payload: dict[str, object],
    *,
    ticker: str,
    ref_id: str,
    remove: tuple[str, ...] = (),
    replace: dict[str, object] | None = None,
) -> tuple[dict[str, object], str]:
    payload = deepcopy(context_payload)
    packets = payload.get("evidence_packets")
    if not isinstance(packets, list):
        raise ValueError("evidence_packets_missing")
    for packet in packets:
        if not isinstance(packet, dict) or packet.get("ticker") != ticker:
            continue
        evidence_rows = packet.get("evidence")
        if not isinstance(evidence_rows, list):
            continue
        for evidence in evidence_rows:
            if not isinstance(evidence, dict) or evidence.get("ref_id") != ref_id:
                continue
            statement = json.loads(str(evidence["statement"]))
            for field_name in remove:
                statement.pop(field_name, None)
            statement.update(replace or {})
            evidence["statement"] = json.dumps(
                statement,
                ensure_ascii=False,
                sort_keys=True,
            )
            packet["evidence_sha256"] = canonical_sha256(
                {
                    "evidence": evidence_rows,
                    "technical_context_id": packet.get("technical_context_id"),
                    "technical_context_status": packet.get(
                        "technical_context_status"
                    ),
                }
            )
            return payload, f"/evidence_packets/{ticker}/{ref_id}/statement"
    raise ValueError(f"evidence_not_found:{ticker}:{ref_id}")


def mutate_ref(
    row: DecisionEvidenceRef,
    *,
    remove: tuple[str, ...] = (),
    replace: dict[str, object] | None = None,
    row_update: dict[str, object] | None = None,
) -> DecisionEvidenceRef:
    statement = json.loads(row.statement)
    for field_name in remove:
        statement.pop(field_name, None)
    statement.update(replace or {})
    return row.model_copy(
        update={
            "statement": json.dumps(statement, ensure_ascii=False, sort_keys=True),
            **(row_update or {}),
        }
    )


def classification_record(
    fixture_id: str,
    row: DecisionEvidenceRef,
    *,
    expected: str,
    scope: str,
) -> dict[str, object]:
    kind = symbolic_maturity_evidence_kind(row)
    projection = project_maturity_provenance(
        {row.ref_id: row},
        (row.ref_id,),
    )
    observed = kind.value if kind is not None else None
    assertion = (
        observed is not None and expected == "RECOGNIZE"
    ) or (observed is None and expected == "REJECT")
    return {
        "fixture_id": fixture_id,
        "input_sha256": sha256(row.model_dump(mode="json")),
        "expected_contract_result": expected,
        "observed_result": observed,
        "projection": {
            "as_of": projection.as_of,
            "provenance_status": (
                projection.provenance_status.value
                if projection.provenance_status is not None
                else None
            ),
            "invalid_ref_ids": list(projection.invalid_ref_ids),
        },
        "assertion_result": "PASS" if assertion else "FAIL",
        "evidence_scope": scope,
    }


def materializer_record(
    fixture_id: str,
    context: AcceptedV2ProductionContext,
    raw: dict[str, object],
    *,
    expected_error: str | None,
) -> tuple[dict[str, object], object | None]:
    before = sha256(raw)
    try:
        output = materialize_accepted_v2_stage2_output(context, raw)
        observed = "ACCEPTED"
        error_type = None
        output_hash = sha256(output.model_dump(mode="json"))
    except Exception as exc:
        output = None
        observed = str(exc)
        error_type = type(exc).__name__
        output_hash = None
    after = sha256(raw)
    if expected_error is None:
        assertion = observed == "ACCEPTED"
    else:
        assertion = expected_error in observed
    return (
        {
            "fixture_id": fixture_id,
            "input_sha256_before": before,
            "input_sha256_after": after,
            "input_unchanged": before == after,
            "expected_contract_result": (
                "ACCEPT" if expected_error is None else f"REJECT:{expected_error}"
            ),
            "observed_result": observed,
            "exception_type": error_type,
            "output_sha256": output_hash,
            "assertion_result": "PASS" if assertion else "FAIL",
            "evidence_scope": "ACTUAL_TYPED_MATERIALIZER",
        },
        output,
    )


def find_symbolic_row(raw: dict[str, object]) -> int:
    candidate = raw["candidates"][0]
    for index, row in enumerate(candidate["driver_maturity"]):
        refs = tuple(row.get("supporting_evidence_refs", ())) + tuple(
            row.get("contradicting_evidence_refs", ())
        )
        if FINANCIAL_REF in refs:
            return index
    raise ValueError("financial_quality_row_not_found")


def probe(args: argparse.Namespace) -> dict[str, object]:
    raw_root = args.m12ce_root.resolve() / "raw" / "reproof-no-repair" / "us"
    context_path = raw_root / "context.json"
    context_payload = json.loads(context_path.read_text(encoding="utf-8"))
    context = AcceptedV2ProductionContext.model_validate(context_payload)
    packet = next(row for row in context.evidence_packets if row.ticker == "SKHY")
    evidence = {row.ref_id: row for row in packet.evidence}
    raw_path = raw_root / "batch-03.output.json"
    raw = subset_raw(json.loads(raw_path.read_text(encoding="utf-8")), "SKHY")
    skhy_context = subset_context(context, ("SKHY",))
    row_index = find_symbolic_row(raw)
    results: list[dict[str, object]] = []

    baseline_record, baseline_output = materializer_record(
        "G01",
        skhy_context,
        deepcopy(raw),
        expected_error=None,
    )
    if baseline_output is not None:
        candidate = baseline_output.candidates[0]
        maturity = candidate.driver_maturity[row_index]
        baseline_record.update(
            {
                "candidate_row_count": len(candidate.driver_maturity),
                "symbolic_row_index": row_index,
                "symbolic_as_of": maturity.as_of,
                "symbolic_provenance_status": maturity.provenance_status.value,
                "decisive_row_preserved": maturity.decisive,
            }
        )
    results.append(baseline_record)

    missing_financial_payload, pointer = mutate_context_statement(
        context_payload,
        ticker="SKHY",
        ref_id=FINANCIAL_REF,
        remove=("source_period",),
    )
    missing_financial_context = subset_context(
        AcceptedV2ProductionContext.model_validate(missing_financial_payload),
        ("SKHY",),
    )
    missing_record, _ = materializer_record(
        "G02",
        missing_financial_context,
        deepcopy(raw),
        expected_error="stage2_materialization_unresolvable_provenance",
    )
    missing_record["mutation_json_pointer"] = pointer + "/source_period"
    missing_record["typed_context_parse"] = "PASS"
    results.append(missing_record)

    results.append(
        classification_record(
            "G03",
            evidence[EARNINGS_REF],
            expected="RECOGNIZE",
            scope="TYPED_CLASSIFIER_AND_PROJECTOR_ONLY_AT_EXISTING_ATOMIC_BOUNDARY",
        )
    )
    for fixture_id, remove in (
        ("G04", ("period_label",)),
        ("G05", ("period_type",)),
        ("G06", ("period_label", "period_type")),
    ):
        results.append(
            classification_record(
                fixture_id,
                mutate_ref(evidence[EARNINGS_REF], remove=remove),
                expected="REJECT",
                scope="TYPED_CLASSIFIER_AND_PROJECTOR_ONLY_AT_EXISTING_ATOMIC_BOUNDARY",
            )
        )

    invalid_values: tuple[object, ...] = ("null", "", 0, False, {}, [])
    g07_variants: list[dict[str, object]] = []
    for ref_id, field_name in (
        (FINANCIAL_REF, "source_period"),
        (EARNINGS_REF, "period_label"),
        (EARNINGS_REF, "period_type"),
    ):
        for invalid_value in invalid_values:
            record = classification_record(
                "G07",
                mutate_ref(
                    evidence[ref_id],
                    replace={field_name: invalid_value},
                ),
                expected="REJECT",
                scope="TYPED_CLASSIFIER_AND_PROJECTOR",
            )
            record.update(
                {
                    "ref_id": ref_id,
                    "field_name": field_name,
                    "invalid_value": invalid_value,
                    "invalid_value_type": type(invalid_value).__name__,
                }
            )
            g07_variants.append(record)
    results.append(
        {
            "fixture_id": "G07",
            "variant_count": len(g07_variants),
            "variants": g07_variants,
            "assertion_result": (
                "PASS"
                if all(row["assertion_result"] == "PASS" for row in g07_variants)
                else "FAIL"
            ),
            "evidence_scope": "TYPED_CLASSIFIER_AND_PROJECTOR",
        }
    )

    owned = next(row for row in context.evidence_ownership if row.ticker == "SKHY")
    visible = set((*owned.core_ref_ids, *owned.timing_ref_ids))
    concrete_ref = next(
        row.ref_id
        for row in packet.evidence
        if row.ref_id in visible and concrete_evidence_date(row.as_of) is not None
    )
    mixed_raw = deepcopy(raw)
    mixed_row = mixed_raw["candidates"][0]["driver_maturity"][row_index]
    mixed_row["supporting_evidence_refs"] = [concrete_ref, FINANCIAL_REF]
    mixed_row["contradicting_evidence_refs"] = []
    g08, _ = materializer_record(
        "G08",
        missing_financial_context,
        deepcopy(mixed_raw),
        expected_error="stage2_materialization_unresolvable_provenance",
    )
    g08["concrete_peer_ref"] = concrete_ref
    results.append(g08)
    g09, g09_output = materializer_record(
        "G09",
        skhy_context,
        deepcopy(mixed_raw),
        expected_error=None,
    )
    if g09_output is not None:
        mixed_output_row = g09_output.candidates[0].driver_maturity[row_index]
        g09.update(
            {
                "as_of": mixed_output_row.as_of,
                "provenance_status": mixed_output_row.provenance_status.value,
                "concrete_peer_ref": concrete_ref,
            }
        )
    results.append(g09)

    g10_variants: list[dict[str, object]] = []
    for name, remove, replace, row_update in (
        ("missing_decision_version", ("decision_version",), {}, {}),
        ("bad_source_ref", (), {}, {"source_ref": "fixture"}),
        ("bad_source_type", (), {"source_type": "reported"}, {}),
        ("bad_state", (), {"state": "verified"}, {}),
        ("missing_reason_codes", ("reason_codes",), {}, {}),
        ("bad_reason_codes_type", (), {"reason_codes": "bad"}, {}),
    ):
        record = classification_record(
            "G10",
            mutate_ref(
                evidence[FINANCIAL_REF],
                remove=remove,
                replace=replace,
                row_update=row_update,
            ),
            expected="REJECT",
            scope="TYPED_CLASSIFIER_AND_PROJECTOR",
        )
        record["variant"] = name
        g10_variants.append(record)
    malformed = evidence[FINANCIAL_REF].model_copy(update={"statement": "{"})
    malformed_record = classification_record(
        "G10",
        malformed,
        expected="REJECT",
        scope="TYPED_CLASSIFIER_AND_PROJECTOR",
    )
    malformed_record["variant"] = "malformed_statement"
    g10_variants.append(malformed_record)
    results.append(
        {
            "fixture_id": "G10",
            "variant_count": len(g10_variants),
            "variants": g10_variants,
            "assertion_result": (
                "PASS"
                if all(row["assertion_result"] == "PASS" for row in g10_variants)
                else "FAIL"
            ),
            "evidence_scope": "TYPED_CLASSIFIER_AND_PROJECTOR",
        }
    )

    g11_variants: list[dict[str, object]] = []
    for name, value in (
        ("arbitrary_current", "current"),
        ("padded", " latest "),
        ("bad_calendar", "2026-02-30"),
    ):
        record = classification_record(
            "G11",
            evidence[FINANCIAL_REF].model_copy(update={"as_of": value}),
            expected="REJECT",
            scope="TYPED_CLASSIFIER_AND_PROJECTOR",
        )
        record["variant"] = name
        g11_variants.append(record)
    future_raw = deepcopy(raw)
    future_row = future_raw["candidates"][0]["driver_maturity"][row_index]
    future_ref = concrete_ref
    future_row["supporting_evidence_refs"] = [future_ref]
    future_row["contradicting_evidence_refs"] = []
    future_context_payload, _ = mutate_context_statement(
        context_payload,
        ticker="SKHY",
        ref_id=FINANCIAL_REF,
    )
    packets = future_context_payload["evidence_packets"]
    for packet_payload in packets:
        if packet_payload["ticker"] != "SKHY":
            continue
        for row_payload in packet_payload["evidence"]:
            if row_payload["ref_id"] == future_ref:
                assessment = date.fromisoformat(str(context.assessment_date))
                row_payload["as_of"] = (assessment + timedelta(days=1)).isoformat()
        packet_payload["evidence_sha256"] = canonical_sha256(
            {
                "evidence": packet_payload["evidence"],
                "technical_context_id": packet_payload.get("technical_context_id"),
                "technical_context_status": packet_payload.get(
                    "technical_context_status"
                ),
            }
        )
    future_context = subset_context(
        AcceptedV2ProductionContext.model_validate(future_context_payload),
        ("SKHY",),
    )
    future_record, _ = materializer_record(
        "G11",
        future_context,
        future_raw,
        expected_error="stage2_materialization_future_derived_date",
    )
    future_record["variant"] = "future_concrete"
    g11_variants.append(future_record)
    cross_raw = deepcopy(raw)
    cross_row = cross_raw["candidates"][0]["driver_maturity"][row_index]
    cross_row["supporting_evidence_refs"] = ["cross-ticker:missing"]
    cross_row["contradicting_evidence_refs"] = []
    cross_record, _ = materializer_record(
        "G11",
        skhy_context,
        cross_raw,
        expected_error="stage2_materialization_unresolvable_provenance",
    )
    cross_record["variant"] = "cross_ticker_unknown"
    g11_variants.append(cross_record)
    results.append(
        {
            "fixture_id": "G11",
            "variant_count": len(g11_variants),
            "variants": g11_variants,
            "assertion_result": (
                "PASS"
                if all(row["assertion_result"] == "PASS" for row in g11_variants)
                else "FAIL"
            ),
            "evidence_scope": "CLASSIFIER_PROJECTOR_AND_ACTUAL_MATERIALIZER",
        }
    )

    g12_variants: list[dict[str, object]] = []
    for field_name, value, error in (
        ("as_of", None, "stage2_model_authored_as_of_forbidden"),
        ("as_of", "2026-09-15", "stage2_model_authored_as_of_forbidden"),
        (
            "provenance_status",
            "SYMBOLIC_ONLY_NO_CONCRETE_DATE",
            "stage2_model_authored_provenance_status_forbidden",
        ),
        (
            "provenance_status",
            "INVALID",
            "stage2_model_authored_provenance_status_forbidden",
        ),
    ):
        authored_raw = deepcopy(raw)
        authored_raw["candidates"][0]["driver_maturity"][row_index][field_name] = value
        record, _ = materializer_record(
            "G12",
            skhy_context,
            authored_raw,
            expected_error=error,
        )
        record.update({"field": field_name, "value": value})
        g12_variants.append(record)
    results.append(
        {
            "fixture_id": "G12",
            "variant_count": len(g12_variants),
            "variants": g12_variants,
            "assertion_result": (
                "PASS"
                if all(row["assertion_result"] == "PASS" for row in g12_variants)
                else "FAIL"
            ),
            "evidence_scope": "RAW_INGRESS_BEFORE_MATERIALIZATION",
        }
    )

    if baseline_output is None:
        g13 = {
            "fixture_id": "G13",
            "assertion_result": "NOT_PROVEN",
            "reason": "baseline_materialization_unavailable",
        }
    else:
        validation = validate_preconfirmation_candidate(
            missing_financial_context.evidence_packets[0],
            baseline_output.candidates[0],
        )
        matching_errors = [
            error
            for error in validation.errors
            if error.startswith("maturity_provenance_unresolvable:")
        ]
        g13 = {
            "fixture_id": "G13",
            "forged_candidate_sha256": sha256(
                baseline_output.candidates[0].model_dump(mode="json")
            ),
            "independent_validator_valid": validation.valid,
            "validator_errors": list(validation.errors),
            "expected_contract_result": "REJECT_MISSING_CANONICAL_METADATA",
            "observed_result": "REJECTED" if matching_errors else "NOT_REJECTED",
            "assertion_result": "PASS" if matching_errors else "FAIL",
            "evidence_scope": "INDEPENDENT_PRECONFIRMATION_VALIDATOR",
        }
    results.append(g13)

    g14_variants: list[dict[str, object]] = []
    for identity in ("us_fixture", "kr_fixture"):
        ref_id = f"canonical:{identity}:financial_quality:latest"
        valid = evidence[FINANCIAL_REF].model_copy(
            update={
                "ref_id": ref_id,
                "source_ref": f"stock.fact_catalog.{ref_id.removeprefix('canonical:')}",
            }
        )
        valid_record = classification_record(
            "G14",
            valid,
            expected="RECOGNIZE",
            scope="GENERIC_TYPED_CLASSIFIER",
        )
        valid_record.update({"identity": identity, "variant": "explicit_null"})
        g14_variants.append(valid_record)
        invalid_record = classification_record(
            "G14",
            mutate_ref(valid, remove=("source_period",)),
            expected="REJECT",
            scope="GENERIC_TYPED_CLASSIFIER",
        )
        invalid_record.update({"identity": identity, "variant": "missing_key"})
        g14_variants.append(invalid_record)
    results.append(
        {
            "fixture_id": "G14",
            "variant_count": len(g14_variants),
            "variants": g14_variants,
            "assertion_result": (
                "PASS"
                if all(row["assertion_result"] == "PASS" for row in g14_variants)
                else "FAIL"
            ),
            "evidence_scope": "GENERIC_TYPED_CLASSIFIER",
        }
    )

    return {
        "contract": "m12cg-r2-guard-boundary-probe-v1",
        "runtime_label": args.runtime_label,
        "source": {
            "context_sha256": hashlib.sha256(context_path.read_bytes()).hexdigest(),
            "raw_output_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            "ticker": "SKHY",
            "symbolic_row_index": row_index,
        },
        "results": results,
        "fixture_count": len(results),
        "variant_count": sum(
            int(row.get("variant_count", 1)) for row in results
        ),
        "pass_count": sum(row.get("assertion_result") == "PASS" for row in results),
        "status": (
            "PASS"
            if all(row.get("assertion_result") == "PASS" for row in results)
            else "FAIL"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m12ce-root", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--runtime-label", required=True)
    args = parser.parse_args()
    result = probe(args)
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_bytes(pretty_bytes(result))


if __name__ == "__main__":
    main()
