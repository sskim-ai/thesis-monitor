import argparse
import asyncio
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo
from xml.etree import ElementTree

import httpx
from pydantic import BaseModel, Field

from app.providers.news import clean_text


TREND_FORCE_SEMICONDUCTORS_RSS = "https://www.trendforce.com/feed/Semiconductors.html"
FEED_NAME = "trendforce_semiconductors_rss"
USER_AGENT = "thesis-monitor/DRAM-RSS-probe"
KST = ZoneInfo("Asia/Seoul")

_DAILY_EXPRESS_RE = re.compile(r"daily\s+express", re.IGNORECASE)
_SPOT_MARKET_TODAY_RE = re.compile(r"spot\s+market\s+today", re.IGNORECASE)
_DRAM_CONTEXT_RE = re.compile(r"\bdram\b|\bddr[345]\b", re.IGNORECASE)
_DIRECT_CONTRACT_RE = re.compile(
    r"\bdram\b.{0,80}\bcontract\s+(?:price|prices|pricing)\b"
    r"|\bcontract\s+(?:price|prices|pricing)\b.{0,80}\bdram\b",
    re.IGNORECASE,
)
_PRICING_CONTEXT_RE = re.compile(
    r"\bcontract\b|\bpricing\b|\basp\b|\baverage\s+selling\s+price",
    re.IGNORECASE,
)
_SPOT_PRICE_RE = re.compile(
    r"average\s+price\s+of\s+"
    r"(?P<item>(?:lp)?ddr[345][^.;,]{2,90}?)\s+"
    r"(?P<verb>rises?|rose|increases?|increased|climbs?|climbed|"
    r"drops?|dropped|falls?|fell|declines?|declined|decreases?|decreased|"
    r"stays?|remains?|holds?|held)"
    r"(?:\s+by\s+(?P<change_pct>\d+(?:\.\d+)?)\s*%)?"
    r"\s+(?:to|at)\s+USD\s*\$?\s*(?P<price>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_TITLE_DATE_RE = re.compile(
    r"daily\s+express\s+(?P<month>[A-Za-z]{3,9})\.?\s*"
    r"(?P<day>\d{1,2}),\s*(?P<year>\d{4})",
    re.IGNORECASE,
)
_PERCENT_RANGE_RE = re.compile(
    r"(?P<low>\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*"
    r"(?P<high>\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE,
)
_SINGLE_PERCENT_RE = re.compile(r"(?<!\d)(?P<value>\d+(?:\.\d+)?)\s*%")


class DramRssEntry(BaseModel):
    title: str
    published_at: datetime | None = None
    link: str
    summary: str | None = None
    category: str | None = None


class DramSpotProbe(BaseModel):
    item: str
    price_usd: float
    direction: str
    reported_change_pct: float | None = None
    source_date: date | None = None
    source_title: str
    source_link: str
    parse_confidence: str = "high"


class DramContractNewsProbe(BaseModel):
    title: str
    published_at: datetime | None = None
    link: str
    summary: str | None = None
    category: str | None = None
    relevance: str
    reported_change_pct_low: float | None = None
    reported_change_pct_high: float | None = None


class DramRssProbeResult(BaseModel):
    status: str
    feed: str = FEED_NAME
    source_url: str = TREND_FORCE_SEMICONDUCTORS_RSS
    fetched_at: datetime
    reason: str | None = None
    entry_count: int = 0
    daily_express_count: int = 0
    dram_daily_express_count: int = 0
    price_parseable_daily_count: int = 0
    dram_price_observation_count: int = 0
    contract_news_count: int = 0
    representative_product: str | None = None
    representative_product_observation_count: int = 0
    representative_product_coverage_pct: float | None = None
    latest_dram_date: date | None = None
    latest_product: str | None = None
    latest_price_usd: float | None = None
    latest_direction: str | None = None
    freshness_lag_calendar_days: int | None = None
    computed_change_abs: float | None = None
    computed_change_pct: float | None = None
    missing_weekdays: list[date] = Field(default_factory=list)
    entries: list[DramRssEntry] = Field(default_factory=list)
    price_observations: list[DramSpotProbe] = Field(default_factory=list)
    contract_news: list[DramContractNewsProbe] = Field(default_factory=list)
    recommendation: str = "not_recommended"

    def compact_summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "feed": self.feed,
            "entry_count": self.entry_count,
            "daily_express_count": self.daily_express_count,
            "dram_price_observation_count": self.dram_price_observation_count,
            "latest_dram_date": self.latest_dram_date,
            "latest_product": self.latest_product,
            "latest_price_usd": self.latest_price_usd,
            "contract_news_count": self.contract_news_count,
            "recommendation": self.recommendation,
            "reason": self.reason,
        }


def _published_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (IndexError, TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _source_date(title: str, published_at: datetime | None) -> date | None:
    match = _TITLE_DATE_RE.search(title)
    if match:
        try:
            month = datetime.strptime(match.group("month")[:3], "%b").month
            return date(int(match.group("year")), month, int(match.group("day")))
        except ValueError:
            pass
    return published_at.astimezone(KST).date() if published_at else None


def _direction(verb: str) -> str:
    normalized = verb.lower()
    if normalized.startswith(("rise", "rose", "increase", "climb")):
        return "up"
    if normalized.startswith(("drop", "fall", "fell", "decline", "decrease")):
        return "down"
    return "flat"


def _rss_entries(root: ElementTree.Element) -> list[DramRssEntry]:
    entries: list[DramRssEntry] = []
    for item in root.findall(".//item"):
        title = clean_text(item.findtext("title"))
        link = clean_text(item.findtext("link"))
        if not title or not link:
            continue
        summary = clean_text(item.findtext("description") or item.findtext("summary"))
        categories = [clean_text(node.text) for node in item.findall("category") if node.text]
        entries.append(
            DramRssEntry(
                title=title,
                published_at=_published_at(item.findtext("pubDate")),
                link=link,
                summary=summary or None,
                category=", ".join(category for category in categories if category) or None,
            )
        )
    return entries


def _is_daily_express(entry: DramRssEntry) -> bool:
    return bool(
        _DAILY_EXPRESS_RE.search(entry.title) and _SPOT_MARKET_TODAY_RE.search(entry.title)
    )


def _has_dram_context(entry: DramRssEntry) -> bool:
    return bool(_DRAM_CONTEXT_RE.search(f"{entry.title} {entry.summary or ''}"))


def _spot_observations(entry: DramRssEntry) -> list[DramSpotProbe]:
    source_date = _source_date(entry.title, entry.published_at)
    observations: list[DramSpotProbe] = []
    for match in _SPOT_PRICE_RE.finditer(entry.summary or ""):
        item = " ".join(match.group("item").split())
        observations.append(
            DramSpotProbe(
                item=item,
                price_usd=float(match.group("price")),
                direction=_direction(match.group("verb")),
                reported_change_pct=(
                    float(match.group("change_pct")) if match.group("change_pct") else None
                ),
                source_date=source_date,
                source_title=entry.title,
                source_link=entry.link,
            )
        )
    return observations


def _reported_change_range(text: str) -> tuple[float | None, float | None]:
    range_match = _PERCENT_RANGE_RE.search(text)
    if range_match:
        return float(range_match.group("low")), float(range_match.group("high"))
    single_match = _SINGLE_PERCENT_RE.search(text)
    if single_match:
        value = float(single_match.group("value"))
        return value, value
    return None, None


def _contract_news(entry: DramRssEntry) -> DramContractNewsProbe | None:
    if _is_daily_express(entry):
        return None
    title = entry.title
    combined = f"{title} {entry.summary or ''}"
    if not _DRAM_CONTEXT_RE.search(combined) or not _PRICING_CONTEXT_RE.search(combined):
        return None
    if _DIRECT_CONTRACT_RE.search(title):
        relevance = "high"
    elif _DIRECT_CONTRACT_RE.search(combined):
        relevance = "medium"
    else:
        relevance = "low"
    change_low, change_high = _reported_change_range(combined)
    return DramContractNewsProbe(
        title=title,
        published_at=entry.published_at,
        link=entry.link,
        summary=entry.summary,
        category=entry.category,
        relevance=relevance,
        reported_change_pct_low=change_low,
        reported_change_pct_high=change_high,
    )


def _missing_weekdays(source_dates: set[date]) -> list[date]:
    if len(source_dates) < 2:
        return []
    missing: list[date] = []
    current = min(source_dates)
    latest = max(source_dates)
    while current <= latest:
        if current.weekday() < 5 and current not in source_dates:
            missing.append(current)
        current += timedelta(days=1)
    return missing


def _representative_product(
    observations: list[DramSpotProbe],
) -> tuple[str | None, list[DramSpotProbe]]:
    if not observations:
        return None, []
    counts = Counter(observation.item for observation in observations)
    latest_dates = {
        item: max(
            (observation.source_date or date.min)
            for observation in observations
            if observation.item == item
        )
        for item in counts
    }
    product = max(counts, key=lambda item: (counts[item], latest_dates[item]))
    selected = sorted(
        (observation for observation in observations if observation.item == product),
        key=lambda observation: observation.source_date or date.min,
    )
    return product, selected


def _recommendation(result: DramRssProbeResult) -> str:
    if result.status != "ok":
        return "not_recommended"
    parse_rate = (
        result.price_parseable_daily_count / result.dram_daily_express_count
        if result.dram_daily_express_count
        else 0.0
    )
    continuity = result.representative_product_observation_count >= min(
        3, result.dram_daily_express_count
    )
    fresh = result.freshness_lag_calendar_days is not None and (
        result.freshness_lag_calendar_days <= 1
    )
    if (
        result.daily_express_count
        and parse_rate >= 0.8
        and continuity
        and fresh
        and result.contract_news_count
    ):
        return "recommended"
    if result.daily_express_count and (
        result.dram_price_observation_count or result.contract_news_count
    ):
        return "conditional"
    if result.contract_news_count:
        return "conditional"
    return "not_recommended"


def parse_dram_rss(
    xml_text: str,
    *,
    fetched_at: datetime | None = None,
    run_date: date | None = None,
) -> DramRssProbeResult:
    fetched_at = fetched_at or datetime.now(timezone.utc)
    run_date = run_date or datetime.now(KST).date()
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        return DramRssProbeResult(
            status="unavailable",
            fetched_at=fetched_at,
            reason=f"malformed_xml:{type(exc).__name__}",
        )

    entries = _rss_entries(root)
    if not entries:
        return DramRssProbeResult(
            status="unavailable",
            fetched_at=fetched_at,
            reason="empty_feed",
        )

    daily_entries = [entry for entry in entries if _is_daily_express(entry)]
    dram_daily_entries = [entry for entry in daily_entries if _has_dram_context(entry)]
    observations = [
        observation for entry in dram_daily_entries for observation in _spot_observations(entry)
    ]
    parseable_titles = {observation.source_title for observation in observations}
    contract_news = [
        news for entry in entries if (news := _contract_news(entry)) is not None
    ]
    representative_product, representative_observations = _representative_product(
        observations
    )
    latest = representative_observations[-1] if representative_observations else None
    previous = (
        representative_observations[-2]
        if len(representative_observations) >= 2
        else None
    )
    source_dates = {
        source_date
        for entry in dram_daily_entries
        if (source_date := _source_date(entry.title, entry.published_at)) is not None
    }
    result = DramRssProbeResult(
        status="ok",
        fetched_at=fetched_at,
        entry_count=len(entries),
        daily_express_count=len(daily_entries),
        dram_daily_express_count=len(dram_daily_entries),
        price_parseable_daily_count=len(parseable_titles),
        dram_price_observation_count=len(observations),
        contract_news_count=len(contract_news),
        representative_product=representative_product,
        representative_product_observation_count=len(representative_observations),
        representative_product_coverage_pct=(
            round(len(representative_observations) / len(dram_daily_entries) * 100, 2)
            if dram_daily_entries
            else None
        ),
        latest_dram_date=latest.source_date if latest else None,
        latest_product=latest.item if latest else None,
        latest_price_usd=latest.price_usd if latest else None,
        latest_direction=latest.direction if latest else None,
        freshness_lag_calendar_days=(
            (run_date - latest.source_date).days if latest and latest.source_date else None
        ),
        computed_change_abs=(
            round(latest.price_usd - previous.price_usd, 6)
            if latest and previous and latest.parse_confidence == previous.parse_confidence == "high"
            else None
        ),
        computed_change_pct=(
            round((latest.price_usd / previous.price_usd - 1) * 100, 6)
            if latest
            and previous
            and previous.price_usd != 0
            and latest.parse_confidence == previous.parse_confidence == "high"
            else None
        ),
        missing_weekdays=_missing_weekdays(source_dates),
        entries=entries,
        price_observations=sorted(
            observations,
            key=lambda observation: observation.source_date or date.min,
            reverse=True,
        ),
        contract_news=sorted(
            contract_news,
            key=lambda news: news.published_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        ),
    )
    result.recommendation = _recommendation(result)
    return result


async def fetch_live_probe(
    *,
    transport: httpx.AsyncBaseTransport | None = None,
    run_date: date | None = None,
) -> DramRssProbeResult:
    fetched_at = datetime.now(timezone.utc)
    try:
        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            transport=transport,
            headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, text/xml"},
        ) as client:
            response = await client.get(TREND_FORCE_SEMICONDUCTORS_RSS)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return DramRssProbeResult(
            status="unavailable",
            fetched_at=fetched_at,
            reason=f"rss_fetch_failed:{type(exc).__name__}",
        )
    return parse_dram_rss(response.text, fetched_at=fetched_at, run_date=run_date)


def _display(value: object | None) -> str:
    return "없음" if value is None else str(value)


def _display_unit(value: object | None, unit: str) -> str:
    return "없음" if value is None else f"{value}{unit}"


def render_feasibility_report(result: DramRssProbeResult, *, morning_date: date) -> str:
    parse_rate = (
        result.price_parseable_daily_count / result.dram_daily_express_count * 100
        if result.dram_daily_express_count
        else 0.0
    )
    price_rows = [
        "| Date | Product | USD | Direction | Reported change | Confidence |",
        "|---|---|---:|---|---:|---|",
    ]
    price_rows.extend(
        "| "
        + " | ".join(
            (
                _display(observation.source_date),
                observation.item,
                f"{observation.price_usd:g}",
                observation.direction,
                _display(observation.reported_change_pct),
                observation.parse_confidence,
            )
        )
        + " |"
        for observation in result.price_observations[:10]
    )
    if not result.price_observations:
        price_rows.append("| 없음 | 없음 | 없음 | 없음 | 없음 | 없음 |")

    news_rows = [
        "| Published | Relevance | Reported range | Title |",
        "|---|---|---|---|",
    ]
    news_rows.extend(
        "| "
        + " | ".join(
            (
                _display(news.published_at.date() if news.published_at else None),
                news.relevance,
                (
                    f"{news.reported_change_pct_low:g}-{news.reported_change_pct_high:g}%"
                    if news.reported_change_pct_low is not None
                    and news.reported_change_pct_high is not None
                    else "없음"
                ),
                news.title.replace("|", "/"),
            )
        )
        + " |"
        for news in result.contract_news[:10]
    )
    if not result.contract_news:
        news_rows.append("| 없음 | 없음 | 없음 | 없음 |")

    q1 = "Yes" if result.daily_express_count else "No"
    q2 = (
        "Yes"
        if result.price_parseable_daily_count and parse_rate >= 80
        else "Partial" if result.dram_price_observation_count else "No"
    )
    q3 = "Yes" if result.contract_news_count else "No in the current feed window"
    if result.freshness_lag_calendar_days is None:
        q4 = "No for daily spot; contract news remains event-driven"
    elif result.freshness_lag_calendar_days <= 1:
        q4 = "Yes"
    else:
        q4 = "Conditional"
    published_entries = [entry for entry in result.entries if entry.published_at]
    latest_feed_date = (
        max(entry.published_at for entry in published_entries).date()
        if published_entries
        else None
    )
    oldest_feed_date = (
        min(entry.published_at for entry in published_entries).date()
        if published_entries
        else None
    )
    latest_contract = next(
        (news for news in result.contract_news if news.published_at is not None),
        None,
    )
    contract_lag = (
        (morning_date - latest_contract.published_at.astimezone(KST).date()).days
        if latest_contract and latest_contract.published_at
        else None
    )
    recent_titles = [
        f"- `{_display(entry.published_at.date() if entry.published_at else None)}` "
        f"{entry.title}"
        for entry in result.entries[:5]
    ] or ["- 없음"]
    if result.recommendation == "recommended":
        recommendation_reason = (
            "Spot observations are fresh and consistent, and contract-news detection is available."
        )
    elif result.contract_news_count and not result.dram_price_observation_count:
        recommendation_reason = (
            "Spot automation is not supported by the current RSS window, while official "
            "contract-news detection works. Enable contract news only in a future implementation."
        )
    elif result.dram_price_observation_count:
        recommendation_reason = (
            "Spot observations exist but cadence, continuity, freshness, or contract-news "
            "coverage needs more validation."
        )
    else:
        recommendation_reason = (
            "The current RSS window does not provide enough evidence for automated DRAM context."
        )
    return "\n".join(
        (
            "# TrendForce DRAM RSS Feasibility Probe",
            "",
            "## 1. Source",
            "",
            f"- Feed: `{result.source_url}`",
            "- Subscription reference: `https://www.trendforce.com/presscenter/rss.html`",
            f"- Fetched at: `{result.fetched_at.isoformat()}`",
            f"- Morning run date: `{morning_date.isoformat()}`",
            "",
            "## 2. Terms-safe Method",
            "",
            "TrendForce price page scraping was not used. Only the official Semiconductors RSS feed was accessed programmatically.",
            "The probe consumed RSS title, description, pubDate, link, and category only. It did not fetch article bodies, member reports, paywalled content, hidden endpoints, or browser-rendered price pages.",
            "",
            "## 3. RSS Fetch Result",
            "",
            f"- Status: `{result.status}`",
            f"- Reason: `{_display(result.reason)}`",
            f"- Feed entries: `{result.entry_count}`",
            f"- Feed publication window: `{_display(oldest_feed_date)}` to `{_display(latest_feed_date)}`",
            f"- Daily Express entries: `{result.daily_express_count}`",
            f"- DRAM-context Daily Express entries: `{result.dram_daily_express_count}`",
            f"- Price-parseable Daily Express entries: `{result.price_parseable_daily_count}` (`{parse_rate:.1f}%`)",
            "- Recent feed titles:",
            *recent_titles,
            "",
            "## 4. Daily Express Coverage",
            "",
            f"- Q1: `{q1}` - Daily Express / Spot Market Today entries were {'found' if result.daily_express_count else 'not found'}.",
            f"- Q2: `{q2}` - exact representative prices were parsed only from explicit RSS summary wording.",
            "- Direction is taken from rises/drops/stays wording. A reported percentage is null unless the RSS states it explicitly.",
            "",
            "## 5. Parseable DRAM Product",
            "",
            f"- Representative product: `{_display(result.representative_product)}`",
            f"- Representative observations: `{result.representative_product_observation_count}`",
            "- Coverage of DRAM Daily Express entries: "
            f"`{_display_unit(result.representative_product_coverage_pct, '%')}`",
            f"- Latest price: `{_display_unit(result.latest_price_usd, ' USD')}`",
            f"- Latest direction: `{_display(result.latest_direction)}`",
            "",
            "## 6. Recent Samples",
            "",
            *price_rows,
            "",
            "## 7. Same-product Continuity",
            "",
            "- Computed latest change: "
            f"`{_display_unit(result.computed_change_abs, ' USD')}` / "
            f"`{_display_unit(result.computed_change_pct, '%')}`",
            "- The computed change is produced only between high-confidence observations with the exact same product identity.",
            "- A DDR4 observation is never linked to a DDR5 observation.",
            "",
            "## 8. Contract-news Coverage",
            "",
            f"- Q3: `{q3}`",
            f"- Contract-news candidates: `{result.contract_news_count}`",
            f"- Latest detected contract news lag: `{_display(contract_lag)}` calendar day(s)",
            "- These are news observations, not contract quote-table observations. Numeric ranges are preserved only when present in RSS title/summary.",
            "",
            *news_rows,
            "",
            "## 9. Freshness",
            "",
            f"- Latest DRAM source date: `{_display(result.latest_dram_date)}`",
            f"- Lag to morning run: `{_display(result.freshness_lag_calendar_days)}` calendar day(s)",
            f"- Q4: `{q4}`. Last-known values must always display their RSS source date.",
            "",
            "## 10. Missing Days",
            "",
            f"- Missing weekdays inside the observed Daily Express date range: `{', '.join(map(str, result.missing_weekdays)) or 'none'}`",
            "- Weekends and market holidays may legitimately have no new Daily Express entry.",
            "",
            "## 11. Parser Confidence",
            "",
            "- `high`: exact product, direction verb, USD value, source date, and source link are present in the RSS item.",
            "- Commentary without a matching price sentence remains context-only and does not create a numeric observation.",
            "- Malformed XML, HTTP failure, and empty feeds return `unavailable` instead of raising through the job.",
            "",
            "## 12. Production Recommendation",
            "",
            f"Decision: **{result.recommendation}**",
            "",
            recommendation_reason,
            "",
            "A production implementation must continue to use the official RSS only. If spot extraction is not reliable enough, omit the price and retain contract news when available; do not fall back to HTML scraping. Authorized APIs, licensed downloads, or user-provided local snapshots are the acceptable alternatives.",
            "",
        )
    )


async def _run(args: argparse.Namespace) -> DramRssProbeResult:
    run_date = date.fromisoformat(args.as_of) if args.as_of else datetime.now(KST).date()
    if args.fixture:
        try:
            xml_text = args.fixture.read_text(encoding="utf-8")
        except OSError as exc:
            return DramRssProbeResult(
                status="unavailable",
                fetched_at=datetime.now(timezone.utc),
                reason=f"fixture_read_failed:{type(exc).__name__}",
            )
        return parse_dram_rss(xml_text, run_date=run_date)
    return await fetch_live_probe(run_date=run_date)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Probe TrendForce's official Semiconductors RSS for DRAM feasibility."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="Fetch the official RSS once.")
    mode.add_argument("--fixture", type=Path, help="Parse a local RSS XML fixture.")
    parser.add_argument("--as-of", help="Morning run date in YYYY-MM-DD format.")
    parser.add_argument("--output", type=Path, help="Write parsed probe metadata as JSON.")
    parser.add_argument("--report", type=Path, help="Write a Markdown feasibility report.")
    args = parser.parse_args()
    result = asyncio.run(_run(args))
    if args.output:
        args.output.write_text(
            json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.report:
        morning_date = date.fromisoformat(args.as_of) if args.as_of else datetime.now(KST).date()
        args.report.write_text(
            render_feasibility_report(result, morning_date=morning_date),
            encoding="utf-8",
        )
    print(json.dumps(result.compact_summary(), ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
