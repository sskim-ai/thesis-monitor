from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.services.canonical_fact_service import compact_krw_amount


NumericScope = Literal["market", "stock", "both"]


@dataclass(frozen=True)
class NumericSemanticSpec:
    semantic_type: str
    units: tuple[str, ...]
    approved_labels: tuple[str, ...]
    usage_patterns: tuple[str, ...]
    formatter: str
    prose_allowed: bool
    scope: NumericScope


@dataclass(frozen=True)
class NumericFieldRule:
    fact_types: tuple[str, ...]
    field_pattern: str
    semantic_type: str
    unit: str


def _spec(
    semantic_type: str,
    units: tuple[str, ...],
    labels: tuple[str, ...],
    patterns: tuple[str, ...],
    formatter: str,
    *,
    prose_allowed: bool = True,
    scope: NumericScope = "stock",
) -> NumericSemanticSpec:
    return NumericSemanticSpec(
        semantic_type=semantic_type,
        units=units,
        approved_labels=labels,
        usage_patterns=patterns,
        formatter=formatter,
        prose_allowed=prose_allowed,
        scope=scope,
    )


NUMERIC_SEMANTICS = {
    "revenue": _spec(
        "revenue",
        ("KRW", "USD", "JPY", "EUR"),
        ("매출", "매출액", "revenue"),
        (r"매출(?:액)?", r"\brevenue\b"),
        "currency_amount",
    ),
    "operating_income": _spec(
        "operating_income",
        ("KRW", "USD", "JPY", "EUR"),
        ("영업이익", "operating income"),
        (r"영업이익", r"operating income"),
        "currency_amount",
    ),
    "operating_margin": _spec(
        "operating_margin",
        ("pct",),
        ("영업이익률", "영업마진", "operating margin"),
        (r"영업(?:이익률|마진)", r"operating margin"),
        "percentage",
    ),
    "revenue_qoq": _spec(
        "revenue_qoq",
        ("pct",),
        ("매출 QoQ", "매출 전분기 대비", "revenue QoQ"),
        (r"매출.*(?:qoq|전분기)", r"revenue.*qoq"),
        "percentage",
    ),
    "revenue_yoy": _spec(
        "revenue_yoy",
        ("pct",),
        ("매출 성장률", "매출 YoY", "revenue growth"),
        (r"매출.*(?:성장률|증가율|yoy)", r"revenue.*(?:growth|yoy)"),
        "percentage",
    ),
    "operating_income_qoq": _spec(
        "operating_income_qoq",
        ("pct",),
        ("영업이익 QoQ", "영업이익 전분기 대비"),
        (r"영업이익.*(?:qoq|전분기)", r"operating income.*qoq"),
        "percentage",
    ),
    "operating_income_yoy": _spec(
        "operating_income_yoy",
        ("pct",),
        ("영업이익 성장률", "영업이익 YoY"),
        (
            r"영업이익.*(?:성장률|증가율|yoy)",
            r"operating income.*(?:growth|yoy)",
        ),
        "percentage",
    ),
    "ttm_eps": _spec(
        "ttm_eps",
        ("KRW", "USD", "JPY", "EUR"),
        ("TTM EPS", "최근 4개 분기 EPS"),
        (r"ttm\s*eps", r"최근\s*4개\s*분기\s*eps"),
        "currency",
    ),
    "bvps": _spec(
        "bvps",
        ("KRW", "USD", "JPY", "EUR"),
        ("BVPS", "주당순자산"),
        (r"\bbvps\b", r"주당순자산"),
        "currency",
    ),
    "forward_eps": _spec(
        "forward_eps",
        ("KRW", "USD", "JPY", "EUR"),
        ("예상 EPS", "추정 EPS", "forward EPS"),
        (r"(?:예상|추정)\s*eps", r"forward\s*eps"),
        "currency",
    ),
    "forward_bvps": _spec(
        "forward_bvps",
        ("KRW", "USD", "JPY", "EUR"),
        ("예상 BVPS", "추정 BVPS", "forward BVPS"),
        (r"(?:예상|추정)\s*bvps", r"forward\s*bvps"),
        "currency",
    ),
    "trailing_pe": _spec(
        "trailing_pe",
        ("x",),
        ("현재 PER", "trailing PE", "PER"),
        (r"현재\s*per", r"trailing\s*pe", r"\bper\b"),
        "multiple",
    ),
    "price_to_book": _spec(
        "price_to_book",
        ("x",),
        ("현재 PBR", "price to book", "PBR"),
        (r"현재\s*pbr", r"price to book", r"\bpbr\b"),
        "multiple",
    ),
    "forward_pe": _spec(
        "forward_pe",
        ("x",),
        ("fPER", "선행 PER", "forward PE"),
        (r"\bfper\b", r"선행\s*per", r"forward\s*pe"),
        "multiple",
    ),
    "forward_price_to_book": _spec(
        "forward_price_to_book",
        ("x",),
        ("fPBR", "선행 PBR", "forward PBR"),
        (r"\bfpbr\b", r"선행\s*pbr", r"forward\s*pbr"),
        "multiple",
    ),
    "share_price": _spec(
        "share_price",
        ("KRW", "USD", "JPY", "EUR"),
        ("현재가", "주가", "share price"),
        (r"현재가", r"주가", r"(?:current|share) price"),
        "currency",
    ),
    "contract_amount": _spec(
        "contract_amount",
        ("KRW", "USD", "JPY", "EUR"),
        ("계약금액", "수주금액", "contract amount"),
        (r"(?:계약|수주)금액", r"(?:contract amount|order value)"),
        "currency_amount",
    ),
    "sales_ratio": _spec(
        "sales_ratio",
        ("pct",),
        ("매출액 대비", "sales ratio"),
        (r"매출액?\s*대비", r"sales ratio"),
        "percentage",
    ),
    "transaction_shares": _spec(
        "transaction_shares",
        ("shares",),
        ("거래 주식 수", "처분 주식 수", "transaction shares"),
        (r"(?:거래|처분|취득)\s*주식\s*수", r"transaction shares"),
        "shares",
    ),
    "share_ratio": _spec(
        "share_ratio",
        ("pct",),
        ("주식 비율", "지분 비율", "share ratio"),
        (r"(?:주식|지분)\s*비율", r"share ratio"),
        "percentage",
    ),
    "transaction_amount": _spec(
        "transaction_amount",
        ("KRW", "USD", "JPY", "EUR"),
        ("거래금액", "처분금액", "transaction amount"),
        (r"(?:거래|처분|취득)금액", r"transaction amount"),
        "currency_amount",
    ),
    "market_cap": _spec(
        "market_cap",
        ("KRW", "USD", "JPY", "EUR"),
        ("시가총액", "market cap"),
        (r"시가총액", r"market cap"),
        "currency_amount",
    ),
    "market_cap_ratio": _spec(
        "market_cap_ratio",
        ("pct",),
        ("시가총액 비율", "market cap ratio"),
        (r"시가총액\s*비율", r"market cap ratio"),
        "percentage",
    ),
    "foreign_net_buy_qty": _spec(
        "foreign_net_buy_qty",
        ("shares",),
        ("외국인 순매수", "외국인 순매도"),
        (r"외국인.*(?:순매수|순매도)", r"foreign.*net (?:buy|sell)"),
        "signed_shares",
    ),
    "institution_net_buy_qty": _spec(
        "institution_net_buy_qty",
        ("shares",),
        ("기관 순매수", "기관 순매도"),
        (r"기관.*(?:순매수|순매도)", r"institution.*net (?:buy|sell)"),
        "signed_shares",
    ),
    "individual_net_buy_qty": _spec(
        "individual_net_buy_qty",
        ("shares",),
        ("개인 순매수", "개인 순매도"),
        (r"개인.*(?:순매수|순매도)", r"individual.*net (?:buy|sell)"),
        "signed_shares",
    ),
    "foreign_net_buy_qty_5d": _spec(
        "foreign_net_buy_qty_5d", ("shares",),
        ("외국인 5일 순매수", "외국인 5일 순매도"),
        (r"외국인.*5일.*(?:순매수|순매도)", r"5일.*외국인.*(?:순매수|순매도)"),
        "signed_shares",
    ),
    "institution_net_buy_qty_5d": _spec(
        "institution_net_buy_qty_5d", ("shares",),
        ("기관 5일 순매수", "기관 5일 순매도"),
        (r"기관.*5일.*(?:순매수|순매도)", r"5일.*기관.*(?:순매수|순매도)"),
        "signed_shares",
    ),
    "individual_net_buy_qty_5d": _spec(
        "individual_net_buy_qty_5d", ("shares",),
        ("개인 5일 순매수", "개인 5일 순매도"),
        (r"개인.*5일.*(?:순매수|순매도)", r"5일.*개인.*(?:순매수|순매도)"),
        "signed_shares",
    ),
    "foreign_net_buy_qty_20d": _spec(
        "foreign_net_buy_qty_20d", ("shares",),
        ("외국인 20일 순매수", "외국인 20일 순매도"),
        (r"외국인.*20일.*(?:순매수|순매도)", r"20일.*외국인.*(?:순매수|순매도)"),
        "signed_shares",
    ),
    "institution_net_buy_qty_20d": _spec(
        "institution_net_buy_qty_20d", ("shares",),
        ("기관 20일 순매수", "기관 20일 순매도"),
        (r"기관.*20일.*(?:순매수|순매도)", r"20일.*기관.*(?:순매수|순매도)"),
        "signed_shares",
    ),
    "individual_net_buy_qty_20d": _spec(
        "individual_net_buy_qty_20d", ("shares",),
        ("개인 20일 순매수", "개인 20일 순매도"),
        (r"개인.*20일.*(?:순매수|순매도)", r"20일.*개인.*(?:순매수|순매도)"),
        "signed_shares",
    ),
    "foreign_holding_qty": _spec(
        "foreign_holding_qty",
        ("shares",),
        ("외국인 보유 주식 수", "foreign holding shares"),
        (r"외국인.*보유.*주식", r"foreign holding.*shares"),
        "shares",
    ),
    "foreign_holding_ratio": _spec(
        "foreign_holding_ratio",
        ("pct",),
        ("외국인 보유율", "foreign holding ratio"),
        (r"외국인.*보유율", r"foreign holding ratio"),
        "percentage",
    ),
    "futures_close": _spec(
        "futures_close",
        ("points",),
        ("야간선물 종가", "최근월물", "futures close"),
        (r"(?:야간선물\s*종가|최근월물)", r"futures close"),
        "points",
        scope="market",
    ),
    "futures_point_change": _spec(
        "futures_point_change",
        ("points",),
        ("야간선물 등락폭", "point change"),
        (r"야간선물.*(?:등락폭|포인트)", r"futures.*point change"),
        "signed_points",
        scope="market",
    ),
    "futures_return_pct": _spec(
        "futures_return_pct",
        ("pct",),
        ("야간선물 등락률", "futures return"),
        (r"야간선물.*(?:등락률|상승|하락)", r"futures.*(?:return|change)"),
        "signed_percentage",
        scope="market",
    ),
    "fx_rate": _spec(
        "fx_rate",
        ("KRW",),
        ("환율", "원/달러", "원/100엔", "원/유로"),
        (r"(?:환율|원/(?:달러|100엔|유로))", r"exchange rate"),
        "currency",
        scope="market",
    ),
    "fx_point_change": _spec(
        "fx_point_change",
        ("KRW",),
        ("환율 변동폭", "exchange-rate change"),
        (r"환율.*(?:변동폭|등락폭)", r"exchange[- ]rate change"),
        "signed_currency",
        scope="market",
    ),
    "fx_return_pct": _spec(
        "fx_return_pct",
        ("pct",),
        ("환율 등락률", "exchange-rate return"),
        (r"환율.*(?:등락률|상승|하락)", r"exchange[- ]rate.*(?:return|change)"),
        "signed_percentage",
        scope="market",
    ),
    "market_return_pct": _spec(
        "market_return_pct",
        ("pct",),
        ("시장 등락률", "지수 등락률", "market return"),
        (r"(?:시장|지수).*등락률", r"market.*(?:return|change)"),
        "signed_percentage",
        scope="market",
    ),
    "chart_open_price": _spec(
        "chart_open_price", ("KRW", "USD"), ("시가", "open"),
        (r"(?:일봉|주봉|월봉)?\s*시가", r"(?:daily|weekly|monthly)?\s*open"),
        "currency",
    ),
    "chart_high_price": _spec(
        "chart_high_price", ("KRW", "USD"), ("고가", "high"),
        (r"(?:일봉|주봉|월봉)?\s*고가", r"(?:daily|weekly|monthly)?\s*high"),
        "currency",
    ),
    "chart_low_price": _spec(
        "chart_low_price", ("KRW", "USD"), ("저가", "low"),
        (r"(?:일봉|주봉|월봉)?\s*저가", r"(?:daily|weekly|monthly)?\s*low"),
        "currency",
    ),
    "chart_close_price": _spec(
        "chart_close_price", ("KRW", "USD"), ("종가", "close"),
        (r"(?:일봉|주봉|월봉)?\s*종가", r"(?:daily|weekly|monthly)?\s*close"),
        "currency",
    ),
    "chart_volume": _spec(
        "chart_volume", ("shares",), ("거래량", "volume"),
        (r"거래량", r"\bvolume\b"), "shares",
    ),
    "chart_trading_value": _spec(
        "chart_trading_value", ("provider_value",), (), (), "decimal",
        prose_allowed=False,
    ),
    "candle_body_pct": _spec(
        "candle_body_pct", ("pct",), ("캔들 몸통", "candle body"),
        (r"캔들.*몸통", r"candle body"), "percentage",
    ),
    "candle_range_pct": _spec(
        "candle_range_pct", ("pct",), ("캔들 변동폭", "candle range"),
        (r"캔들.*(?:변동폭|범위)", r"candle range"), "percentage",
    ),
    "candle_close_location_pct": _spec(
        "candle_close_location_pct", ("pct",), ("종가 위치", "close location"),
        (r"종가.*위치", r"close location"), "percentage",
    ),
    "candle_upper_wick_pct": _spec(
        "candle_upper_wick_pct", ("pct",), ("윗꼬리", "upper wick"),
        (r"윗꼬리", r"upper wick"), "percentage",
    ),
    "candle_lower_wick_pct": _spec(
        "candle_lower_wick_pct", ("pct",), ("아랫꼬리", "lower wick"),
        (r"아랫꼬리", r"lower wick"), "percentage",
    ),
    "chart_period_return_pct": _spec(
        "chart_period_return_pct", ("pct",), ("기간 수익률", "period return"),
        (r"(?:일봉|주봉|월봉)?.*수익률", r"period return"), "signed_percentage",
    ),
    "chart_range_position_pct": _spec(
        "chart_range_position_pct", ("pct",), ("가격 범위 위치", "range position"),
        (r"가격.*범위.*위치", r"range position"), "percentage",
    ),
    "bollinger_upper_price": _spec(
        "bollinger_upper_price", ("KRW", "USD"), ("볼린저 상단선", "Bollinger upper"),
        (r"(?:3|5|6|12|24|54)개월.*상단선", r"bollinger.*upper"), "currency",
    ),
    "bollinger_distance_pct": _spec(
        "bollinger_distance_pct", ("pct",), ("볼린저 이격", "Bollinger distance"),
        (r"(?:3|5|6|12|24|54)개월.*이격", r"bollinger.*distance"), "signed_percentage",
    ),
    "volume_ratio_20": _spec(
        "volume_ratio_20", ("x",), ("20일 거래량비", "20-day volume ratio"),
        (r"20일.*거래량비", r"20[- ]day volume ratio"), "multiple",
    ),
    "rsi_14": _spec(
        "rsi_14", ("index",), ("RSI14", "RSI"),
        (r"\brsi\s*14?\b",), "decimal",
    ),
    "macd": _spec(
        "macd", ("KRW", "USD"), ("MACD",), (r"\bmacd\b",), "currency",
    ),
    "macd_signal": _spec(
        "macd_signal", ("KRW", "USD"), ("MACD signal",),
        (r"macd.*signal", r"macd.*시그널"), "currency",
    ),
    "macd_histogram": _spec(
        "macd_histogram", ("KRW", "USD"), ("MACD histogram",),
        (r"macd.*histogram", r"macd.*히스토그램"), "currency",
    ),
    "stored_confirmation_price": _spec(
        "stored_confirmation_price", ("KRW", "USD"), ("상향 확인 가격",),
        (r"상향.*확인.*가격", r"confirmation price"), "currency",
    ),
    "stored_support_price": _spec(
        "stored_support_price", ("KRW", "USD"), ("저장 지지 가격", "지지구간"),
        (r"(?:저장.*)?지지(?:구간|가격)", r"stored support"), "currency",
    ),
    "stored_warning_price": _spec(
        "stored_warning_price", ("KRW", "USD"), ("재점검 시작 가격", "경고 가격"),
        (r"(?:재점검.*시작|경고).*가격", r"warning price"), "currency",
    ),
    "stored_invalidation_price": _spec(
        "stored_invalidation_price", ("KRW", "USD"), ("재점검 가격", "무효화 가격"),
        (r"(?:재점검|무효화).*가격", r"invalidation price"), "currency",
    ),
    "price_rule_distance_pct": _spec(
        "price_rule_distance_pct", ("pct",), ("가격 기준 이격",),
        (r"(?:확인|지지|경고|무효화|재점검).*이격", r"price rule distance"),
        "signed_percentage",
    ),
    "chart_atr": _spec(
        "chart_atr", ("KRW", "USD"), ("ATR14", "Wilder ATR14"),
        (r"(?:일봉|주봉|월봉)?\s*(?:wilder\s*)?atr\s*14?",), "currency",
    ),
    "support_zone_price": _spec(
        "support_zone_price", ("KRW", "USD"), ("동적 지지구간", "지지구간"),
        (r"(?:동적\s*)?지지(?:구간|대)", r"support zone"), "currency",
    ),
    "resistance_zone_price": _spec(
        "resistance_zone_price", ("KRW", "USD"), ("동적 저항구간", "저항구간"),
        (r"(?:동적\s*)?저항(?:구간|대)", r"resistance zone"), "currency",
    ),
    "active_zone_price": _spec(
        "active_zone_price", ("KRW", "USD"), ("현재 활성구간", "활성구간"),
        (r"(?:현재\s*)?활성구간", r"active zone"), "currency",
    ),
    "distance_to_zone_pct": _spec(
        "distance_to_zone_pct", ("pct",), ("구간 이격", "지지 이격", "저항 이격"),
        (r"(?:구간|지지|저항).*이격", r"distance.*zone"), "percentage",
    ),
    "box_boundary_price": _spec(
        "box_boundary_price", ("KRW", "USD"), ("박스 하단", "박스 상단"),
        (r"박스.*(?:하단|상단)", r"box.*(?:low|high)"), "currency",
    ),
    "box_width_pct": _spec(
        "box_width_pct", ("pct",), ("박스 폭",),
        (r"박스.*폭", r"box width"), "percentage",
    ),
    "major_swing_price": _spec(
        "major_swing_price", ("KRW", "USD"), ("Major Swing", "주요 스윙"),
        (r"(?:major swing|주요 스윙).*(?:고점|저점|high|low)?",), "currency",
    ),
    "fibonacci_anchor_price": _spec(
        "fibonacci_anchor_price", ("KRW", "USD"), ("Fibonacci 앵커", "피보나치 앵커"),
        (r"(?:fibonacci|피보나치).*앵커",), "currency",
    ),
    "fibonacci_retracement_price": _spec(
        "fibonacci_retracement_price", ("KRW", "USD"),
        ("Fibonacci 되돌림", "피보나치 되돌림"),
        (r"(?:fibonacci|피보나치).*되돌림",), "currency",
    ),
    "fibonacci_extension_price": _spec(
        "fibonacci_extension_price", ("KRW", "USD"),
        ("Fibonacci 확장", "피보나치 확장"),
        (r"(?:fibonacci|피보나치).*확장",), "currency",
    ),
    "scenario_entry_price": _spec(
        "scenario_entry_price", ("KRW", "USD"), ("시나리오 진입가", "시나리오 기준가"),
        (r"시나리오.*(?:진입가|기준가)", r"scenario entry"), "currency",
    ),
    "chart_target_price": _spec(
        "chart_target_price", ("KRW", "USD"), ("가까운 저항 목표", "차트 목표"),
        (r"(?:가까운\s*저항\s*목표|차트\s*목표)", r"chart target"), "currency",
    ),
    "chart_invalidation_price": _spec(
        "chart_invalidation_price", ("KRW", "USD"),
        ("차트 무효화 가격", "가격 시나리오 무효화"),
        (r"(?:차트|가격\s*시나리오).*무효화", r"chart invalidation"), "currency",
    ),
    "chart_price_risk": _spec(
        "chart_price_risk", ("KRW", "USD"), ("차트 하방 위험", "차트 상승 여지"),
        (r"차트.*(?:하방\s*위험|상승\s*여지)", r"chart.*(?:upside|downside)"), "currency",
    ),
    "risk_reward_ratio": _spec(
        "risk_reward_ratio", ("x",), ("차트 손익비", "RR"),
        (r"(?:차트\s*)?손익비", r"\brr\b", r"risk.?reward"), "multiple",
    ),
    "historical_pe_multiple": _spec(
        "historical_pe_multiple",
        ("x",),
        ("역사적 PER", "과거 PER"),
        (r"(?:역사적|과거).*per", r"historical pe"),
        "multiple",
    ),
    "historical_pb_multiple": _spec(
        "historical_pb_multiple",
        ("x",),
        ("역사적 PBR", "과거 PBR"),
        (r"(?:역사적|과거).*pbr", r"historical pbr"),
        "multiple",
    ),
    "historical_pe_percentile": _spec(
        "historical_pe_percentile",
        ("pct",),
        ("PER 역사적 백분위", "PER 과거 백분위"),
        (r"per.*(?:역사적|과거).*백분위", r"historical pe percentile"),
        "percentage",
    ),
    "historical_pb_percentile": _spec(
        "historical_pb_percentile",
        ("pct",),
        ("PBR 역사적 백분위", "PBR 과거 백분위"),
        (r"pbr.*(?:역사적|과거).*백분위", r"historical pbr percentile"),
        "percentage",
    ),
    "audit_count": _spec(
        "audit_count",
        ("count",),
        (),
        (),
        "integer",
        prose_allowed=False,
        scope="both",
    ),
    "audit_years": _spec(
        "audit_years",
        ("years",),
        (),
        (),
        "decimal",
        prose_allowed=False,
    ),
    "audit_ratio": _spec(
        "audit_ratio",
        ("pct", "number"),
        (),
        (),
        "decimal",
        prose_allowed=False,
        scope="both",
    ),
    "share_denominator": _spec(
        "share_denominator",
        ("shares",),
        (),
        (),
        "shares",
        prose_allowed=False,
    ),
}


_FIELD_RULES = (
    NumericFieldRule(("earnings",), r"fields\.revenue\.value", "revenue", "currency"),
    NumericFieldRule(
        ("earnings",),
        r"fields\.operating_income\.value",
        "operating_income",
        "currency",
    ),
    NumericFieldRule(
        ("earnings",),
        r"fields\.operating_margin_pct",
        "operating_margin",
        "pct",
    ),
    NumericFieldRule(("earnings",), r"fields\.revenue_qoq_pct", "revenue_qoq", "pct"),
    NumericFieldRule(("earnings",), r"fields\.revenue_yoy_pct", "revenue_yoy", "pct"),
    NumericFieldRule(
        ("earnings",),
        r"fields\.operating_income_qoq_pct",
        "operating_income_qoq",
        "pct",
    ),
    NumericFieldRule(
        ("earnings",),
        r"fields\.operating_income_yoy_pct",
        "operating_income_yoy",
        "pct",
    ),
    NumericFieldRule(("valuation",), r"fields\.ttm_eps", "ttm_eps", "currency"),
    NumericFieldRule(("valuation",), r"fields\.bvps", "bvps", "currency"),
    NumericFieldRule(("valuation",), r"fields\.forward_eps", "forward_eps", "currency"),
    NumericFieldRule(("valuation",), r"fields\.forward_bvps", "forward_bvps", "currency"),
    NumericFieldRule(("valuation",), r"fields\.trailing_pe", "trailing_pe", "x"),
    NumericFieldRule(("valuation",), r"fields\.price_to_book", "price_to_book", "x"),
    NumericFieldRule(("valuation",), r"fields\.forward_pe", "forward_pe", "x"),
    NumericFieldRule(
        ("valuation",),
        r"fields\.forward_price_to_book",
        "forward_price_to_book",
        "x",
    ),
    NumericFieldRule(
        ("valuation",),
        r"fields\.historical_pe_statistics\.(?:current_value|historical_(?:median|mean)|percentile_(?:10|25|50|75|90))",
        "historical_pe_multiple",
        "x",
    ),
    NumericFieldRule(
        ("valuation",),
        r"fields\.historical_pb_statistics\.(?:current_value|historical_(?:median|mean)|percentile_(?:10|25|50|75|90))",
        "historical_pb_multiple",
        "x",
    ),
    NumericFieldRule(
        ("valuation",),
        r"fields\.historical_pe_statistics\.current_percentile",
        "historical_pe_percentile",
        "pct",
    ),
    NumericFieldRule(
        ("valuation",),
        r"fields\.historical_pb_statistics\.current_percentile",
        "historical_pb_percentile",
        "pct",
    ),
    NumericFieldRule(
        ("valuation",),
        r"fields\.historical_(?:pe|pb)_statistics\.(?:observation_count|raw_observation_count|deduplicated_observation_count)",
        "audit_count",
        "count",
    ),
    NumericFieldRule(
        ("valuation",),
        r"fields\.historical_(?:pe|pb)_statistics\.(?:lookback_years|target_lookback_years)",
        "audit_years",
        "years",
    ),
    NumericFieldRule(
        ("valuation",),
        r"fields\.historical_(?:pe|pb)_statistics\.history_coverage_ratio",
        "audit_ratio",
        "number",
    ),
    NumericFieldRule(("price",), r"fields\.current_price", "share_price", "currency"),
    NumericFieldRule(
        ("contract_award",),
        r"fields\.contract_amount\.value",
        "contract_amount",
        "currency",
    ),
    NumericFieldRule(("contract_award",), r"fields\.sales_ratio_pct", "sales_ratio", "pct"),
    NumericFieldRule(("*",), r"fields\.relevance_score", "audit_ratio", "number"),
    NumericFieldRule(
        ("treasury_stock_transaction",),
        r"fields\.transaction_shares",
        "transaction_shares",
        "shares",
    ),
    NumericFieldRule(
        ("treasury_stock_transaction",),
        r"fields\.share_denominator",
        "share_denominator",
        "shares",
    ),
    NumericFieldRule(
        ("treasury_stock_transaction",),
        r"fields\.share_ratio_pct",
        "share_ratio",
        "pct",
    ),
    NumericFieldRule(
        ("treasury_stock_transaction",),
        r"fields\.transaction_amount\.value",
        "transaction_amount",
        "currency",
    ),
    NumericFieldRule(
        ("treasury_stock_transaction",),
        r"fields\.market_cap\.value",
        "market_cap",
        "currency",
    ),
    NumericFieldRule(
        ("treasury_stock_transaction",),
        r"fields\.market_cap_ratio_pct",
        "market_cap_ratio",
        "pct",
    ),
    NumericFieldRule(("positioning",), r"fields\.foreign_net_buy_qty", "foreign_net_buy_qty", "shares"),
    NumericFieldRule(
        ("positioning",),
        r"fields\.institution_net_buy_qty",
        "institution_net_buy_qty",
        "shares",
    ),
    NumericFieldRule(
        ("positioning",),
        r"fields\.individual_net_buy_qty",
        "individual_net_buy_qty",
        "shares",
    ),
    NumericFieldRule(
        ("positioning",),
        r"fields\.foreign_holding_qty",
        "foreign_holding_qty",
        "shares",
    ),
    NumericFieldRule(
        ("positioning",),
        r"fields\.foreign_holding_ratio",
        "foreign_holding_ratio",
        "pct",
    ),
    NumericFieldRule(("positioning",), r"fields\.foreign_net_buy_qty_5", "foreign_net_buy_qty_5d", "shares"),
    NumericFieldRule(("positioning",), r"fields\.institution_net_buy_qty_5", "institution_net_buy_qty_5d", "shares"),
    NumericFieldRule(("positioning",), r"fields\.individual_net_buy_qty_5", "individual_net_buy_qty_5d", "shares"),
    NumericFieldRule(("positioning",), r"fields\.foreign_net_buy_qty_20", "foreign_net_buy_qty_20d", "shares"),
    NumericFieldRule(("positioning",), r"fields\.institution_net_buy_qty_20", "institution_net_buy_qty_20d", "shares"),
    NumericFieldRule(("positioning",), r"fields\.individual_net_buy_qty_20", "individual_net_buy_qty_20d", "shares"),
    NumericFieldRule(("chart_timeframe",), r"fields\.candle\.open", "chart_open_price", "currency"),
    NumericFieldRule(("chart_timeframe",), r"fields\.candle\.high", "chart_high_price", "currency"),
    NumericFieldRule(("chart_timeframe",), r"fields\.candle\.low", "chart_low_price", "currency"),
    NumericFieldRule(("chart_timeframe",), r"fields\.candle\.close", "chart_close_price", "currency"),
    NumericFieldRule(("chart_timeframe",), r"fields\.candle\.volume", "chart_volume", "shares"),
    NumericFieldRule(("chart_timeframe",), r"fields\.candle\.trading_value", "chart_trading_value", "provider_value"),
    NumericFieldRule(("chart_timeframe",), r"fields\.candle\.body_pct", "candle_body_pct", "pct"),
    NumericFieldRule(("chart_timeframe",), r"fields\.candle\.range_pct", "candle_range_pct", "pct"),
    NumericFieldRule(("chart_timeframe",), r"fields\.candle\.close_location_pct", "candle_close_location_pct", "pct"),
    NumericFieldRule(("chart_timeframe",), r"fields\.candle\.upper_wick_pct", "candle_upper_wick_pct", "pct"),
    NumericFieldRule(("chart_timeframe",), r"fields\.candle\.lower_wick_pct", "candle_lower_wick_pct", "pct"),
    NumericFieldRule(("chart_timeframe",), r"fields\.period_return_pct", "chart_period_return_pct", "pct"),
    NumericFieldRule(("chart_timeframe",), r"fields\.range_position_pct", "chart_range_position_pct", "pct"),
    NumericFieldRule(("chart_timeframe",), r"fields\.bollinger_upper\.[^.]+", "bollinger_upper_price", "currency"),
    NumericFieldRule(("chart_timeframe",), r"fields\.bollinger_distance_pct\.[^.]+", "bollinger_distance_pct", "pct"),
    NumericFieldRule(("chart_timeframe",), r"fields\.volume_ratio_20", "volume_ratio_20", "x"),
    NumericFieldRule(("chart_timeframe",), r"fields\.rsi_14", "rsi_14", "index"),
    NumericFieldRule(("chart_timeframe",), r"fields\.macd", "macd", "currency"),
    NumericFieldRule(("chart_timeframe",), r"fields\.macd_signal", "macd_signal", "currency"),
    NumericFieldRule(("chart_timeframe",), r"fields\.macd_histogram", "macd_histogram", "currency"),
    NumericFieldRule(("chart_price_rules",), r"fields\.confirmation_price", "stored_confirmation_price", "currency"),
    NumericFieldRule(("chart_price_rules",), r"fields\.support_zone_(?:low|high)", "stored_support_price", "currency"),
    NumericFieldRule(("chart_price_rules",), r"fields\.warning_price", "stored_warning_price", "currency"),
    NumericFieldRule(("chart_price_rules",), r"fields\.invalidation_price", "stored_invalidation_price", "currency"),
    NumericFieldRule(("chart_price_rules",), r"fields\.distance_pct\.[^.]+", "price_rule_distance_pct", "pct"),
    NumericFieldRule(("chart_structure_atr",), r"fields\.value", "chart_atr", "currency"),
    NumericFieldRule(("chart_support_zone",), r"fields\.zone_(?:low|high)", "support_zone_price", "currency"),
    NumericFieldRule(("chart_resistance_zone",), r"fields\.zone_(?:low|high)", "resistance_zone_price", "currency"),
    NumericFieldRule(("chart_active_zone",), r"fields\.zone_(?:low|high)", "active_zone_price", "currency"),
    NumericFieldRule(
        ("chart_support_zone", "chart_resistance_zone", "chart_active_zone"),
        r"fields\.(?:distance_pct|distance_to_(?:lower|upper)_pct)",
        "distance_to_zone_pct",
        "pct",
    ),
    NumericFieldRule(("chart_box",), r"fields\.box_(?:low|high)", "box_boundary_price", "currency"),
    NumericFieldRule(("chart_box",), r"fields\.width_pct", "box_width_pct", "pct"),
    NumericFieldRule(("chart_major_swing",), r"fields\.price", "major_swing_price", "currency"),
    NumericFieldRule(
        ("chart_fibonacci",),
        r"fields\.(?:low_price|high_price)",
        "fibonacci_anchor_price",
        "currency",
    ),
    NumericFieldRule(
        ("chart_fibonacci",),
        r"fields\.retracements\..+",
        "fibonacci_retracement_price",
        "currency",
    ),
    NumericFieldRule(
        ("chart_fibonacci",),
        r"fields\.extensions\..+",
        "fibonacci_extension_price",
        "currency",
    ),
    NumericFieldRule(
        ("chart_invalidation",),
        r"fields\.price",
        "chart_invalidation_price",
        "currency",
    ),
    NumericFieldRule(
        ("chart_invalidation",),
        r"fields\.support_low",
        "support_zone_price",
        "currency",
    ),
    NumericFieldRule(
        ("chart_invalidation",), r"fields\.entry", "scenario_entry_price", "currency"
    ),
    NumericFieldRule(
        ("chart_invalidation",), r"fields\.buffer", "chart_price_risk", "currency"
    ),
    NumericFieldRule(
        ("chart_risk_reward",), r"fields\.entry", "scenario_entry_price", "currency"
    ),
    NumericFieldRule(
        ("chart_risk_reward",), r"fields\.target", "chart_target_price", "currency"
    ),
    NumericFieldRule(
        ("chart_risk_reward",),
        r"fields\.invalidation",
        "chart_invalidation_price",
        "currency",
    ),
    NumericFieldRule(
        ("chart_risk_reward",),
        r"fields\.(?:upside|downside)",
        "chart_price_risk",
        "currency",
    ),
    NumericFieldRule(("chart_risk_reward",), r"fields\.ratio", "risk_reward_ratio", "x"),
    NumericFieldRule(("night_futures",), r"fields\.value", "futures_close", "points"),
    NumericFieldRule(
        ("night_futures",),
        r"fields\.change_value",
        "futures_point_change",
        "points",
    ),
    NumericFieldRule(
        ("night_futures",),
        r"fields\.change_pct",
        "futures_return_pct",
        "pct",
    ),
    NumericFieldRule(("fx",), r"fields\.value", "fx_rate", "KRW"),
    NumericFieldRule(("fx",), r"fields\.change_value", "fx_point_change", "KRW"),
    NumericFieldRule(("fx",), r"fields\.change_pct", "fx_return_pct", "pct"),
    NumericFieldRule(
        ("market_return",),
        r"fields\.(?:percent_change|change_pct)",
        "market_return_pct",
        "pct",
    ),
)


def semantic_spec(semantic_type: str) -> NumericSemanticSpec | None:
    return NUMERIC_SEMANTICS.get(semantic_type)


def resolve_numeric_semantic(
    fact_type: str,
    field_path: str,
    fields: dict[str, object],
) -> tuple[NumericSemanticSpec | None, str]:
    for rule in _FIELD_RULES:
        if (
            (fact_type in rule.fact_types or "*" in rule.fact_types)
            and re.fullmatch(rule.field_pattern, field_path)
        ):
            spec = semantic_spec(rule.semantic_type)
            if spec is None:
                return None, "number"
            unit = _currency_for_path(field_path, fields) if rule.unit == "currency" else rule.unit
            return spec, unit
    return None, "number"


def _currency_for_path(field_path: str, fields: dict[str, object]) -> str:
    if field_path.endswith(".value"):
        node: object = fields
        for part in field_path.rsplit(".", 1)[0].split(".")[1:]:
            node = node.get(part) if isinstance(node, dict) else None
        if isinstance(node, dict) and node.get("currency"):
            return str(node["currency"])
    return str(fields.get("currency") or "unknown")


def usage_matches_semantic(semantic_type: str, usage: str) -> bool:
    spec = semantic_spec(semantic_type)
    if spec is None or not spec.prose_allowed:
        return False
    lowered = usage.lower()
    return any(re.search(pattern, lowered) for pattern in spec.usage_patterns)


def usage_direction_matches(semantic_type: str, value: float, usage: str) -> bool:
    spec = semantic_spec(semantic_type)
    if spec is None or spec.formatter != "signed_shares":
        return True
    lowered = usage.lower()
    sell = "순매도" in usage or "net sell" in lowered
    buy = "순매수" in usage or "net buy" in lowered
    if value < 0:
        return sell and not buy
    if value > 0:
        return buy and not sell
    return True


def _plain_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.12g}"


def approved_display_variants(
    spec: NumericSemanticSpec,
    value: float,
    unit: str,
) -> list[str]:
    variants = [_plain_number(value), f"{value:,.12g}"]
    if unit == "pct":
        for digits in (1, 2, 4):
            rounded = _plain_number(float(round(value, digits)))
            variants.extend((f"{rounded}%", f"약 {rounded}%"))
    elif unit == "KRW":
        if spec.formatter == "currency_amount":
            if compact := compact_krw_amount(value):
                variants.append(compact)
        variants.extend((f"{_plain_number(value)} KRW", f"{value:,.0f}원"))
    elif unit == "USD":
        variants.extend((f"${_plain_number(value)}", f"{_plain_number(value)} USD"))
    elif unit in {"JPY", "EUR"}:
        variants.append(f"{_plain_number(value)} {unit}")
    elif unit == "shares":
        variants.append(f"{value:,.0f}주")
        if spec.formatter == "signed_shares":
            variants.append(f"{abs(value):,.0f}주")
    elif unit == "x":
        variants.append(f"{_plain_number(value)}배")
        for digits in (1, 2, 4):
            variants.append(f"{_plain_number(float(round(value, digits)))}배")
    elif unit == "points":
        variants.extend(
            (f"{_plain_number(value)}pt", f"{_plain_number(value)}포인트")
        )
    return list(dict.fromkeys(variants))


def build_numeric_registry(
    facts: list[dict[str, object]],
) -> list[dict[str, object]]:
    registry: list[dict[str, object]] = []
    for fact in facts:
        fact_id = str(fact.get("fact_id") or "")
        fact_type = str(fact.get("fact_type") or "")
        fields = fact.get("fields")
        if not fact_id or not isinstance(fields, dict):
            continue

        def walk(value: object, path: str) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    walk(item, f"{path}.{key}")
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    walk(item, f"{path}.{index}")
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                spec, unit = resolve_numeric_semantic(fact_type, path, fields)
                registered = spec is not None
                prose_allowed = bool(
                    spec is not None
                    and spec.prose_allowed
                    and unit in spec.units
                    and unit != "unknown"
                )
                registry.append(
                    {
                        "fact_id": fact_id,
                        "field_path": path,
                        "value": value,
                        "unit": unit,
                        "semantic_type": (
                            spec.semantic_type
                            if spec is not None
                            else f"unregistered:{fact_type}:{path}"
                        ),
                        "registered": registered,
                        "prose_allowed": prose_allowed,
                        "formatter": spec.formatter if spec is not None else None,
                        "approved_labels": (
                            list(spec.approved_labels) if spec is not None else []
                        ),
                        "approved_display_variants": (
                            approved_display_variants(spec, float(value), unit)
                            if spec is not None and prose_allowed
                            else []
                        ),
                    }
                )

        walk(fields, "fields")
    return registry


def numeric_registry_coverage(
    registries: list[list[dict[str, object]]],
) -> dict[str, object]:
    entries = [item for registry in registries for item in registry]
    unsupported = [
        f"{item.get('fact_id')}:{item.get('field_path')}"
        for item in entries
        if item.get("registered") is not True
    ]
    return {
        "entry_count": len(entries),
        "registered_count": sum(item.get("registered") is True for item in entries),
        "prose_allowed_count": sum(item.get("prose_allowed") is True for item in entries),
        "prose_denied_count": sum(item.get("prose_allowed") is not True for item in entries),
        "unsupported": unsupported,
        "ready": not unsupported,
    }
