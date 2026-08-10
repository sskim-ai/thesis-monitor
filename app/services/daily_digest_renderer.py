from app.services.daily_digest import (
    DailyDigest,
    EXPECTATION_LABELS,
    VALUATION_LABELS,
)


def _bullet_lines(items: list[str], empty: str) -> list[str]:
    return [f"• {item}" for item in items] or [f"• {empty}"]


def render_daily_digest(
    digest: DailyDigest,
    *,
    include_stock_details: bool = True,
) -> str:
    macro = digest.macro
    portfolio = digest.portfolio
    thesis = portfolio.thesis_counts
    valuation = portfolio.valuation_counts
    lines = [
        f"🌍 시장환경 점검 · {digest.digest_date}",
        f"⚠️ {macro.regime_label} 국면 · 판단 신뢰도 {macro.confidence:.0%}",
        "",
        "🎯 오늘 한 줄",
        macro.one_line,
        "",
        "📈 오늘 가장 중요한 변화",
        *_bullet_lines(macro.key_changes, "임계치를 넘은 핵심 시장 변화가 없습니다."),
        "",
        "🧭 현재 시장 상황",
    ]
    for label, explanation in macro.axis_explanations:
        lines.extend([f"• {label}: {explanation}"])
    lines.extend(["", "💡 종합 해석", *macro.integrated_view, "", "🔄 시장 가정"])
    lines.extend(_bullet_lines(macro.market_assumptions, "방향을 바꿀 신규 확정 근거가 없습니다."))
    lines.extend(
        [
            "",
            "📊 모니터링 현황",
            (
                f"투자 논리 · 강화 {thesis['strengthened']} · 유지 {thesis['maintained']} · "
                f"약화/검토 {thesis['weakened']} · 무효화 {thesis['invalidated']}"
            ),
            (
                f"Valuation · 확장 {valuation['expansion']} · 중립 {valuation['neutral']} · "
                f"혼재 {valuation['mixed']} · 압축 {valuation['compression']} · "
                f"판단 자료 부족 {valuation['unknown']}"
            ),
            "",
            "🏢 오늘 종목 점검",
        ]
    )
    if portfolio.tickers:
        for item in portfolio.tickers:
            lines.append(
                f"• {item.company_name}({item.ticker}) · {item.display_reason} · "
                f"기대 {EXPECTATION_LABELS.get(item.expectation_level, item.expectation_level)} · "
                f"Valuation {VALUATION_LABELS.get(item.valuation, item.valuation)}"
            )
    else:
        lines.append("• 오늘 저장이 완료된 종목 평가가 없습니다.")

    if include_stock_details and portfolio.focus_tickers:
        lines.extend(["", "🔎 오늘 상세 점검"])
        for index, item in enumerate(portfolio.focus_tickers, start=1):
            lines.extend(
                [
                    "",
                    f"{index}. {item.company_name}({item.ticker})",
                    f"투자 논리: {item.display_reason}",
                    f"시장 기대: {EXPECTATION_LABELS.get(item.expectation_level, item.expectation_level)}",
                    f"Valuation: {VALUATION_LABELS.get(item.valuation, item.valuation)}",
                    "",
                    "[확인된 사실]",
                    *(_bullet_lines(item.confirmed_facts, "오늘 투자 논리를 바꿀 신규 회사 사실은 확인되지 않았습니다.")),
                    "",
                    "[현재 확인된 경고]",
                    *(_bullet_lines(item.confirmed_warnings, "현재 확인된 핵심 경고는 없습니다.")),
                    "",
                    "[계속 감시]",
                    *(_bullet_lines(item.watch_items, "등록된 약화 조건과 검증 지표를 계속 확인합니다.")),
                    "",
                    "[시장환경 영향]",
                    *_bullet_lines(item.macro_paths, "사업 투자 논리나 Valuation을 바꿀 강한 거시 전달 경로가 없습니다."),
                    "",
                    "[오늘 확인]",
                    *_bullet_lines(item.check_metrics, "등록된 핵심 검증 지표를 계속 확인합니다."),
                    "",
                    "[신규 관찰자]",
                    item.new_observer_view,
                    "",
                    "[보유자]",
                    item.holder_view,
                ]
            )

    lines.extend(["", "📅 오늘/근접 일정", "오늘:"])
    lines.extend(_bullet_lines(digest.schedule.today, "등록된 주요 일정 없음"))
    if digest.schedule.next_seven_days:
        lines.extend(["향후 7일:", *_bullet_lines(digest.schedule.next_seven_days, "")])
    lines.extend(["", "⚠️ 데이터 주의"])
    lines.extend(_bullet_lines(digest.data_quality.items, "특이사항 없음"))
    lines.append(digest.data_quality.conclusion)
    return "\n".join(lines).strip()
