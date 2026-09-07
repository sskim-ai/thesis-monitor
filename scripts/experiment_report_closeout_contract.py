from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


REPORT_INPUT_NORMALIZATION_CONTRACT = "experiment-report-input-normalization-v1"


class ReportInputConflict(ValueError):
    """Raised when two report fields claim different values for one semantic count."""


def _count_value(value: object, *, source: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReportInputConflict(f"invalid_nonnegative_count:{source}:{value!r}")
    return value


def resolve_count(
    semantic: str,
    candidates: Sequence[tuple[str, object]],
) -> dict[str, object]:
    observed: list[dict[str, object]] = []
    values: dict[int, list[str]] = {}
    explicit_unknown_sources: list[str] = []
    for source, raw_value in candidates:
        value = _count_value(raw_value, source=source)
        observed.append({"source": source, "value": value})
        if value is None:
            explicit_unknown_sources.append(source)
            continue
        values.setdefault(value, []).append(source)
    if len(values) > 1:
        detail = ",".join(
            f"{value}:{'|'.join(sorted(sources))}" for value, sources in sorted(values.items())
        )
        raise ReportInputConflict(f"contradictory_report_count:{semantic}:{detail}")
    if values:
        value = next(iter(values))
        return {
            "semantic": semantic,
            "value": value,
            "status": "RESOLVED",
            "sources": observed,
        }
    return {
        "semantic": semantic,
        "value": None,
        "status": ("UNKNOWN_EXPLICIT" if explicit_unknown_sources else "UNKNOWN_ABSENT"),
        "sources": observed,
    }


def _present(document: Mapping[str, object], key: str) -> list[tuple[str, object]]:
    return [(key, document[key])] if key in document else []


def _list_count(
    document: Mapping[str, object], key: str, *, unique: bool = False
) -> list[tuple[str, object]]:
    if key not in document:
        return []
    value = document[key]
    if value is None:
        return [(f"len({key})", None)]
    if not isinstance(value, list):
        raise ReportInputConflict(f"list_required_for_count:{key}")
    if unique:
        rendered = [str(item) for item in value]
        if len(rendered) != len(set(rendered)):
            raise ReportInputConflict(f"duplicate_membership_rows:{key}")
    return [(f"len({key})", len(value))]


def _derived_difference(
    document: Mapping[str, object],
    *,
    minuend_keys: Sequence[str],
    subtrahend_keys: Sequence[str],
    source: str,
) -> list[tuple[str, object]]:
    minuends = [document[key] for key in minuend_keys if key in document]
    subtrahends = [document[key] for key in subtrahend_keys if key in document]
    if not minuends or not subtrahends:
        return []
    left = _count_value(minuends[0], source=f"{source}:minuend")
    right = _count_value(subtrahends[0], source=f"{source}:subtrahend")
    if left is None or right is None:
        return [(source, None)]
    if right > left:
        raise ReportInputConflict(f"negative_derived_count:{source}:{left}-{right}")
    return [(source, left - right)]


def normalize_registry_report(document: Mapping[str, object]) -> dict[str, object]:
    reconciled_candidates = [
        *_present(document, "reconciled_registry_count"),
        *_list_count(document, "rows"),
        *_list_count(document, "all_excluded_issuer_keys", unique=True),
    ]
    reconciled = resolve_count("reconciled_registry_count", reconciled_candidates)
    prior = resolve_count(
        "prior_real_issuer_exposure_registry_count",
        [
            *_present(document, "prior_registry_count"),
            *_present(document, "registry_count"),
            *_derived_difference(
                document,
                minuend_keys=("reconciled_registry_count",),
                subtrahend_keys=("appended_exposed_issuer_count",),
                source=("reconciled_registry_count-appended_exposed_issuer_count"),
            ),
        ],
    )
    return {"prior": prior, "reconciled": reconciled}


def normalize_exclusion_report(document: Mapping[str, object]) -> dict[str, object]:
    reconciled = resolve_count(
        "new_holdout_exclusion_count",
        [
            *_present(document, "new_holdout_exclusion_count"),
            *_present(document, "reconciled_count"),
            *_list_count(document, "excluded_issuer_keys", unique=True),
        ],
    )
    prior = resolve_count(
        "prior_exclusion_count",
        [
            *_present(document, "prior_count"),
            *_derived_difference(
                document,
                minuend_keys=("reconciled_count", "new_holdout_exclusion_count"),
                subtrahend_keys=("appended_count",),
                source="reconciled_exclusion_count-appended_count",
            ),
        ],
    )
    return {"prior": prior, "reconciled": reconciled}


def _row_source_failure_counts(
    document: Mapping[str, object],
) -> dict[str, list[tuple[str, object]]]:
    if "rows" not in document:
        return {}
    rows = document["rows"]
    if rows is None:
        return {
            name: [(f"rows.classification:{name}", None)]
            for name in (
                "source_sufficient_count",
                "source_insufficient_count",
                "pipeline_coverage_gap_count",
                "source_absence_count",
                "unknown_failure_count",
            )
        }
    if not isinstance(rows, list):
        raise ReportInputConflict("source_audit_rows_must_be_list")
    sufficient = 0
    insufficient = 0
    pipeline = 0
    absent = 0
    unknown = 0
    for index, raw_row in enumerate(rows):
        if not isinstance(raw_row, Mapping):
            raise ReportInputConflict(f"source_audit_row_must_be_object:{index}")
        if (
            raw_row.get("source_sufficiency_status") == ("SUFFICIENT_FOR_DIRECTIONAL_JUDGMENT")
            or raw_row.get("fundamental_source_sufficient") is True
        ):
            sufficient += 1
            continue
        insufficient += 1
        eligibility = raw_row.get("final_diagnostic_eligibility")
        if eligibility == "FUNDAMENTAL_SOURCE_INSUFFICIENT":
            absent += 1
        elif eligibility == "PIPELINE_COVERAGE_GAP":
            pipeline += 1
        else:
            unknown += 1
    return {
        "source_sufficient_count": [("rows.source_sufficiency", sufficient)],
        "source_insufficient_count": [("rows.source_sufficiency", insufficient)],
        "pipeline_coverage_gap_count": [("rows.failure_class", pipeline)],
        "source_absence_count": [("rows.failure_class", absent)],
        "unknown_failure_count": [("rows.failure_class", unknown)],
    }


def normalize_source_audit(document: Mapping[str, object], *, market: str) -> dict[str, object]:
    row_counts = _row_source_failure_counts(document)
    fields: dict[str, dict[str, object]] = {}
    aliases = {
        "target_count": ("target_count",),
        "attempted_count": ("attempted_count",),
        "source_sufficient_count": ("source_sufficient_count",),
        "source_insufficient_count": ("source_insufficient_count",),
        "pipeline_coverage_gap_count": ("pipeline_coverage_gap_count",),
        "source_absence_count": ("source_absence_count",),
        "unknown_failure_count": ("unknown_failure_count",),
    }
    for semantic, keys in aliases.items():
        candidates = [pair for key in keys for pair in _present(document, key)]
        if semantic == "attempted_count":
            candidates.extend(_list_count(document, "rows"))
        candidates.extend(row_counts.get(semantic, ()))
        fields[semantic] = resolve_count(f"{market}_{semantic}", candidates)

    attempted = fields["attempted_count"]["value"]
    sufficient = fields["source_sufficient_count"]["value"]
    insufficient = fields["source_insufficient_count"]["value"]
    if None not in (attempted, sufficient, insufficient) and attempted != (
        sufficient + insufficient
    ):
        raise ReportInputConflict(
            f"source_audit_total_mismatch:{market}:{attempted}!={sufficient}+{insufficient}"
        )
    category_values = [
        fields[name]["value"]
        for name in (
            "pipeline_coverage_gap_count",
            "source_absence_count",
            "unknown_failure_count",
        )
    ]
    if insufficient is not None and all(value is not None for value in category_values):
        category_total = sum(int(value) for value in category_values)
        if category_total != insufficient:
            raise ReportInputConflict(
                f"source_failure_category_mismatch:{market}:{category_total}!={insufficient}"
            )
    return {
        "market": market,
        "fields": fields,
        "source_target_status": document.get("source_target_status"),
    }


def normalize_completion_inputs(
    *,
    registry: Mapping[str, object],
    exclusion: Mapping[str, object],
    us_audit: Mapping[str, object],
    kr_audit: Mapping[str, object],
) -> dict[str, object]:
    registry_result = normalize_registry_report(registry)
    exclusion_result = normalize_exclusion_report(exclusion)
    markets = {
        "us": normalize_source_audit(us_audit, market="us"),
        "kr": normalize_source_audit(kr_audit, market="kr"),
    }
    fields: dict[str, Any] = {
        "prior_real_issuer_exposure_registry_count": registry_result["prior"]["value"],
        "new_holdout_exclusion_count": exclusion_result["reconciled"]["value"],
    }
    for market, normalized in markets.items():
        for name, field in normalized["fields"].items():
            fields[f"{market}_{name}"] = field["value"]
        fields[f"{market}_source_target_status"] = normalized["source_target_status"]
    return {
        "contract": REPORT_INPUT_NORMALIZATION_CONTRACT,
        "canonical_fields": fields,
        "provenance": {
            "registry": registry_result,
            "exclusion": exclusion_result,
            "markets": markets,
        },
        "status": "PASS",
    }
