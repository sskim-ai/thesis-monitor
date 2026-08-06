import json
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.macro import MacroRegimeAssessment, MacroThesis


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
    for thesis in theses:
        old_confidence = thesis.confidence
        if thesis.thesis_key == "us_soft_landing_disinflation":
            delta = int(regime.growth_momentum >= -1) + int(regime.inflation_pressure <= 0) - 1
        elif thesis.thesis_key == "fed_policy_path":
            delta = int(regime.financial_conditions >= 0) - int(regime.financial_conditions <= -1)
        elif thesis.thesis_key == "ai_capex_cycle":
            delta = regime.earnings_momentum
        elif thesis.thesis_key == "china_korea_export_cycle":
            delta = regime.growth_momentum
        else:
            delta = -1 if regime.inflation_pressure >= 2 else 0
        thesis.confidence = round(max(0.05, min(0.95, old_confidence + delta * 0.05)), 2)
        if thesis.confidence >= 0.7:
            thesis.status = "strengthening"
        elif thesis.confidence >= 0.4:
            thesis.status = "intact"
        elif thesis.confidence >= 0.2:
            thesis.status = "weakening"
        else:
            thesis.status = "structural_break"
        thesis.last_reviewed_at = now
        thesis.updated_at = now
        session.add(thesis)
    session.commit()
    return theses
