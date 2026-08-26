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
    "inventory_growth_signed_gap_pct_point": _spec(
        "inventory_growth_signed_gap_pct_point",
        ("pct_point",),
        ("재고 증가율 방향 격차", "Directional inventory growth gap"),
        (
            r"재고\s*증가율.*(?:매출|매출원가)\s*증가율.*(?:앞섰|밑돌)",
            r"inventory growth.*(?:revenue|cogs).*(?:higher|lower|above|below|trails?|exceeds?)",
        ),
        "directional_percentage_point",
    ),
    "inventory_growth_absolute_gap_pct_point": _spec(
        "inventory_growth_absolute_gap_pct_point",
        ("pct_point",),
        ("재고 증가율 절대 격차", "Absolute inventory growth gap"),
        (
            r"재고\s*증가율.*(?:절대\s*)?(?:차이|격차)",
            r"absolute inventory growth gap|inventory growth.*difference",
        ),
        "percentage_point",
    ),
    "operating_cash_flow": _spec(
        "operating_cash_flow",
        ("KRW", "USD", "TWD", "JPY", "EUR"),
        ("영업현금흐름", "OCF", "operating cash flow"),
        (r"영업현금흐름", r"\bocf\b", r"operating cash flow"),
        "currency_amount",
    ),
    "ppe_capex_cash_outflow": _spec(
        "ppe_capex_cash_outflow",
        ("KRW", "USD", "TWD", "JPY", "EUR"),
        ("PPE 취득 현금지출", "PPE CAPEX", "PPE cash outflow"),
        (
            r"ppe\s*(?:취득\s*현금지출|capex|투자)",
            r"ppe cash outflow",
        ),
        "currency_amount",
    ),
    "free_cash_flow_ppe": _spec(
        "free_cash_flow_ppe",
        ("KRW", "USD", "TWD", "JPY", "EUR"),
        (
            "PPE 투자 후 잉여현금흐름",
            "잉여현금흐름(OCF-PPE CAPEX 기준)",
            "PPE-only FCF",
        ),
        (
            r"ppe\s*(?:투자\s*후|기준|[- ]?only).*?(?:잉여현금흐름|fcf)",
            r"잉여현금흐름\s*\(\s*ocf\s*-\s*ppe\s*capex\s*기준\s*\)",
        ),
        "currency_amount",
    ),
    "revenue": _spec(
        "revenue",
        ("KRW", "USD", "TWD", "JPY", "EUR"),
        ("매출", "매출액", "revenue"),
        (r"매출(?:액)?", r"\brevenue\b"),
        "currency_amount",
    ),
    "operating_income": _spec(
        "operating_income",
        ("KRW", "USD", "TWD", "JPY", "EUR"),
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
        (
            r"(?:매출.*(?:qoq|전분기)|(?:qoq|전분기).*매출)",
            r"(?:revenue.*qoq|qoq.*revenue)",
        ),
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
        (
            r"(?:영업이익.*(?:qoq|전분기)|(?:qoq|전분기).*영업이익)",
            r"(?:operating income.*qoq|qoq.*operating income)",
        ),
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
        ("KRW", "USD", "TWD", "JPY", "EUR"),
        ("TTM EPS", "최근 4개 분기 EPS"),
        (r"ttm\s*eps", r"최근\s*4개\s*분기\s*eps"),
        "currency",
    ),
    "bvps": _spec(
        "bvps",
        ("KRW", "USD", "TWD", "JPY", "EUR"),
        ("BVPS", "주당순자산"),
        (r"\bbvps\b", r"주당순자산"),
        "currency",
    ),
    "forward_eps": _spec(
        "forward_eps",
        ("KRW", "USD", "TWD", "JPY", "EUR"),
        ("예상 EPS", "추정 EPS", "forward EPS"),
        (r"(?:예상|추정)\s*eps", r"forward\s*eps"),
        "currency",
    ),
    "forward_bvps": _spec(
        "forward_bvps",
        ("KRW", "USD", "TWD", "JPY", "EUR"),
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
        ("외국인 당일 순매수", "외국인 당일 순매도"),
        (r"외국인.*(?:당일)?.*(?:순매수|순매도)", r"foreign.*net (?:buy|sell)"),
        "signed_shares",
    ),
    "institution_net_buy_qty": _spec(
        "institution_net_buy_qty",
        ("shares",),
        ("기관 당일 순매수", "기관 당일 순매도"),
        (r"기관.*(?:당일)?.*(?:순매수|순매도)", r"institution.*net (?:buy|sell)"),
        "signed_shares",
    ),
    "individual_net_buy_qty": _spec(
        "individual_net_buy_qty",
        ("shares",),
        ("개인 당일 순매수", "개인 당일 순매도"),
        (r"개인.*(?:당일)?.*(?:순매수|순매도)", r"individual.*net (?:buy|sell)"),
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
        scope="both",
    ),
    "fx_point_change": _spec(
        "fx_point_change",
        ("KRW",),
        ("환율 변동폭", "exchange-rate change"),
        (r"환율.*(?:변동폭|등락폭)", r"exchange[- ]rate change"),
        "signed_currency",
        scope="both",
    ),
    "fx_return_pct": _spec(
        "fx_return_pct",
        ("pct",),
        ("환율 등락률", "exchange-rate return"),
        (r"환율.*(?:등락률|상승|하락)", r"exchange[- ]rate.*(?:return|change)"),
        "signed_percentage",
        scope="both",
    ),
    "market_return_pct": _spec(
        "market_return_pct",
        ("pct",),
        ("시장 등락률", "지수 등락률", "market return"),
        (r"(?:시장|지수).*등락률", r"market.*(?:return|change)"),
        "signed_percentage",
        scope="market",
    ),
    "index_return_pct": _spec(
        "index_return_pct",
        ("pct",),
        ("S&P500 등락률", "Nasdaq 등락률", "Russell 2000 등락률"),
        (r"(?:s&p\s*500|nasdaq|russell\s*2000|지수).*(?:등락|수익|상승|하락)",),
        "signed_percentage",
        scope="both",
    ),
    "sector_return_pct": _spec(
        "sector_return_pct",
        ("pct",),
        ("반도체 업종 등락률", "SOXX 등락률", "섹터 ETF 등락률"),
        (r"(?:반도체|soxx|xl[a-z]{1,2}|섹터).*(?:등락|수익|상승|하락)",),
        "signed_percentage",
        scope="both",
    ),
    "sector_proxy_level": _spec(
        "sector_proxy_level",
        ("index",),
        ("섹터 ETF 수준", "sector proxy level"),
        (r"(?:soxx|xl[a-z]{1,2}|섹터).*(?:수준|종가|level|close)",),
        "index",
        scope="market",
    ),
    "style_return_pct": _spec(
        "style_return_pct",
        ("pct",),
        ("S&P500 동일가중 등락률", "RSP 등락률"),
        (r"(?:s&p\s*500\s*동일가중|rsp).*(?:등락|수익|상승|하락)",),
        "signed_percentage",
        scope="market",
    ),
    "style_proxy_level": _spec(
        "style_proxy_level",
        ("index",),
        ("S&P500 동일가중 수준", "RSP level"),
        (r"(?:s&p\s*500\s*동일가중|rsp).*(?:수준|종가|level|close)",),
        "index",
        scope="market",
    ),
    "growth_relative_return_pct": _spec(
        "growth_relative_return_pct",
        ("pct",),
        ("Nasdaq 상대수익률", "S&P500 대비 Nasdaq"),
        (r"(?:nasdaq.*상대수익률|s&p\s*500.*대비.*nasdaq|nasdaq.*웃돌|nasdaq.*밑돌)",),
        "signed_percentage",
        scope="both",
    ),
    "sector_relative_return_pct": _spec(
        "sector_relative_return_pct",
        ("pct",),
        ("반도체 상대수익률", "S&P500 대비 반도체"),
        (r"(?:반도체.*상대수익률|s&p\s*500.*대비.*반도체|반도체.*웃돌|반도체.*밑돌)",),
        "signed_percentage",
        scope="both",
    ),
    "style_relative_return_pct": _spec(
        "style_relative_return_pct",
        ("pct",),
        ("S&P500 대비 동일가중 상대수익률", "RSP 상대수익률"),
        (
            r"(?:s&p\s*500.*대비.*동일가중|rsp.*상대수익률|동일가중.*(?:웃돌|밑돌))",
        ),
        "signed_percentage",
        scope="market",
    ),
    "market_index_close": _spec(
        "market_index_close", ("index",), ("시장 지수 종가", "index close"),
        (r"(?:시장|지수).*종가", r"index close"), "index", scope="market",
    ),
    "market_eligible_count": _spec(
        "market_eligible_count", ("count",), ("적격 종목 수",),
        (r"적격.*종목.*수", r"eligible.*count"), "count", scope="market",
    ),
    "market_advance_count": _spec(
        "market_advance_count", ("count",), ("상승 종목 수",),
        (r"상승.*종목.*수", r"advance.*count"), "count", scope="market",
    ),
    "market_decline_count": _spec(
        "market_decline_count", ("count",), ("하락 종목 수",),
        (r"하락.*종목.*수", r"decline.*count"), "count", scope="market",
    ),
    "market_unchanged_count": _spec(
        "market_unchanged_count", ("count",), ("보합 종목 수",),
        (r"보합.*종목.*수", r"unchanged.*count"), "count", scope="market",
    ),
    "sector_listed_issue_count": _spec(
        "sector_listed_issue_count", ("count",), ("업종 상장 종목 수",),
        (r"(?:업종|섹터).*상장.*종목.*수", r"sector.*listed.*count"), "count", scope="market",
    ),
    "sector_advance_count": _spec(
        "sector_advance_count", ("count",), ("업종 상승 종목 수",),
        (r"(?:업종|섹터).*상승.*종목.*수", r"sector.*advance.*count"), "count", scope="market",
    ),
    "sector_decline_count": _spec(
        "sector_decline_count", ("count",), ("업종 하락 종목 수",),
        (r"(?:업종|섹터).*하락.*종목.*수", r"sector.*decline.*count"), "count", scope="market",
    ),
    "sector_unchanged_count": _spec(
        "sector_unchanged_count", ("count",), ("업종 보합 종목 수",),
        (r"(?:업종|섹터).*보합.*종목.*수", r"sector.*unchanged.*count"), "count", scope="market",
    ),
    "sector_limit_up_count_audit": _spec(
        "sector_limit_up_count_audit", ("count",), (), (), "count",
        prose_allowed=False, scope="market",
    ),
    "sector_limit_down_count_audit": _spec(
        "sector_limit_down_count_audit", ("count",), (), (), "count",
        prose_allowed=False, scope="market",
    ),
    "market_advance_ratio": _spec(
        "market_advance_ratio", ("pct",), ("상승 종목 비율",),
        (r"상승.*종목.*비율", r"advance.*ratio"), "percentage", scope="market",
    ),
    "market_positive_return_pct": _spec(
        "market_positive_return_pct", ("pct",), ("양의 수익률 종목 비율",),
        (r"양의.*수익률.*종목.*비율", r"positive.*return.*pct"), "percentage", scope="market",
    ),
    "market_negative_return_pct": _spec(
        "market_negative_return_pct", ("pct",), ("음의 수익률 종목 비율",),
        (r"음의.*수익률.*종목.*비율", r"negative.*return.*pct"), "percentage", scope="market",
    ),
    "market_ad_ratio": _spec(
        "market_ad_ratio", ("x",), ("상승/하락 종목 비율", "A/D ratio"),
        (r"(?:상승/하락|a/d).*비율", r"a/d ratio"), "multiple", scope="market",
    ),
    "market_median_return_pct": _spec(
        "market_median_return_pct", ("pct",), ("종목 수익률 중앙값",),
        (r"종목.*수익률.*중앙값", r"median.*return"), "signed_percentage", scope="market",
    ),
    "market_equal_weight_return_pct": _spec(
        "market_equal_weight_return_pct", ("pct",), ("동일가중 수익률",),
        (r"동일가중.*수익률", r"equal.weight.*return"), "signed_percentage", scope="market",
    ),
    "market_concentration_gap_pct": _spec(
        "market_concentration_gap_pct", ("pct",), ("집중도 격차",),
        (r"집중도.*격차", r"concentration.*gap"), "signed_percentage", scope="market",
    ),
    "market_total_volume": _spec(
        "market_total_volume", ("shares",), ("시장 총거래량",),
        (r"시장.*총거래량", r"market.*total volume"), "shares", scope="market",
    ),
    "market_total_trading_value": _spec(
        "market_total_trading_value", ("KRW", "USD"), ("시장 총거래대금",),
        (r"시장.*총거래대금", r"market.*trading value"), "currency_amount", scope="market",
    ),
    "market_foreign_net_buy_amount": _spec(
        "market_foreign_net_buy_amount", ("KRW", "USD"), ("시장 외국인 순매수",),
        (r"시장.*외국인.*순매수",), "currency_amount", scope="market",
    ),
    "market_institution_net_buy_amount": _spec(
        "market_institution_net_buy_amount", ("KRW", "USD"), ("시장 기관 순매수",),
        (r"시장.*기관.*순매수",), "currency_amount", scope="market",
    ),
    "market_retail_net_buy_amount": _spec(
        "market_retail_net_buy_amount", ("KRW", "USD"), ("시장 개인 순매수",),
        (r"시장.*개인.*순매수",), "currency_amount", scope="market",
    ),
    "nominal_yield_level": _spec(
        "nominal_yield_level",
        ("pct",),
        ("미국 10년물 금리", "US 10-year yield"),
        (r"(?:미국|us).*10년물.*(?:금리|yield)",),
        "percentage",
        scope="both",
    ),
    "nominal_yield_change_bp": _spec(
        "nominal_yield_change_bp",
        ("bp",),
        ("미국 10년물 금리 변동", "US 10-year yield change"),
        (r"(?:미국|us).*10년물.*(?:금리|yield)",),
        "signed_basis_points",
        scope="both",
    ),
    "real_yield_level": _spec(
        "real_yield_level",
        ("pct",),
        ("미국 10년물 실질금리", "US 10-year real yield"),
        (r"(?:미국|us).*(?:10년물|장기).*실질금리|real yield",),
        "percentage",
        scope="both",
    ),
    "real_yield_change_bp": _spec(
        "real_yield_change_bp",
        ("bp",),
        ("미국 10년물 실질금리 변동", "US 10-year real-yield change"),
        (
            r"(?:미국|us).*(?:10년물|장기).*실질금리.*(?:변동|change)"
            r"|real yield.*change",
        ),
        "signed_basis_points",
        scope="both",
    ),
    "breakeven_inflation_level": _spec(
        "breakeven_inflation_level",
        ("pct",),
        ("미국 기대인플레이션", "US breakeven inflation"),
        (r"기대인플레이션|breakeven inflation",),
        "percentage",
        scope="both",
    ),
    "breakeven_inflation_change_bp": _spec(
        "breakeven_inflation_change_bp",
        ("bp",),
        ("미국 기대인플레이션 변동", "US breakeven-inflation change"),
        (r"기대인플레이션|breakeven inflation",),
        "signed_basis_points",
        scope="both",
    ),
    "credit_spread_level": _spec(
        "credit_spread_level",
        ("pct",),
        ("하이일드 신용스프레드", "high-yield credit spread"),
        (r"(?:하이일드|high.?yield).*신용?스프레드|credit spread",),
        "percentage",
        scope="both",
    ),
    "credit_spread_change_bp": _spec(
        "credit_spread_change_bp",
        ("bp",),
        ("하이일드 신용스프레드 변동", "high-yield spread change"),
        (r"(?:하이일드|high.?yield).*신용?스프레드|credit spread",),
        "signed_basis_points",
        scope="both",
    ),
    "oil_price": _spec(
        "oil_price",
        ("USD_per_barrel",),
        ("WTI 유가", "WTI oil price"),
        (r"(?:wti|유가)",),
        "usd_per_barrel",
        scope="both",
    ),
    "oil_return_pct": _spec(
        "oil_return_pct",
        ("pct",),
        ("WTI 등락률", "WTI return"),
        (r"(?:wti|유가).*(?:등락|수익|상승|하락|return)",),
        "signed_percentage",
        scope="both",
    ),
    "volatility_index_level": _spec(
        "volatility_index_level",
        ("index",),
        ("VIX", "변동성지수"),
        (r"(?:vix|변동성지수)",),
        "index",
        scope="both",
    ),
    "volatility_return_pct": _spec(
        "volatility_return_pct",
        ("pct",),
        ("VIX 등락률", "VIX return"),
        (r"(?:vix|변동성지수).*(?:등락|수익|상승|하락|return)",),
        "signed_percentage",
        scope="both",
    ),
    "dollar_index_level": _spec(
        "dollar_index_level",
        ("index",),
        ("미 달러지수", "broad dollar index"),
        (r"(?:미\s*달러지수|broad dollar index)",),
        "index",
        scope="both",
    ),
    "dollar_index_return_pct": _spec(
        "dollar_index_return_pct",
        ("pct",),
        ("미 달러지수 등락률", "broad dollar-index return"),
        (r"(?:미\s*달러지수|broad dollar index).*(?:등락|수익|상승|하락|return)",),
        "signed_percentage",
        scope="both",
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
        "risk_reward_ratio",
        ("x",),
        ("차트 손익비", "RR"),
        (r"(?:차트\s*)?손익비", r"\brr\b", r"risk.?reward"),
        "multiple",
    ),
    "current_price_risk_reward_ratio": _spec(
        "current_price_risk_reward_ratio",
        ("x",),
        ("현재가 기준 차트 손익비",),
        (r"현재가\s*기준\s*차트\s*손익비", r"current price.*risk.?reward"),
        "multiple",
    ),
    "support_entry_risk_reward_ratio": _spec(
        "support_entry_risk_reward_ratio",
        ("x",),
        ("동적 지지 접근 가정 차트 손익비",),
        (
            r"동적\s*지지\s*접근\s*가정\s*차트\s*손익비",
            r"support entry.*risk.?reward",
        ),
        "multiple",
    ),
    "previous_risk_reward_ratio": _spec(
        "previous_risk_reward_ratio", ("x",), ("이전 차트 손익비",),
        (r"이전.*(?:차트\s*)?손익비", r"previous.*risk.?reward"), "multiple",
    ),
    "current_risk_reward_ratio": _spec(
        "current_risk_reward_ratio", ("x",), ("현재 차트 손익비",),
        (r"현재.*(?:차트\s*)?손익비", r"current.*risk.?reward"), "multiple",
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
    "peer_pe_multiple": _spec(
        "peer_pe_multiple",
        ("x",),
        ("peer PER 중앙값", "동종업계 PER 중앙값", "비교군 PER"),
        (
            r"(?:peer|동종업계|비교군).*per",
            r"per.*(?:peer|동종업계|비교군)",
        ),
        "multiple",
    ),
    "peer_pb_multiple": _spec(
        "peer_pb_multiple",
        ("x",),
        ("peer PBR 중앙값", "동종업계 PBR 중앙값", "비교군 PBR"),
        (
            r"(?:peer|동종업계|비교군).*pbr",
            r"pbr.*(?:peer|동종업계|비교군)",
        ),
        "multiple",
    ),
    "peer_sample_count": _spec(
        "peer_sample_count",
        ("count",),
        ("비교군 표본 수",),
        (r"비교군\s*표본\s*수", r"peer sample"),
        "count",
    ),
    "peer_pe_relative_pct": _spec(
        "peer_pe_relative_pct",
        ("pct",),
        ("peer PER 대비", "PER peer 프리미엄", "PER peer 할인"),
        (r"(?:peer|동종업계|비교군).*per.*(?:대비|프리미엄|할인)",),
        "signed_percentage",
    ),
    "peer_pb_relative_pct": _spec(
        "peer_pb_relative_pct",
        ("pct",),
        ("peer PBR 대비", "PBR peer 프리미엄", "PBR peer 할인"),
        (r"(?:peer|동종업계|비교군).*pbr.*(?:대비|프리미엄|할인)",),
        "signed_percentage",
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


_INVESTOR_FLOW_WINDOWS = ("1d", "5d", "20d")
_INVESTOR_FLOW_PARTICIPANTS = (
    "foreign",
    "institution",
    "individual",
    "other_corporation",
    "domestic_foreign",
)
_INVESTOR_FLOW_RECONCILIATION_RULES: list[NumericFieldRule] = []

for _window in _INVESTOR_FLOW_WINDOWS:
    for _participant in _INVESTOR_FLOW_PARTICIPANTS:
        _semantic_type = (
            f"investor_flow_{_participant}_net_buy_qty_{_window}_audit"
        )
        NUMERIC_SEMANTICS[_semantic_type] = _spec(
            _semantic_type,
            ("shares",),
            (),
            (),
            "signed_shares",
            prose_allowed=False,
        )
        _INVESTOR_FLOW_RECONCILIATION_RULES.append(
            NumericFieldRule(
                ("positioning",),
                rf"fields\.reconciliations\.{_window}\.participant_flows\.{_participant}",
                _semantic_type,
                "shares",
            )
        )
    for _field in ("displayed_net", "omitted_net", "all_participant_net"):
        _semantic_type = f"investor_flow_{_field}_qty_{_window}_audit"
        NUMERIC_SEMANTICS[_semantic_type] = _spec(
            _semantic_type,
            ("shares",),
            (),
            (),
            "signed_shares",
            prose_allowed=False,
        )
        _INVESTOR_FLOW_RECONCILIATION_RULES.append(
            NumericFieldRule(
                ("positioning",),
                rf"fields\.reconciliations\.{_window}\.{_field}",
                _semantic_type,
                "shares",
            )
        )
    for _field, _unit in (
        ("constituent_count", "count"),
        ("display_coverage_ratio", "number"),
    ):
        _semantic_type = f"investor_flow_{_field}_{_window}_audit"
        NUMERIC_SEMANTICS[_semantic_type] = _spec(
            _semantic_type,
            (_unit,),
            (),
            (),
            "integer" if _unit == "count" else "decimal",
            prose_allowed=False,
        )
        _INVESTOR_FLOW_RECONCILIATION_RULES.append(
            NumericFieldRule(
                ("positioning",),
                rf"fields\.reconciliations\.{_window}\.{_field}",
                _semantic_type,
                _unit,
            )
        )


_FIELD_RULES = (
    *_INVESTOR_FLOW_RECONCILIATION_RULES,
    NumericFieldRule(
        ("working_capital_inventory_relation",),
        r"fields\.gap_percentage_points_signed",
        "inventory_growth_signed_gap_pct_point",
        "pct_point",
    ),
    NumericFieldRule(
        ("working_capital_inventory_relation",),
        r"fields\.gap_percentage_points_abs",
        "inventory_growth_absolute_gap_pct_point",
        "pct_point",
    ),
    NumericFieldRule(
        ("cash_flow_ocf",),
        r"fields\.value",
        "operating_cash_flow",
        "currency",
    ),
    NumericFieldRule(
        ("cash_flow_ppe_capex",),
        r"fields\.value",
        "ppe_capex_cash_outflow",
        "currency",
    ),
    NumericFieldRule(
        ("cash_flow_fcf_ppe",),
        r"fields\.value",
        "free_cash_flow_ppe",
        "currency",
    ),
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
        ("peer_valuation",),
        r"fields\.pe_(?:median|mean|percentile_25|percentile_75)",
        "peer_pe_multiple",
        "x",
    ),
    NumericFieldRule(
        ("peer_valuation",),
        r"fields\.pb_(?:median|mean|percentile_25|percentile_75)",
        "peer_pb_multiple",
        "x",
    ),
    NumericFieldRule(
        ("peer_valuation",),
        r"fields\.company_pe_vs_median_pct",
        "peer_pe_relative_pct",
        "pct",
    ),
    NumericFieldRule(
        ("peer_valuation",),
        r"fields\.company_pb_vs_median_pct",
        "peer_pb_relative_pct",
        "pct",
    ),
    NumericFieldRule(
        ("peer_valuation",),
        r"fields\.(?:pe|pb)_sample_count",
        "audit_count",
        "count",
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
        ("chart_risk_reward_current_price", "chart_risk_reward_support_entry"),
        r"fields\.entry",
        "scenario_entry_price",
        "currency",
    ),
    NumericFieldRule(
        ("chart_risk_reward_current_price", "chart_risk_reward_support_entry"),
        r"fields\.target",
        "chart_target_price",
        "currency",
    ),
    NumericFieldRule(
        ("chart_risk_reward_current_price", "chart_risk_reward_support_entry"),
        r"fields\.invalidation",
        "chart_invalidation_price",
        "currency",
    ),
    NumericFieldRule(
        ("chart_risk_reward_current_price", "chart_risk_reward_support_entry"),
        r"fields\.(?:upside|downside)",
        "chart_price_risk",
        "currency",
    ),
    NumericFieldRule(
        ("chart_risk_reward",), r"fields\.ratio", "risk_reward_ratio", "x"
    ),
    NumericFieldRule(
        ("chart_risk_reward_current_price",),
        r"fields\.ratio",
        "current_price_risk_reward_ratio",
        "x",
    ),
    NumericFieldRule(
        ("chart_risk_reward_support_entry",),
        r"fields\.ratio",
        "support_entry_risk_reward_ratio",
        "x",
    ),
    NumericFieldRule(
        ("monitoring_metric_transition",),
        r"fields\.previous_ratio",
        "previous_risk_reward_ratio",
        "x",
    ),
    NumericFieldRule(
        ("monitoring_metric_transition",),
        r"fields\.current_ratio",
        "current_risk_reward_ratio",
        "x",
    ),
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
    NumericFieldRule(
        ("market_index",), r"fields\.return_pct", "index_return_pct", "pct"
    ),
    NumericFieldRule(
        ("market_sector",), r"fields\.return_pct", "sector_return_pct", "pct"
    ),
    NumericFieldRule(
        ("market_sector",), r"fields\.level", "sector_proxy_level", "index"
    ),
    NumericFieldRule(
        ("market_style",), r"fields\.return_pct", "style_return_pct", "pct"
    ),
    NumericFieldRule(
        ("market_style",), r"fields\.level", "style_proxy_level", "index"
    ),
    NumericFieldRule(
        ("market_growth_relative",),
        r"fields\.relative_return_pct",
        "growth_relative_return_pct",
        "pct",
    ),
    NumericFieldRule(
        ("market_sector_relative",),
        r"fields\.relative_return_pct",
        "sector_relative_return_pct",
        "pct",
    ),
    NumericFieldRule(
        ("market_style_relative",),
        r"fields\.relative_return_pct",
        "style_relative_return_pct",
        "pct",
    ),
    NumericFieldRule(("market_cross_section_index",), r"fields\.close", "market_index_close", "index"),
    NumericFieldRule(("market_cross_section_index",), r"fields\.return_pct", "index_return_pct", "pct"),
    NumericFieldRule(("market_cross_section_sector",), r"fields\.return_pct", "sector_return_pct", "pct"),
    NumericFieldRule(("market_cross_section_sector",), r"fields\.advance_ratio_pct", "market_advance_ratio", "pct"),
    NumericFieldRule(("market_cross_section_sector",), r"fields\.relative_return_pct", "sector_relative_return_pct", "pct"),
    NumericFieldRule(("market_cross_section_sector",), r"fields\.listed_count", "sector_listed_issue_count", "count"),
    NumericFieldRule(("market_cross_section_sector",), r"fields\.advance_count", "sector_advance_count", "count"),
    NumericFieldRule(("market_cross_section_sector",), r"fields\.decline_count", "sector_decline_count", "count"),
    NumericFieldRule(("market_cross_section_sector",), r"fields\.unchanged_count", "sector_unchanged_count", "count"),
    NumericFieldRule(("market_cross_section_sector",), r"fields\.limit_up_count", "sector_limit_up_count_audit", "count"),
    NumericFieldRule(("market_cross_section_sector",), r"fields\.limit_down_count", "sector_limit_down_count_audit", "count"),
    NumericFieldRule(("market_breadth_counts",), r"fields\.eligible_count", "market_eligible_count", "count"),
    NumericFieldRule(("market_breadth_counts",), r"fields\.advance_count", "market_advance_count", "count"),
    NumericFieldRule(("market_breadth_counts",), r"fields\.decline_count", "market_decline_count", "count"),
    NumericFieldRule(("market_breadth_counts",), r"fields\.unchanged_count", "market_unchanged_count", "count"),
    NumericFieldRule(("market_breadth_returns",), r"fields\.advance_ratio_pct", "market_advance_ratio", "pct"),
    NumericFieldRule(("market_breadth_returns",), r"fields\.ad_ratio", "market_ad_ratio", "x"),
    NumericFieldRule(("market_breadth_returns",), r"fields\.median_return_pct", "market_median_return_pct", "pct"),
    NumericFieldRule(("market_breadth_returns",), r"fields\.equal_weight_return_pct", "market_equal_weight_return_pct", "pct"),
    NumericFieldRule(("market_breadth_returns",), r"fields\.positive_return_pct", "market_positive_return_pct", "pct"),
    NumericFieldRule(("market_breadth_returns",), r"fields\.negative_return_pct", "market_negative_return_pct", "pct"),
    NumericFieldRule(("market_breadth_activity",), r"fields\.total_trading_volume", "market_total_volume", "shares"),
    NumericFieldRule(("market_breadth_activity",), r"fields\.total_trading_value", "market_total_trading_value", "currency"),
    NumericFieldRule(("market_concentration",), r"fields\.concentration_gap_pct", "market_concentration_gap_pct", "pct"),
    NumericFieldRule(("market_flow",), r"fields\.net_buy_amount", "market_foreign_net_buy_amount", "currency"),
    NumericFieldRule(
        ("market_nominal_yield",),
        r"fields\.level_pct",
        "nominal_yield_level",
        "pct",
    ),
    NumericFieldRule(
        ("market_nominal_yield",),
        r"fields\.change_bp",
        "nominal_yield_change_bp",
        "bp",
    ),
    NumericFieldRule(
        ("market_real_yield",),
        r"fields\.level_pct",
        "real_yield_level",
        "pct",
    ),
    NumericFieldRule(
        ("market_real_yield",),
        r"fields\.change_bp",
        "real_yield_change_bp",
        "bp",
    ),
    NumericFieldRule(
        ("market_breakeven_inflation",),
        r"fields\.level_pct",
        "breakeven_inflation_level",
        "pct",
    ),
    NumericFieldRule(
        ("market_breakeven_inflation",),
        r"fields\.change_bp",
        "breakeven_inflation_change_bp",
        "bp",
    ),
    NumericFieldRule(
        ("market_credit_spread",),
        r"fields\.level_pct",
        "credit_spread_level",
        "pct",
    ),
    NumericFieldRule(
        ("market_credit_spread",),
        r"fields\.change_bp",
        "credit_spread_change_bp",
        "bp",
    ),
    NumericFieldRule(("market_fx",), r"fields\.value", "fx_rate", "KRW"),
    NumericFieldRule(
        ("market_fx",), r"fields\.change_pct", "fx_return_pct", "pct"
    ),
    NumericFieldRule(
        ("market_oil",), r"fields\.price_usd_per_barrel", "oil_price", "USD_per_barrel"
    ),
    NumericFieldRule(
        ("market_oil",), r"fields\.return_pct", "oil_return_pct", "pct"
    ),
    NumericFieldRule(
        ("market_volatility",),
        r"fields\.level",
        "volatility_index_level",
        "index",
    ),
    NumericFieldRule(
        ("market_volatility",),
        r"fields\.return_pct",
        "volatility_return_pct",
        "pct",
    ),
    NumericFieldRule(
        ("market_dollar_index",),
        r"fields\.level",
        "dollar_index_level",
        "index",
    ),
    NumericFieldRule(
        ("market_dollar_index",),
        r"fields\.return_pct",
        "dollar_index_return_pct",
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
    if fact_type == "market_flow" and field_path == "fields.net_buy_amount":
        actor = str(fields.get("actor") or "")
        semantic_type = {
            "foreign": "market_foreign_net_buy_amount",
            "institution": "market_institution_net_buy_amount",
            "retail": "market_retail_net_buy_amount",
        }.get(actor)
        if semantic_type is None:
            return None, "number"
        return semantic_spec(semantic_type), str(fields.get("currency") or "unknown")
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


_INDEX_SERIES_LABELS = {
    "SPY": "S&P500",
    "QQQ": "Nasdaq",
    "IWM": "Russell 2000",
}
_RELATIVE_SERIES_LABELS = {
    **_INDEX_SERIES_LABELS,
    "RSP": "S&P500 동일가중",
    "SOXX": "반도체",
}
_NIGHT_FUTURES_LABELS = {
    "KRX_KOSPI200_NIGHT_FUT": "KOSPI200 야간선물",
    "KRX_KOSDAQ150_NIGHT_FUT": "KOSDAQ150 야간선물",
}
_MARKET_SERIES_LABELS = {
    ("nominal_yield_level", "DGS10"): "미국 10년물 금리",
    ("nominal_yield_change_bp", "DGS10"): "미국 10년물 금리 변동",
    ("real_yield_level", "DFII10"): "미국 10년물 실질금리",
    ("real_yield_change_bp", "DFII10"): "미국 10년물 실질금리 변동",
    ("breakeven_inflation_level", "T10YIE"): "미국 기대인플레이션",
    ("breakeven_inflation_change_bp", "T10YIE"): "미국 기대인플레이션 변동",
    ("credit_spread_level", "BAMLH0A0HYM2"): "하이일드 신용스프레드",
    ("credit_spread_change_bp", "BAMLH0A0HYM2"): "하이일드 신용스프레드 변동",
    ("oil_price", "DCOILWTICO"): "WTI 유가",
    ("oil_return_pct", "DCOILWTICO"): "WTI 등락률",
    ("volatility_index_level", "VIXCLS"): "VIX",
    ("volatility_return_pct", "VIXCLS"): "VIX 등락률",
    ("fx_rate", "USDKRW"): "원/달러 환율",
    ("fx_return_pct", "USDKRW"): "원/달러 환율 등락률",
    ("fx_rate", "USDKRW_KR_CLOSE"): "원/달러 환율",
    ("fx_point_change", "USDKRW_KR_CLOSE"): "원/달러 환율 변동폭",
    ("fx_return_pct", "USDKRW_KR_CLOSE"): "원/달러 환율 등락률",
    ("fx_rate", "JPYKRW100_KR_CLOSE"): "원/100엔 환율",
    ("fx_point_change", "JPYKRW100_KR_CLOSE"): "원/100엔 환율 변동폭",
    ("fx_return_pct", "JPYKRW100_KR_CLOSE"): "원/100엔 환율 등락률",
    ("fx_rate", "EURKRW_KR_CLOSE"): "원/유로 환율",
    ("fx_point_change", "EURKRW_KR_CLOSE"): "원/유로 환율 변동폭",
    ("fx_return_pct", "EURKRW_KR_CLOSE"): "원/유로 환율 등락률",
}
_SOURCE_LABEL_SEMANTICS = {
    "forward_eps",
    "forward_pe",
    "forward_bvps",
    "forward_price_to_book",
    "historical_pe_multiple",
    "historical_pb_multiple",
}
_FINANCIAL_PERIOD_LABEL_SEMANTICS = {
    "revenue",
    "operating_income",
    "net_income",
    "operating_margin",
    "revenue_qoq",
    "revenue_yoy",
    "operating_income_qoq",
    "operating_income_yoy",
}
_INSTRUMENT_LABEL_SEMANTICS = {
    "index_return_pct",
    "sector_return_pct",
    "sector_proxy_level",
    "style_return_pct",
    "style_proxy_level",
    "growth_relative_return_pct",
    "sector_relative_return_pct",
    "style_relative_return_pct",
    "futures_close",
    "futures_point_change",
    "futures_return_pct",
    "sector_listed_issue_count",
    "sector_advance_count",
    "sector_decline_count",
    "sector_unchanged_count",
    *{semantic for semantic, _ in _MARKET_SERIES_LABELS},
}


def _source_label_kind(
    semantic_type: str,
    fields: dict[str, object],
) -> str | None:
    if (
        semantic_type in _FINANCIAL_PERIOD_LABEL_SEMANTICS
        and fields.get("financial_period_required") is True
    ):
        return "period"
    if semantic_type in _SOURCE_LABEL_SEMANTICS:
        return "source"
    if semantic_type in _INSTRUMENT_LABEL_SEMANTICS:
        return "instrument"
    return None


def _source_aware_label(
    semantic_type: str,
    fields: dict[str, object],
    field_path: str = "",
) -> str | None:
    if historical_label := valuation_comparison_label(field_path):
        return historical_label
    if semantic_type in _FINANCIAL_PERIOD_LABEL_SEMANTICS:
        source_fields = {
            "revenue": "latest_revenue",
            "operating_income": "latest_operating_income",
            "operating_margin": "latest_operating_margin",
            "revenue_qoq": "latest_revenue_qoq",
            "revenue_yoy": "latest_revenue_yoy",
            "operating_income_qoq": "latest_operating_income_qoq",
            "operating_income_yoy": "latest_operating_income_yoy",
        }
        field_period_labels = fields.get("field_period_labels")
        period_label = str(
            (
                field_period_labels.get(source_fields.get(semantic_type, ""))
                if isinstance(field_period_labels, dict)
                else None
            )
            or fields.get("period_label")
            or ""
        ).strip()
        spec = semantic_spec(semantic_type)
        period_suffix = {
            "revenue_qoq": "전분기 대비 매출 변화율",
            "revenue_yoy": "전년 동기 대비 매출 성장률",
            "operating_income_qoq": "전분기 대비 영업이익 변화율",
            "operating_income_yoy": "전년 동기 대비 영업이익 성장률",
        }.get(semantic_type)
        if period_label and period_suffix:
            return f"{period_label} {period_suffix}"
        if period_label and spec is not None and spec.approved_labels:
            return f"{period_label} {spec.approved_labels[0]}"
        if fields.get("financial_period_required") is True:
            return None
    series = str(fields.get("series_code") or "")
    if label := _MARKET_SERIES_LABELS.get((semantic_type, series)):
        return label
    if semantic_type in {"forward_eps", "forward_pe"}:
        source = str(fields.get("forward_pe_source") or "")
        if source == "modeled_forward":
            return "내부 추정 EPS" if semantic_type == "forward_eps" else "내부 추정 fPER"
        if source == "consensus_forward":
            return "시장 예상 EPS" if semantic_type == "forward_eps" else "시장 예상 fPER"
    if semantic_type in {"forward_bvps", "forward_price_to_book"}:
        source = str(fields.get("forward_price_to_book_source") or "")
        if source == "modeled_forward":
            return "내부 추정 BVPS" if semantic_type == "forward_bvps" else "내부 추정 fPBR"
        if source == "consensus_forward":
            return "시장 예상 BVPS" if semantic_type == "forward_bvps" else "시장 예상 fPBR"
    if semantic_type == "index_return_pct":
        series = str(fields.get("series_code") or "")
        if label := _INDEX_SERIES_LABELS.get(series):
            return f"{label} 등락률"
    if semantic_type == "sector_return_pct":
        series = str(fields.get("series_code") or "")
        if series == "SOXX":
            return "반도체 업종 등락률"
        if series:
            return f"{series} 업종 등락률"
    if semantic_type == "sector_proxy_level":
        series = str(fields.get("series_code") or "")
        if series:
            return f"{series} 수준"
    if semantic_type.startswith("sector_") and semantic_type.endswith("_count"):
        sector = str(fields.get("sector") or "").strip()
        market_scope = str(fields.get("market_scope") or "").strip()
        if sector:
            prefix = f"{market_scope} {sector}".strip()
            suffix = {
                "sector_listed_issue_count": "상장 종목 수",
                "sector_advance_count": "상승 종목 수",
                "sector_decline_count": "하락 종목 수",
                "sector_unchanged_count": "보합 종목 수",
            }.get(semantic_type)
            if suffix:
                return f"{prefix} {suffix}"
    if semantic_type == "style_return_pct":
        series = str(fields.get("series_code") or "")
        if series == "RSP":
            return "S&P500 동일가중 등락률"
    if semantic_type == "style_proxy_level":
        series = str(fields.get("series_code") or "")
        if series == "RSP":
            return "S&P500 동일가중 수준"
    if semantic_type in {
        "growth_relative_return_pct",
        "sector_relative_return_pct",
        "style_relative_return_pct",
    }:
        subject = _RELATIVE_SERIES_LABELS.get(str(fields.get("subject") or ""))
        benchmark = _RELATIVE_SERIES_LABELS.get(
            str(fields.get("benchmark") or "")
        )
        if subject and benchmark:
            return f"{benchmark} 대비 {subject} 상대수익률"
    if semantic_type in {
        "futures_close",
        "futures_point_change",
        "futures_return_pct",
    }:
        product = _NIGHT_FUTURES_LABELS.get(str(fields.get("series_code") or ""))
        if product:
            suffix = {
                "futures_close": "종가",
                "futures_point_change": "등락폭",
                "futures_return_pct": "등락률",
            }[semantic_type]
            return f"{product} {suffix}"
    return None


def valuation_comparison_label(field_path: str) -> str | None:
    match = re.fullmatch(
        r"fields\.historical_(pe|pb)_statistics\."
        r"(current_value|historical_median|historical_mean|percentile_(?:10|25|50|75|90))",
        field_path,
    )
    if match is None:
        return None
    metric_code, comparison_role = match.groups()
    metric = "PER" if metric_code == "pe" else "PBR"
    if comparison_role == "current_value":
        return f"현재 {metric}"
    if comparison_role == "historical_median":
        return f"역사적 {metric} 중앙값"
    if comparison_role == "historical_mean":
        return f"역사적 {metric} 평균"
    percentile = comparison_role.rsplit("_", maxsplit=1)[-1]
    return f"역사적 {metric} {percentile}백분위 값"


def valuation_comparison_role(field_path: str) -> str | None:
    match = re.fullmatch(
        r"fields\.historical_(?:pe|pb)_statistics\."
        r"(current_value|historical_median|historical_mean|percentile_(?:10|25|50|75|90)|current_percentile)",
        field_path,
    )
    return match.group(1) if match is not None else None


def usage_matches_semantic(semantic_type: str, usage: str) -> bool:
    spec = semantic_spec(semantic_type)
    if spec is None or not spec.prose_allowed:
        return False
    lowered = usage.lower()
    change_markers = re.compile(
        r"(?:등락|상승|하락|변동|증가|감소|올랐|내렸|return|change|rose|fell)",
        flags=re.IGNORECASE,
    )
    if semantic_type in {
        "fx_rate",
        "oil_price",
        "volatility_index_level",
        "dollar_index_level",
    }:
        if "%" in usage or change_markers.search(usage):
            return False
    if semantic_type in {
        "nominal_yield_level",
        "real_yield_level",
        "breakeven_inflation_level",
        "credit_spread_level",
    } and (
        "bp" in lowered
        or "베이시스포인트" in usage
        or change_markers.search(usage)
    ):
        return False
    return any(re.search(pattern, lowered) for pattern in spec.usage_patterns)


_WORKING_CAPITAL_LOWER = re.compile(
    r"밑돌|낮(?:았|은|다)|하회|\b(?:lower|below|trails?)\b",
    re.IGNORECASE,
)
_WORKING_CAPITAL_HIGHER = re.compile(
    r"앞섰|높(?:았|은|다)|상회|\b(?:higher|above|exceeds?)\b",
    re.IGNORECASE,
)


def usage_direction_matches(
    semantic_type: str,
    value: float,
    usage: str,
    source: dict[str, object] | None = None,
) -> bool:
    spec = semantic_spec(semantic_type)
    if spec is None:
        return False
    if semantic_type == "inventory_growth_absolute_gap_pct_point":
        return not (
            _WORKING_CAPITAL_LOWER.search(usage)
            or _WORKING_CAPITAL_HIGHER.search(usage)
        )
    if semantic_type == "inventory_growth_signed_gap_pct_point":
        lower = bool(_WORKING_CAPITAL_LOWER.search(usage))
        higher = bool(_WORKING_CAPITAL_HIGHER.search(usage))
        direction = str((source or {}).get("relation_direction") or "")
        expected = "LOWER" if value < 0 else "GREATER" if value > 0 else "EQUAL"
        if direction and direction != expected:
            return False
        if expected == "LOWER":
            return lower and not higher
        if expected == "GREATER":
            return higher and not lower
        return not lower and not higher
    if spec.formatter != "signed_shares":
        return True
    lowered = usage.lower()
    sell = "순매도" in usage or "net sell" in lowered
    buy = "순매수" in usage or "net buy" in lowered
    if value < 0:
        return sell and not buy
    if value > 0:
        return buy and not sell
    return True


def usage_relation_matches(
    semantic_type: str,
    usage: str,
    source: dict[str, object],
) -> bool:
    if semantic_type not in {
        "inventory_growth_signed_gap_pct_point",
        "inventory_growth_absolute_gap_pct_point",
    }:
        return True
    lowered = usage.lower()
    if "재고" not in usage and "inventory" not in lowered:
        return False
    if source.get("relation_semantics_contract") != "working-capital-relation-semantics-v1":
        return False
    if source.get("lhs_semantic") != "inventory_growth":
        return False
    if source.get("comparison_basis") != "year_over_year_growth_rate_percentage_points":
        return False
    family = str(source.get("relation_family") or "")
    rhs = str(source.get("rhs_semantic") or "")
    if family == "inventory_vs_cogs" and rhs == "cogs_growth":
        return "매출원가" in usage or bool(re.search(r"\bcogs?\b", lowered))
    if family == "inventory_vs_revenue" and rhs == "revenue_growth":
        return (
            ("매출" in usage and "매출원가" not in usage)
            or bool(re.search(r"\brevenue\b", lowered))
        )
    return False


def _plain_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.12g}"


def _fixed_number(value: float, digits: int) -> str:
    return f"{value:,.{digits}f}".rstrip("0").rstrip(".")


def _compact_amount(value: float, prefix: str, suffix: str = "") -> str:
    absolute = abs(value)
    for scale, marker in (
        (1_000_000_000_000, "T"),
        (1_000_000_000, "B"),
        (1_000_000, "M"),
    ):
        if absolute >= scale:
            sign = "-" if value < 0 else ""
            return f"{prefix}{sign}{_fixed_number(absolute / scale, 2)}{marker}{suffix}"
    sign = "-" if value < 0 else ""
    return f"{prefix}{sign}{absolute:,.0f}{suffix}"


def canonical_display_value(
    spec: NumericSemanticSpec,
    value: float,
    unit: str,
) -> str | None:
    """Render the single backend-owned display value used by numeric binding."""
    formatter = spec.formatter
    if unit == "KRW":
        if formatter == "currency_amount":
            return compact_krw_amount(value)
        return f"{value:,.0f}원"
    if unit == "USD":
        if formatter == "currency_amount":
            return _compact_amount(value, "$")
        return f"${_fixed_number(value, 2)}"
    if unit == "TWD":
        if formatter == "currency_amount":
            return _compact_amount(value, "NT$")
        return f"NT${_fixed_number(value, 2)}"
    if unit in {"JPY", "EUR"}:
        prefix = "¥" if unit == "JPY" else "€"
        if formatter == "currency_amount":
            return _compact_amount(value, prefix)
        return f"{prefix}{_fixed_number(value, 2)}"
    if unit == "pct":
        digits = 2 if spec.semantic_type == "futures_return_pct" else 1
        rendered = _fixed_number(value, digits)
        if formatter == "signed_percentage" and value > 0:
            rendered = f"+{rendered}"
        return f"{rendered}%"
    if unit == "pct_point":
        displayed = abs(value) if formatter == "directional_percentage_point" else value
        return f"{_fixed_number(displayed, 1)}%p"
    if unit == "bp":
        rendered = _fixed_number(value, 1)
        if formatter == "signed_basis_points" and value > 0:
            rendered = f"+{rendered}"
        return f"{rendered}bp"
    if unit == "x":
        return f"{_fixed_number(value, 2)}배"
    if unit == "shares":
        displayed = abs(value) if formatter == "signed_shares" else value
        return f"{displayed:,.0f}주"
    if unit == "points":
        rendered = _fixed_number(value, 2)
        if formatter == "signed_points" and value > 0:
            rendered = f"+{rendered}"
        return f"{rendered}포인트"
    if unit == "USD_per_barrel":
        return f"${_fixed_number(value, 2)}/bbl"
    if unit == "index":
        return _fixed_number(value, 2)
    if unit == "count":
        return f"{value:,.0f}개"
    return None


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
    elif unit == "TWD":
        variants.extend((f"NT${_plain_number(value)}", f"{_plain_number(value)} TWD"))
        if spec.formatter == "currency_amount":
            variants.append(_compact_amount(value, "NT$"))
    elif unit in {"JPY", "EUR"}:
        variants.append(f"{_plain_number(value)} {unit}")
    elif unit == "shares":
        variants.append(f"{value:,.0f}주")
        if spec.formatter == "signed_shares":
            variants.append(f"{abs(value):,.0f}주")
    elif unit == "pct_point":
        variants.append(f"{_plain_number(value)}%p")
        if spec.formatter == "directional_percentage_point":
            variants.append(f"{_plain_number(abs(value))}%p")
    elif unit == "x":
        variants.append(f"{_plain_number(value)}배")
        for digits in (1, 2, 4):
            variants.append(f"{_plain_number(float(round(value, digits)))}배")
    elif unit == "points":
        variants.extend(
            (f"{_plain_number(value)}pt", f"{_plain_number(value)}포인트")
        )
    elif unit == "bp":
        variants.extend((f"{_plain_number(value)}bp", f"{_plain_number(value)}bp 변동"))
    elif unit == "USD_per_barrel":
        variants.extend(
            (
                f"${_plain_number(value)}/bbl",
                f"{_plain_number(value)}달러/배럴",
            )
        )
    elif unit == "index":
        variants.extend((f"{_plain_number(value)}", f"{_plain_number(value)}포인트"))
    elif unit == "count":
        variants.extend((f"{value:,.0f}개", f"{value:,.0f}종목"))
    if (canonical := canonical_display_value(spec, value, unit)) is not None:
        variants.append(canonical)
    return list(dict.fromkeys(variants))


def _registry_contract_metadata(
    fact_type: str,
    field_path: str,
    fact_id: str,
    fields: dict[str, object],
    *,
    registered: bool,
    prose_allowed: bool,
) -> dict[str, object]:
    if not registered:
        return {
            "registry_class": "UNSUPPORTED_BLOCKING",
            "canonical_fact_or_relation_ref": fact_id,
            "audit_only": False,
            "allowed_sections": [],
        }
    reconciliation = re.fullmatch(
        r"fields\.reconciliations\.(1d|5d|20d)\."
        r"(?:(?:participant_flows\.([a-z_]+))|([a-z_]+))",
        field_path,
    )
    if fact_type == "positioning" and reconciliation is not None:
        return {
            "registry_class": "REGISTERED_INTERNAL_DERIVED",
            "canonical_fact_or_relation_ref": fact_id,
            "owner": "positioning",
            "window": reconciliation.group(1),
            "participant": reconciliation.group(2),
            "audit_only": True,
            "allowed_sections": [],
        }
    registry_class = (
        "REGISTERED_PROSE_ELIGIBLE"
        if registered and prose_allowed
        else "REGISTERED_AUDIT_ONLY"
    )
    metadata: dict[str, object] = {
        "registry_class": registry_class,
        "canonical_fact_or_relation_ref": fact_id,
        "audit_only": registered and not prose_allowed,
        "allowed_sections": [],
    }
    if fact_type == "positioning":
        metadata["owner"] = "positioning"
        if prose_allowed:
            metadata["allowed_sections"] = ["supply_analysis"]
    if fact_type == "market_cross_section_sector":
        source_ref = str(fields.get("source_ref") or "")
        metadata.update(
            {
                "owner": "market_context",
                "market_scope": fields.get("market_scope"),
                "sector_scope": fields.get("sector"),
                "session_basis": "same_session_cross_section",
                "source_owner": source_ref.split(":", 1)[0] if source_ref else None,
                "comparison_eligible": False,
            }
        )
        if prose_allowed:
            metadata["allowed_sections"] = ["market_context"]
    return metadata


def _relation_semantic_metadata(
    fact_type: str,
    fields: dict[str, object],
) -> dict[str, object]:
    if fact_type != "working_capital_inventory_relation":
        return {}
    return {
        "relation_semantics_contract": fields.get("relation_semantics_contract"),
        "relation_direction": fields.get("direction"),
        "relation_family": fields.get("relation_family"),
        "lhs_semantic": fields.get("lhs_semantic"),
        "rhs_semantic": fields.get("rhs_semantic"),
        "comparison_basis": fields.get("comparison_basis"),
        "relation_balance_date": fields.get("balance_date"),
        "relation_semantic_scope": fields.get("semantic_scope"),
        "relation_input_fact_ids": list(fields.get("input_fact_ids") or []),
    }


def numeric_declaration_fact_ids(
    facts: list[dict[str, object]],
    *,
    source_fact: dict[str, object],
    path: str,
    value: object,
) -> list[str]:
    """Return exact typed valuation facts that may declare a parent numeric source."""
    if (
        source_fact.get("fact_type") != "valuation"
        or not isinstance(value, (int, float))
        or isinstance(value, bool)
    ):
        return []
    parts = path.split(".")[1:]
    aliases: list[str] = []
    for candidate in facts:
        if (
            candidate.get("fact_type") != "valuation_interpretation"
            or candidate.get("interpretation_eligible") is not True
        ):
            continue
        candidate_value: object = candidate.get("fields")
        for part in parts:
            if not isinstance(candidate_value, dict) or part not in candidate_value:
                candidate_value = None
                break
            candidate_value = candidate_value[part]
        if (
            isinstance(candidate_value, (int, float))
            and not isinstance(candidate_value, bool)
            and float(candidate_value) == float(value)
        ):
            candidate_id = str(candidate.get("fact_id") or "")
            if candidate_id:
                aliases.append(candidate_id)
    return sorted(set(aliases))


def build_numeric_registry(
    facts: list[dict[str, object]],
) -> list[dict[str, object]]:
    registry: list[dict[str, object]] = []
    for fact in facts:
        if fact.get("numeric_registry_eligible") is False:
            continue
        fact_id = str(fact.get("fact_id") or "")
        fact_type = str(fact.get("fact_type") or "")
        fields = fact.get("fields")
        if not fact_id or not isinstance(fields, dict):
            continue
        field_quality = (
            fact.get("field_quality")
            if isinstance(fact.get("field_quality"), dict)
            else {}
        )

        def quality_for_path(path: str) -> dict[str, object]:
            candidate = path
            while candidate.startswith("fields"):
                value = field_quality.get(candidate)
                if isinstance(value, dict):
                    return value
                if "." not in candidate:
                    break
                candidate = candidate.rsplit(".", 1)[0]
            return {}

        def walk(value: object, path: str) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    walk(item, f"{path}.{key}")
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    walk(item, f"{path}.{index}")
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                spec, unit = resolve_numeric_semantic(fact_type, path, fields)
                declaration_aliases = numeric_declaration_fact_ids(
                    facts,
                    source_fact=fact,
                    path=path,
                    value=value,
                )
                registered = spec is not None
                canonical_label = (
                    _source_aware_label(spec.semantic_type, fields, path)
                    if spec is not None
                    else None
                )
                source_label_kind = (
                    _source_label_kind(spec.semantic_type, fields)
                    if spec is not None
                    else None
                )
                quality = quality_for_path(path)
                quality_state = str(quality.get("state") or "verified_usable")
                quality_prose_eligible = quality.get("prose_eligible") is not False
                prose_allowed = bool(
                    spec is not None
                    and spec.prose_allowed
                    and unit in spec.units
                    and unit != "unknown"
                    and (source_label_kind is None or canonical_label is not None)
                    and quality_state in {"verified_usable", "caution_usable"}
                    and quality_prose_eligible
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
                        "comparison_role": valuation_comparison_role(path),
                        "registered": registered,
                        "prose_allowed": prose_allowed,
                        "formatter": spec.formatter if spec is not None else None,
                        "scope": spec.scope if spec is not None else None,
                        "approved_labels": (
                            list(spec.approved_labels) if spec is not None else []
                        ),
                        "canonical_label": canonical_label,
                        "canonical_label_required": source_label_kind is not None,
                        "canonical_label_kind": source_label_kind,
                        "financial_quality_state": quality_state,
                        "financial_quality_reason_codes": list(
                            quality.get("quality_reason_codes") or []
                        ),
                        "dependency_fields": list(
                            quality.get("dependency_fields") or []
                        ),
                        "dependency_periods": list(
                            quality.get("dependency_periods") or []
                        ),
                        "denominator_period": quality.get("denominator_period"),
                        "financial_source_period": quality.get("source_period"),
                        "financial_source_type": quality.get("source_type"),
                        "financial_source_provider": quality.get("provider"),
                        "lineage_verification_status": quality.get(
                            "lineage_verification_status"
                        ),
                        "denial_reason": quality.get("denial_reason"),
                        "quality_decision_version": quality.get("decision_version"),
                        "approved_display_variants": (
                            approved_display_variants(spec, float(value), unit)
                            if spec is not None and prose_allowed
                            else []
                        ),
                        "canonical_display_value": (
                            canonical_display_value(spec, float(value), unit)
                            if spec is not None and prose_allowed
                            else None
                        ),
                        "declaration_fact_ids": sorted(
                            {fact_id, *declaration_aliases}
                        ),
                        **_registry_contract_metadata(
                            fact_type,
                            path,
                            fact_id,
                            fields,
                            registered=registered,
                            prose_allowed=prose_allowed,
                        ),
                        **_relation_semantic_metadata(fact_type, fields),
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
