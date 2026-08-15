from __future__ import annotations

from datetime import date, datetime
import json
import re


SECURITY_IDENTITY_DECISION_VERSION = "security-identity-v2"
VERIFIED_DEPOSITARY = "verified_depositary"
VERIFIED_NON_DEPOSITARY = "verified_non_depositary"
IDENTITY_CONFLICT = "conflict"
IDENTITY_UNKNOWN = "unknown"

TIER_A_AUTHORITATIVE = "tier_a_authoritative"
TIER_B_DETERMINISTIC_REFERENCE = "tier_b_deterministic_reference"
TIER_C_EXPLICIT_LOCAL = "tier_c_explicit_local"
TIER_D_INFERRED_DEFAULT = "tier_d_inferred_default"

_TIER_RANK = {
    TIER_A_AUTHORITATIVE: 1,
    TIER_B_DETERMINISTIC_REFERENCE: 2,
    TIER_C_EXPLICIT_LOCAL: 3,
    TIER_D_INFERRED_DEFAULT: 4,
}

_DEPOSITARY_ISSUER_TYPES = {"adr", "ads", "depositary_security"}
_NON_DEPOSITARY_ISSUER_TYPES = {
    "domestic_us",
    "krx",
    "foreign_private_issuer",
    "other_foreign",
}
_DEPOSITARY_SECURITY_TYPES = {
    "adr",
    "ads",
    "depositary_receipt",
    "depositary_security",
    "american_depositary_receipt",
    "american_depositary_share",
}
_NON_DEPOSITARY_SECURITY_TYPES = {
    "common",
    "common_share",
    "common_shares",
    "common_stock",
    "ordinary_share",
    "ordinary_shares",
    "cp",
}
_DEPOSITARY_NAME = re.compile(
    r"\b(?:adr|ads)\b|american\s+depositary\s+(?:receipt|share)s?",
    re.IGNORECASE,
)
_CONFLICT_WARNING = re.compile(
    r"conflict|mismatch|inconsistent|불일치|상충",
    re.IGNORECASE,
)
_ADR_RATIO_DIRECTION = "ordinary_shares_per_adr"


def _normalized(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _json_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [value]
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _serialized(value: object) -> object:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _attribute(value: object | None, name: str) -> object:
    return getattr(value, name, None) if value is not None else None


def identity_source_tier(provider: object, quality: object = None) -> str:
    """Classify identity provenance without treating a local default as verification."""
    provider_value = _normalized(provider)
    quality_value = _normalized(quality)
    if provider_value in {
        "sec_official_identity",
        "official_exchange_identity",
        "issuer_official_identity",
    }:
        return TIER_A_AUTHORITATIVE
    if provider_value in {
        "openfigi_deterministic_match",
        "deterministic_reference_identity",
    }:
        return TIER_B_DETERMINISTIC_REFERENCE
    if quality_value in {"full", "verified"} and provider_value in {
        "explicit_local_identity",
        "fixture_identity",
    }:
        return TIER_C_EXPLICIT_LOCAL
    return TIER_D_INFERRED_DEFAULT


def _higher_priority(left: str, right: str) -> bool:
    return _TIER_RANK[left] < _TIER_RANK[right]


def _verified_adr_ratio_direction(
    *,
    state: str,
    ratio: float | None,
    ratio_source: str | None,
    provenance: dict[str, object],
) -> str | None:
    if state != VERIFIED_DEPOSITARY or ratio is None or ratio <= 0 or not ratio_source:
        return None
    if provenance.get("adr_ratio_direction") != _ADR_RATIO_DIRECTION:
        return None
    fields = provenance.get("field_provenance")
    if not isinstance(fields, dict):
        return None
    ratio_fact = fields.get("adr_ratio")
    direction_fact = fields.get("adr_ratio_direction")
    if not isinstance(ratio_fact, dict) or not isinstance(direction_fact, dict):
        return None
    if ratio_fact.get("verification_status") != "verified":
        return None
    if direction_fact.get("verification_status") != "verified":
        return None
    if ratio_fact.get("value") != ratio:
        return None
    if direction_fact.get("value") != _ADR_RATIO_DIRECTION:
        return None
    return _ADR_RATIO_DIRECTION


def resolve_security_identity(
    *,
    company_name: str | None,
    watchlist_item: object | None = None,
    security_master: object | None = None,
    legacy_issuer_type: str | None = None,
    legacy_security_type: str | None = None,
    legacy_is_depositary: bool | None = None,
    identity_provenance: dict[str, object] | None = None,
) -> dict[str, object]:
    """Resolve identity without converting absence into non-depositary evidence."""
    watch_issuer = _normalized(_attribute(watchlist_item, "issuer_type"))
    security_issuer = _normalized(
        _attribute(security_master, "issuer_type") or legacy_issuer_type
    )
    security_type = _normalized(
        _attribute(security_master, "security_type") or legacy_security_type
    )
    adr_identifier = str(_attribute(security_master, "adr_identifier") or "").strip()
    figi = str(_attribute(security_master, "figi") or "").strip()
    ordinary_identifier = str(
        _attribute(watchlist_item, "ordinary_share_identifier")
        or _attribute(security_master, "ordinary_share_identifier")
        or ""
    ).strip()
    watch_ratio = _attribute(watchlist_item, "adr_ratio")
    watch_created_at = _attribute(watchlist_item, "created_at")
    security_ratio = _attribute(security_master, "adr_ratio")
    identity_quality = _normalized(_attribute(security_master, "identity_quality"))
    identity_provider = str(
        _attribute(security_master, "identity_provider") or ""
    ).strip()
    source_tier = identity_source_tier(identity_provider, identity_quality)
    identity_warnings = _json_list(_attribute(security_master, "identity_warnings"))
    country = str(_attribute(security_master, "country") or "").strip()
    ticker = str(_attribute(security_master, "ticker") or "").strip().upper()
    exchange = str(
        _attribute(security_master, "exchange")
        or _attribute(watchlist_item, "exchange")
        or ""
    ).strip()
    name_has_depositary_hint = bool(_DEPOSITARY_NAME.search(company_name or ""))
    provenance = dict(identity_provenance or {})

    evidence: list[dict[str, object]] = []

    def add(source: str, value: object, meaning: str) -> None:
        if value not in (None, "", [], False):
            evidence.append(
                {
                    "source": source,
                    "value": _serialized(value),
                    "meaning": meaning,
                }
            )

    add("watchlist.issuer_type", watch_issuer, "issuer_type")
    add("watchlist.created_at", watch_created_at, "explicit_assertion_as_of")
    add("security_master.issuer_type", security_issuer, "issuer_type")
    add("security_master.security_type", security_type, "security_type")
    add("security_master.ticker", ticker, "listing_identifier")
    add("security_master.adr_identifier", adr_identifier, "depositary_evidence")
    add("security_master.figi", figi, "reference_instrument_identifier")
    add("security_master.identity_quality", identity_quality, "identity_quality")
    add("security_master.identity_provider", identity_provider, "identity_provider")
    add("security_master.identity_source_tier", source_tier, "identity_source_tier")
    add("security_master.country", country, "listing_country")
    add("security_master.exchange", exchange, "listing_exchange")
    add("profile.company_name", company_name if name_has_depositary_hint else None, "depositary_hint")
    add("watchlist.ordinary_share_identifier", ordinary_identifier, "ordinary_share_identity")
    add("watchlist.adr_ratio", watch_ratio, "depositary_ratio")
    add("security_master.adr_ratio", security_ratio, "depositary_ratio")
    for warning in identity_warnings:
        add("security_master.identity_warnings", warning, "identity_warning")
    for field_name, field_value in dict(provenance.get("field_provenance") or {}).items():
        if isinstance(field_value, dict):
            evidence.append(
                {
                    "source": f"identity_provenance.{field_name}",
                    "value": field_value.get("value"),
                    "meaning": "authoritative_field_provenance",
                    "source_tier": field_value.get("source_tier"),
                    "provider": field_value.get("provider"),
                    "source_url": field_value.get("source_url"),
                    "source_reference": field_value.get("source_reference"),
                    "as_of": field_value.get("as_of"),
                    "verification_status": field_value.get("verification_status"),
                    "resolution_reason": field_value.get("resolution_reason"),
                }
            )

    issuer_depositary = {
        value
        for value in (watch_issuer, security_issuer)
        if value in _DEPOSITARY_ISSUER_TYPES
    }
    issuer_non_depositary = {
        value
        for value in (watch_issuer, security_issuer)
        if value in _NON_DEPOSITARY_ISSUER_TYPES
    }
    security_depositary = security_type in _DEPOSITARY_SECURITY_TYPES
    security_non_depositary = security_type in _NON_DEPOSITARY_SECURITY_TYPES
    has_ratio_identity = bool(
        ordinary_identifier
        and any(
            isinstance(value, (int, float)) and float(value) > 0
            for value in (watch_ratio, security_ratio)
        )
    )
    raw_depositary_evidence = bool(
        issuer_depositary or security_depositary or adr_identifier or has_ratio_identity
    )
    non_depositary_tuple = bool(
        issuer_non_depositary
        and security_non_depositary
        and not adr_identifier
        and not has_ratio_identity
    )

    master_verified = bool(
        identity_quality in {"full", "verified"}
        and source_tier != TIER_D_INFERRED_DEFAULT
        and country
        and exchange
    )
    watch_depositary_explicit = bool(
        watch_issuer in _DEPOSITARY_ISSUER_TYPES
        and (ordinary_identifier or isinstance(watch_ratio, (int, float)))
    )
    watch_non_depositary_explicit = bool(
        watch_issuer in _NON_DEPOSITARY_ISSUER_TYPES
        and watch_created_at is not None
        and exchange
    )
    watch_tier = (
        TIER_C_EXPLICIT_LOCAL
        if watch_depositary_explicit or watch_non_depositary_explicit
        else TIER_D_INFERRED_DEFAULT
    )

    conflicts: list[str] = []
    resolved_conflicts: list[str] = []
    if watch_issuer and security_issuer and watch_issuer != security_issuer:
        if master_verified and _higher_priority(source_tier, watch_tier):
            resolved_conflicts.append(
                "watchlist_security_master_issuer_type_conflict_resolved_by_higher_tier"
            )
        elif _higher_priority(watch_tier, source_tier):
            resolved_conflicts.append(
                "security_master_inferred_issuer_type_ignored"
            )
        elif watch_tier == TIER_D_INFERRED_DEFAULT:
            resolved_conflicts.append(
                "inferred_watchlist_issuer_type_ignored"
            )
        else:
            conflicts.append("watchlist_security_master_issuer_type_conflict")
    if (
        issuer_depositary
        and issuer_non_depositary
        and not resolved_conflicts
    ):
        conflicts.append("depositary_non_depositary_issuer_conflict")
    if security_depositary and security_issuer in {"domestic_us", "krx"}:
        conflicts.append("issuer_security_type_conflict")
    if security_non_depositary and security_issuer in _DEPOSITARY_ISSUER_TYPES:
        conflicts.append("issuer_security_type_conflict")
    if adr_identifier and security_issuer in {"domestic_us", "krx"}:
        conflicts.append("adr_identifier_issuer_type_conflict")
    if name_has_depositary_hint and non_depositary_tuple:
        conflicts.append("profile_depositary_hint_conflicts_with_security_master")
    ratio_conflict = bool(
        isinstance(watch_ratio, (int, float))
        and isinstance(security_ratio, (int, float))
        and not abs(float(watch_ratio) - float(security_ratio)) <= 1e-6
    )
    if ratio_conflict:
        if master_verified and _higher_priority(source_tier, watch_tier):
            resolved_conflicts.append("adr_ratio_conflict_resolved_by_higher_tier")
        else:
            conflicts.append("adr_ratio_conflict")
    if any(_CONFLICT_WARNING.search(item) for item in identity_warnings):
        conflicts.append("provider_identity_warning")
    conflicts = list(dict.fromkeys(conflicts))

    verified_non_depositary = bool(
        non_depositary_tuple
        and (master_verified or watch_non_depositary_explicit)
    )
    legacy_affirmative_depositary_reference = bool(
        _normalized(identity_provider) == "local+openfigi"
        and identity_quality in {"full", "verified"}
        and figi
        and adr_identifier
        and security_depositary
        and country
        and exchange
        and security_issuer not in {"domestic_us", "krx"}
    )
    krx_listing_assertion = bool(
        re.fullmatch(r"\d{6}", ticker)
        and country.upper() == "KR"
        and exchange.upper() in {"KRX", "KOSPI", "KOSDAQ"}
        and security_issuer == "krx"
        and security_non_depositary
        and identity_quality in {"full", "verified"}
    )
    verified_non_depositary = bool(
        verified_non_depositary or krx_listing_assertion
    )
    verified_depositary = bool(
        (master_verified and (security_depositary or adr_identifier))
        or watch_depositary_explicit
        or legacy_affirmative_depositary_reference
    )

    selected_issuer_type = security_issuer if master_verified else watch_issuer or security_issuer
    selected_security_type = security_type
    selected_ratio: float | None = None
    selected_ratio_source: str | None = None
    if isinstance(security_ratio, (int, float)) and float(security_ratio) > 0 and (
        master_verified or not isinstance(watch_ratio, (int, float))
    ):
        selected_ratio = float(security_ratio)
        selected_ratio_source = str(
            _attribute(security_master, "adr_ratio_source") or identity_provider or ""
        ) or None
    elif isinstance(watch_ratio, (int, float)) and float(watch_ratio) > 0:
        selected_ratio = float(watch_ratio)
        selected_ratio_source = "watchlist_explicit_assertion"

    if conflicts:
        state = IDENTITY_CONFLICT
        verification = "conflicted"
        decision = "security_share_basis_dependent_valuation_denied"
    elif verified_depositary:
        state = VERIFIED_DEPOSITARY
        verification = "verified"
        decision = "requires_verified_current_security_denominator"
    elif verified_non_depositary:
        state = VERIFIED_NON_DEPOSITARY
        verification = "verified"
        decision = "provider_native_multiple_may_be_eligible"
    else:
        state = IDENTITY_UNKNOWN
        verification = "unverified"
        decision = "security_share_basis_dependent_valuation_denied"

    if raw_depositary_evidence and not verified_depositary and not conflicts:
        decision = "unverified_depositary_evidence_requires_authoritative_resolution"

    # A legacy false flag is retained as evidence only; it never proves non-depositary status.
    if legacy_is_depositary is True and state == VERIFIED_NON_DEPOSITARY:
        state = IDENTITY_CONFLICT
        verification = "conflicted"
        conflicts.append("legacy_depositary_flag_conflict")
        decision = "security_share_basis_dependent_valuation_denied"

    adr_ratio_direction = _verified_adr_ratio_direction(
        state=state,
        ratio=selected_ratio,
        ratio_source=selected_ratio_source,
        provenance=provenance,
    )
    updated_at = _attribute(security_master, "updated_at")
    return {
        "decision_version": SECURITY_IDENTITY_DECISION_VERSION,
        "identity_state": state,
        "evidence_sources": evidence,
        "evidence_values": {
            "watchlist_issuer_type": watch_issuer or None,
            "security_master_issuer_type": security_issuer or None,
            "security_type": security_type or None,
            "adr_identifier": adr_identifier or None,
            "figi": figi or None,
            "ordinary_share_identifier": ordinary_identifier or None,
            "watchlist_adr_ratio": watch_ratio,
            "security_master_adr_ratio": security_ratio,
            "name_has_depositary_hint": name_has_depositary_hint,
            "legacy_is_depositary_security": legacy_is_depositary,
        },
        "conflict_reasons": conflicts,
        "resolved_conflict_reasons": resolved_conflicts,
        "verification_status": verification,
        "as_of": _serialized(updated_at),
        "source_provenance": identity_provider or "packet_legacy_identity",
        "source_tier": source_tier,
        "verification_source_tier": (
            source_tier
            if master_verified
            else TIER_C_EXPLICIT_LOCAL
            if (
                legacy_affirmative_depositary_reference
                or watch_depositary_explicit
                or watch_non_depositary_explicit
                or krx_listing_assertion
            )
            else source_tier
        ),
        "identity_provenance": provenance,
        "selected_issuer_type": selected_issuer_type or None,
        "selected_security_type": selected_security_type or None,
        "selected_adr_ratio": selected_ratio,
        "selected_adr_ratio_source": selected_ratio_source,
        "is_depositary_evidence_present": raw_depositary_evidence,
        "adr_ratio_direction": adr_ratio_direction,
        "eligibility_decision": decision,
    }


def resolve_packet_security_identity(stock: dict[str, object]) -> dict[str, object]:
    valuation = stock.get("valuation")
    valuation = valuation if isinstance(valuation, dict) else {}
    state = str(valuation.get("security_identity_state") or "")
    if state in {
        VERIFIED_DEPOSITARY,
        VERIFIED_NON_DEPOSITARY,
        IDENTITY_CONFLICT,
        IDENTITY_UNKNOWN,
    }:
        return {
            "decision_version": valuation.get("security_identity_decision_version"),
            "identity_state": state,
            "evidence_sources": valuation.get("security_identity_evidence", []),
            "evidence_values": valuation.get("security_identity_evidence_values", {}),
            "conflict_reasons": valuation.get("security_identity_conflict_reasons", []),
            "resolved_conflict_reasons": valuation.get(
                "security_identity_resolved_conflict_reasons", []
            ),
            "verification_status": valuation.get(
                "security_identity_verification_status", "unverified"
            ),
            "as_of": valuation.get("security_identity_as_of"),
            "source_provenance": valuation.get("security_identity_source_provenance"),
            "source_tier": valuation.get("security_identity_source_tier"),
            "verification_source_tier": valuation.get(
                "security_identity_verification_source_tier"
            )
            or valuation.get("security_identity_source_tier"),
            "identity_provenance": valuation.get("security_identity_provenance", {}),
            "eligibility_decision": valuation.get(
                "security_identity_eligibility_decision"
            ),
        }
    return resolve_security_identity(
        company_name=str(stock.get("company_name") or ""),
        legacy_issuer_type=str(valuation.get("resolved_issuer_type") or ""),
        legacy_security_type=str(valuation.get("resolved_security_type") or ""),
        legacy_is_depositary=(
            valuation.get("is_depositary_security")
            if isinstance(valuation.get("is_depositary_security"), bool)
            else None
        ),
    )
