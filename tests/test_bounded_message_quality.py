from __future__ import annotations

from copy import deepcopy

from app.services.free_analyst_message_service import (
    cross_message_synthesis_specificity_report,
    entity_specific_synthesis_report,
)
from app.services.free_analyst_production_integration_service import (
    build_production_candidate,
    select_limited_canary,
)
from app.services.kr_market_digest_quality_service import (
    build_kr_market_digest_plan,
    kr_domestic_context_richness,
)


def _kr_context() -> dict[str, object]:
    return {
        "contract_version": "market-context-adapter-v1",
        "market": "KR",
        "assessment_date": "2026-08-25",
        "session_date": "2026-08-25",
        "as_of": "2026-08-26T00:18:27+09:00",
        "cutoff": "2026-08-26T00:18:27+09:00",
        "indices": [
            {
                "symbol": "KOSPI",
                "name": "KOSPI",
                "close": 6742.74,
                "return_pct": 0.68,
                "basis": "official_or_provider_index",
                "as_of_date": "2026-08-25",
                "source_ref": "index:kospi",
            },
            {
                "symbol": "KOSDAQ",
                "name": "KOSDAQ",
                "close": 827.15,
                "return_pct": 1.70,
                "basis": "official_or_provider_index",
                "as_of_date": "2026-08-25",
                "source_ref": "index:kosdaq",
            },
        ],
        "breadth": {
            "availability": "AVAILABLE",
            "advancers": 1833,
            "decliners": 692,
            "unchanged": 108,
            "eligible_count": 2633,
            "breadth_ratio": 0.7259,
            "source_refs": ["breadth:all"],
        },
        "breadth_by_scope": [
            {
                "scope": "KOSPI",
                "breadth": {
                    "availability": "AVAILABLE",
                    "advancers": 647,
                    "decliners": 226,
                    "unchanged": 34,
                    "eligible_count": 907,
                    "breadth_ratio": 0.7411,
                    "source_refs": ["breadth:kospi"],
                },
            },
            {
                "scope": "KOSDAQ",
                "breadth": {
                    "availability": "AVAILABLE",
                    "advancers": 1186,
                    "decliners": 466,
                    "unchanged": 74,
                    "eligible_count": 1726,
                    "breadth_ratio": 0.7179,
                    "source_refs": ["breadth:kosdaq"],
                },
            },
        ],
        "size_context": [
            {
                "name": "대형주",
                "return_pct": 0.62,
                "basis": "official_size_index",
                "as_of_date": "2026-08-25",
                "source_ref": "size:large",
            },
            {
                "name": "중형주",
                "return_pct": 1.37,
                "basis": "official_size_index",
                "as_of_date": "2026-08-25",
                "source_ref": "size:medium",
            },
            {
                "name": "소형주",
                "return_pct": 1.54,
                "basis": "official_size_index",
                "as_of_date": "2026-08-25",
                "source_ref": "size:small",
            },
        ],
        "sectors": [],
        "market_flows": [
            {
                "participant": actor,
                "net_flow": amount,
                "unit": "KRW",
                "scope": scope,
                "as_of_date": "2026-08-25",
                "source_ref": f"flow:{scope}:{actor}",
            }
            for scope, actor, amount in (
                ("KOSPI", "foreign", -4_000_100_000_000),
                ("KOSPI", "institution", 1_252_100_000_000),
                ("KOSPI", "retail", 1_158_500_000_000),
                ("KOSDAQ", "foreign", 136_100_000_000),
                ("KOSDAQ", "institution", 21_100_000_000),
                ("KOSDAQ", "retail", -147_200_000_000),
            )
        ],
        "concentration": [],
        "deterministic_relations": [],
        "session_context": {
            "role": "pre_market",
            "assessment_state": "final",
            "market_date": "2026-08-26",
            "latest_completed_regular_session_date": "2026-08-25",
            "timezone": "Asia/Seoul",
            "provider_publication_state": "PROVIDER_COMPLETE",
        },
        "official_event_sources": ["KRX"],
        "data_gaps": [],
    }


KR_MARKET_SOURCE = """🤖 AI 보조 한국시장 마감 · KR Pilot 1/1

🎯 현재 시장 한 줄
미국 반도체 상대 약세에도 국내 시장의 폭은 강했습니다.

🧭 시장 구조
KOSDAQ이 KOSPI보다 강했고 양 시장 모두 상승 종목 우위였습니다.

📌 다음 확인
• 다음 반도체와 S&P500 상대수익률을 확인합니다.
"""

KR_MARKET_REFERENCE = """🌎 한국시장 마감

📈 중요한 변화
• KOSDAQ과 KOSPI가 상승했습니다.

🧭 투자적 의미
미국 반도체 약세가 국내 위험자산을 압박할 수 있습니다.

📌 다음 확인
• 다음 반도체 상대수익률을 확인합니다.
"""


def test_kr_domestic_richness_requires_typed_session_indices_breadth_and_context() -> None:
    rich = kr_domestic_context_richness(_kr_context())
    assert rich.status is True
    assert rich.completed_session is True
    assert rich.kospi_kosdaq_indices is True
    assert rich.kospi_kosdaq_breadth is True

    incomplete = deepcopy(_kr_context())
    incomplete["breadth_by_scope"] = incomplete["breadth_by_scope"][:1]
    assert kr_domestic_context_richness(incomplete).status is False


def test_kr_rich_digest_keeps_judgment_interpretation_and_next_check_local_first() -> None:
    candidate = build_production_candidate(
        KR_MARKET_SOURCE,
        deterministic_text=KR_MARKET_REFERENCE,
        message_key="market:kr-rich",
        market="kr",
        packet_owner="packet:kr-rich",
        is_market_digest=True,
        market_context={"adapter_context": _kr_context()},
    )

    assert candidate.eligible is True
    assert "KOSDAQ이 KOSPI보다 강했고" in candidate.candidate_text
    assert "외국인은 KOSPI에서 순매도하고 KOSDAQ에서 순매수" in candidate.candidate_text
    assert "기관은 양 시장에서 순매수" in candidate.candidate_text
    assert "상승 종목 우위가 유지되는지" in candidate.candidate_text
    assert "S&P500 상대수익률" not in candidate.candidate_text
    quality = candidate.quality_v2["kr_market_digest"]
    assert quality["richness"]["status"] is True
    assert quality["local_first"] == "PASS"


def test_kr_global_contradiction_is_typed_but_does_not_displace_local_priority() -> None:
    plan = build_kr_market_digest_plan(
        _kr_context(),
        available_text="미국 반도체 상대 약세가 이어졌습니다.",
    )
    assert plan.global_context_retained is True
    assert plan.judgment.priority.value.startswith("P1_")
    assert plan.interpretation.priority.value.startswith("P2_")
    assert plan.next_check.priority.value.startswith("P2_")
    assert plan.concentration_scopes_used == ()


def _stock_message(core: str, next_check: str) -> str:
    return f"""🤖 AI 보조 종목 점검 · US Pilot 1/1

🏢 Example Corp.(EX)
투자 논리: 유지 · 오늘 중요한 신규 변화 없음
구조적 위험: 보통
시장 기대: 매우 높음

🎯 핵심 판단
{core}

📈 사업·실적
현재 사업 수치는 다음 공식 자료에서 확인합니다.

📌 다음 확인
• {next_check}
"""


def _reference(core: str, next_check: str) -> str:
    return f"""🏢 Example Corp.(EX)

투자 논리: 유지 · 오늘 중요한 신규 변화 없음
구조적 위험: 보통
시장 기대: 매우 높음

🎯 핵심
{core}

📌 다음 확인
• {next_check}
"""


def test_tsm_style_foundry_support_cannot_inherit_hpc_transition_synthesis() -> None:
    source = _stock_message(
        "첨단공정 수요와 마진 방향을 확인해야 합니다.",
        "첨단공정 가동률과 wafer ASP를 확인합니다.",
    )
    reference = _reference(
        "첨단공정 지배력과 가동률이 gross margin을 지지하며 해외 팹 비용에 따른 마진 희석이 핵심 변수다.",
        "첨단공정 가동률과 wafer ASP를 확인합니다.",
    )
    candidate = build_production_candidate(
        source,
        deterministic_text=reference,
        message_key="stock:foundry",
        market="us",
    )

    assert candidate.eligible is True
    assert candidate.result.analysis.industry_context_owner == "semiconductor_foundry"
    assert "첨단공정" in candidate.candidate_text
    assert "HPC 실행" not in candidate.candidate_text


def test_same_industry_candidates_retain_distinct_supported_drivers() -> None:
    fixtures = (
        ("HPC billing 전력과 코로케이션 마진", "billing 전력과 코로케이션 마진"),
        ("전력 인입과 준공·가동·NOI", "준공 일정과 NOI"),
        ("HPC lease revenue와 가동 MW", "HPC lease revenue와 가동 MW"),
    )
    candidates = [
        build_production_candidate(
            _stock_message(f"{driver}의 전환 확인이 필요합니다.", check),
            deterministic_text=_reference(
                f"{driver}가 사업 실행을 구분하는 핵심 근거다.",
                check,
            ),
            message_key=f"stock:hpc-{index}",
            market="us",
        )
        for index, (driver, check) in enumerate(fixtures, start=1)
    ]
    selection = select_limited_canary(candidates)

    assert all(candidate.eligible for candidate in candidates)
    assert selection.specificity_audit["status"] == "PASS"
    assert selection.specificity_audit["cross_industry_generic_repetition_count"] == 0
    assert len({candidate.candidate_text for candidate in candidates}) == 3


def test_cross_industry_generic_repetition_fails_but_same_industry_overlap_passes() -> None:
    generic = "현재 근거는 핵심 사업 조건을 보여도 다음 확인까지 닫지는 못합니다."
    failed = cross_message_synthesis_specificity_report(
        [
            {
                "message_key": "stock:a",
                "industry_owner": "hpc_data_center",
                "specific_support_available": True,
                "text": _stock_message(generic, "billing 전력을 확인합니다."),
            },
            {
                "message_key": "stock:b",
                "industry_owner": "semiconductor_foundry",
                "specific_support_available": True,
                "text": _stock_message(generic, "wafer ASP를 확인합니다."),
            },
        ]
    )
    assert failed["status"] == "FAIL"
    assert failed["rejected_message_keys"] == ["stock:a", "stock:b"]

    leaked_hpc = cross_message_synthesis_specificity_report(
        [
            {
                "message_key": "stock:hpc",
                "industry_owner": "hpc_data_center",
                "specific_support_available": True,
                "supported_discriminators": ["hpc_transition"],
                "text": _reference(
                    "현재 근거로는 HPC 실행과 현금 전환을 더 확인해야 합니다.",
                    "billing 전력을 확인합니다.",
                ),
            },
            {
                "message_key": "stock:foundry",
                "industry_owner": "semiconductor_foundry",
                "specific_support_available": True,
                "supported_discriminators": ["foundry_advanced_node"],
                "text": _reference(
                    "현재 근거로는 HPC 실행과 현금 전환을 더 확인해야 합니다.",
                    "첨단공정 가동률을 확인합니다.",
                ),
            },
        ]
    )
    assert leaked_hpc["status"] == "FAIL"
    assert leaked_hpc["rejected_message_keys"] == ["stock:foundry"]

    shared = "현재 근거로는 HPC 실행과 가동·청구의 연결을 더 확인해야 합니다."
    passed = cross_message_synthesis_specificity_report(
        [
            {
                "message_key": "stock:a",
                "industry_owner": "hpc_data_center",
                "specific_support_available": True,
                "text": _stock_message(shared, "billing 전력을 확인합니다."),
            },
            {
                "message_key": "stock:b",
                "industry_owner": "hpc_data_center",
                "specific_support_available": True,
                "text": _stock_message(shared, "가동 MW를 확인합니다."),
            },
        ]
    )
    assert passed["status"] == "PASS"
    assert passed["same_industry_acceptable_overlap_count"] == 1


def test_specificity_gate_does_not_accept_external_driver_injection() -> None:
    report = entity_specific_synthesis_report(
        _stock_message(
            "첨단공정 가동률이 핵심입니다.",
            "wafer ASP를 확인합니다.",
        ),
        support_text=_reference(
            "billing 전력과 코로케이션 마진이 핵심입니다.",
            "billing 전력을 확인합니다.",
        ),
        selected_renderer="DIRECT_ANALYST",
    )
    assert report["status"] == "FAIL"
    assert report["covered_discriminators"] == []
