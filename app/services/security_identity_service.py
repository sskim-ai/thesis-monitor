from __future__ import annotations

from datetime import date, datetime
import json
import re


SECURITY_IDENTITY_DECISION_VERSION = "security-identity-v1"
VERIFIED_DEPOSITARY = "verified_depositary"
VERIFIED_NON_DEPOSITARY = "verified_non_depositary"
IDENTITY_CONFLICT = "conflict"
IDENTITY_UNKNOWN = "unknown"

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


def resolve_security_identity(
    *,
    company_name: str | None,
    watchlist_item: object | None = None,
    security_master: object | None = None,
    legacy_issuer_type: str | None = None,
    legacy_security_type: str | None = None,
    legacy_is_depositary: bool | None = None,
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
    ordinary_identifier = str(
        _attribute(watchlist_item, "ordinary_share_identifier")
        or _attribute(security_master, "ordinary_share_identifier")
        or ""
    ).strip()
    watch_ratio = _attribute(watchlist_item, "adr_ratio")
    security_ratio = _attribute(security_master, "adr_ratio")
    identity_quality = _normalized(_attribute(security_master, "identity_quality"))
    identity_provider = str(
        _attribute(security_master, "identity_provider") or ""
    ).strip()
    identity_warnings = _json_list(_attribute(security_master, "identity_warnings"))
    country = str(_attribute(security_master, "country") or "").strip()
    exchange = str(
        _attribute(security_master, "exchange")
        or _attribute(watchlist_item, "exchange")
        or ""
    ).strip()
    name_has_depositary_hint = bool(_DEPOSITARY_NAME.search(company_name or ""))

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
    add("security_master.issuer_type", security_issuer, "issuer_type")
    add("security_master.security_type", security_type, "security_type")
    add("security_master.adr_identifier", adr_identifier, "depositary_evidence")
    add("security_master.identity_quality", identity_quality, "identity_quality")
    add("security_master.identity_provider", identity_provider, "identity_provider")
    add("security_master.country", country, "listing_country")
    add("security_master.exchange", exchange, "listing_exchange")
    add("profile.company_name", company_name if name_has_depositary_hint else None, "depositary_hint")
    add("watchlist.ordinary_share_identifier", ordinary_identifier, "ordinary_share_identity")
    add("watchlist.adr_ratio", watch_ratio, "depositary_ratio")
    add("security_master.adr_ratio", security_ratio, "depositary_ratio")
    for warning in identity_warnings:
        add("security_master.identity_warnings", warning, "identity_warning")

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
    depositary_evidence = bool(
        issuer_depositary
        or security_depositary
        or adr_identifier
        or has_ratio_identity
    )
    non_depositary_tuple = bool(
        issuer_non_depositary
        and security_non_depositary
        and not adr_identifier
        and not has_ratio_identity
    )

    conflicts: list[str] = []
    if watch_issuer and security_issuer and watch_issuer != security_issuer:
        conflicts.append("watchlist_security_master_issuer_type_conflict")
    if issuer_depositary and issuer_non_depositary:
        conflicts.append("depositary_non_depositary_issuer_conflict")
    if security_depositary and security_issuer in {"domestic_us", "krx"}:
        conflicts.append("issuer_security_type_conflict")
    if security_non_depositary and security_issuer in _DEPOSITARY_ISSUER_TYPES:
        conflicts.append("issuer_security_type_conflict")
    if adr_identifier and security_issuer in {"domestic_us", "krx"}:
        conflicts.append("adr_identifier_issuer_type_conflict")
    if name_has_depositary_hint and non_depositary_tuple:
        conflicts.append("profile_depositary_hint_conflicts_with_security_master")
    if (
        isinstance(watch_ratio, (int, float))
        and isinstance(security_ratio, (int, float))
        and not abs(float(watch_ratio) - float(security_ratio)) <= 1e-6
    ):
        conflicts.append("adr_ratio_conflict")
    if any(_CONFLICT_WARNING.search(item) for item in identity_warnings):
        conflicts.append("provider_identity_warning")
    conflicts = list(dict.fromkeys(conflicts))

    verified_identity_record = bool(
        identity_quality in {"full", "verified"}
        and identity_provider
        and country
        and exchange
    )
    watchlist_confirms_non_depositary = bool(
        watch_issuer in _NON_DEPOSITARY_ISSUER_TYPES
        and security_issuer == watch_issuer
        and security_non_depositary
    )
    verified_non_depositary = bool(
        non_depositary_tuple
        and (verified_identity_record or watchlist_confirms_non_depositary)
    )

    if conflicts:
        state = IDENTITY_CONFLICT
        verification = "conflicted"
        decision = "security_share_basis_dependent_valuation_denied"
    elif depositary_evidence:
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

    # A legacy false flag is retained as evidence only; it never proves non-depositary status.
    if legacy_is_depositary is True and state == VERIFIED_NON_DEPOSITARY:
        state = IDENTITY_CONFLICT
        verification = "conflicted"
        conflicts.append("legacy_depositary_flag_conflict")
        decision = "security_share_basis_dependent_valuation_denied"

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
            "ordinary_share_identifier": ordinary_identifier or None,
            "watchlist_adr_ratio": watch_ratio,
            "security_master_adr_ratio": security_ratio,
            "name_has_depositary_hint": name_has_depositary_hint,
            "legacy_is_depositary_security": legacy_is_depositary,
        },
        "conflict_reasons": conflicts,
        "verification_status": verification,
        "as_of": _serialized(updated_at),
        "source_provenance": identity_provider or "packet_legacy_identity",
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
            "verification_status": valuation.get(
                "security_identity_verification_status", "unverified"
            ),
            "as_of": valuation.get("security_identity_as_of"),
            "source_provenance": valuation.get("security_identity_source_provenance"),
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
