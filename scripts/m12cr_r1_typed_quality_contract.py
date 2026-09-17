from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from enum import StrEnum
from scripts.m12cn_policy_contract import DataQualityEffect, DataQualityReasonClass
from scripts.m12cp_valuation_policy_contract import depositary_basis_audit


CONTRACT_VERSION = "m12cr-r1-typed-quality-security-basis-v1"


class BusinessEvidenceQualityState(StrEnum):
    NONE = "NONE"
    CONFIDENCE_ONLY = "CONFIDENCE_ONLY"


class SecurityValuationBasisState(StrEnum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"


FINANCIAL_QUALITY_STATES = frozenset({"verified_usable", "caution_usable", "denied", "unknown"})
SECURITY_BASIS_ONLY_REASON_CODES = frozenset(
    {
        "missing_adr_ratio",
        "per_share_basis_insufficient",
        "security_identity_unverified",
        "security_share_basis_unresolved",
    }
)
FRESHNESS_REASON_CODES = frozenset(
    {
        "foreign_latest_filing_not_financial",
        "official_financial_period_unresolved",
        "reporting_cadence_exceeded",
    }
)
PROVIDER_REASON_CODES = frozenset({"provider_not_supported"})
SAFE_SECURITY_DECISION = "provider_native_multiple_may_be_eligible"
UNSAFE_SECURITY_DECISIONS = frozenset(
    {
        "requires_verified_current_security_denominator",
        "security_share_basis_dependent_valuation_denied",
        "unverified_depositary_evidence_requires_authoritative_resolution",
    }
)

_SERIALIZED_SCALAR = re.compile(
    r'"(?P<key>[^"\\]+)"\s*:\s*'
    r'(?P<value>"(?:\\.|[^"\\])*"|true|false|null|-?\d+(?:\.\d+)?)'
)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _rows(value: object) -> list[Mapping[str, object]]:
    return [row for row in value or () if isinstance(row, Mapping)]


def _statement_mapping(row: Mapping[str, object]) -> dict[str, object] | None:
    statement = row.get("statement")
    if isinstance(statement, Mapping):
        return dict(statement)
    if not isinstance(statement, str) or not statement.strip():
        return None
    try:
        parsed = json.loads(statement)
    except json.JSONDecodeError:
        return None
    return dict(parsed) if isinstance(parsed, Mapping) else None


def _serialized_scalar(statement: object, key: str) -> object:
    if isinstance(statement, Mapping):
        return statement.get(key)
    if not isinstance(statement, str):
        return None
    parsed = _statement_mapping({"statement": statement})
    if parsed is not None:
        return parsed.get(key)
    for match in _SERIALIZED_SCALAR.finditer(statement):
        if match.group("key") == key:
            return json.loads(match.group("value"))
    return None


def _evidence_rows(container: Mapping[str, object]) -> list[Mapping[str, object]]:
    return _rows(container.get("eligible_non_price_evidence") or container.get("evidence"))


def _evidence_by_ref(
    container: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    return {str(row.get("ref_id")): row for row in _evidence_rows(container) if row.get("ref_id")}


def _financial_quality_row(
    context: Mapping[str, object],
) -> Mapping[str, object] | None:
    rows = [
        row
        for row in _evidence_rows(context)
        if str(row.get("ref_id") or "").startswith("canonical:financial_quality:")
        or str(row.get("label") or "") == "financial_quality"
    ]
    return rows[0] if len(rows) == 1 else None


def project_business_evidence_quality(
    context: Mapping[str, object],
) -> dict[str, object]:
    preprojected = context.get("business_evidence_quality_state")
    if isinstance(preprojected, Mapping) and preprojected.get("contract") == CONTRACT_VERSION:
        return deepcopy(dict(preprojected))
    row = _financial_quality_row(context)
    expected = context.get("business_quality_expected") is not False
    if row is None:
        if not expected:
            return {
                "contract": CONTRACT_VERSION,
                "state": BusinessEvidenceQualityState.NONE.value,
                "effect": DataQualityEffect.NONE.value,
                "reason_class": DataQualityReasonClass.NOT_APPLICABLE.value,
                "reason": None,
                "reason_codes": [],
                "source_refs": [],
                "record_ref": None,
                "source_presence": "LEGITIMATELY_NOT_APPLICABLE",
                "directional_use_allowed": False,
                "owner": "DETERMINISTIC_SOURCE_PROJECTION",
                "status": "MAPPED",
            }
        return {
            "contract": CONTRACT_VERSION,
            "state": BusinessEvidenceQualityState.CONFIDENCE_ONLY.value,
            "effect": DataQualityEffect.CONFIDENCE_ONLY.value,
            "reason_class": DataQualityReasonClass.PROVIDER_LIMITATION.value,
            "reason": "필수 typed business-quality record가 없어 확신도만 제한합니다.",
            "reason_codes": ["expected_business_quality_record_absent"],
            "source_refs": [],
            "record_ref": None,
            "source_presence": "EXPECTED_RECORD_ABSENT",
            "directional_use_allowed": False,
            "owner": "DETERMINISTIC_SOURCE_PROJECTION",
            "status": "MAPPED_FAIL_CLOSED",
        }

    record = _statement_mapping(row)
    ref_id = str(row.get("ref_id") or "")
    if record is None:
        return {
            "contract": CONTRACT_VERSION,
            "state": BusinessEvidenceQualityState.CONFIDENCE_ONLY.value,
            "effect": DataQualityEffect.CONFIDENCE_ONLY.value,
            "reason_class": DataQualityReasonClass.PROVIDER_LIMITATION.value,
            "reason": "typed business-quality record를 해석할 수 없어 확신도만 제한합니다.",
            "reason_codes": ["business_quality_record_unparseable"],
            "source_refs": [ref_id] if ref_id else [],
            "record_ref": ref_id or None,
            "source_presence": "UNPARSEABLE",
            "directional_use_allowed": False,
            "owner": "DETERMINISTIC_SOURCE_PROJECTION",
            "status": "MAPPED_FAIL_CLOSED",
        }

    state = str(record.get("state") or "unknown")
    raw_reasons = sorted(
        {
            str(reason)
            for reason in record.get("reason_codes") or record.get("quality_reason_codes") or ()
            if str(reason)
        }
    )
    business_reasons = [
        reason for reason in raw_reasons if reason not in SECURITY_BASIS_ONLY_REASON_CODES
    ]
    clean = state == "verified_usable" and not business_reasons
    if clean:
        quality_state = BusinessEvidenceQualityState.NONE
        effect = DataQualityEffect.NONE
        reason_class = DataQualityReasonClass.NOT_APPLICABLE
        reason = None
        source_refs: list[str] = []
    else:
        quality_state = BusinessEvidenceQualityState.CONFIDENCE_ONLY
        effect = DataQualityEffect.CONFIDENCE_ONLY
        source_refs = [ref_id] if ref_id else []
        if set(business_reasons) & FRESHNESS_REASON_CODES:
            reason_class = DataQualityReasonClass.STALE_OR_UNSUPPORTED
        else:
            reason_class = DataQualityReasonClass.PROVIDER_LIMITATION
        reason = "typed business evidence 상태는 방향이 아니라 확신도에만 반영합니다."
    status = "MAPPED" if state in FINANCIAL_QUALITY_STATES else "UNMAPPED_STATE"
    return {
        "contract": CONTRACT_VERSION,
        "state": quality_state.value,
        "effect": effect.value,
        "reason_class": reason_class.value,
        "reason": reason,
        "reason_codes": business_reasons,
        "excluded_security_basis_reason_codes": sorted(
            set(raw_reasons) & SECURITY_BASIS_ONLY_REASON_CODES
        ),
        "financial_quality_state": state,
        "source_type": record.get("source_type"),
        "source_period": record.get("source_period"),
        "source_refs": source_refs,
        "record_ref": ref_id or None,
        "source_presence": "PRESENT",
        "directional_use_allowed": False,
        "owner": "DETERMINISTIC_SOURCE_PROJECTION",
        "status": status,
    }


def build_r1_pass_a_context(
    base_context: Mapping[str, object],
    *,
    source_packet: Mapping[str, object] | None = None,
) -> dict[str, object]:
    projected = project_business_evidence_quality(source_packet or base_context)
    pass_a_projection = {
        key: deepcopy(projected[key])
        for key in (
            "contract",
            "state",
            "effect",
            "reason_class",
            "reason",
            "reason_codes",
            "source_refs",
            "source_presence",
            "directional_use_allowed",
            "owner",
            "status",
        )
    }
    result = deepcopy(dict(base_context))
    quality = dict(_mapping(result.get("data_quality_catalog")))
    directional_refs = set(quality.get("material_disclosure_failure_refs") or ()) | set(
        quality.get("positive_quality_refs") or ()
    )
    hidden_refs = {
        ref
        for ref in _evidence_by_ref(base_context)
        if ref.startswith("canonical:financial_quality:")
        or ref
        in {
            "canonical:security_identity:current",
            "canonical:security_basis:current",
        }
    }
    result["eligible_non_price_evidence"] = [
        deepcopy(dict(row))
        for row in _evidence_rows(base_context)
        if str(row.get("ref_id") or "") not in hidden_refs
        or str(row.get("ref_id") or "") in directional_refs
    ]
    visible_claims = [
        deepcopy(dict(row))
        for row in _rows(base_context.get("accepted_fundamental_claims"))
        if not (set(row.get("parent_source_refs") or ()) & hidden_refs - directional_refs)
    ]
    visible_claim_refs = {
        str(row.get("claim_ref")) for row in visible_claims if row.get("claim_ref")
    }
    result["accepted_fundamental_claims"] = visible_claims
    result["eligible_claim_refs"] = [
        ref
        for ref in base_context.get("eligible_claim_refs") or ()
        if str(ref) in visible_claim_refs
    ]
    result["premium_eligible_claim_refs"] = [
        ref
        for ref in base_context.get("premium_eligible_claim_refs") or ()
        if str(ref) in visible_claim_refs
    ]
    quality["evidence_refs"] = list(projected.get("source_refs") or ())
    result["data_quality_catalog"] = quality
    result["business_evidence_quality_state"] = pass_a_projection
    return result


def project_security_valuation_basis(
    packet: Mapping[str, object],
    *,
    trading_currency: str | None = None,
    expected_depositary_status: str | None = None,
) -> dict[str, object]:
    evidence = _evidence_by_ref(packet)
    identity_row = evidence.get("canonical:security_identity:current")
    basis_row = evidence.get("canonical:security_basis:current")
    identity_statement = identity_row.get("statement") if identity_row else None
    basis_statement = basis_row.get("statement") if basis_row else None
    identity_decision = _serialized_scalar(identity_statement, "eligibility_decision")
    identity_state = _serialized_scalar(identity_statement, "identity_state")
    identity_verification = _serialized_scalar(identity_statement, "verification_status")
    selected_security_type = _serialized_scalar(identity_statement, "selected_security_type")
    basis_decision = _serialized_scalar(basis_statement, "eligibility_decision")
    basis_identity_state = _serialized_scalar(basis_statement, "security_identity_state")
    price_currency = _serialized_scalar(basis_statement, "price_currency")
    book_currency = _serialized_scalar(basis_statement, "book_value_currency")
    eps_currency = _serialized_scalar(basis_statement, "earnings_per_share_currency")
    eps_basis = _serialized_scalar(basis_statement, "earnings_per_share_security_basis")
    depositary = depositary_basis_audit(
        {"ticker": packet.get("ticker"), "evidence": _evidence_rows(packet)}
    )
    reasons: list[str] = []
    if depositary.get("affected") and depositary.get("status") != "RESOLVED":
        reasons.append("depositary_security_basis_unresolved")
        reasons.extend(
            f"depositary_missing:{field}" for field in depositary.get("missing_fields") or ()
        )
    if expected_depositary_status and expected_depositary_status != depositary.get("status"):
        reasons.append("m12cp_depositary_status_mismatch")
    if identity_decision is None:
        reasons.append("security_identity_decision_missing")
    elif identity_decision != SAFE_SECURITY_DECISION:
        reasons.append(f"security_identity:{identity_decision}")
    if basis_decision is None:
        reasons.append("security_basis_decision_missing")
    elif basis_decision != SAFE_SECURITY_DECISION:
        reasons.append(f"security_basis:{basis_decision}")
    effective_trading_currency = trading_currency or (
        str(price_currency) if price_currency else None
    )
    reporting_currencies = {str(value) for value in (book_currency, eps_currency) if value}
    if (
        effective_trading_currency
        and reporting_currencies
        and any(value != effective_trading_currency for value in reporting_currencies)
    ):
        reasons.append("reporting_trading_currency_mismatch")
    state = (
        SecurityValuationBasisState.UNRESOLVED if reasons else SecurityValuationBasisState.RESOLVED
    )
    source_refs = [
        ref
        for ref in (
            "canonical:security_identity:current",
            "canonical:security_basis:current",
        )
        if ref in evidence
    ]
    return {
        "contract": CONTRACT_VERSION,
        "state": state.value,
        "unresolved_reasons": sorted(set(reasons)),
        "source_refs": source_refs,
        "identity_state": identity_state or basis_identity_state,
        "identity_verification_status": identity_verification,
        "selected_security_type": selected_security_type,
        "identity_eligibility_decision": identity_decision,
        "basis_eligibility_decision": basis_decision,
        "earnings_per_share_security_basis": eps_basis,
        "reporting_currencies": sorted(reporting_currencies),
        "trading_currency": effective_trading_currency,
        "depositary_basis_status": depositary.get("status"),
        "depositary_affected": bool(depositary.get("affected")),
        "depositary_missing_fields": list(depositary.get("missing_fields") or ()),
        "unsafe_per_share_projection_blocked": state is SecurityValuationBasisState.UNRESOLVED,
        "directional_use_allowed": False,
        "overall_use_allowed": False,
        "holder_use_allowed": False,
        "new_buyer_price_resolution_use_allowed": True,
        "owner": "DETERMINISTIC_SOURCE_PROJECTION",
        "status": "MAPPED",
    }


def gate_policy_option_for_security_basis(
    policy_option: Mapping[str, object],
    security_basis: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    option = deepcopy(dict(policy_option))
    unresolved = security_basis.get("state") == SecurityValuationBasisState.UNRESOLVED.value
    originally_resolved = option.get("status") == "RESOLVED"
    if unresolved and originally_resolved:
        option.update(
            {
                "status": "UNRESOLVED",
                "option_id": None,
                "low": None,
                "high": None,
                "currency": None,
                "method_family": None,
                "selection_basis": None,
                "evidence_refs": [],
                "source_candidate_ids": [],
                "methods_averaged": False,
                "unresolved_reasons": sorted(
                    {
                        *(option.get("unresolved_reasons") or ()),
                        "SECURITY_VALUATION_BASIS_UNRESOLVED",
                    }
                ),
            }
        )
    return option, {
        "contract": "m12cr-r1-security-basis-policy-option-gate-v1",
        "ticker": policy_option.get("ticker"),
        "basis_state": security_basis.get("state"),
        "input_status": policy_option.get("status"),
        "output_status": option.get("status"),
        "unsafe_projection_blocked": bool(unresolved and originally_resolved),
        "status": "PASS" if not unresolved or option.get("status") != "RESOLVED" else "FAIL",
    }


def validate_security_valuation_basis_gate(
    *,
    policy_options: Mapping[str, Mapping[str, object]],
    security_basis_by_ticker: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    violations = sorted(
        ticker
        for ticker, basis in security_basis_by_ticker.items()
        if basis.get("state") == SecurityValuationBasisState.UNRESOLVED.value
        and policy_options.get(ticker, {}).get("status") == "RESOLVED"
    )
    return {
        "contract": "m12cr-r1-security-valuation-basis-gate-v1",
        "unresolved_subjects": sorted(
            ticker
            for ticker, basis in security_basis_by_ticker.items()
            if basis.get("state") == SecurityValuationBasisState.UNRESOLVED.value
        ),
        "resolved_option_violations": violations,
        "unsafe_security_basis_projection_count": len(violations),
        "status": "PASS" if not violations else "FAIL",
    }


def _value(row: object, field: str) -> object:
    if isinstance(row, Mapping):
        return row.get(field)
    return getattr(row, field, None)


def _expanded_source_refs(
    refs: Sequence[str],
    catalog: Mapping[str, object],
) -> set[str]:
    claims = {
        str(row.get("claim_ref")): {str(ref) for ref in row.get("parent_source_refs") or ()}
        for row in _rows(catalog.get("atomic_claims"))
        if row.get("claim_ref")
    }
    expanded: set[str] = set()
    for ref in refs:
        expanded.update(claims.get(str(ref), {str(ref)}))
    return expanded


def validate_quality_basis_decision_ownership(
    decisions: Sequence[object],
    *,
    catalogs: Mapping[str, Mapping[str, object]],
    typed_states: Mapping[str, Mapping[str, Mapping[str, object]]],
) -> dict[str, object]:
    errors: list[str] = []
    rows: list[dict[str, object]] = []
    for decision in decisions:
        ticker = str(_value(decision, "ticker") or "")
        catalog = catalogs[ticker]
        state = typed_states[ticker]
        business = _mapping(state.get("business_evidence_quality"))
        security = _mapping(state.get("security_valuation_basis"))
        directional_refs = set(state.get("directional_disclosure_refs") or ())
        business_refs = set(business.get("source_refs") or ())
        security_refs = set(security.get("source_refs") or ())
        nondirectional_quality_refs = business_refs | security_refs

        overall = str(_value(decision, "overall_direction") or "")
        overall_refs = _expanded_source_refs(
            list(_value(decision, "decisive_supporting_claim_refs") or ()), catalog
        )
        holder = str(_value(decision, "holder") or "")
        holder_refs = _expanded_source_refs(
            list(_value(decision, "holder_reason_evidence_refs") or ()), catalog
        )
        row_errors: list[str] = []
        if (
            overall in {"HOLD", "SELL"}
            and overall_refs
            and overall_refs <= nondirectional_quality_refs
            and not overall_refs.intersection(directional_refs)
        ):
            if overall_refs <= security_refs:
                row_errors.append("security_basis_sole_overall_downgrade")
            else:
                row_errors.append("business_confidence_sole_overall_downgrade")
        if (
            holder in {"REVIEW", "REDUCE"}
            and holder_refs
            and holder_refs <= nondirectional_quality_refs
            and not holder_refs.intersection(directional_refs)
        ):
            if holder_refs <= security_refs:
                row_errors.append("security_basis_sole_holder_downgrade")
            else:
                row_errors.append("business_confidence_sole_holder_downgrade")
        errors.extend(f"{ticker}:{error}" for error in row_errors)
        rows.append(
            {
                "ticker": ticker,
                "overall": overall,
                "holder": holder,
                "expanded_overall_source_refs": sorted(overall_refs),
                "expanded_holder_source_refs": sorted(holder_refs),
                "errors": row_errors,
            }
        )
    return {
        "contract": "m12cr-r1-pass-b-quality-basis-policy-validation-v1",
        "rows": rows,
        "errors": sorted(set(errors)),
        "error_count": len(set(errors)),
        "status": "PASS" if not errors else "FAIL",
    }


def typed_quality_source_semantics() -> dict[str, object]:
    return {
        "contract": "m12cr-r1-typed-quality-source-semantics-v1",
        "business_evidence_quality": [
            {
                "source_state": "verified_usable",
                "condition": "no applicable business-quality reason code",
                "output": "NONE",
                "directional_use_allowed": False,
                "evidence": "financial-quality-taint-v2 PROSE_USABLE_STATES and state producer",
            },
            {
                "source_state": "verified_usable",
                "condition": "freshness/cadence business reason present",
                "output": "CONFIDENCE_ONLY",
                "directional_use_allowed": False,
                "evidence": "financial freshness reason-code contract",
            },
            {
                "source_state": "caution_usable",
                "condition": "any",
                "output": "CONFIDENCE_ONLY",
                "directional_use_allowed": False,
                "evidence": "financial-quality-taint-v2 caution semantics",
            },
            {
                "source_state": "denied|unknown",
                "condition": "any",
                "output": "CONFIDENCE_ONLY",
                "directional_use_allowed": False,
                "evidence": "financial-quality-taint-v2 fail-closed semantics",
            },
        ],
        "security_valuation_basis": [
            {
                "source_decision": SAFE_SECURITY_DECISION,
                "output": "RESOLVED",
                "directional_use_allowed": False,
                "evidence": "security-identity-v2 verified non-depositary decision",
            },
            *[
                {
                    "source_decision": decision,
                    "output": "UNRESOLVED",
                    "directional_use_allowed": False,
                    "evidence": "security-identity-v2 valuation eligibility decision",
                }
                for decision in sorted(UNSAFE_SECURITY_DECISIONS)
            ],
        ],
        "security_only_reason_codes": sorted(SECURITY_BASIS_ONLY_REASON_CODES),
        "freshness_reason_codes": sorted(FRESHNESS_REASON_CODES),
        "unresolved_mapping_count": 0,
        "status": "PASS",
    }


def r1_semantic_rule_inventory(
    base_inventory: Mapping[str, object],
) -> dict[str, object]:
    new_rules = [
        ("M12CR-R1-DET-001", "typed_business_quality_state_mapping", "DETERMINISTIC_MATERIALIZER"),
        ("M12CR-R1-DET-002", "clean_ref_presence_not_limitation", "DETERMINISTIC_MATERIALIZER"),
        ("M12CR-R1-DET-003", "security_basis_state_mapping", "DETERMINISTIC_MATERIALIZER"),
        ("M12CR-R1-DET-004", "security_basis_policy_option_gate", "DETERMINISTIC_MATERIALIZER"),
        (
            "M12CR-R1-XREF-001",
            "security_basis_not_sole_overall_reason",
            "CROSS_REFERENCE_VALIDATOR_ONLY",
        ),
        (
            "M12CR-R1-XREF-002",
            "security_basis_not_sole_holder_reason",
            "CROSS_REFERENCE_VALIDATOR_ONLY",
        ),
        (
            "M12CR-R1-XREF-003",
            "business_confidence_not_sole_overall_reason",
            "CROSS_REFERENCE_VALIDATOR_ONLY",
        ),
        (
            "M12CR-R1-XREF-004",
            "business_confidence_not_sole_holder_reason",
            "CROSS_REFERENCE_VALIDATOR_ONLY",
        ),
        (
            "M12CR-R1-XREF-005",
            "directional_disclosure_allowlist_exception",
            "CROSS_REFERENCE_VALIDATOR_ONLY",
        ),
    ]
    rules = [deepcopy(dict(row)) for row in base_inventory.get("rules") or ()]
    rules.extend(
        {
            "rule_id": rule_id,
            "stage": "R1_TYPED_QUALITY_BASIS",
            "rule": rule,
            "upstream_enforcement": layer,
        }
        for rule_id, rule, layer in new_rules
    )
    missing = [
        row for row in rules if row.get("upstream_enforcement") == "MISSING_UPSTREAM_ENFORCEMENT"
    ]
    return {
        "contract": "m12cr-r1-semantic-validator-rule-inventory-v1",
        "base_rule_count": base_inventory.get("rule_count"),
        "new_rule_count": len(new_rules),
        "rule_count": len(rules),
        "rules": rules,
        "missing_upstream_enforcement_count": len(missing),
        "status": "PASS" if not missing else "FAIL",
    }
