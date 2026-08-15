from app.models.security import SecurityMaster
from app.models.watchlist import WatchlistItem
from app.services.financial_quality_service import build_financial_quality_state
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.security_identity_service import (
    IDENTITY_CONFLICT,
    IDENTITY_UNKNOWN,
    VERIFIED_DEPOSITARY,
    VERIFIED_NON_DEPOSITARY,
    resolve_packet_security_identity,
    resolve_security_identity,
)


def _security(**overrides: object) -> SecurityMaster:
    values: dict[str, object] = {
        "canonical_company_id": "company:fixture",
        "canonical_security_id": "security:fixture:nasdaq",
        "ticker": "FIXTURE",
        "exchange": "NASDAQ",
        "country": "US",
        "company_name": "Fixture Corp",
        "security_type": "common_stock",
        "issuer_type": "domestic_us",
        "identity_quality": "verified",
        "identity_provider": "fixture_identity",
    }
    values.update(overrides)
    return SecurityMaster(**values)


def _watchlist(**overrides: object) -> WatchlistItem:
    values: dict[str, object] = {
        "ticker": "FIXTURE",
        "company_name": "Fixture Corp",
        "exchange": "NASDAQ",
        "issuer_type": "domestic_us",
    }
    values.update(overrides)
    return WatchlistItem(**values)


def _consensus_snapshot(identity_state: str) -> dict[str, object]:
    return {
        "current_price": 100.0,
        "currency": "USD",
        "provider": "finnhub",
        "security_identity_state": identity_state,
        "security_identity_decision_version": "security-identity-v1",
        "forward_eps": 10.0,
        "forward_pe": 10.0,
        "forward_pe_source": "consensus_forward",
        "forward_pe_input_period": "FY1",
        "forward_pe_basis_status": "not_applicable",
        "forward_pe_basis_conflict": False,
    }


def test_absent_depositary_evidence_does_not_verify_non_depositary() -> None:
    result = resolve_security_identity(
        company_name="Fixture Corp",
        legacy_issuer_type="domestic_us",
        legacy_security_type="common_stock",
        legacy_is_depositary=False,
    )

    assert result["identity_state"] == IDENTITY_UNKNOWN
    assert result["verification_status"] == "unverified"


def test_verified_common_stock_requires_positive_identity_evidence() -> None:
    result = resolve_security_identity(
        company_name="Fixture Corp",
        watchlist_item=_watchlist(),
        security_master=_security(),
    )

    assert result["identity_state"] == VERIFIED_NON_DEPOSITARY
    assert result["eligibility_decision"] == "provider_native_multiple_may_be_eligible"


def test_profile_adr_hint_conflicts_with_non_depositary_security_master() -> None:
    result = resolve_security_identity(
        company_name="Fixture Corp ADR",
        security_master=_security(company_name="Fixture Corp ADR"),
    )

    assert result["identity_state"] == IDENTITY_CONFLICT
    assert "profile_depositary_hint_conflicts_with_security_master" in result[
        "conflict_reasons"
    ]


def test_depositary_security_is_verified_without_guessing_ratio() -> None:
    result = resolve_security_identity(
        company_name="Fixture Depositary Receipt",
        watchlist_item=_watchlist(issuer_type="foreign_private_issuer"),
        security_master=_security(
            issuer_type="foreign_private_issuer",
            security_type="Depositary Receipt",
            adr_identifier="FIXADR",
        ),
    )

    assert result["identity_state"] == VERIFIED_DEPOSITARY
    assert result["evidence_values"]["watchlist_adr_ratio"] is None
    assert result["evidence_values"]["security_master_adr_ratio"] is None


def test_explicit_watchlist_depositary_evidence_outranks_inferred_local_default() -> None:
    result = resolve_security_identity(
        company_name="Fixture Depositary Receipt",
        watchlist_item=_watchlist(
            issuer_type="adr",
            ordinary_share_identifier="FIXORD",
            adr_ratio=0.5,
        ),
        security_master=_security(
            issuer_type="domestic_us",
            security_type="common_stock",
            identity_quality="inferred",
            identity_provider="local",
        ),
    )

    assert result["identity_state"] == VERIFIED_DEPOSITARY
    assert "security_master_inferred_issuer_type_ignored" in result[
        "resolved_conflict_reasons"
    ]


def test_ratio_and_issuer_conflicts_are_not_resolved_by_source_priority() -> None:
    result = resolve_security_identity(
        company_name="Fixture ADR",
        watchlist_item=_watchlist(
            issuer_type="adr",
            ordinary_share_identifier="FIXORD",
            adr_ratio=5,
        ),
        security_master=_security(
            issuer_type="foreign_private_issuer",
            security_type="Depositary Receipt",
            adr_identifier="FIXADR",
            ordinary_share_identifier="FIXORD",
            adr_ratio=10,
        ),
    )

    assert result["identity_state"] == IDENTITY_CONFLICT
    assert "watchlist_security_master_issuer_type_conflict" in result[
        "conflict_reasons"
    ]
    assert "adr_ratio_conflict" in result["conflict_reasons"]


def test_provider_native_consensus_requires_verified_non_depositary_state() -> None:
    verified = build_financial_quality_state(
        _consensus_snapshot(VERIFIED_NON_DEPOSITARY)
    )
    conflicted = build_financial_quality_state(
        {
            **_consensus_snapshot(IDENTITY_CONFLICT),
            "security_identity_conflict_reasons": ["fixture_conflict"],
        }
    )
    unknown = build_financial_quality_state(
        _consensus_snapshot(IDENTITY_UNKNOWN)
    )

    assert verified["fields"]["forward_pe"]["state"] == "verified_usable"
    assert conflicted["fields"]["forward_pe"]["state"] == "denied"
    assert conflicted["fields"]["forward_pe"]["prose_eligible"] is False
    assert unknown["fields"]["forward_pe"]["state"] == "unknown"
    assert unknown["fields"]["forward_pe"]["prose_eligible"] is False


def test_conflicted_multiple_has_no_display_and_placeholder_binding_fails() -> None:
    quality = build_financial_quality_state(
        {
            **_consensus_snapshot(IDENTITY_CONFLICT),
            "security_identity_conflict_reasons": ["fixture_conflict"],
        }
    )["fields"]["forward_pe"]
    facts = [
        {
            "fact_id": "valuation:current",
            "fact_type": "valuation",
            "fields": {
                "forward_pe": 10.0,
                "forward_pe_source": "consensus_forward",
            },
            "field_quality": {"fields.forward_pe": quality},
        }
    ]
    registry = build_numeric_registry(facts)
    row = registry[0]
    packet = {"stocks": [{"ticker": "FIXTURE", "numeric_registry": registry}]}
    output = {
        "stock_reviews": [
            {
                "ticker": "FIXTURE",
                "facts_used": ["valuation:current"],
                "core_judgment": {"text": "{{numeric:fpe}}를 확인합니다."},
                "numeric_claims": [],
                "numeric_fact_refs": [
                    {
                        "ref_id": "fpe",
                        "fact_id": "valuation:current",
                        "field_path": "fields.forward_pe",
                        "text_ref": "core_judgment.text",
                    }
                ],
            }
        ]
    }

    binding = bind_numeric_fact_references(packet, output)

    assert row["prose_allowed"] is False
    assert row["canonical_display_value"] is None
    assert row["approved_display_variants"] == []
    assert row["denial_reason"] == "security_identity_conflict"
    assert any(
        "numeric_fact_ref_semantic_not_supported" in item
        for item in binding.errors
    )


def test_legacy_skhynix_style_packet_resolves_explicit_conflict() -> None:
    result = resolve_packet_security_identity(
        {
            "company_name": "SK hynix Inc. ADR",
            "valuation": {
                "resolved_issuer_type": "domestic_us",
                "resolved_security_type": "common_stock",
                "is_depositary_security": False,
            },
        }
    )

    assert result["identity_state"] == IDENTITY_CONFLICT


def test_legacy_common_packet_without_verification_remains_unknown() -> None:
    result = resolve_packet_security_identity(
        {
            "company_name": "Fixture Corp",
            "valuation": {
                "resolved_issuer_type": "domestic_us",
                "resolved_security_type": "common_stock",
                "is_depositary_security": False,
            },
        }
    )

    assert result["identity_state"] == IDENTITY_UNKNOWN
