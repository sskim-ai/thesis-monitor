from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from typing import Any


PASS = "PASS"
FAIL = "FAIL"
NOT_PROVEN = "NOT_PROVEN"
NOT_RUN = "NOT_RUN"
BLOCKED_BY_DEPENDENCY = "BLOCKED_BY_DEPENDENCY"
NOT_APPLICABLE = "NOT_APPLICABLE"

KNOWN_RESULTS = {
    PASS,
    FAIL,
    NOT_PROVEN,
    NOT_RUN,
    BLOCKED_BY_DEPENDENCY,
    NOT_APPLICABLE,
}
NON_PASS_RESULTS = {FAIL, NOT_PROVEN, NOT_RUN, BLOCKED_BY_DEPENDENCY}


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def exact_node_coverage(
    nodes: Sequence[Mapping[str, object]],
    required_node_ids: Sequence[str],
) -> dict[str, object]:
    required = tuple(required_node_ids)
    observed_ids = [str(row.get("node_id") or "") for row in nodes]
    counts = Counter(observed_ids)
    by_id = {str(row.get("node_id") or ""): dict(row) for row in nodes}
    missing = [node_id for node_id in required if counts[node_id] == 0]
    duplicate = [node_id for node_id in required if counts[node_id] > 1]
    unknown = sorted(node_id for node_id in counts if node_id not in set(required))
    non_pass = [
        node_id
        for node_id in required
        if node_id in by_id and by_id[node_id].get("status") != PASS
    ]
    return {
        "required_node_count": len(required),
        "observed_node_count": len(nodes),
        "missing_node_ids": missing,
        "duplicate_node_ids": duplicate,
        "unknown_node_ids": unknown,
        "non_pass_node_ids": non_pass,
        "status": (
            PASS
            if required
            and not missing
            and not duplicate
            and not unknown
            and not non_pass
            else FAIL
        ),
    }


def aggregate_fixture_rows(
    rows: Sequence[Mapping[str, object] | None],
    *,
    required_fixture_ids: Sequence[str],
    required_variant_ids: Sequence[str],
) -> dict[str, object]:
    required_fixtures = tuple(required_fixture_ids)
    required_variants = tuple(required_variant_ids)
    errors: list[str] = []
    normalized: list[Mapping[str, object]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"null_or_invalid_row:{index}")
            continue
        normalized.append(row)

    fixture_ids = [str(row.get("fixture_id") or "") for row in normalized]
    variant_ids = [str(row.get("variant_id") or "") for row in normalized]
    fixture_counts = Counter(fixture_ids)
    variant_counts = Counter(variant_ids)
    required_fixture_set = set(required_fixtures)
    required_variant_set = set(required_variants)

    if not required_fixtures:
        errors.append("required_fixture_inventory_empty")
    if not required_variants:
        errors.append("required_variant_inventory_empty")
    errors.extend(
        f"missing_fixture:{fixture_id}"
        for fixture_id in required_fixtures
        if fixture_counts[fixture_id] == 0
    )
    errors.extend(
        f"unknown_fixture:{fixture_id}"
        for fixture_id in sorted(set(fixture_ids) - required_fixture_set)
        if fixture_id
    )
    errors.extend(
        f"missing_variant:{variant_id}"
        for variant_id in required_variants
        if variant_counts[variant_id] == 0
    )
    errors.extend(
        f"duplicate_variant:{variant_id}"
        for variant_id, count in variant_counts.items()
        if variant_id and count > 1
    )
    errors.extend(
        f"unknown_variant:{variant_id}"
        for variant_id in sorted(set(variant_ids) - required_variant_set)
        if variant_id
    )

    result_counts: Counter[str] = Counter()
    proven_variants: list[str] = []
    pending_variants: list[str] = []
    failed_variants: list[str] = []
    for index, row in enumerate(normalized):
        fixture_id = str(row.get("fixture_id") or f"row-{index}")
        variant_id = str(row.get("variant_id") or f"row-{index}")
        result = row.get("assertion_result")
        if not isinstance(result, str) or result not in KNOWN_RESULTS:
            errors.append(f"unknown_or_missing_status:{fixture_id}:{variant_id}:{result!r}")
            continue
        result_counts[result] += 1
        denominator = row.get("denominator")
        evidence = row.get("evidence")
        if not isinstance(denominator, int) or isinstance(denominator, bool) or denominator < 1:
            errors.append(f"missing_or_zero_denominator:{fixture_id}:{variant_id}")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"missing_evidence:{fixture_id}:{variant_id}")
        observed_result = row.get("observed_result")
        expected_result = row.get("expected_result")
        if observed_result is None or observed_result == "":
            errors.append(f"missing_observed_result:{fixture_id}:{variant_id}")
        if expected_result is None or expected_result == "":
            errors.append(f"missing_expected_result:{fixture_id}:{variant_id}")
        if not _is_sha256(row.get("source_sha256")):
            errors.append(f"invalid_source_sha256:{fixture_id}:{variant_id}")
        if not _is_sha256(row.get("runtime_sha256")):
            errors.append(f"invalid_runtime_sha256:{fixture_id}:{variant_id}")

        if result == NOT_APPLICABLE:
            disposition = row.get("approved_disposition") is True
            equivalent = row.get("equivalent_evidence")
            if not disposition or not isinstance(equivalent, list) or not equivalent:
                errors.append(f"unsupported_not_applicable:{fixture_id}:{variant_id}")
                failed_variants.append(variant_id)
            else:
                proven_variants.append(variant_id)
        elif result == PASS:
            proven_variants.append(variant_id)
        elif result == FAIL:
            failed_variants.append(variant_id)
        else:
            pending_variants.append(variant_id)

    if errors or failed_variants:
        status = FAIL
    elif pending_variants:
        status = NOT_PROVEN
    elif len(proven_variants) == len(required_variants) and required_variants:
        status = PASS
    else:
        status = FAIL
        errors.append("proven_variant_denominator_mismatch")

    return {
        "required_fixture_count": len(required_fixtures),
        "required_variant_count": len(required_variants),
        "observed_row_count": len(rows),
        "proven_variant_count": len(proven_variants),
        "pending_variant_count": len(pending_variants),
        "failed_variant_count": len(failed_variants),
        "result_counts": dict(sorted(result_counts.items())),
        "proven_variant_ids": proven_variants,
        "pending_variant_ids": pending_variants,
        "failed_variant_ids": failed_variants,
        "errors": list(dict.fromkeys(errors)),
        "status": status,
    }


def evaluate_expected_exception(
    operation: Callable[[], Any],
    *,
    expected_type: type[Exception],
    expected_code: str,
) -> dict[str, object]:
    try:
        operation()
    except Exception as exc:
        observed_code = str(exc)
        matched = type(exc) is expected_type and observed_code == expected_code
        return {
            "expected_exception_type": expected_type.__name__,
            "expected_code": expected_code,
            "observed_exception_type": type(exc).__name__,
            "observed_code": observed_code,
            "status": PASS if matched else FAIL,
        }
    return {
        "expected_exception_type": expected_type.__name__,
        "expected_code": expected_code,
        "observed_exception_type": None,
        "observed_code": None,
        "status": FAIL,
    }
