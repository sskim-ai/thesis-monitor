import json
from datetime import datetime, time, timezone

from sqlmodel import Session, select

from app.models.macro import MacroRegimeAssessment, MacroThesis, MacroThesisEvidence


DEFAULT_MACRO_THESES = [
    {
        "thesis_key": "us_soft_landing_disinflation",
        "title": "미국 연착륙과 점진적 디스인플레이션",
        "description": "미국 성장이 침체 없이 완만해지고 물가 압력이 점진적으로 둔화한다.",
        "region": "US",
        "expected_evidence": ["물가 압력 둔화", "성장 급락 회피", "신용스프레드 안정"],
        "weakening_evidence": ["서비스 물가 재가속", "고용 급락", "신용스트레스 확대"],
        "kill_conditions": ["침체와 신용경색 동시 발생", "기조적 물가 재가속의 지속"],
        "valuation_channels": ["discount_rate", "demand", "credit"],
        "affected_assets": ["SPY", "QQQ", "IWM"],
    },
    {
        "thesis_key": "fed_policy_path",
        "title": "연준 정책경로와 장기 실질금리",
        "description": "인플레이션과 성장 둔화에 맞춰 연준 긴축 강도가 점진적으로 낮아진다.",
        "region": "US",
        "expected_evidence": ["실질금리 안정", "기대인플레이션 안정"],
        "weakening_evidence": ["실질금리 급등", "달러와 신용스프레드 동반 상승"],
        "kill_conditions": ["금융여건의 구조적 재긴축"],
        "valuation_channels": ["discount_rate", "funding", "liquidity"],
        "affected_assets": ["QQQ", "IWM", "XLF"],
    },
    {
        "thesis_key": "ai_capex_cycle",
        "title": "AI CAPEX와 반도체 수요",
        "description": "Hyperscaler의 AI 인프라 투자가 반도체와 데이터센터 수요를 지지한다.",
        "region": "global",
        "expected_evidence": ["빅테크 CAPEX 유지", "반도체 실적과 가이던스 개선"],
        "weakening_evidence": ["CAPEX 가이던스 하향", "재고와 공급과잉 확대"],
        "kill_conditions": ["주요 hyperscaler의 동시 CAPEX 축소"],
        "valuation_channels": ["capex", "demand", "earnings"],
        "affected_assets": ["NVDA", "SOXX", "000660"],
    },
    {
        "thesis_key": "china_korea_export_cycle",
        "title": "중국 경기와 한국 수출 사이클",
        "description": "중국 수요와 글로벌 교역 회복이 한국 수출 및 제조업을 지지한다.",
        "region": "CN_KR",
        "expected_evidence": ["한국 수출 개선", "중국 산업수요 회복"],
        "weakening_evidence": ["수출 둔화", "중국 제조업과 원자재 수요 약화"],
        "kill_conditions": ["한국 수출과 중국 수요의 구조적 동반 하락"],
        "valuation_channels": ["demand", "fx", "inventory"],
        "affected_assets": ["EWY", "000660"],
    },
    {
        "thesis_key": "oil_supply_shock",
        "title": "유가와 공급충격",
        "description": "유가 변동을 수요 회복과 공급 차질로 구분해 비용 및 물가 영향을 평가한다.",
        "region": "global",
        "expected_evidence": ["재고와 생산 데이터가 가격 방향을 설명"],
        "weakening_evidence": ["유가와 신용스트레스 동반 급등"],
        "kill_conditions": ["지속적 공급차질로 스태그플레이션 위험 현실화"],
        "valuation_channels": ["cost", "pricing", "inflation"],
        "affected_assets": ["XLE", "airlines", "chemicals"],
    },
]


def ensure_default_macro_theses(session: Session) -> list[MacroThesis]:
    rows: list[MacroThesis] = []
    for definition in DEFAULT_MACRO_THESES:
        thesis = session.exec(
            select(MacroThesis)
            .where(MacroThesis.thesis_key == definition["thesis_key"])
            .order_by(MacroThesis.version.desc())
        ).first()
        if thesis is None:
            thesis = MacroThesis(
                thesis_key=str(definition["thesis_key"]),
                title=str(definition["title"]),
                description=str(definition["description"]),
                region=str(definition["region"]),
                expected_evidence=json.dumps(definition["expected_evidence"], ensure_ascii=False),
                weakening_evidence=json.dumps(
                    definition["weakening_evidence"], ensure_ascii=False
                ),
                kill_conditions=json.dumps(definition["kill_conditions"], ensure_ascii=False),
                valuation_channels=json.dumps(
                    definition["valuation_channels"], ensure_ascii=False
                ),
                affected_assets=json.dumps(definition["affected_assets"], ensure_ascii=False),
            )
            session.add(thesis)
            session.commit()
            session.refresh(thesis)
        rows.append(thesis)
    return rows


def update_macro_theses(
    session: Session,
    regime: MacroRegimeAssessment,
) -> list[MacroThesis]:
    theses = ensure_default_macro_theses(session)
    now = datetime.now(timezone.utc)
    reviewed_at = datetime.combine(regime.assessment_date, time.min, tzinfo=timezone.utc)
    for thesis in theses:
        old_confidence = thesis.confidence
        already_reviewed_today = (
            thesis.last_reviewed_at is not None
            and thesis.last_reviewed_at.date() == regime.assessment_date
        )
        if thesis.thesis_key == "us_soft_landing_disinflation":
            if (
                regime.growth_momentum >= 1
                and regime.inflation_pressure <= 0
            ) or (
                regime.growth_momentum >= 0
                and regime.inflation_pressure <= -1
            ):
                delta = 1
            elif regime.growth_momentum <= -1 or regime.inflation_pressure >= 1:
                delta = -1
            else:
                delta = 0
        elif thesis.thesis_key == "fed_policy_path":
            delta = int(regime.financial_conditions >= 1) - int(
                regime.financial_conditions <= -1
            )
        elif thesis.thesis_key == "ai_capex_cycle":
            delta = regime.earnings_momentum
        elif thesis.thesis_key == "china_korea_export_cycle":
            delta = regime.growth_momentum
        else:
            delta = -1 if regime.inflation_pressure >= 2 else 0
        today_signal = "positive" if delta > 0 else "negative" if delta < 0 else "neutral"
        rationale = {
            "us_soft_landing_disinflation": (
                f"성장 {regime.growth_momentum:+d}, 물가 {regime.inflation_pressure:+d}. "
                "당일 신호이며 공식 성장·물가 데이터의 지속 확인 전에는 상태를 바꾸지 않습니다."
            ),
            "fed_policy_path": (
                f"금융여건 {regime.financial_conditions:+d}. 당일 금리·스프레드 움직임은 "
                "정책경로의 영구 변화가 아니라 오늘 신호로 분리합니다."
            ),
            "ai_capex_cycle": (
                f"반도체 가격 기반 단기 신호 {regime.earnings_momentum:+d}. 실제 CAPEX, 주문, "
                "HBM 출하 또는 이익 추정치 변화가 확인되지 않으면 시장 가정은 유지합니다."
            ),
            "china_korea_export_cycle": (
                f"가격 기반 성장 신호 {regime.growth_momentum:+d}. 공식 수출·생산 데이터의 "
                "반복 확인 전에는 시장 가정 상태를 바꾸지 않습니다."
            ),
            "oil_supply_shock": (
                f"물가·유가 기반 당일 신호 {regime.inflation_pressure:+d}. 재고·생산 자료로 "
                "공급 충격의 지속성이 확인돼야 상태를 변경합니다."
            ),
        }[thesis.thesis_key]
        independent_evidence = session.exec(
            select(MacroThesisEvidence).where(
                MacroThesisEvidence.macro_thesis_id == thesis.id,
                MacroThesisEvidence.persistence != "temporary",
                MacroThesisEvidence.confidence >= 0.6,
            )
        ).all()
        independent_keys = {
            (item.observation_id, item.event_id)
            for item in independent_evidence
            if item.observation_id is not None or item.event_id is not None
        }
        persistent_signal = len(independent_keys) >= 2 and not regime.provisional
        confidence_delta = (
            0
            if already_reviewed_today or not persistent_signal
            else delta * 0.03
        )
        thesis.confidence = round(
            max(0.05, min(0.95, old_confidence + confidence_delta)), 2
        )
        if thesis.confidence < 0.2 and delta < 0 and persistent_signal:
            thesis.status = "structural_break"
        elif delta < 0 and persistent_signal:
            thesis.status = "weakening"
        elif delta > 0 and persistent_signal:
            thesis.status = "strengthening"
        elif not persistent_signal:
            thesis.status = "intact"
        thesis.today_signal = today_signal
        thesis.today_signal_rationale = rationale
        thesis.today_signal_date = regime.assessment_date
        thesis.last_reviewed_at = reviewed_at
        thesis.updated_at = now
        session.add(thesis)
    session.commit()
    return theses
