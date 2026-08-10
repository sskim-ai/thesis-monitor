import json
from datetime import date

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import MonitoringItemCreate
from app.services.monitoring_service import register_monitoring_item


AS_OF_DATE = date(2026, 8, 10)
COMMON_BASIS = [
    "저장된 기업 논리와 구조화된 가격 규칙에 기반한 정성 기대 수준",
    "실시간 컨센서스와 현재 멀티플 수치는 아직 자동 연결되지 않음",
]


def expectation(
    level: str,
    summary: str,
    priced_in: list[str],
    upside: list[str],
    downside: list[str],
) -> dict[str, object]:
    return {
        "as_of_date": AS_OF_DATE,
        "level": level,
        "summary": summary,
        "priced_in": priced_in,
        "upside_surprises": upside,
        "downside_surprises": downside,
        "evidence_basis": COMMON_BASIS,
    }


def framework(
    primary: str,
    secondary: list[str],
    rationale: str,
    inputs: list[str],
    basis: list[str],
    caveats: list[str],
) -> dict[str, object]:
    return {
        "primary_method": primary,
        "secondary_methods": secondary,
        "rationale": rationale,
        "key_inputs": inputs,
        "peer_or_historical_basis": basis,
        "valuation_caveats": caveats,
    }


VALUATION_DATA: dict[str, dict[str, object]] = {
    "000660": {
        "expectations": expectation(
            "very_high",
            "HBM4 실행과 높은 메모리 수익성 지속 기대가 상당 부분 반영된 구간으로 본다.",
            ["HBM 리더십 유지", "AI 서버 메모리 수요 지속", "높은 현금창출력"],
            ["HBM4 수율·고객 확대가 예상보다 빠름", "FCF와 ROIC가 CAPEX 증가에도 개선"],
            ["HBM 점유율 또는 ASP가 기대 하회", "CAPEX 증가가 FCF를 예상보다 크게 훼손"],
        ),
        "framework": framework(
            "cycle-adjusted forward P/E",
            ["EV/EBITDA", "normalized FCF yield"],
            "메모리 피크 이익의 낮은 P/E 착시를 피하고 HBM 구조 성장과 범용 메모리 사이클을 분리한다.",
            ["정상화 EPS", "HBM 매출 비중·마진", "CAPEX", "FCF", "순현금"],
            ["글로벌 메모리 동종사", "과거 메모리 사이클 중간 구간"],
            ["피크 이익 적용 시 저평가로 오인 가능", "HBM 경쟁 격화 시 구조 성장 프리미엄 축소"],
        ),
        "expansion": ["HBM4 고객 채택과 수율이 예상 상회", "ROIC와 FCF가 CAPEX 증가에도 개선", "장기공급계약의 가격 하방 보호가 확인"],
        "compression": ["HBM 점유율 또는 가격 프리미엄 하락", "메모리 이익 추정치 하향", "실질금리 상승과 장기 성장주 할인율 확대"],
    },
    "003690": {
        "expectations": expectation(
            "balanced",
            "양호한 수급과 이익 안정성 기대는 반영 중이지만 대형 성장주 수준의 과도한 기대 구간으로 보지는 않는다.",
            ["재보험 이익 안정성", "자본 건전성 유지", "주주환원 지속"],
            ["ROE와 배당이 예상 상회", "갱신 보험료율과 손해율이 동시 개선"],
            ["대형 재해손실로 손해율 급등", "자본비율 또는 배당여력 약화"],
        ),
        "framework": framework(
            "P/B-ROE model",
            ["dividend yield", "normalized P/E"],
            "보험사는 장부가치 성장과 지속 가능한 ROE가 적정 P/B를 결정한다.",
            ["지배주주 ROE", "BPS 성장", "합산비율", "자본비율", "배당성향"],
            ["글로벌 재보험사", "자기자본비용 대비 ROE 스프레드"],
            ["대형 자연재해의 연도별 변동성", "회계기준 변화에 따른 비교 왜곡"],
        ),
        "expansion": ["ROE가 자기자본비용을 안정적으로 상회", "손해율 개선과 보험료율 상승이 동반", "배당성향 또는 자사주 환원이 확대"],
        "compression": ["대형 재해손실로 정상화 ROE 하락", "자본비율 하락 또는 배당여력 축소", "갱신 보험료율 하락과 경쟁 심화"],
    },
    "005490": {
        "expectations": expectation(
            "balanced",
            "철강 회복과 리튬·소재 흑자 전환 기대가 공존하며 실제 ROIC·FCF 증명이 필요한 구간이다.",
            ["철강 업황의 점진적 개선", "리튬·소재 손익 회복"],
            ["소재 흑자 전환과 FCF 개선이 예상보다 빠름", "비핵심 자산 가치 현실화"],
            ["중국 철강 수요와 스프레드 악화", "리튬 가격·가동률 부진과 추가 자금조달"],
        ),
        "framework": framework(
            "sum-of-the-parts",
            ["through-cycle EV/EBITDA", "P/B-ROE"],
            "철강 본업과 성장 소재 사업의 수익성·위험이 달라 사업별 가치를 분리한다.",
            ["철강 정상화 EBITDA", "리튬 생산량·원가", "소재 EBITDA", "순차입금", "희석 가능성"],
            ["글로벌 철강사", "리튬·배터리 소재 동종사", "과거 경기중간 P/B"],
            ["적자 성장사업에 과도한 매출배수 적용 위험", "원자재 가격 변동과 지주회사 할인"],
        ),
        "expansion": ["리튬·소재 사업 흑자가 연속 확인", "연결 ROIC와 FCF가 동시 개선", "순차입금 감소와 희석 우려 완화"],
        "compression": ["철강 스프레드와 가동률 동반 악화", "리튬 적자 지속 또는 투자비 증가", "유상증자·전환증권 등 희석 위험 확대"],
    },
    "005930": {
        "expectations": expectation(
            "elevated",
            "AI 메모리와 DS 이익 회복 기대가 높으며 HBM 실행과 현금흐름이 기대를 넘어야 추가 재평가가 가능하다.",
            ["DS 이익 급증", "HBM4·HBM4E 출하 확대", "강한 영업현금흐름"],
            ["HBM 고객 채택과 DS 마진이 예상 상회", "FCF 개선과 주주환원이 동시 확대"],
            ["HBM 인증·출하 지연", "DX 부진과 CAPEX로 FCF가 기대 하회"],
        ),
        "framework": framework(
            "sum-of-the-parts",
            ["cycle-adjusted P/B", "normalized forward P/E"],
            "메모리, 파운드리, 모바일·가전의 이익 특성이 달라 사업별 정상화 가치를 합산한다.",
            ["DS 정상화 이익", "HBM 매출·마진", "파운드리 손익", "DX 이익", "순현금·FCF"],
            ["글로벌 메모리·파운드리 동종사", "과거 메모리 회복기 P/B"],
            ["피크 메모리 이익을 영구화할 위험", "파운드리 적자와 복합기업 할인"],
        ),
        "expansion": ["HBM 고객 채택과 출하가 예상 상회", "DS 마진과 FCF가 동시 개선", "파운드리 적자 축소가 가시화"],
        "compression": ["HBM 실행 지연 또는 점유율 하락", "메모리 가격과 이익 추정치 하향", "CAPEX 증가 대비 FCF·ROIC 악화"],
    },
    "086280": {
        "expectations": expectation(
            "elevated",
            "양호한 수급과 장기 성장 기대가 반영됐으나 높은 가격대에서 실적 상향이 뒤따라야 한다.",
            ["완성차 물류 성장", "수익성 개선과 안정적 현금흐름"],
            ["비계열 물량과 마진이 예상 상회", "FCF와 주주환원 확대"],
            ["완성차 판매·운임 둔화", "운전자본과 CAPEX 부담 확대"],
        ),
        "framework": framework(
            "forward P/E",
            ["EV/EBITDA", "FCF yield"],
            "물류 물량 성장과 마진 개선의 지속성을 정상화 이익과 현금흐름으로 평가한다.",
            ["물류 매출 성장", "영업이익률", "비계열 비중", "운전자본", "FCF"],
            ["글로벌 자동차 물류사", "자체 과거 성장·마진 구간"],
            ["계열사 의존도", "운임·환율 변화에 따른 이익 변동"],
        ),
        "expansion": ["비계열 매출 비중과 마진이 동시 상승", "이익 추정치와 FCF가 동시 상향", "자본효율 또는 주주환원이 개선"],
        "compression": ["완성차 물량과 운임이 동반 둔화", "운전자본 증가로 FCF 악화", "높은 가격대에서 이익 추정치 하향"],
    },
    "CRCL": {
        "expectations": expectation(
            "speculative",
            "USDC와 스테이블코인 인프라의 고성장 기대가 크며 금리 의존도를 낮출 비이자 수익 증명이 필요하다.",
            ["USDC 유통량 성장", "규제 명확성 진전", "reserve income 지속"],
            ["결제·플랫폼 매출이 예상보다 빠르게 확대", "금리 하락에도 이익 성장이 유지"],
            ["USDC 점유율 둔화", "금리 하락으로 reserve income 급감"],
        ),
        "framework": framework(
            "scenario-based normalized P/E",
            ["EV/revenue", "DCF"],
            "reserve income과 비이자 플랫폼 수익을 분리하고 금리 시나리오별 정상 이익을 사용한다.",
            ["USDC 유통량", "준비자산 수익률", "비이자 매출", "수익배분율", "규제비용"],
            ["결제·거래 인프라 동종사", "금리 시나리오별 정상화 마진"],
            ["현재 금리 수익을 구조적 이익으로 오인할 위험", "규제와 토큰 점유율 변동"],
        ),
        "expansion": ["비이자성 플랫폼 매출 비중 상승", "USDC 점유율과 유통량이 동시 확대", "금리 하락에도 정상화 이익이 유지"],
        "compression": ["USDC 성장 또는 점유율 둔화", "금리 하락으로 reserve income 추정치 급감", "규제비용 또는 수익배분율 상승"],
    },
    "GOOGL": {
        "expectations": expectation(
            "elevated",
            "Search 방어와 Cloud·AI 성장 기대가 높고 대규모 CAPEX가 장기 ROIC로 전환되는지가 핵심이다.",
            ["Search 매출의 견조함", "Cloud 고성장과 마진 개선", "AI CAPEX 지속"],
            ["Cloud 성장·backlog와 마진이 예상 상회", "AI CAPEX 대비 FCF 회복이 빠름"],
            ["Search 수익화 약화", "CAPEX 증가가 FCF와 ROIC를 장기간 훼손"],
        ),
        "framework": framework(
            "forward P/E",
            ["EV/FCF", "sum-of-the-parts DCF"],
            "Search 현금창출과 Cloud·AI 성장 가치를 분리하고 CAPEX 이후 FCF를 중시한다.",
            ["Search 성장", "Cloud 성장·마진", "CAPEX", "FCF", "순현금"],
            ["글로벌 광고·클라우드 플랫폼", "자체 과거 성장률 대비 P/E"],
            ["AI 투자비와 감가상각 시차", "규제·반독점 할인"],
        ),
        "expansion": ["Cloud 성장과 영업마진이 동시 상향", "AI 수익화가 Search 잠식을 상쇄", "CAPEX 이후 FCF·ROIC 회복이 확인"],
        "compression": ["Search 성장 또는 수익화 둔화", "CAPEX 상향 대비 매출·FCF 추정치 정체", "반독점 규제로 사업가치 할인 확대"],
    },
    "IBM": {
        "expectations": expectation(
            "balanced",
            "Software·Red Hat·AI 성장 기대는 반영됐지만 전사 성장과 FCF 가속은 아직 증명이 필요하다.",
            ["Software 반복매출 성장", "Red Hat과 AI 수요"],
            ["Consulting 회복과 Software 성장 가속", "FCF가 예상보다 빠르게 증가"],
            ["Software 성장 둔화", "Consulting 부진과 FCF 정체"],
        ),
        "framework": framework(
            "EV/FCF",
            ["forward P/E", "sum-of-the-parts"],
            "반복매출 품질과 현금전환을 중심으로 성숙 하드웨어·서비스와 성장 소프트웨어를 구분한다.",
            ["Software 성장", "Red Hat 성장", "Consulting 매출", "FCF", "순부채"],
            ["대형 소프트웨어·IT 서비스사", "자체 FCF 성장 구간"],
            ["인수 관련 무형자산과 조정이익 의존", "저성장 부문의 복합기업 할인"],
        ),
        "expansion": ["Software와 Red Hat 성장률이 동시 가속", "Consulting 회복과 FCF 상향이 동반", "순부채 감소와 현금전환 개선"],
        "compression": ["Software 성장률 둔화", "Consulting 부진과 FCF 추정치 하향", "인수·부채 증가로 자본효율 악화"],
    },
    "MU": {
        "expectations": expectation(
            "very_high",
            "HBM·DRAM 공급부족과 초고마진 지속 기대가 높아 추가 상승에는 이익과 FCF의 연속 상향이 필요하다.",
            ["HBM·DRAM ASP 상승", "AI 데이터센터 수요", "강한 FCF"],
            ["ASP·gross margin과 FCF가 예상 상회", "장기 고객계약이 가격 하방을 보호"],
            ["메모리 가격 상승률 둔화", "재고와 CAPEX가 예상보다 빠르게 증가"],
        ),
        "framework": framework(
            "cycle-adjusted forward P/E",
            ["EV/EBITDA", "normalized FCF yield"],
            "메모리 피크 이익과 HBM 구조 성장을 분리해 중간 사이클 이익을 평가한다.",
            ["정상화 EPS", "HBM 믹스", "DRAM ASP", "재고", "CAPEX·FCF"],
            ["글로벌 메모리 동종사", "과거 메모리 사이클"],
            ["피크 마진 영구화 위험", "공급 증설과 재고 사이클 반전"],
        ),
        "expansion": ["HBM 매출·ASP·gross margin이 예상 상회", "전략 고객계약이 가격 가시성을 높임", "CAPEX 증가에도 FCF가 상향"],
        "compression": ["DRAM·HBM 가격 추정치 하향", "재고일수와 공급증설이 동시 증가", "피크 gross margin 이후 하락 신호 확인"],
    },
    "RXRX": {
        "expectations": expectation(
            "speculative",
            "플랫폼 가능성과 파트너 진전 기대가 크지만 임상 성공과 반복 가능한 경제성은 아직 미증명이다.",
            ["AI 신약발굴 플랫폼 가치", "파트너 타깃 선택과 초기 임상 진전"],
            ["임상 데이터와 milestone이 예상 상회", "현금소진 없이 파트너 수익이 확대"],
            ["임상 실패 또는 일정 지연", "현금소진과 희석이 예상 상회"],
        ),
        "framework": framework(
            "risk-adjusted NPV",
            ["cash-adjusted pipeline value", "platform partnership value"],
            "임상 단계별 성공확률과 현금소진을 반영하고 매출배수만으로 플랫폼을 평가하지 않는다.",
            ["후보별 성공확률", "시장 규모", "milestone·royalty", "현금 보유", "분기 현금소진"],
            ["유사 단계 바이오 파이프라인", "파트너 계약의 실제 경제조건"],
            ["초기 파이프라인의 높은 실패확률", "현금조달과 희석 위험"],
        ),
        "expansion": ["핵심 임상 데이터가 사전 기준 충족", "파트너 milestone과 타깃 선택이 확대", "현금 runway가 희석 없이 연장"],
        "compression": ["핵심 임상 실패 또는 일정 지연", "분기 현금소진이 계획 상회", "유상증자·주식보상으로 희석 확대"],
    },
    "SNDK": {
        "expectations": expectation(
            "speculative",
            "AI 데이터센터 NAND와 높은 마진·RPO 기대가 강하게 반영돼 계약의 현금화와 사이클 지속 검증이 필요하다.",
            ["NAND 가격 상승", "데이터센터 SSD 수요", "장기계약과 RPO"],
            ["RPO 매출전환과 FCF가 예상 상회", "가격 상승 없이도 마진이 유지"],
            ["NAND 가격 반전", "RPO 전환 지연 또는 재고 증가"],
        ),
        "framework": framework(
            "cycle-adjusted EV/EBITDA",
            ["normalized P/E", "FCF yield"],
            "NAND 가격 사이클과 데이터센터 구조 성장을 분리하고 정상화 마진을 사용한다.",
            ["NAND ASP", "데이터센터 매출", "RPO 전환", "gross margin", "재고·FCF"],
            ["NAND·스토리지 동종사", "과거 NAND 중간 사이클"],
            ["가격 상승기 마진을 영구화할 위험", "고객 계약의 취소·전환 시차"],
        ),
        "expansion": ["RPO의 매출·현금 전환이 예상 상회", "데이터센터 믹스로 gross margin이 유지", "재고 감소와 FCF 상향이 동반"],
        "compression": ["NAND ASP 추정치 하향", "RPO 매출전환 지연", "재고 증가와 FCF 악화가 동반"],
    },
    "TSLA": {
        "expectations": expectation(
            "speculative",
            "Robotaxi·FSD·AI의 장기 옵션가치가 크게 반영됐으며 자동차 이익과 FCF가 이를 방어하지 못하는 구간이다.",
            ["Robotaxi 대규모 상용화", "FSD 고마진 수익화", "AI 옵션가치"],
            ["Robotaxi 단위경제성과 이용률이 예상 상회", "자동차 마진·FCF가 동시에 회복"],
            ["Robotaxi 규제·상용화 지연", "자동차 마진과 FCF 부진 장기화"],
        ),
        "framework": framework(
            "scenario-based sum-of-the-parts DCF",
            ["automotive normalized EV/EBIT", "option-value scenarios"],
            "자동차 본업과 FSD·Robotaxi·에너지 옵션을 확률가중 시나리오로 분리한다.",
            ["자동차 인도·마진", "Robotaxi 이용률·차량당 이익", "FSD 채택률", "CAPEX", "FCF"],
            ["글로벌 자동차사", "플랫폼·자율주행 시나리오"],
            ["먼 미래 현금흐름에 대한 과도한 종단가치", "규제·기술 성공확률 민감도"],
        ),
        "expansion": ["Robotaxi 단위경제성과 유료 이용률 확인", "FSD 고마진 매출이 예상 상회", "자동차 마진과 FCF가 동시 회복"],
        "compression": ["Robotaxi 상용화 또는 규제 일정 지연", "자동차 가격 인하로 마진 추정치 하향", "FCF 적자와 CAPEX 부담 장기화"],
    },
    "TSM": {
        "expectations": expectation(
            "very_high",
            "AI/HPC 성장과 첨단공정 지배력·높은 마진 지속 기대가 높아 실행 상회가 추가 재평가 조건이다.",
            ["AI/HPC 고성장", "첨단공정 가격결정력", "높은 가동률과 gross margin"],
            ["첨단공정 매출·마진과 FCF가 예상 상회", "해외 팹 비용 희석이 예상보다 작음"],
            ["hyperscaler CAPEX 둔화", "해외 팹 비용과 감가상각으로 마진 하락"],
        ),
        "framework": framework(
            "forward P/E",
            ["DCF", "EV/EBITDA"],
            "첨단공정 성장 지속기간과 높은 ROIC·현금창출을 반영하되 지정학·해외 팹 비용을 할인한다.",
            ["첨단공정 매출", "가동률", "gross margin", "CAPEX·감가상각", "FCF"],
            ["글로벌 반도체 제조·플랫폼사", "자체 성장·마진 구간"],
            ["지정학 할인", "해외 팹 원가와 고객 CAPEX 집중"],
        ),
        "expansion": ["첨단공정 성장과 gross margin이 동시 상향", "가격결정력과 가동률이 예상 상회", "CAPEX 이후 FCF·ROIC가 개선"],
        "compression": ["hyperscaler CAPEX와 주문 가시성 둔화", "해외 팹 비용으로 마진 추정치 하향", "지정학 위험 프리미엄 확대"],
    },
    "WRD": {
        "expectations": expectation(
            "speculative",
            "규제 승인과 fleet 확대 기대가 크지만 차량당 이용률·gross margin·현금소진 경제성은 미증명이다.",
            ["Robotaxi 승인 지역 확대", "fleet와 유료 이용 증가"],
            ["차량당 이용률과 gross margin이 예상 상회", "현금소진 없이 도시 확장이 반복"],
            ["승인·상용화 지연", "fleet 확대에도 손실과 현금소진 증가"],
        ),
        "framework": framework(
            "scenario-based EV/revenue",
            ["unit-economics DCF", "cash-adjusted fleet value"],
            "초기 매출배수는 차량당 이용률과 도시별 단위경제성이 검증될 때만 정당화한다.",
            ["유료 fleet", "차량당 운행·매출", "gross margin", "도시별 손익분기", "현금소진"],
            ["자율주행 플랫폼 동종사", "도시별 성숙 단계 시나리오"],
            ["초기 매출의 낮은 품질", "규제·안전사고와 자금조달 위험"],
        ),
        "expansion": ["차량당 유료 이용률과 매출이 동시 상승", "도시별 gross margin 또는 공헌이익 개선", "추가 증자 없이 fleet 확대"],
        "compression": ["규제 승인 또는 상용화 일정 지연", "fleet 증가 대비 이용률·매출 정체", "영업손실·현금소진과 희석 확대"],
    },
}


def _latest_thesis(session: Session, ticker: str) -> InvestmentThesis | None:
    return session.exec(
        select(InvestmentThesis)
        .where(InvestmentThesis.ticker == ticker, InvestmentThesis.status == "active")
        .order_by(InvestmentThesis.version.desc())
    ).first()


def main() -> None:
    init_db()
    with Session(engine) as session:
        active_items = session.exec(
            select(WatchlistItem).where(WatchlistItem.active.is_(True))
        ).all()
        active_by_ticker = {item.ticker: item for item in active_items}
        missing = sorted(set(VALUATION_DATA) - set(active_by_ticker))
        unexpected = sorted(set(active_by_ticker) - set(VALUATION_DATA))
        if missing or unexpected:
            raise RuntimeError(
                f"valuation coverage mismatch: missing={missing}, unexpected={unexpected}"
            )

        for ticker, values in VALUATION_DATA.items():
            item = active_by_ticker[ticker]
            thesis = _latest_thesis(session, ticker)
            if thesis is None:
                raise RuntimeError(f"active thesis not found: {ticker}")
            result = register_monitoring_item(
                session,
                MonitoringItemCreate(
                    ticker=ticker,
                    company_name=item.company_name,
                    exchange=item.exchange,
                    core_thesis=thesis.core_thesis,
                    time_horizon=thesis.time_horizon,
                    thesis_drivers=json.loads(thesis.thesis_drivers),
                    validation_metrics=json.loads(thesis.validation_metrics),
                    market_expectations=values["expectations"],
                    valuation_framework=values["framework"],
                    multiple_expansion_signals=values["expansion"],
                    multiple_compression_signals=values["compression"],
                    strengthen_signals=json.loads(thesis.strengthen_signals),
                    weaken_signals=json.loads(thesis.weaken_signals),
                    invalidation_signals=json.loads(thesis.invalidation_signals),
                    price_rules=json.loads(thesis.price_rules) or None,
                    macro_exposures=json.loads(thesis.macro_exposures),
                ),
            )
            print(f"{result.ticker} {result.company_name} v{result.thesis.version}")


if __name__ == "__main__":
    main()
