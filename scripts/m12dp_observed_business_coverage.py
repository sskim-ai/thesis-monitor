"""Offline source sufficiency gate. Never grants authority or invokes a model."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime

from scripts.m12da_source_use_contract import SourceUse, canonical_sha256
from scripts.m12dk_current_source_authority import build_current_source_authority


CONTRACT = "m12dp-observed-business-source-coverage-v1"
READY = "DIRECTIONAL_BUSINESS_SOURCE_READY"
_ISSUER_OWNERS = {
    "us": ("SecFinancialSnapshotService._resolve_cik", "sec_edgar", "CIK:", "cik"),
    "kr": ("OpenDARTProvider._resolve_opendart_company", "opendart", "DART:", "corp_code"),
}


def _validate_issuer_binding(binding, *, expected_sha256, ticker, generation, market):
    """Use the separately frozen exact provider mapping, never an ADR ratio/price."""
    if canonical_sha256(binding) != expected_sha256:
        raise ValueError("coverage_issuer_binding_digest_mismatch")
    payload = {k: v for k, v in binding.items() if k != "binding_sha256"}
    if binding.get("binding_sha256") != canonical_sha256(payload):
        raise ValueError("coverage_issuer_binding_self_digest_mismatch")
    if (
        binding.get("contract") != "m12dp-existing-provider-issuer-binding-v1"
        or binding.get("ticker") != ticker
        or binding.get("market") != market
        or binding.get("source_generation_id") != generation
    ):
        raise ValueError("coverage_issuer_binding_identity_mismatch")
    if binding.get("status") != "PASS":
        return False
    owner, provider, prefix, field = _ISSUER_OWNERS[market]
    record = binding.get("source_record") or {}
    identifier = record.get(field)
    width = 10 if market == "us" else 8
    if (
        binding.get("owner") != owner
        or binding.get("provider") != provider
        or record.get("ticker") != ticker
        or not isinstance(identifier, str)
        or len(identifier) != width
        or not identifier.isdigit()
        or binding.get("issuer_id") != prefix + identifier
        or binding.get("security_denominator_inferred") is not False
    ):
        raise ValueError("coverage_issuer_mapping_owner_or_record_mismatch")
    try:
        observed = datetime.fromisoformat(binding["observed_at"])
        if observed.tzinfo is None:
            raise ValueError("unqualified_time")
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("coverage_issuer_mapping_timestamp_unverified") from exc
    return True


def evaluate_subject(
    *,
    ticker: str,
    source_generation_id: str,
    source_packet: Mapping[str, object],
    evidence_packet: Mapping[str, object],
    catalog: Mapping[str, object],
    source_metadata: Sequence[Mapping[str, object]],
    frozen_binding: Mapping[str, object],
    issuer_binding: Mapping[str, object],
    expected_issuer_binding_sha256: str,
) -> dict[str, object]:
    current = build_current_source_authority(
        ticker=ticker, source_generation_id=source_generation_id, source_packet=source_packet,
        evidence_packet=evidence_packet, catalog=catalog, source_metadata=source_metadata,
        frozen_binding=frozen_binding,
    )
    issuer_ok = _validate_issuer_binding(
        issuer_binding, expected_sha256=expected_issuer_binding_sha256, ticker=ticker,
        generation=source_generation_id, market=source_packet["market"],
    )
    metadata = {r["ref_id"]: r for r in source_metadata}
    records = {r["ref_id"]: r for r in current["authority"]["authority_records"]}
    stock = next(s for s in source_packet["stocks"] if s["ticker"] == ticker)
    sources, eligible = [], []
    for receipt in current["family_receipts"]:
        ref = receipt["ref_id"]
        record, raw = records[ref], metadata[ref]
        lineage = receipt.get("earnings_lineage") or {}
        direction = (
            receipt["source_family"] == "OBSERVED_EARNINGS_FACT"
            and record["authority_state"] == "RESOLVED"
            and SourceUse.OVERALL_DIRECTION.value in record["allowed_uses"]
            and lineage.get("status") == "PASS"
        )
        sources.append({
            "ref_id": ref, "source_ref": raw.get("source_ref"),
            "source_family": receipt["source_family"],
            "source_metadata_sha256": canonical_sha256(raw),
            "as_of": raw.get("as_of"), "field_lineage": deepcopy(lineage),
            "authority_overall_direction_eligible": direction,
            "overall_direction_eligible": direction and issuer_ok,
            "allowed_uses": deepcopy(record["allowed_uses"]),
            "denial_reasons": list(receipt["errors"]),
            "authority_denial_reasons": deepcopy(record["denial_reasons"]),
        })
        if direction and issuer_ok:
            eligible.append(ref)
    observed = [s for s in sources if s["source_family"] == "OBSERVED_EARNINGS_FACT"]
    if not issuer_ok:
        status = "ISSUER_SECURITY_BINDING_UNRESOLVED"
    elif eligible:
        status = READY
    elif observed and any(s["field_lineage"].get("fields") for s in observed):
        status = "SOURCE_QUALITY_UNUSABLE"
    elif observed or not source_metadata:
        status = "SOURCE_UNAVAILABLE"
    else:
        status = "ONLY_CONTEXT_OR_BASELINE_THESIS"
    return {
        "contract": CONTRACT, "ticker": ticker, "market": source_packet["market"],
        "source_generation_id": source_generation_id, "status": status,
        "ready_for_authority_aware_core_preflight": status == READY,
        "directional_source_refs": sorted(eligible),
        "issuer_binding": deepcopy(issuer_binding),
        "issuer_binding_sha256": expected_issuer_binding_sha256,
        "source_authority": current, "sources": sources,
        "available_earnings_fact_ids": [f.get("fact_id") for f in stock.get("fact_catalog", ())
                                       if f.get("fact_type") == "earnings"],
        "limitations": [
            "Observed financial periods remain report periods, not current trading-session facts.",
            "Current-source authority remains whole-row; denied fields are never silently dropped.",
            "Same-security issuer mapping does not infer per-share/ADR valuation or cross-listing transfer.",
            "No Core/A/B request or model call is authorized by an individual subject result.",
        ],
    }


def evaluate_cohort(subjects, *, expected_subjects: Sequence[str]) -> dict[str, object]:
    """Evaluate every active subject; no partial ready list escapes a failed cohort."""
    expected = list(expected_subjects)
    tickers = [s.get("ticker") for s in subjects]
    if not expected or len(set(expected)) != len(expected) or Counter(tickers) != Counter(expected):
        raise ValueError("coverage_active_population_mismatch")
    generations = {s.get("source_generation_id") for s in subjects}
    if len(generations) != 1 or not next(iter(generations)):
        raise ValueError("coverage_cohort_generation_mismatch")
    rows, identity_errors = [], []
    for subject in subjects:
        try:
            rows.append(evaluate_subject(**subject))
        except (ValueError, KeyError, TypeError) as exc:
            code = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            identity_errors.append({"ticker": subject["ticker"], "error": code})
            rows.append({"ticker": subject["ticker"], "status": "SOURCE_QUALITY_UNUSABLE",
                         "directional_source_refs": [], "binding_error": code})
    ready = sum(r["status"] == READY for r in rows)
    complete = ready == len(expected) and not identity_errors
    return {
        "contract": CONTRACT, "subjects": rows, "active_count": len(expected),
        "ready_count": ready, "status_counts": dict(Counter(r["status"] for r in rows)),
        "binding_errors": identity_errors,
        "allow_core_preflight": complete,
        "allow_model_calls": False,
        "next_gate": "AUTHORITY_AWARE_CORE_SCHEMA_PREFLIGHT" if complete else None,
        "terminal": (
            "SOURCE_COVERAGE_PASS_PENDING_CORE_PREFLIGHT" if complete else
            "M12DP_CURRENT_SOURCE_COLLECTION_OR_BINDING_FAILED" if identity_errors else
            "M12DP_OBSERVED_BUSINESS_SOURCE_COVERAGE_INCOMPLETE"
        ),
        "production_ready": False, "comparison": "NOT_PERFORMED",
    }
