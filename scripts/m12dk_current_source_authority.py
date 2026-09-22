"""Explicit, frozen-input source permissions. No grants from claims or display text."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path

from app.schemas.thesis import MacroExposureInput
from app.services.cross_market_decision_engine_service import _compact
from app.services.financial_quality_service import (
    CRITICAL_REASON_CODES,
    DECISION_VERSION,
    PROSE_USABLE_STATES,
)
from scripts.m12da_source_use_contract import (
    SourceUse,
    build_trusted_source_authority_manifest,
    canonical_sha256,
)


CONTRACT = "m12dk-current-source-authority-v1"
POLICY_SHA256 = "c0491528da620352f80044a0d351ecc3b414e0d701c4f6d4ec916656117b3103"
_ROW_FIELDS = {
    "as_of",
    "category",
    "label",
    "logical_condition",
    "metric_refs",
    "numeric_prose_eligible",
    "ref_id",
    "source_ref",
    "statement",
    "unit",
    "value",
}
_FIELD_OWNERS = {
    "revenue": ("latest_revenue", "fields.revenue.value"),
    "operating_income": ("latest_operating_income", "fields.operating_income.value"),
    "operating_margin_pct": ("latest_operating_margin", "fields.operating_margin_pct"),
    "revenue_qoq_pct": ("latest_revenue_qoq", "fields.revenue_qoq_pct"),
    "revenue_yoy_pct": ("latest_revenue_yoy", "fields.revenue_yoy_pct"),
    "operating_income_qoq_pct": ("latest_operating_income_qoq", "fields.operating_income_qoq_pct"),
    "operating_income_yoy_pct": ("latest_operating_income_yoy", "fields.operating_income_yoy_pct"),
}
_PERIOD_FIELDS = {
    "period",
    "period_type",
    "period_label",
    "field_period_labels",
    "field_statement_basis",
    "financial_period_required",
    "preliminary",
}
_PROVIDER_SOURCE_TYPES = {
    "sec_companyfacts": {"full_statement"},
    "sec_foreign_filing": {"full_statement", "preliminary_earnings"},
    "opendart": {"formal", "full_statement", "preliminary_earnings"},
}
_NEW_OWNER_FAMILIES = {
    "CONFIGURED_CORE_THESIS_DEFINITION",
    "CONFIGURED_MACRO_EXPOSURE_DEFINITION",
    "THESIS_REEVALUATION_CONDITION",
    "OBSERVED_EARNINGS_FACT",
}


def policy() -> dict[str, object]:
    raw = Path(__file__).with_name("m12dk_current_source_authority_policy.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != POLICY_SHA256:
        raise ValueError("current_authority_policy_digest_mismatch")
    result = json.loads(raw)
    if result.get("contract") != CONTRACT:
        raise ValueError("current_authority_policy_version_unknown")
    return result


def _day(value: object) -> bool:
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _match(path: str, pattern: str) -> bool:
    if pattern.endswith(":*"):
        return path.startswith(pattern[:-1]) and len(path) > len(pattern[:-1])
    return path == pattern


def family_rule(row: Mapping[str, object]) -> dict[str, object] | None:
    matches = [
        r
        for r in policy()["family_rules"]
        if any(_match(str(row.get("source_ref") or ""), p) for p in r["patterns"])
    ]
    return matches[0] if len(matches) == 1 else None


def freeze_current_source_binding(
    *,
    source_generation_id: str,
    source_packet: Mapping[str, object],
    evidence_packet: Mapping[str, object],
) -> dict[str, object]:
    ticker = str(evidence_packet.get("ticker") or "")
    stocks = [s for s in source_packet.get("stocks", ()) if s.get("ticker") == ticker]
    if not ticker or len(stocks) != 1 or not source_generation_id:
        raise ValueError("current_authority_source_subject_missing_or_duplicate")
    if source_packet.get("market") not in {"us", "kr"} or not source_packet.get("packet_id"):
        raise ValueError("current_authority_packet_identity_missing")
    result = {
        "contract": CONTRACT,
        "policy_sha256": POLICY_SHA256,
        "source_generation_id": source_generation_id,
        "ticker": ticker,
        "source_packet_id": source_packet["packet_id"],
        "source_packet_sha256": canonical_sha256(source_packet),
        "stock_sha256": canonical_sha256(stocks[0]),
        "evidence_packet_sha256": canonical_sha256(evidence_packet),
    }
    result["binding_sha256"] = canonical_sha256(result)
    return result


def _definition_errors(row, stock, source_packet):
    path = row["source_ref"]
    key = path.removeprefix("stock.thesis.")
    source = stock.get("thesis", {}).get(key)
    expected_category = {
        "core_thesis": "thesis",
        "macro_exposures": "macro",
        "strengthen_signals": "thesis",
        "weaken_signals": "risks",
        "invalidation_signals": "risks",
    }[key]
    errors = []
    if row.get("category") != expected_category or not str(row.get("ref_id", "")).startswith(
        "decision-evidence:"
    ):
        errors.append("definition_category_or_ref_mismatch")
    if row.get("as_of") != source_packet.get("assessment_date") or not _day(row.get("as_of")):
        errors.append("definition_period_mismatch")
    values = source if isinstance(source, list) else [source]
    candidates = [v for v in values if v is not None and _compact(v) == row.get("statement")]
    if not candidates:
        return errors + ["definition_not_in_frozen_same_subject_source"]
    if key == "macro_exposures":
        try:
            for value in candidates:
                if not isinstance(value, dict) or not set(value).issubset(
                    MacroExposureInput.model_fields
                ):
                    raise ValueError("unsupported_macro_shape")
                MacroExposureInput.model_validate(value, strict=True)
        except ValueError:
            errors.append("macro_definition_shape_unknown")
    elif not all(isinstance(v, str) and v.strip() for v in candidates):
        errors.append("definition_shape_unknown")
    if key in {"core_thesis", "macro_exposures"}:
        if row.get("logical_condition") is not None:
            errors.append("definition_unexpected_condition")
    else:
        condition = row.get("logical_condition") or {}
        if (
            condition.get("contract") != "source-owned-logical-condition-v1"
            or condition.get("subject") != stock["ticker"]
            or condition.get("generation_id") != source_packet["packet_id"]
        ):
            errors.append("condition_ownership_unknown")
    return errors


def earnings_lineage_receipt(row, stock, source_packet):
    """Authorize a whole immutable earnings row only when every exposed field is safe."""
    fact_id = str(row.get("source_ref", "")).removeprefix("stock.fact_catalog.")
    matches = [f for f in stock.get("fact_catalog", ()) if f.get("fact_id") == fact_id]
    receipt = {
        "ref_id": row["ref_id"],
        "ticker": stock["ticker"],
        "fact_id": fact_id,
        "fields": [],
        "errors": [],
    }
    errors = receipt["errors"]
    if len(matches) != 1:
        errors.append("earnings_fact_missing_or_duplicate")
        receipt["status"] = "FAIL"
        return receipt
    fact = matches[0]
    fields = fact.get("fields") or {}
    quality = fact.get("financial_quality") or {}
    snapshot = quality.get("source_snapshot") or {}
    period = fields.get("period")
    receipt["frozen_fact_sha256"] = canonical_sha256(fact)
    receipt["source_snapshot"] = snapshot
    if (
        row.get("ref_id") != f"canonical:{fact_id}"
        or row.get("category") != "earnings"
        or fact.get("fact_type") != "earnings"
    ):
        errors.append("earnings_typed_identity_mismatch")
    if row.get("statement") != _compact(fields):
        errors.append("earnings_metadata_frozen_fact_mismatch")
    if (
        not _day(period)
        or any(
            v != period for v in (row.get("as_of"), fact.get("as_of_date"), snapshot.get("period"))
        )
        or fact_id != f"earnings:{period}"
    ):
        errors.append("earnings_period_mismatch")
    if (
        fields.get("financial_period_required") is not True
        or fields.get("period_type") != snapshot.get("period_type")
        or fields.get("period_type")
        not in {"Q1", "Q2", "Q3", "Q4", "H1", "H2", "FY", "9M", "YTD", "TTM"}
    ):
        errors.append("earnings_period_semantics_unknown")
    if (
        not _day(snapshot.get("filing_date"))
        or not _day(source_packet.get("assessment_date"))
        or str(snapshot.get("filing_date")) > str(source_packet.get("assessment_date"))
        or str(snapshot.get("filing_date")) < str(period)
    ):
        errors.append("earnings_availability_unverified")
    if (
        quality.get("decision_version") != DECISION_VERSION
        or fact.get("interpretation_eligible") is not True
        or fact.get("prose_eligible") is not True
    ):
        errors.append("earnings_envelope_quality_unusable")
    if set(fields) - _PERIOD_FIELDS - set(_FIELD_OWNERS):
        errors.append("earnings_field_shape_unknown")
    present = [name for name in _FIELD_OWNERS if name in fields and fields[name] is not None]
    if not present:
        errors.append("earnings_no_actual_fields")
    for name in present:
        logical, path = _FIELD_OWNERS[name]
        q = (fact.get("field_quality") or {}).get(path) or {}
        field_errors = []
        value = fields[name]
        if isinstance(value, Mapping):
            if set(value) != {"value", "currency"} or not value.get("currency"):
                field_errors.append("field_currency_or_shape_unknown")
            value = value.get("value")
        if (
            isinstance(value, bool)
            or not isinstance(value, (float, int))
            or not math.isfinite(value)
        ):
            field_errors.append("field_value_not_finite")
        if not q or q != (quality.get("fields") or {}).get(logical):
            field_errors.append("field_quality_owner_mismatch")
        if (
            q.get("decision_version") != DECISION_VERSION
            or q.get("state") not in PROSE_USABLE_STATES
            or q.get("prose_eligible") is not True
            or q.get("lineage_verification_status") != "verified"
            or q.get("denial_reason")
        ):
            field_errors.append("field_denied_critical_or_unverified")
        if set(q.get("quality_reason_codes") or ()) & CRITICAL_REASON_CODES:
            field_errors.append("field_critical_taint")
        provider = q.get("provider")
        if (
            q.get("source_type") not in _PROVIDER_SOURCE_TYPES.get(provider, set())
            or provider != snapshot.get("provider")
            or snapshot.get("source_type") not in _PROVIDER_SOURCE_TYPES.get(provider, set())
        ):
            field_errors.append("field_provider_or_source_type_unknown")
        if (
            q.get("source_period") != period
            or period not in (q.get("dependency_periods") or ())
            or not all(_day(p) and p <= period for p in q.get("dependency_periods") or ())
        ):
            field_errors.append("field_period_lineage_mismatch")
        if q.get("dependency_fields") != [f"earnings.{logical}"]:
            field_errors.append("field_dependency_owner_mismatch")
        if q.get("financial_lineage_contract") not in {None, "financial-lineage-v2"} or q.get(
            "statement_basis_contract"
        ) not in {None, "financial-statement-basis-v1"}:
            field_errors.append("field_lineage_contract_unknown")
        if provider == "opendart":
            if (
                q.get("financial_lineage_contract") != "financial-lineage-v2"
                or q.get("statement_basis_contract") != "financial-statement-basis-v1"
                or q.get("statement_basis_state")
                not in {"verified_consolidated", "verified_separate"}
            ):
                field_errors.append("field_statement_contract_unverified")
            if (
                not q.get("source_row_identity")
                or not q.get("source_filing_identifier")
                or not _day(q.get("amount_period_start"))
                or q.get("amount_period_end") != period
                or str(q.get("amount_period_start")) > str(period)
            ):
                field_errors.append("field_occurrence_period_unverified")
            if q.get("amount_period_type") not in {"single_quarter", "cumulative", "annual"}:
                field_errors.append("field_flow_duration_unknown")
        receipt["fields"].append(
            {
                "field_path": path,
                "quality": q,
                "status": "FAIL" if field_errors else "PASS",
                "errors": field_errors,
            }
        )
        errors.extend(f"{path}:{e}" for e in field_errors)
    receipt["status"] = "FAIL" if errors else "PASS"
    receipt["caution_usable"] = any(
        f["quality"].get("state") == "caution_usable" for f in receipt["fields"]
    )
    receipt["supported_field_paths"] = [
        f["field_path"] for f in receipt["fields"] if f["status"] == "PASS"
    ]
    receipt["permission_granularity"] = "WHOLE_IMMUTABLE_ROW_ALL_EXPOSED_FIELDS_MUST_PASS"
    return receipt


def build_current_source_authority(
    *,
    ticker: str,
    source_generation_id: str,
    source_packet: Mapping[str, object],
    evidence_packet: Mapping[str, object],
    catalog: Mapping[str, object],
    source_metadata: Sequence[Mapping[str, object]],
    frozen_binding: Mapping[str, object],
) -> dict[str, object]:
    expected = freeze_current_source_binding(
        source_generation_id=source_generation_id,
        source_packet=source_packet,
        evidence_packet=evidence_packet,
    )
    if (
        expected != frozen_binding
        or ticker != expected["ticker"]
        or ticker != catalog.get("ticker")
    ):
        raise ValueError("current_authority_frozen_input_identity_mismatch")
    stock = next(s for s in source_packet["stocks"] if s["ticker"] == ticker)
    all_refs = {str(row["ref_id"]): row for row in evidence_packet["evidence"]}
    if len(all_refs) != len(evidence_packet["evidence"]) or any(
        all_refs.get(str(r.get("ref_id"))) != r for r in source_metadata
    ):
        raise ValueError("current_authority_metadata_not_in_frozen_packet")
    manifest = build_trusted_source_authority_manifest(
        ticker=ticker,
        source_generation_id=source_generation_id,
        catalog=catalog,
        source_metadata=source_metadata,
    )
    if manifest["status"] != "PASS":
        raise ValueError("current_authority_canonical_manifest_invalid")
    rows = {r["ref_id"]: r for r in source_metadata}
    receipts, excluded = [], []
    for record in manifest["authority_records"]:
        row = rows[record["ref_id"]]
        rule = family_rule(row)
        receipt = {
            "ref_id": row["ref_id"],
            "ticker": ticker,
            "source_metadata_sha256": canonical_sha256(row),
            "source_family": rule["id"] if rule else "UNKNOWN",
            "errors": [],
        }
        if rule and rule.get("pass_a_model_visible") is False:
            excluded.append(row["ref_id"])
        if rule and rule["id"] in _NEW_OWNER_FAMILIES:
            if set(row) - _ROW_FIELDS:
                receipt["errors"].append("source_metadata_shape_or_version_unknown")
            if rule["id"] == "OBSERVED_EARNINGS_FACT":
                lineage = earnings_lineage_receipt(row, stock, source_packet)
                receipt["earnings_lineage"] = lineage
                receipt["errors"].extend(lineage["errors"])
            else:
                receipt["errors"].extend(_definition_errors(row, stock, source_packet))
            # Never override an existing restrictive owner, even for a spoofed source path.
            if record["source_family"] != "unclassified":
                receipt["errors"].append("existing_restrictive_family_cannot_be_rebound")
            if not receipt["errors"]:
                allowed = {SourceUse.CONTEXT.value, *rule["allow"]} - set(rule["prohibit"])
                record.update(
                    {
                        "authority_state": "RESOLVED",
                        "authority_basis": CONTRACT + ":" + rule["id"],
                        "source_type": rule["id"],
                        "source_family": rule["id"],
                        "source_scope": (
                            "observed_fields_with_verified_quality"
                            if rule["id"] == "OBSERVED_EARNINGS_FACT"
                            else "configured_definition_not_occurrence_evidence"
                        ),
                        "allowed_uses": sorted(allowed),
                        "prohibited_uses": sorted({u.value for u in SourceUse} - allowed),
                        "denial_reasons": ["not_authorized_by:" + CONTRACT],
                        "required_metadata": [
                            "exact_frozen_same_subject_source",
                            "policy_sha256",
                            "family_category_shape",
                            "verified_field_lineage_for_earnings",
                        ],
                        "compatible_source_versions": [CONTRACT],
                    }
                )
            else:
                record["denial_reasons"] = sorted(set(record["denial_reasons"] + receipt["errors"]))
        receipt["allowed_uses"] = record["allowed_uses"]
        receipt["authority_state"] = record["authority_state"]
        receipt["authority_basis"] = record["authority_basis"]
        receipts.append(receipt)
    manifest.update(
        {
            "current_source_owner_contract": CONTRACT,
            "current_source_policy_sha256": POLICY_SHA256,
            "current_source_binding": expected,
            "current_source_family_receipts_sha256": canonical_sha256(receipts),
        }
    )
    manifest.pop("authority_manifest_sha256")
    manifest["authority_manifest_sha256"] = canonical_sha256(manifest)
    return {
        "authority": manifest,
        "family_receipts": receipts,
        "pass_a_visibility_exclusions": sorted(excluded),
        "frozen_binding": expected,
    }
