from app.services.free_source_peer_service import (
    FREE_PEER_PROVIDER_POLICY,
    build_free_source_peer_state,
    derive_free_current_metric,
    render_free_peer_context,
    select_free_peer_candidates,
)


PRICE_DATE = "2026-08-17"


def _subject(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "ticker": "TARGET",
        "market": "us",
        "issuer_id": "issuer:target",
        "identity_safe": True,
        "profile_quality": "verified",
        "taxonomy": "semiconductor",
        "industry": "Semiconductors",
        "sector": "Technology",
        "framework": "semiconductor",
    }
    value.update(overrides)
    return value


def _candidate(ticker: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "ticker": ticker,
        "market": "us",
        "issuer_id": f"issuer:{ticker}",
        "security_id": f"security:{ticker}",
        "issuer_dedup_reliable": True,
        "identity_conflict": False,
        "is_depositary_security": False,
        "security_type": "common_stock",
        "profile_quality": "verified",
        "taxonomy": "semiconductor",
        "industry": "Semiconductors",
        "sector": "Technology",
    }
    value.update(overrides)
    return value


def _fact(ticker: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "ticker": ticker,
        "source": "finnhub_free_basic_financials",
        "source_entitlement": "free_existing",
        "identity_safe": True,
        "price": 100.0,
        "price_as_of": PRICE_DATE,
        "price_currency": "USD",
        "ttm_eps": 10.0,
        "ttm_eps_period_end": "2026-06-30",
        "eps_currency": "USD",
        "eps_security_basis": "provider_security_per_share",
        "bvps": 50.0,
        "bvps_period_end": "2026-06-30",
        "bvps_currency": "USD",
        "bvps_security_basis": "provider_security_per_share",
    }
    value.update(overrides)
    return value


def _snapshot() -> dict[str, object]:
    return {
        "price_as_of": PRICE_DATE,
        "ttm_eps": 10.0,
        "trailing_pe": 12.0,
        "trailing_pe_status": "value",
        "trailing_pe_source": "derived_trailing",
        "trailing_pe_basis_status": "directly_comparable",
        "trailing_pe_denominator_period_end": "2026-06-30",
        "trailing_pe_denominator_filing_date": "2026-08-01",
        "bvps": 50.0,
        "price_to_book": 2.4,
        "price_to_book_status": "value",
        "price_to_book_source": "derived_trailing",
        "price_to_book_basis_status": "directly_comparable",
        "pbr_denominator_period_end": "2026-06-30",
        "pbr_denominator_filing_date": "2026-08-01",
    }


def test_candidate_selection_separates_candidate_and_security_eligibility() -> None:
    candidates = [
        _candidate("A"),
        _candidate("B"),
        _candidate("B2", issuer_id="issuer:B"),
        _candidate("ADR", is_depositary_security=True),
        _candidate("PREF", security_type="preferred_stock"),
        _candidate("OTHER", taxonomy="software", industry="Software"),
    ]

    selected = select_free_peer_candidates(_subject(), candidates)

    assert selected["group_basis"] == "taxonomy"
    assert selected["candidate_count"] == 5
    assert selected["issuer_deduplicated_count"] == 2
    assert {item["reason"] for item in selected["excluded"]} == {
        "same_issuer_duplicate",
        "adr_basis_conflict",
        "non_common_security",
    }


def test_subject_and_same_issuer_are_never_candidates() -> None:
    selected = select_free_peer_candidates(
        _subject(),
        [
            _candidate("TARGET"),
            _candidate("CLASSC", issuer_id="issuer:target"),
            _candidate("A"),
        ],
    )

    assert {item["ticker"] for item in selected["eligible_candidates"]} == {"A"}
    assert {item["reason"] for item in selected["excluded"]} == {"subject_issuer"}


def test_free_derived_per_and_pbr_require_current_safe_denominators() -> None:
    pe, reason, lineage = derive_free_current_metric(
        _fact("A"), "trailing_pe", target_session=PRICE_DATE
    )
    pbr, pbr_reason, _ = derive_free_current_metric(
        _fact("A"), "price_to_book", target_session=PRICE_DATE
    )

    assert reason is None and pe == 10.0
    assert pbr_reason is None and pbr == 2.0
    assert lineage["calculation"] == "price/ttm_eps"


def test_free_assembly_fails_closed_on_basis_session_and_denominator() -> None:
    cases = (
        (_fact("A", identity_safe=False), "trailing_pe", "security_basis_unknown"),
        (_fact("A", price_as_of="2026-08-14"), "trailing_pe", "session_mismatch"),
        (_fact("A", ttm_eps=-1.0), "trailing_pe", "negative_eps"),
        (_fact("A", bvps=-1.0), "price_to_book", "negative_equity"),
        (_fact("A", eps_currency="KRW"), "trailing_pe", "currency_mismatch"),
        (_fact("A", ttm_eps_period_end="2025-06-30"), "trailing_pe", "stale_denominator"),
        (_fact("A", provider_conflict=True), "trailing_pe", "provider_conflict"),
    )
    for fact, metric, expected in cases:
        value, reason, _ = derive_free_current_metric(
            fact, metric, target_session=PRICE_DATE
        )
        assert value is None
        assert reason == expected


def test_missing_free_fact_is_unavailable_not_a_source_entitlement_claim() -> None:
    value, reason, lineage = derive_free_current_metric(
        {}, "trailing_pe", target_session=PRICE_DATE
    )

    assert value is None
    assert reason == "free_current_valuation_unavailable"
    assert lineage == {}


def test_three_independent_free_peers_produce_medium_context() -> None:
    candidates = [_candidate(ticker) for ticker in ("A", "B", "C")]
    facts = {
        "A": _fact("A", price=80.0),
        "B": _fact("B", price=100.0),
        "C": _fact("C", price=120.0),
    }

    state = build_free_source_peer_state(
        _subject(), candidates, _snapshot(), facts, target_session=PRICE_DATE
    )

    assert state["provider_policy"] == FREE_PEER_PROVIDER_POLICY
    assert state["coverage_state"] == "MEDIUM"
    assert state["metrics"]["trailing_pe"]["available"] is True
    assert state["metrics"]["trailing_pe"]["median"] == 10.0
    assert state["metrics"]["trailing_pe"]["company_vs_median_pct"] == 20.0
    assert state["metrics"]["price_to_book"]["median"] == 2.0
    assert state["canonical_fact"]["fields"]["pe_median"] == 10.0
    assert len(state["numeric_provenance"]) == 8
    assert {
        item["semantic_type"] for item in state["numeric_provenance"]
    } >= {"peer_pe_multiple", "peer_pb_multiple", "peer_sample_count"}


def test_fewer_than_three_clean_peers_are_suppressed() -> None:
    state = build_free_source_peer_state(
        _subject(),
        [_candidate("A"), _candidate("B")],
        _snapshot(),
        {"A": _fact("A"), "B": _fact("B")},
        target_session=PRICE_DATE,
    )

    assert state["available"] is False
    assert state["coverage_state"] == "LOW"
    assert state["metrics"]["trailing_pe"]["sample_count"] == 2


def test_broad_sector_fallback_remains_audit_only() -> None:
    candidates = [
        _candidate(
            ticker,
            taxonomy=f"taxonomy_{ticker}",
            industry=f"industry_{ticker}",
        )
        for ticker in ("A", "B", "C")
    ]
    state = build_free_source_peer_state(
        _subject(),
        candidates,
        _snapshot(),
        {ticker: _fact(ticker) for ticker in ("A", "B", "C")},
        target_session=PRICE_DATE,
    )

    assert state["selection"]["group_basis"] == "sector"
    assert state["available"] is False
    assert state["metrics"]["trailing_pe"]["audit_available"] is True


def test_memory_semiconductor_fallback_is_not_user_visible() -> None:
    subject = _subject(
        framework="memory",
        taxonomy="memory",
        industry="memory",
        sector="Semiconductors",
    )
    candidates = [
        _candidate(
            ticker,
            taxonomy="semiconductor",
            industry="Semiconductors",
            sector="Semiconductors",
        )
        for ticker in ("A", "B", "C")
    ]

    state = build_free_source_peer_state(
        subject,
        candidates,
        _snapshot(),
        {ticker: _fact(ticker) for ticker in ("A", "B", "C")},
        target_session=PRICE_DATE,
    )

    assert state["selection"]["group_basis"] == "sector"
    assert state["coverage_state"] == "LOW"
    assert state["available"] is False


def test_biotech_and_hpc_are_not_meaningful_even_with_metrics() -> None:
    for framework in ("biotech", "hpc_crypto_infrastructure"):
        state = build_free_source_peer_state(
            _subject(framework=framework),
            [_candidate(ticker) for ticker in ("A", "B", "C")],
            _snapshot(),
            {ticker: _fact(ticker) for ticker in ("A", "B", "C")},
            target_session=PRICE_DATE,
        )
        assert state["coverage_state"] == "NOT_MEANINGFUL"
        assert state["available"] is False


def test_adr_subject_is_suppressed_without_ratio_basis() -> None:
    state = build_free_source_peer_state(
        _subject(identity_safe=False),
        [_candidate(ticker) for ticker in ("A", "B", "C")],
        _snapshot(),
        {ticker: _fact(ticker) for ticker in ("A", "B", "C")},
        target_session=PRICE_DATE,
    )

    assert state["coverage_state"] == "SUPPRESSED"
    assert state["reason"] == "subject_security_basis_unsafe"


def test_rendering_uses_precomputed_statistics_without_valuation_verdict() -> None:
    state = build_free_source_peer_state(
        _subject(),
        [_candidate(ticker) for ticker in ("A", "B", "C")],
        _snapshot(),
        {ticker: _fact(ticker) for ticker in ("A", "B", "C")},
        target_session=PRICE_DATE,
    )

    text = render_free_peer_context(state)

    assert text is not None
    assert "3개 peer" in text
    assert "저평가" not in text
    assert "고평가" not in text


def test_automotive_display_prefers_per_while_pbr_remains_auditable() -> None:
    state = build_free_source_peer_state(
        _subject(framework="automotive"),
        [_candidate(ticker) for ticker in ("A", "B", "C")],
        _snapshot(),
        {ticker: _fact(ticker) for ticker in ("A", "B", "C")},
        target_session=PRICE_DATE,
    )

    assert state["display_metric"] == "trailing_pe"
    assert "peer PER 중앙값" in render_free_peer_context(state)
    assert state["metrics"]["price_to_book"]["available"] is True
