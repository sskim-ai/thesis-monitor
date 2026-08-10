from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlmodel import Session, select

from app.models.event import Event
from app.models.macro import MacroBriefing, MacroEvent, ThesisMacroImpact
from app.models.thesis import InvestmentThesis, MonitorRun, ThesisAssessment
from app.models.watchlist import WatchlistItem


@dataclass(frozen=True)
class SignificanceThresholds:
    sp500_pct: float = 1.0
    nasdaq_relative_pp: float = 0.4
    soxx_relative_pp: float = 0.5
    us10y_bp: float = 5.0
    real_yield_bp: float = 3.0
    vix_pct: float = 5.0
    usdkrw_pct: float = 0.7
    wti_pct: float = 2.0


SIGNIFICANCE = SignificanceThresholds()
USABLE_QUALITY = {"fresh", "revised"}

SERIES_LABELS = {
    "SPY": "S&P500",
    "QQQ": "Nasdaq",
    "IWM": "Russell 2000",
    "SOXX": "반도체",
    "DGS10": "미국 10년물 금리",
    "DFII10": "미국 10년물 실질금리",
    "T10YIE": "미국 기대인플레이션",
    "BAMLH0A0HYM2": "미국 하이일드 신용스프레드",
    "DTWEXBGS": "미 달러지수(광의)",
    "USDKRW": "원/달러 환율",
    "DCOILWTICO": "WTI 유가",
    "VIXCLS": "VIX",
}

STATUS_LABELS = {
    "strengthened": "강화",
    "no_material_change": "유지",
    "needs_review": "검토 중",
    "mixed": "혼재",
    "weakened": "약화",
    "invalidation_candidate": "무효화 후보",
    "invalidated": "무효화",
}

EXPECTATION_LABELS = {
    "depressed": "매우 낮음",
    "low": "낮음",
    "balanced": "적정",
    "elevated": "높음",
    "very_high": "매우 높음",
    "speculative": "투기적",
    "unknown": "판단 자료 부족",
}

VALUATION_LABELS = {
    "expansion": "확장",
    "neutral": "중립",
    "mixed": "혼재",
    "compression": "압축",
    "unknown": "판단 자료 부족",
}


@dataclass(frozen=True)
class MacroInterpretation:
    regime_label: str
    confidence: float
    one_line: str
    key_changes: list[str]
    axis_explanations: list[tuple[str, str]]
    integrated_view: list[str]
    market_assumptions: list[str]


@dataclass(frozen=True)
class TickerDailySummary:
    ticker: str
    company_name: str
    status: str
    display_reason: str
    expectation_level: str
    valuation: str
    earnings_impact: str
    summary: str
    confirmed_facts: list[str]
    current_warning: str
    macro_paths: list[str]
    check_metrics: list[str]
    new_observer_view: str
    holder_view: str
    priority: tuple[int, int, int, str]


@dataclass(frozen=True)
class PortfolioSummary:
    thesis_counts: dict[str, int]
    valuation_counts: dict[str, int]
    tickers: list[TickerDailySummary]
    focus_tickers: list[TickerDailySummary]


@dataclass(frozen=True)
class ScheduleSummary:
    today: list[str] = field(default_factory=list)
    next_seven_days: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DataQualitySummary:
    items: list[str] = field(default_factory=list)
    conclusion: str = ""


@dataclass(frozen=True)
class DailyDigest:
    digest_date: date
    macro: MacroInterpretation
    portfolio: PortfolioSummary
    schedule: ScheduleSummary
    data_quality: DataQualitySummary


def _json(value: str, fallback: object) -> object:
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return fallback
    return parsed


def _dict(value: str) -> dict[str, object]:
    parsed = _json(value, {})
    return parsed if isinstance(parsed, dict) else {}


def _list(value: str) -> list[object]:
    parsed = _json(value, [])
    return parsed if isinstance(parsed, list) else []


def _text_list(value: str) -> list[str]:
    return [str(item) for item in _list(value) if str(item).strip()]


def _observation_map(briefing: MacroBriefing) -> dict[str, dict[str, object]]:
    market = _dict(briefing.market_summary)
    values = market.get("observations", [])
    if not isinstance(values, list):
        return {}
    return {
        str(item["series_code"]): item
        for item in values
        if isinstance(item, dict) and item.get("series_code")
    }


def _usable(item: dict[str, object] | None) -> bool:
    return bool(item and str(item.get("quality_status", "fresh")) in USABLE_QUALITY)


def _number(item: dict[str, object] | None, key: str) -> float | None:
    if not _usable(item):
        return None
    value = item.get(key) if item else None
    return float(value) if isinstance(value, (int, float)) else None


def _bp(item: dict[str, object] | None) -> float | None:
    value = _number(item, "change_value")
    return value * 100 if value is not None else None


def _direction(value: float, positive: str, negative: str) -> str:
    return positive if value > 0 else negative


def _important_changes(
    observations: dict[str, dict[str, object]],
) -> list[str]:
    spy = _number(observations.get("SPY"), "change_pct")
    qqq = _number(observations.get("QQQ"), "change_pct")
    soxx = _number(observations.get("SOXX"), "change_pct")
    nominal = _bp(observations.get("DGS10"))
    real = _bp(observations.get("DFII10"))
    vix = _number(observations.get("VIXCLS"), "change_pct")
    usdkrw = _number(observations.get("USDKRW"), "change_pct")
    oil = _number(observations.get("DCOILWTICO"), "change_pct")
    candidates: list[tuple[float, bool, str]] = []

    if spy is not None:
        candidates.append(
            (
                abs(spy) / SIGNIFICANCE.sp500_pct,
                abs(spy) >= SIGNIFICANCE.sp500_pct,
                f"S&P500이 {spy:+.1f}% 움직여 시장 전반의 위험선호가 "
                f"{_direction(spy, '개선됐습니다.', '약해졌습니다.')}",
            )
        )
    if spy is not None and qqq is not None:
        gap = qqq - spy
        candidates.append(
            (
                abs(gap) / SIGNIFICANCE.nasdaq_relative_pp,
                abs(gap) >= SIGNIFICANCE.nasdaq_relative_pp,
                f"Nasdaq이 S&P500을 {abs(gap):.1f}%p "
                f"{_direction(gap, '웃돌아 성장주 상대강도가 확인됐습니다.', '밑돌아 성장주 주도력이 약했습니다.')}",
            )
        )
    if spy is not None and soxx is not None:
        gap = soxx - spy
        candidates.append(
            (
                abs(gap) / SIGNIFICANCE.soxx_relative_pp,
                abs(gap) >= SIGNIFICANCE.soxx_relative_pp,
                f"반도체가 S&P500을 {abs(gap):.1f}%p "
                f"{_direction(gap, '웃돌았습니다.', '밑돌았습니다.')} "
                "가격 반응은 수요 심리 신호일 뿐, 실제 AI CAPEX 투자 논리 변화는 주문과 실적으로 확인해야 합니다.",
            )
        )
    if nominal is not None:
        candidates.append(
            (
                abs(nominal) / SIGNIFICANCE.us10y_bp,
                abs(nominal) >= SIGNIFICANCE.us10y_bp,
                f"미국 10년물 금리가 {nominal:+.0f}bp 움직여 "
                f"{_direction(nominal, '장기 자산 할인율에 부담을 더했습니다.', '장기 자산 할인율 부담을 낮췄습니다.')}",
            )
        )
    if real is not None:
        candidates.append(
            (
                abs(real) / SIGNIFICANCE.real_yield_bp,
                abs(real) >= SIGNIFICANCE.real_yield_bp,
                f"미국 실질금리가 {real:+.0f}bp 움직였습니다. "
                f"{_direction(real, '기업 수요와 별개로 성장주 멀티플에는 부정적입니다.', '성장주 멀티플에는 우호적입니다.')}",
            )
        )
    if vix is not None:
        candidates.append(
            (
                abs(vix) / SIGNIFICANCE.vix_pct,
                abs(vix) >= SIGNIFICANCE.vix_pct,
                f"VIX가 {vix:+.1f}% 움직여 단기 위험회피가 "
                f"{_direction(vix, '커졌습니다.', '완화됐습니다.')}",
            )
        )
    if usdkrw is not None:
        candidates.append(
            (
                abs(usdkrw) / SIGNIFICANCE.usdkrw_pct,
                abs(usdkrw) >= SIGNIFICANCE.usdkrw_pct,
                f"원/달러 환율이 {usdkrw:+.1f}% 움직여 국내 수입비용과 외국인 수급의 환율 경로를 점검해야 합니다.",
            )
        )
    if oil is not None:
        candidates.append(
            (
                abs(oil) / SIGNIFICANCE.wti_pct,
                abs(oil) >= SIGNIFICANCE.wti_pct,
                f"WTI가 {oil:+.1f}% 움직여 물가와 운송·에너지 업종의 비용·가격 경로에 영향을 줬습니다.",
            )
        )

    candidates.sort(key=lambda item: (-item[0], item[2]))
    selected = [text for _score, significant, text in candidates if significant][:4]
    if len(selected) < 2:
        selected.extend(
            text
            for _score, _significant, text in candidates
            if text not in selected
        )
    return selected[:4]


def _axis_explanations(
    regime: dict[str, object], observations: dict[str, dict[str, object]]
) -> list[tuple[str, str]]:
    def score(key: str) -> int:
        value = regime.get(key, 0)
        return int(value) if isinstance(value, (int, float)) else 0

    growth = score("growth_momentum")
    inflation = score("inflation_pressure")
    liquidity = score("liquidity_condition")
    financial = score("financial_conditions")
    risk = score("risk_appetite")
    earnings = score("earnings_momentum")

    growth_text = (
        "소형주와 경기민감 신호가 함께 개선돼 경기 기대가 우호적입니다."
        if growth > 0
        else "경기민감 신호가 약해져 성장 둔화 가능성을 확인해야 합니다."
        if growth < 0
        else "경기 개선이나 둔화를 확정할 신호가 부족해 방향 판단을 유지합니다."
    )
    inflation_text = (
        "유가와 기대인플레이션이 물가 부담 쪽으로 움직여 금리 경로에 불리합니다."
        if inflation > 0
        else "물가 압력이 완화되는 신호가 있어 금리 부담을 낮추는 방향입니다."
        if inflation < 0
        else "물가 재가속과 빠른 안정 중 어느 방향도 뚜렷하지 않습니다."
    )
    liquidity_text = (
        "달러 흐름이 글로벌 위험자산 유동성에 우호적인 방향입니다."
        if liquidity > 0
        else "달러 흐름이 글로벌 위험자산 유동성에 부담을 주는 방향입니다."
        if liquidity < 0
        else "글로벌 유동성 방향을 바꿀 뚜렷한 달러 신호가 없습니다."
    )
    financial_text = (
        "금리와 신용비용 조합이 완화돼 자금조달과 멀티플에 우호적입니다."
        if financial > 0
        else "금리 또는 신용비용이 올라 성장주와 차입 의존 기업의 Valuation에 부담입니다."
        if financial < 0
        else "금리와 신용시장 전반이 금융여건 변화를 확정할 정도로 움직이지 않았습니다."
    )
    risk_text = (
        "주가와 변동성 조합이 위험자산을 받아들이는 흐름을 가리킵니다."
        if risk > 0
        else "주가와 변동성 조합이 위험회피 확대를 가리킵니다."
        if risk < 0
        else "주가와 변동성 신호가 엇갈려 위험선호 방향이 분명하지 않습니다."
    )
    earnings_text = (
        "반도체 가격 반응은 긍정적이지만 실제 기업 이익 추정치 상향과는 구분합니다."
        if earnings > 0
        else "반도체 가격 반응이 약해 이익 기대의 추가 확인이 필요합니다."
        if earnings < 0
        else "실제 이익 추정치 방향을 바꿀 새로운 확인 자료가 부족합니다."
    )
    if not _usable(observations.get("DTWEXBGS")):
        liquidity_text = "달러 데이터가 오래됐거나 없어 오늘 글로벌 유동성 방향은 판단을 유보합니다."
    return [
        ("경기", growth_text),
        ("물가", inflation_text),
        ("유동성", liquidity_text),
        ("금융여건", financial_text),
        ("위험선호", risk_text),
        ("기업이익", earnings_text),
    ]


def _macro_interpretation(briefing: MacroBriefing) -> MacroInterpretation:
    regime = _dict(briefing.regime_summary)
    observations = _observation_map(briefing)
    risk = int(regime.get("risk_appetite", 0) or 0)
    financial = int(regime.get("financial_conditions", 0) or 0)
    growth = int(regime.get("growth_momentum", 0) or 0)
    if risk > 0 and financial < 0:
        one_line = "위험선호는 개선됐지만 금리·신용 여건은 성장주 Valuation에 부담인 혼합 시장입니다."
    elif risk > 0:
        one_line = "위험자산 선호가 개선됐으며 실적 근거가 있는 종목에 상대적으로 우호적인 시장입니다."
    elif risk < 0:
        one_line = "위험회피가 커져 높은 기대와 약한 현금흐름을 가진 종목의 변동성에 주의할 환경입니다."
    elif financial < 0:
        one_line = "지수 방향은 뚜렷하지 않지만 할인율 부담이 커져 높은 멀티플 종목에 불리한 환경입니다."
    else:
        one_line = "시장 방향이 엇갈려 가격 움직임보다 기업별 실적과 현금흐름 근거를 우선 확인할 환경입니다."

    integrated = [
        (
            "현재는 경기 확장 하나로 모든 위험자산이 오르는 시장이라기보다, "
            "위험선호와 할인율 신호가 함께 가격을 결정하는 시장입니다."
            if growth <= 0 or financial <= 0
            else "성장과 금융여건이 함께 지지되는 환경이지만 지속성은 실제 기업 실적으로 확인해야 합니다."
        ),
        (
            "실적이 실제로 개선되는 기업에는 상대적으로 우호적이지만, 높은 기대와 멀티플 확장에 "
            "의존하는 종목은 금리와 현금흐름을 함께 확인해야 합니다."
        ),
    ]
    theses = _list(briefing.macro_theses)
    assumptions: list[str] = []
    for item in theses[:5]:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "intact"))
        status_label = {
            "strengthening": "강화",
            "intact": "유지",
            "weakening": "약화",
            "structural_break": "구조적 재검토",
        }.get(status, status)
        signal = int(item.get("daily_signal", 0) or 0)
        key = str(item.get("thesis_key", ""))
        if key == "fed_policy_path":
            real_bp = _bp(observations.get("DFII10"))
            reason = (
                f"실질금리 {real_bp:+.0f}bp가 할인율에 부담"
                if real_bp is not None and real_bp > 0
                else f"실질금리 {real_bp:+.0f}bp가 할인율 부담을 완화"
                if real_bp is not None and real_bp < 0
                else "금리 경로를 바꿀 신규 확정 근거 없음"
            )
        elif key == "ai_capex_cycle":
            reason = (
                "반도체 가격 신호는 우호적이나 실제 CAPEX·주문 확인 전 강화하지 않음"
                if signal > 0
                else "실제 CAPEX·주문을 바꿀 신규 확정 근거 없음"
                if signal == 0
                else "반도체 신호 약화, 실제 주문과 이익 추정치 확인 필요"
            )
        elif key == "us_soft_landing_disinflation":
            reason = (
                "성장 급락과 물가 재가속의 동시 신호가 없음"
                if signal >= 0
                else "성장 둔화 또는 물가 재가속 경고가 확인됨"
            )
        elif key == "china_korea_export_cycle":
            reason = "한국 수출과 중국 실물지표를 바꿀 신규 확정 근거 없음"
        elif key == "oil_supply_shock":
            oil = _number(observations.get("DCOILWTICO"), "change_pct")
            reason = (
                f"WTI {oil:+.1f}%이나 공급충격 확정 수준은 아님"
                if oil is not None
                else "유가 공급충격을 판단할 신규 가격 변화 없음"
            )
        else:
            reason = "오늘 확인 신호가 우호적" if signal > 0 else "오늘 경고 신호가 확인됨" if signal < 0 else "방향을 바꿀 신규 확정 근거 없음"
        assumptions.append(f"{item.get('title', '시장 가정')} → {status_label} · {reason}")

    return MacroInterpretation(
        regime_label={
            "goldilocks": "골디락스",
            "stagflation_risk": "스태그플레이션 위험",
            "recession_risk": "경기침체 위험",
            "liquidity_risk_on": "유동성 주도 위험선호",
            "mixed": "혼합",
        }.get(str(regime.get("label", "mixed")), str(regime.get("label", "혼합"))),
        confidence=float(regime.get("confidence", 0) or 0),
        one_line=one_line,
        key_changes=_important_changes(observations),
        axis_explanations=_axis_explanations(regime, observations),
        integrated_view=integrated,
        market_assumptions=assumptions,
    )


def interpret_macro_briefing(briefing: MacroBriefing) -> MacroInterpretation:
    return _macro_interpretation(briefing)


def _unavailable_macro() -> MacroInterpretation:
    return MacroInterpretation(
        regime_label="판단 보류",
        confidence=0.0,
        one_line="시장환경 수집이 완료되지 않아 거시 방향은 판단을 보류하고 종목별 확인 근거만 점검합니다.",
        key_changes=[],
        axis_explanations=[
            (label, "오늘 방향을 판단할 구조화 데이터가 충분하지 않습니다.")
            for label in ("경기", "물가", "유동성", "금융여건", "위험선호", "기업이익")
        ],
        integrated_view=[
            "거시 데이터가 복구되기 전에는 시장 방향을 종목 투자 논리 변화로 연결하지 않습니다."
        ],
        market_assumptions=[],
    )


def _terms(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9가-힣]+", text.lower()) if len(token) > 1}


def _check_metrics(thesis: InvestmentThesis, assessment: ThesisAssessment) -> list[str]:
    metrics = _text_list(thesis.validation_metrics)
    weaken = _text_list(thesis.weaken_signals)
    invalidation = _text_list(thesis.invalidation_signals)
    evidence = [item for item in _list(assessment.evidence) if isinstance(item, dict)]
    event_text = " ".join(str(item.get("title", "")) for item in evidence)
    earnings_terms = {"매출", "마진", "영업이익", "현금흐름", "fcf", "eps", "asp", "roic"}

    def metric_score(metric: str, index: int) -> tuple[int, int]:
        words = _terms(metric)
        event_overlap = len(words & _terms(event_text))
        invalidation_overlap = max((len(words & _terms(item)) for item in invalidation), default=0)
        weaken_overlap = max((len(words & _terms(item)) for item in weaken), default=0)
        earnings_overlap = len(words & earnings_terms)
        return (
            event_overlap * 100 + invalidation_overlap * 30 + weaken_overlap * 20 + earnings_overlap * 10,
            -index,
        )

    ranked = sorted(enumerate(metrics), key=lambda item: metric_score(item[1], item[0]), reverse=True)
    return [metric for _index, metric in ranked[:5]]


def _display_reason(assessment: ThesisAssessment) -> str:
    status = assessment.business_thesis_change or assessment.status
    if status != "no_material_change":
        return STATUS_LABELS.get(status, status)
    evidence = [item for item in _list(assessment.evidence) if isinstance(item, dict)]
    directions = {str(item.get("direction", "neutral")) for item in evidence}
    if "weaken" in directions or "invalidation" in directions:
        return "유지 · 경고 신호 있으나 임계치 미달"
    if "strengthen" in directions:
        return "유지 · 긍정 신호 있으나 미확정"
    if _text_list(assessment.confirmed_facts):
        return "유지 · 확인 근거 있음"
    return "유지 · 신규 데이터 없음"


def _macro_paths(impact: ThesisMacroImpact | None) -> list[str]:
    if impact is None:
        return []
    evidence = [item for item in _list(impact.evidence) if isinstance(item, dict)]
    lines: list[str] = []
    for item in sorted(evidence, key=lambda value: -abs(float(value.get("contribution", 0) or 0)))[:3]:
        exposure = item.get("exposure", {})
        exposure = exposure if isinstance(exposure, dict) else {}
        factor = str(item.get("series_code") or item.get("factor") or "시장환경")
        label = SERIES_LABELS.get(factor, {
            "hyperscaler_capex": "빅테크 AI CAPEX",
        }.get(factor, factor))
        channel = str(exposure.get("channel", "영향 경로"))
        contribution = float(item.get("contribution", 0) or 0)
        effect = "긍정" if contribution > 0 else "부정"
        target = "Valuation" if channel == "discount_rate" else "사업·이익"
        lines.append(f"{label} → {channel} 경로 → {target} {effect}")
    return lines


def _priority(assessment: ThesisAssessment, impact: ThesisMacroImpact | None) -> tuple[int, int, int, str]:
    status = assessment.business_thesis_change or assessment.status
    status_rank = {
        "invalidated": 0,
        "invalidation_candidate": 1,
        "weakened": 2,
        "strengthened": 3,
        "mixed": 4,
        "needs_review": 7,
        "no_material_change": 9,
    }.get(status, 9)
    earnings = assessment.earnings_estimate_impact or "unknown"
    valuation = assessment.valuation_change or str(_dict(assessment.valuation_context).get("impact", "unknown"))
    secondary = 0 if earnings in {"up", "down", "mixed"} else 1 if valuation in {"compression", "expansion"} else 2 if valuation == "mixed" else 3
    magnitude = -(impact.magnitude if impact else 0)
    return status_rank, secondary, magnitude, assessment.ticker


def _ticker_summary(
    item: WatchlistItem,
    thesis: InvestmentThesis,
    assessment: ThesisAssessment,
    impact: ThesisMacroImpact | None,
) -> TickerDailySummary:
    expectation = _dict(thesis.market_expectations)
    valuation_context = _dict(assessment.valuation_context)
    valuation = assessment.valuation_change or str(valuation_context.get("impact", "unknown"))
    expectation_level = str(expectation.get("level", "unknown"))
    facts = _text_list(assessment.confirmed_facts)
    weaken_signals = _text_list(thesis.weaken_signals)
    warning = weaken_signals[0] if weaken_signals else assessment.summary
    check_metrics = _check_metrics(thesis, assessment)
    new_observer_view = assessment.new_buyer_view
    holder_view = assessment.holder_view
    if (assessment.business_thesis_change or assessment.status) == "no_material_change":
        if expectation_level in {"very_high", "speculative"}:
            new_observer_view = (
                "사업 투자 논리는 유지되지만 높은 시장 기대가 반영돼 있어, "
                "추가 실적 상향과 현금흐름 개선을 확인해야 가격 매력을 높게 볼 수 있습니다."
            )
        elif valuation == "compression":
            new_observer_view = (
                "사업 투자 논리는 유지되지만 멀티플 압축 경로가 있어 가격 안전마진을 우선 확인합니다."
            )
        holder_view = (
            "핵심 투자 논리가 훼손되지는 않았습니다. "
            f"{check_metrics[0] if check_metrics else '핵심 검증 지표'}"
            "의 변화가 기존 논리를 지지하는지 계속 관리합니다."
        )
    return TickerDailySummary(
        ticker=item.ticker,
        company_name=item.company_name,
        status=assessment.business_thesis_change or assessment.status,
        display_reason=_display_reason(assessment),
        expectation_level=expectation_level,
        valuation=valuation,
        earnings_impact=assessment.earnings_estimate_impact or "unknown",
        summary=assessment.summary,
        confirmed_facts=facts[:2],
        current_warning=warning,
        macro_paths=_macro_paths(impact),
        check_metrics=check_metrics,
        new_observer_view=new_observer_view,
        holder_view=holder_view,
        priority=_priority(assessment, impact),
    )


def _portfolio(session: Session, run_date: date, detail_limit: int) -> PortfolioSummary:
    assessments = session.exec(
        select(ThesisAssessment)
        .where(ThesisAssessment.assessment_date == run_date)
        .order_by(ThesisAssessment.ticker)
    ).all()
    tickers: list[TickerDailySummary] = []
    for assessment in assessments:
        item = session.exec(
            select(WatchlistItem).where(WatchlistItem.ticker == assessment.ticker)
        ).first()
        thesis = session.exec(
            select(InvestmentThesis).where(
                InvestmentThesis.ticker == assessment.ticker,
                InvestmentThesis.version == assessment.thesis_version,
            )
        ).first()
        if item is None or thesis is None:
            continue
        impact = session.exec(
            select(ThesisMacroImpact).where(
                ThesisMacroImpact.ticker == assessment.ticker,
                ThesisMacroImpact.thesis_version == assessment.thesis_version,
                ThesisMacroImpact.assessment_date == run_date,
            )
        ).first()
        tickers.append(_ticker_summary(item, thesis, assessment, impact))

    thesis_counts = {"strengthened": 0, "maintained": 0, "weakened": 0, "invalidated": 0}
    valuation_counts = {"expansion": 0, "neutral": 0, "mixed": 0, "compression": 0, "unknown": 0}
    for ticker in tickers:
        if ticker.status == "strengthened":
            thesis_counts["strengthened"] += 1
        elif ticker.status in {"weakened", "mixed", "invalidation_candidate", "needs_review"}:
            thesis_counts["weakened"] += 1
        elif ticker.status == "invalidated":
            thesis_counts["invalidated"] += 1
        else:
            thesis_counts["maintained"] += 1
        valuation_counts[ticker.valuation if ticker.valuation in valuation_counts else "unknown"] += 1

    ordered = sorted(tickers, key=lambda item: item.priority)
    material = [item for item in ordered if item.priority[:2] < (9, 3)]
    focus = material[:detail_limit]
    if len(focus) < min(3, len(ordered)):
        focus.extend(item for item in ordered if item not in focus)
    return PortfolioSummary(
        thesis_counts=thesis_counts,
        valuation_counts=valuation_counts,
        tickers=tickers,
        focus_tickers=focus[:detail_limit],
    )


def _schedule(session: Session, run_date: date) -> ScheduleSummary:
    end_date = run_date + timedelta(days=7)
    macro_events = session.exec(
        select(MacroEvent)
        .where(MacroEvent.scheduled_at.is_not(None))
        .order_by(MacroEvent.scheduled_at)
    ).all()
    company_events = session.exec(
        select(Event)
        .where(Event.date >= run_date, Event.date <= end_date)
        .order_by(Event.date, Event.relevance_score.desc())
    ).all()
    entries: dict[tuple[date, str], str] = {}
    for event in macro_events:
        if event.scheduled_at is None:
            continue
        event_date = event.scheduled_at.date()
        if run_date <= event_date <= end_date:
            entries[(event_date, event.title)] = event.title
    for event in company_events:
        if event.date >= run_date and event.event_type in {
            "earnings_schedule", "shareholder_meeting", "scheduled_guidance", "product_milestone"
        }:
            entries[(event.date, event.title)] = f"{event.ticker} · {event.title}"
    today = [title for (event_date, _key), title in entries.items() if event_date == run_date]
    upcoming = [
        f"{title} · D-{(event_date - run_date).days}"
        for (event_date, _key), title in entries.items()
        if event_date > run_date
    ]
    return ScheduleSummary(today=today[:5], next_seven_days=upcoming[:8])


def _data_quality(
    session: Session,
    briefing: MacroBriefing | None,
    portfolio: PortfolioSummary,
    run_date: date,
) -> DataQualitySummary:
    values = _list(briefing.data_quality) if briefing is not None else []
    lines: list[str] = []
    if briefing is None:
        lines.append("시장환경 브리핑 생성 실패 · 거시 방향 판단 보류")
    for item in values:
        if not isinstance(item, dict):
            continue
        warning = item.get("warning")
        if warning:
            lines.append(str(warning))
            continue
        code = str(item.get("series_code", "데이터"))
        label = SERIES_LABELS.get(code, code)
        status = str(item.get("quality_status", "점검 필요"))
        lines.append(f"{label}: {status} · 당일 방향 판단에서 제외하거나 신뢰도를 낮춤")
    run = session.exec(
        select(MonitorRun).where(
            MonitorRun.run_date == run_date,
            MonitorRun.run_type == "daily",
        )
    ).first()
    if run is not None and len(portfolio.tickers) < run.ticker_count:
        lines.append(
            f"종목 일일 평가 {len(portfolio.tickers)}/{run.ticker_count}건 완료 · "
            f"실패 {run.failure_count}건"
        )
    conclusion = (
        "누락·지연 데이터가 관련 시장 판단의 강도를 낮췄습니다."
        if lines
        else "핵심 입력에서 별도 데이터 경고가 확인되지 않았습니다."
    )
    return DataQualitySummary(items=list(dict.fromkeys(lines))[:8], conclusion=conclusion)


def build_daily_digest(
    session: Session,
    run_date: date,
    detail_limit: int = 5,
) -> DailyDigest:
    briefing = session.exec(
        select(MacroBriefing)
        .where(
            MacroBriefing.briefing_date == run_date,
            MacroBriefing.briefing_type == "morning",
        )
        .order_by(MacroBriefing.created_at.desc())
    ).first()
    portfolio = _portfolio(session, run_date, max(3, min(5, detail_limit)))
    return DailyDigest(
        digest_date=run_date,
        macro=_macro_interpretation(briefing) if briefing is not None else _unavailable_macro(),
        portfolio=portfolio,
        schedule=_schedule(session, run_date),
        data_quality=_data_quality(session, briefing, portfolio, run_date),
    )
