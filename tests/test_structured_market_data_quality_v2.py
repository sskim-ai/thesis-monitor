from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta

import httpx

from app.macro.providers.market import MARKET_SYMBOLS
from app.providers.krx_publication_provider import KrxPublicationProvider
from app.services.free_analyst_message_service import message_quality_v2_report
from app.services.free_analyst_production_integration_service import (
    build_production_candidate,
)
from app.services.market_context_adapter_service import market_context_adapter
from app.services.structured_market_context_service import (
    StructuredMarketContextEnvelope,
    load_current_cross_section,
    load_structured_market_context,
    persist_structured_market_context,
)


SESSION = date(2026, 8, 24)
OBSERVED_AT = datetime(2026, 8, 25, 0, 5, tzinfo=UTC)


def _stock_row(code: str, close: str, change: str) -> dict[str, str]:
    return {
        "BAS_DD": "20260824",
        "ISU_CD": code,
        "ISU_NM": code,
        "MKT_NM": "market",
        "SECT_TP_NM": "주권",
        "TDD_CLSPRC": close,
        "CMPPREVDD_PRC": change,
        "FLUC_RT": "0",
        "ACC_TRDVOL": "100",
        "ACC_TRDVAL": "100000",
        "LIST_SHRS": "1000",
        "MKTCAP": "1000000",
        "TDD_OPNPRC": close,
        "TDD_HGPRC": close,
        "TDD_LWPRC": close,
    }


def _index_row(market: str, name: str, close: str) -> dict[str, str]:
    return {
        "BAS_DD": "20260824",
        "IDX_CLSS": market,
        "IDX_NM": name,
        "CLSPRC_IDX": close,
        "CMPPREVDD_IDX": "1",
        "FLUC_RT": "0.1",
        "OPNPRC_IDX": close,
        "HGPRC_IDX": close,
        "LWPRC_IDX": close,
        "ACC_TRDVOL": "1000",
        "ACC_TRDVAL": "1000000",
        "MKTCAP": "10000000",
    }


def _krx_transport() -> httpx.MockTransport:
    rows = {
        "/sto/stk_bydd_trd": [
            _stock_row("000001", "110", "10"),
            _stock_row("000002", "95", "-5"),
            _stock_row("000003", "100", "0"),
        ],
        "/sto/ksq_bydd_trd": [
            _stock_row("100001", "55", "5"),
            _stock_row("100002", "45", "-5"),
        ],
        "/idx/kospi_dd_trd": [
            _index_row("KOSPI", "코스피", "3000"),
            _index_row("KOSPI", "코스피 200", "400"),
        ],
        "/idx/kosdaq_dd_trd": [
            _index_row("KOSDAQ", "코스닥", "900"),
            _index_row("KOSDAQ", "코스닥 150", "1500"),
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"OutBlock_1": rows[request.url.path]})

    return httpx.MockTransport(handler)


def test_krx_official_rows_preserve_kospi_and_kosdaq_breadth_scope() -> None:
    provider = KrxPublicationProvider(
        api_key="test",
        base_url="https://example.com",
        transport=_krx_transport(),
    )

    section = asyncio.run(
        provider.collect_market_cross_section(
            target_session=SESSION,
            observed_at=OBSERVED_AT,
        )
    )

    assert section.market == "KR"
    assert [item.symbol for item in section.indices] == ["KOSPI", "KOSDAQ"]
    assert section.breadth is not None
    assert section.breadth.eligible_count == 5
    by_scope = {item.scope: item.breadth for item in section.breadth_by_scope}
    assert by_scope["KOSPI"].model_dump()["advance_count"] == 1
    assert by_scope["KOSPI"].decline_count == 1
    assert by_scope["KOSPI"].unchanged_count == 1
    assert by_scope["KOSDAQ"].advance_count == 1
    assert by_scope["KOSDAQ"].decline_count == 1
    assert section.quality.trading_value_semantics == "official_reported"


def test_krx_empty_rows_remain_publication_pending_not_zero() -> None:
    provider = KrxPublicationProvider(
        api_key="test",
        base_url="https://example.com",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, json={"OutBlock_1": []})
        ),
    )

    readiness = asyncio.run(
        provider.probe_publication_readiness(
            target_session=SESSION,
            latest_completed_session=SESSION,
            observed_at=OBSERVED_AT,
        )
    )

    assert readiness.status == "MARKET_COMPLETED_PROVIDER_PENDING"
    assert readiness.current_snapshot_promotable is False
    assert all(item.row_count == 0 for item in readiness.endpoints)


def test_structured_cache_requires_exact_date_hash_and_cutoff(tmp_path) -> None:
    provider = KrxPublicationProvider(
        api_key="test",
        base_url="https://example.com",
        transport=_krx_transport(),
    )
    section = asyncio.run(
        provider.collect_market_cross_section(
            target_session=SESSION,
            observed_at=OBSERVED_AT,
        )
    )
    persist_structured_market_context(
        StructuredMarketContextEnvelope(
            market="KR",
            session_date=SESSION,
            retrieved_at=OBSERVED_AT,
            provider="KRX_OPEN_API",
            publication_state="AVAILABLE_CURRENT",
            source_refs=["KRX"],
            source_payload_sha256=section.source_payload_sha256,
            cross_section=section,
        ),
        directory=tmp_path,
    )

    assert (
        load_current_cross_section(
            "KR",
            SESSION,
            cutoff=OBSERVED_AT + timedelta(seconds=1),
            directory=tmp_path,
        )
        is not None
    )
    assert (
        load_current_cross_section(
            "KR",
            SESSION,
            cutoff=OBSERVED_AT - timedelta(seconds=1),
            directory=tmp_path,
        )
        is None
    )
    assert (
        load_current_cross_section(
            "KR",
            date(2026, 8, 25),
            cutoff=OBSERVED_AT + timedelta(days=1),
            directory=tmp_path,
        )
        is None
    )


def test_publication_pending_envelope_preserves_unknown_without_zero(tmp_path) -> None:
    persist_structured_market_context(
        StructuredMarketContextEnvelope(
            market="KR",
            session_date=SESSION,
            retrieved_at=OBSERVED_AT,
            provider="KRX_OPEN_API",
            publication_state="PUBLICATION_PENDING",
            source_refs=["sto/stk_bydd_trd"],
            data_gaps=["krx_publication:market_completed_provider_pending"],
        ),
        directory=tmp_path,
    )

    envelope = load_structured_market_context(
        "KR",
        SESSION,
        cutoff=OBSERVED_AT + timedelta(seconds=1),
        directory=tmp_path,
    )

    assert envelope is not None
    assert envelope.publication_state == "PUBLICATION_PENDING"
    assert envelope.cross_section is None
    assert (
        load_current_cross_section(
            "KR",
            SESSION,
            cutoff=OBSERVED_AT + timedelta(seconds=1),
            directory=tmp_path,
        )
        is None
    )


def test_us_style_and_sector_facts_use_existing_common_adapter() -> None:
    facts = [
        {
            "fact_id": "market:style:RSP",
            "fact_type": "market_style",
            "as_of_date": "2026-08-24",
            "fields": {
                "series_code": "RSP",
                "label": "S&P500 동일가중",
                "return_pct": 0.12,
            },
        },
        {
            "fact_id": "market:sector:XLF",
            "fact_type": "market_sector",
            "as_of_date": "2026-08-24",
            "fields": {
                "series_code": "XLF",
                "label": "금융",
                "return_pct": 1.29,
            },
        },
        {
            "fact_id": "market:relative:RSP:SPY",
            "fact_type": "market_style_relative",
            "as_of_date": "2026-08-24",
            "fields": {
                "relative_return_pct": 0.41,
                "source_fact_ids": ["market:style:RSP", "market:index:SPY"],
            },
        },
        {
            "fact_id": "market:index:SPY",
            "fact_type": "market_index",
            "as_of_date": "2026-08-24",
            "fields": {
                "series_code": "SPY",
                "label": "S&P500",
                "return_pct": -0.29,
            },
        },
    ]
    context = market_context_adapter("US").normalize(
        assessment_date=SESSION,
        as_of=OBSERVED_AT,
        cutoff=OBSERVED_AT,
        fact_catalog=facts,
    )

    assert context.size_context[0].basis == "equal_weight_price_proxy"
    assert context.sectors[0].name == "금융"
    assert context.deterministic_relations[0].result == 0.41
    assert context.market_flows == []
    assert "us_participant_flow_not_supported" in context.data_gaps


def test_existing_us_acquisition_declares_equal_weight_and_full_sector_set() -> None:
    assert MARKET_SYMBOLS["RSP"] == "style_size"
    assert {
        "XLB",
        "XLC",
        "XLE",
        "XLF",
        "XLI",
        "XLK",
        "XLP",
        "XLRE",
        "XLU",
        "XLV",
        "XLY",
    }.issubset(MARKET_SYMBOLS)


GENERIC_STOCK = """🤖 AI 보조 종목 점검 · US Pilot 1/1

🏢 Core Scientific, Inc.(CORZ)
투자 논리: 유지 · 오늘 중요한 신규 변화 없음
구조적 위험: 보통
시장 기대: 매우 높음

🎯 판단
현재 근거는 핵심 사업 조건의 존재를 보여도 투자 논리의 다음 확인까지 닫지는 못합니다.

🔎 왜 중요한가
현재 근거는 핵심 사업 조건을 보여도 투자 논리의 다음 확인까지 닫지는 못합니다.

📌 다음 확인
• 다음 공식 실적에서 billing 전력, 코로케이션 마진, OCF·PPE CAPEX·FCF를 확인합니다.
"""

CORZ_REFERENCE = """🏢 Core Scientific, Inc.(CORZ)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음

🎯 핵심
Core Scientific은 AI/HPC 데이터센터 코로케이션 중심으로 전환 중입니다.

📌 다음 확인
• billing MW와 코로케이션 마진을 확인합니다.
"""


def test_quality_v2_rejects_generic_duplicate_when_specific_thesis_exists() -> None:
    report = message_quality_v2_report(
        GENERIC_STOCK,
        deterministic_reference=CORZ_REFERENCE,
    )

    assert report["status"] == "FAIL"
    assert report["generic_synthesis_repetition"] == "FAIL"
    assert report["duplicate_substantive_section_claim_count"] == 1


def test_quality_v2_uses_subject_specific_reference_and_removes_duplicate() -> None:
    candidate = build_production_candidate(
        GENERIC_STOCK,
        deterministic_text=CORZ_REFERENCE,
        message_key="stock:CORZ",
        market="us",
        packet_owner="packet:run37",
    )

    assert candidate.eligible is True
    assert candidate.quality_v2 is not None
    assert candidate.quality_v2["status"] == "PASS"
    assert "HPC" in candidate.candidate_text
    assert "현재 근거는 핵심 사업 조건" not in candidate.candidate_text
    assert candidate.quality_v2["duplicate_substantive_section_claim_count"] == 0


def test_supporting_reference_owner_mismatch_fails_closed() -> None:
    candidate = build_production_candidate(
        GENERIC_STOCK,
        deterministic_text=CORZ_REFERENCE.replace("(CORZ)", "(CRCL)"),
        message_key="stock:CORZ",
        market="us",
    )

    assert candidate.eligible is False
    assert any("adaptive_renderer_error" in error for error in candidate.errors)


def test_quality_v2_preserves_one_canonical_supply_owner() -> None:
    source = GENERIC_STOCK.replace(
        "📌 다음 확인\n• 다음 공식 실적에서 billing 전력, 코로케이션 마진, "
        "OCF·PPE CAPEX·FCF를 확인합니다.",
        "📊 수급\n주체별 확인값은 외국인 당일 순매도 10주, 기관 당일 "
        "순매수 10주입니다. 단기 포지셔닝은 사업 실행의 증거가 아닙니다.\n\n"
        "📌 다음 확인\n• 다음 공식 실적에서 billing 전력, 코로케이션 마진, "
        "OCF·PPE CAPEX·FCF를 확인합니다.",
    )
    candidate = build_production_candidate(
        source,
        deterministic_text=CORZ_REFERENCE,
        message_key="stock:CORZ",
        market="kr",
        packet_owner="packet:run38",
    )

    assert candidate.eligible is True
    assert candidate.candidate_text.count("📊 수급") == 1
    assert candidate.candidate_text.count("주체별 확인값") == 1
    assert candidate.candidate_text.count("단기 포지셔닝은 사업 실행의 증거가 아닙니다.") == 1
    assert candidate.quality_v2 is not None
    assert candidate.quality_v2["duplicate_substantive_section_claim_count"] == 0


def test_quality_v2_rejects_duplicate_supply_interpretation() -> None:
    text = GENERIC_STOCK.replace(
        "🔎 왜 중요한가\n현재 근거는 핵심 사업 조건을 보여도 투자 논리의 다음 "
        "확인까지 닫지는 못합니다.",
        "📊 포지셔닝\n단기 수급은 사업 실행의 증거가 아닙니다.",
    ).replace(
        "📌 다음 확인",
        "📊 수급\n외국인 당일 순매도 10주입니다. 단기 수급은 사업 실행의 "
        "증거가 아닙니다.\n\n📌 다음 확인",
    )

    report = message_quality_v2_report(text, deterministic_reference=CORZ_REFERENCE)

    assert report["status"] == "FAIL"
    assert report["duplicate_substantive_section_claim_count"] == 1


def test_inventory_remains_auxiliary_when_primary_thesis_is_available() -> None:
    source = """🤖 AI 보조 종목 점검 · KR Pilot 1/1

🏢 한화에어로스페이스(012450)
투자 논리: 유지 · 오늘 중요한 신규 변화 없음
구조적 위험: 보통
시장 기대: 높음

🎯 판단
재고 관계를 확인합니다.

📈 사업·실적
재고 증가율은 매출 증가율보다 27.1%p 밑돌았습니다.

📌 다음 확인
• 다음 공식 실적에서 지상방산 인도·부문 마진을 확인합니다.
"""
    reference = """🏢 한화에어로스페이스(012450)

🎯 핵심
지상방산 수주잔고가 정상 인도와 높은 수익성으로 전환되는지가 핵심입니다.

📌 다음 확인
• 지상방산 인도와 부문 마진을 확인합니다.
"""

    candidate = build_production_candidate(
        source,
        deterministic_text=reference,
        message_key="stock:012450",
        market="kr",
        packet_owner="packet:run38",
    )

    assert candidate.eligible is True
    judgment = candidate.candidate_text.split("🎯 판단\n", 1)[1].split("\n\n", 1)[0]
    assert "지상방산 수주잔고" in judgment
    assert "재고" not in judgment
