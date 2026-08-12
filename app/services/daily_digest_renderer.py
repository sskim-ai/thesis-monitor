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
    title = {
        "us": f"🌎 미국 종목 점검 · {digest.digest_date}",
        "kr": f"🇰🇷 한국 종목 장마감 점검 · {digest.digest_date}",
    }.get(digest.market_scope, f"🌍 시장환경 점검 · {digest.digest_date}")
    lines = [
        title,
        f"현재 환경: {macro.regime_label}",
    ]
    if macro.assessment_state == "provisional":
        lines.extend(
            [
                "⚠️ 미국장이 진행 중이므로 현재 시장환경 평가는 잠정치입니다.",
                "지수·VIX·금리·종목 가격은 장 종료 후 달라질 수 있습니다.",
            ]
        )
    lines.extend(
        [
        "",
        "🎯 오늘 한 줄",
        macro.one_line,
        "",
        "📈 중요한 변화",
        *_bullet_lines(macro.key_changes[:3], "임계치를 넘은 핵심 시장 변화가 없습니다."),
        "",
        "🧭 현재 시장 상황",
        ]
    )
    for label, explanation in macro.axis_explanations[:3]:
        lines.extend([f"• {label}: {explanation}"])
    lines.extend(["", "💡 투자적 의미", *macro.integrated_view])
    changed_assumptions = [
        item for item in macro.market_assumptions if "오늘 신호: 중립" not in item
    ]
    lines.extend(["", "🔄 시장 가정"])
    lines.extend(changed_assumptions or ["• 나머지 시장 가정의 구조적 변화 없음"])
    lines.extend(
        [
            "",
            f"📊 {len(portfolio.tickers)}종목 상태",
            (
                f"투자 논리 · 강화 {thesis['strengthened']} · 유지 {thesis['maintained']} · "
                f"약화/검토 {thesis['weakened']} · 무효화 {thesis['invalidated']}"
            ),
            (
                f"Valuation · 확장 {valuation['expansion']} · 중립 {valuation['neutral']} · "
                f"혼재 {valuation['mixed']} · 압축 {valuation['compression']} · "
                f"판단 자료 부족 {valuation['unknown']}"
            ),
        ]
    )
    lines.append(f"전체 {len(portfolio.tickers)}개 종목 평가 완료")

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

    if digest.schedule.today or digest.schedule.next_seven_days:
        lines.extend(["", "📅 오늘/근접 일정"])
        if digest.schedule.today:
            lines.extend(["오늘:", *_bullet_lines(digest.schedule.today, "")])
        if digest.schedule.next_seven_days:
            lines.extend(["향후 7일:", *_bullet_lines(digest.schedule.next_seven_days, "")])
    if digest.data_quality.items:
        lines.extend(["", "⚠️ 데이터 주의", *_bullet_lines(digest.data_quality.items, "")])
        lines.append(digest.data_quality.conclusion)
    return "\n".join(lines).strip()
