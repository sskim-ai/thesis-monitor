import argparse
import asyncio
import hashlib
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import exchange_calendars as exchange_calendar
import httpx
from pydantic import BaseModel, Field

from app.config import get_settings


KRX_FUTURES_DAILY_URL = "https://data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd"
KRX_SERVICE_NAME = "fut_bydd_trd"
USER_AGENT = "thesis-monitor/KRX-night-futures-probe"
TARGET_PRODUCTS = ("KOSPI200", "KOSDAQ150")
NIGHT_FUTURES_SESSION_BASIS_CONTRACT = "night-futures-session-basis-v1"
NIGHT_COMPARISON_SEMANTIC = (
    "completed_night_close_minus_immediately_preceding_day_close"
)

_MATURITY_YYYYMM_RE = re.compile(r"(?<!\d)(20\d{2})[./\- ]?(0[1-9]|1[0-2])(?!\d)")
_MATURITY_YYMM_RE = re.compile(r"(?<!\d)(\d{2})[./\- ]?(0[1-9]|1[0-2])(?!\d)")


def expected_latest_completed_krx_session(run_date: date) -> date | None:
    """Return the latest completed KRX night session by its 06:00 end date."""
    try:
        calendar = exchange_calendar.get_calendar("XKRX")
        for days_back in range(8):
            session_date = run_date - timedelta(days=days_back)
            start_date = session_date - timedelta(days=1)
            if calendar.is_session(start_date):
                return session_date
    except (ValueError, IndexError, TypeError):
        return None
    return None


class KrxFuturesRow(BaseModel):
    business_date: date
    product: str
    session: str
    contract_code: str
    contract_name: str
    maturity: str | None = None
    close: float
    volume: int | None = None
    open_interest: int | None = None


class KrxNightFutureObservation(BaseModel):
    product: str
    contract_code: str
    contract_name: str
    maturity: str
    source_date: date
    session_type: str = "NIGHT"
    session_date: date
    reference_session: str = "DAY"
    reference_date: date
    exchange: str = "XKRX"
    regular_close: float
    night_close: float
    reference_price: float
    current_session_price: float
    point_change: float
    change_pct: float
    comparison_semantic: str = NIGHT_COMPARISON_SEMANTIC
    night_source_record_id: str
    reference_source_record_id: str
    night_source_payload_sha256: str | None = None
    reference_source_payload_sha256: str | None = None
    session_evidence: str = "MKT_NM:정규/야간"


class KrxProbeDateStatus(BaseModel):
    query_date: date
    row_count: int = 0
    verified_products: list[str] = Field(default_factory=list)
    result: str


class KrxNightFuturesProbeResult(BaseModel):
    status: str
    service: str = KRX_SERVICE_NAME
    source_url: str = KRX_FUTURES_DAILY_URL
    fetched_at: datetime
    reason: str | None = None
    queried_dates: list[date] = Field(default_factory=list)
    source_date: date | None = None
    field_names: list[str] = Field(default_factory=list)
    row_count: int = 0
    session_values: list[str] = Field(default_factory=list)
    night_session_usable: bool = False
    observations: list[KrxNightFutureObservation] = Field(default_factory=list)
    date_statuses: list[KrxProbeDateStatus] = Field(default_factory=list)
    expected_latest_session_date: date | None = None
    session_freshness: str = "unverified"
    warnings: list[str] = Field(default_factory=list)

    def compact_summary(self) -> dict[str, object]:
        return {
            "status": self.status,
            "service": self.service,
            "queried_dates": self.queried_dates,
            "source_date": self.source_date,
            "row_count": self.row_count,
            "field_names": self.field_names,
            "session_values": self.session_values,
            "night_session_usable": self.night_session_usable,
            "expected_latest_session_date": self.expected_latest_session_date,
            "session_freshness": self.session_freshness,
            "date_statuses": [item.model_dump(mode="json") for item in self.date_statuses],
            "products": [item.model_dump(mode="json") for item in self.observations],
            "reason": self.reason,
            "warnings": self.warnings,
        }


def _number(value: object) -> float | None:
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _integer(value: object) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _business_date(value: object) -> date | None:
    text = str(value or "").strip()
    try:
        return datetime.strptime(text, "%Y%m%d").date()
    except ValueError:
        return None


def _session(value: object) -> str | None:
    text = str(value or "").strip()
    if "야간" in text:
        return "night"
    if "정규" in text or "주간" in text:
        return "regular"
    return None


def _target_product(product_name: object, contract_name: object) -> str | None:
    product = re.sub(r"\s+", "", str(product_name or "")).upper()
    contract = re.sub(r"\s+", " ", str(contract_name or "")).strip()
    if "미니" in product or "미니" in contract or " SP " in f" {contract} ":
        return None
    if product in {"KOSDAQ150선물", "코스닥150선물"} and contract.startswith(
        "코스닥150 F "
    ):
        return "KOSDAQ150"
    if product in {"KOSPI200선물", "코스피200선물"} and contract.startswith(
        "코스피200 F "
    ):
        return "KOSPI200"
    return None


def _maturity(contract_name: str) -> str | None:
    match = _MATURITY_YYYYMM_RE.search(contract_name)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    match = _MATURITY_YYMM_RE.search(contract_name)
    if match:
        year = int(match.group(1))
        if year >= 20:
            return f"20{year:02d}-{match.group(2)}"
    return None


def _rows(payload: object) -> list[dict[str, object]]:
    if not isinstance(payload, dict):
        return []
    value = payload.get("OutBlock_1")
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _parse_row(item: dict[str, object]) -> KrxFuturesRow | None:
    business_date = _business_date(item.get("BAS_DD"))
    product = _target_product(item.get("PROD_NM"), item.get("ISU_NM"))
    session = _session(item.get("MKT_NM"))
    contract_code = str(item.get("ISU_CD") or "").strip()
    contract_name = str(item.get("ISU_NM") or "").strip()
    close = _number(item.get("TDD_CLSPRC"))
    if (
        not all((business_date, product, session, contract_code, contract_name))
        or close is None
    ):
        return None
    return KrxFuturesRow(
        business_date=business_date,
        product=product,
        session=session,
        contract_code=contract_code,
        contract_name=contract_name,
        maturity=_maturity(contract_name),
        close=close,
        volume=_integer(item.get("ACC_TRDVOL")),
        open_interest=_integer(item.get("ACC_OPNINT_QTY")),
    )


def _maturity_key(value: str) -> tuple[int, int]:
    year, month = value.split("-", 1)
    return int(year), int(month)


def _source_record_id(row: KrxFuturesRow) -> str:
    return ":".join(
        (
            row.business_date.isoformat(),
            row.session.upper(),
            row.contract_code,
        )
    )


def _payload_sha256(payload: object) -> str:
    value = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_krx_futures_payloads(
    payloads: dict[date, object],
    *,
    fetched_at: datetime | None = None,
    queried_dates: list[date] | None = None,
    payload_sha256_by_date: dict[date, str] | None = None,
) -> KrxNightFuturesProbeResult:
    """Pair a NIGHT close with the preceding calendar day's DAY close.

    KRX assigns the trading day from the night session's 06:00 end time. A
    NIGHT row for T+1 therefore cannot be compared with the DAY row carrying
    the same BAS_DD; that DAY session occurs later. Both source dates and the
    same contract are required before a change can be promoted.
    """
    fetched_at = fetched_at or datetime.now(timezone.utc)
    payload_sha256_by_date = payload_sha256_by_date or {
        key: _payload_sha256(value) for key, value in payloads.items()
    }
    raw_rows_by_date = {key: _rows(value) for key, value in payloads.items()}
    raw_rows = [row for rows in raw_rows_by_date.values() for row in rows]
    result = KrxNightFuturesProbeResult(
        status="ok" if raw_rows else "unavailable",
        fetched_at=fetched_at,
        queried_dates=queried_dates or list(payloads),
        field_names=sorted({key for row in raw_rows for key in row}),
        row_count=len(raw_rows),
        session_values=sorted(
            {
                str(row.get("MKT_NM") or "").strip()
                for row in raw_rows
                if row.get("MKT_NM")
            }
        ),
        reason=None if raw_rows else "empty_response",
    )
    parsed = [row for item in raw_rows if (row := _parse_row(item)) is not None]
    night_dates = sorted(
        {row.business_date for row in parsed if row.session == "night"},
        reverse=True,
    )
    for session_date in night_dates:
        reference_date = session_date - timedelta(days=1)
        observations: list[KrxNightFutureObservation] = []
        for product in TARGET_PRODUCTS:
            nights = [
                row
                for row in parsed
                if row.product == product
                and row.session == "night"
                and row.business_date == session_date
            ]
            candidates: list[tuple[tuple[int, int], KrxFuturesRow, KrxFuturesRow]] = []
            for night in nights:
                regular = [
                    row
                    for row in parsed
                    if row.product == product
                    and row.session == "regular"
                    and row.business_date == reference_date
                    and row.contract_code == night.contract_code
                    and row.maturity == night.maturity
                ]
                if (
                    len(regular) != 1
                    or night.maturity is None
                    or regular[0].close == 0
                ):
                    continue
                if _maturity_key(night.maturity) < (
                    reference_date.year,
                    reference_date.month,
                ):
                    continue
                candidates.append((_maturity_key(night.maturity), regular[0], night))
            if not candidates:
                if nights:
                    result.warnings.append(
                        f"{product}:preceding-day same-contract DAY reference unavailable"
                    )
                continue
            _, regular, night = min(candidates, key=lambda item: item[0])
            point_change = night.close - regular.close
            observations.append(
                KrxNightFutureObservation(
                    product=product,
                    contract_code=night.contract_code,
                    contract_name=night.contract_name,
                    maturity=night.maturity or "",
                    source_date=session_date,
                    session_date=session_date,
                    reference_date=reference_date,
                    regular_close=regular.close,
                    night_close=night.close,
                    reference_price=regular.close,
                    current_session_price=night.close,
                    point_change=round(point_change, 8),
                    change_pct=round(point_change / regular.close * 100, 8),
                    night_source_record_id=_source_record_id(night),
                    reference_source_record_id=_source_record_id(regular),
                    night_source_payload_sha256=payload_sha256_by_date.get(
                        session_date
                    ),
                    reference_source_payload_sha256=payload_sha256_by_date.get(
                        reference_date
                    ),
                )
            )
        if observations:
            result.source_date = session_date
            result.observations = observations
            result.night_session_usable = True
            result.reason = None
            return result
    if parsed:
        result.reason = "night_reference_session_or_contract_identity_not_verifiable"
    return result


def parse_krx_futures_payload(
    payload: object,
    *,
    fetched_at: datetime | None = None,
    queried_dates: list[date] | None = None,
) -> KrxNightFuturesProbeResult:
    dates = {
        row.business_date
        for item in _rows(payload)
        if (row := _parse_row(item)) is not None
    }
    key = max(dates) if dates else date.min
    return parse_krx_futures_payloads(
        {key: payload},
        fetched_at=fetched_at,
        queried_dates=queried_dates,
    )


async def fetch_live_probe(
    *,
    run_date: date | None = None,
    api_key: str | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
    max_lookback_days: int = 7,
) -> KrxNightFuturesProbeResult:
    run_date = run_date or date.today()
    api_key = api_key if api_key is not None else get_settings().krx_open_api_key
    fetched_at = datetime.now(timezone.utc)
    if not api_key:
        return KrxNightFuturesProbeResult(
            status="not_configured",
            fetched_at=fetched_at,
            reason="KRX_OPEN_API_KEY is not configured",
        )
    queried_dates: list[date] = []
    skipped_warnings: list[str] = []
    last_fetch_error: str | None = None
    successful_response_count = 0
    date_statuses: list[KrxProbeDateStatus] = []
    calendar_expected_date = expected_latest_completed_krx_session(run_date)
    payloads: dict[date, object] = {}
    payload_shas: dict[date, str] = {}
    async with httpx.AsyncClient(
        timeout=get_settings().macro_provider_timeout_seconds,
        transport=transport,
        headers={"AUTH_KEY": api_key, "User-Agent": USER_AGENT},
    ) as client:
        for days_back in range(max(1, max_lookback_days)):
            target_date = run_date - timedelta(days=days_back)
            queried_dates.append(target_date)
            try:
                response = await client.get(
                    KRX_FUTURES_DAILY_URL,
                    params={"basDd": target_date.strftime("%Y%m%d")},
                )
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError, TypeError) as exc:
                last_fetch_error = f"krx_fetch_failed:{type(exc).__name__}"
                date_statuses.append(
                    KrxProbeDateStatus(query_date=target_date, result="fetch_error")
                )
                skipped_warnings.append(
                    f"{target_date}: fetch failed ({type(exc).__name__})"
                )
                continue
            successful_response_count += 1
            payloads[target_date] = payload
            payload_shas[target_date] = hashlib.sha256(response.content).hexdigest()
            row_count = len(_rows(payload))
            date_statuses.append(
                KrxProbeDateStatus(
                    query_date=target_date,
                    row_count=row_count,
                    result="rows_without_verified_pair" if row_count else "empty",
                )
            )
            result = parse_krx_futures_payloads(
                payloads,
                fetched_at=fetched_at,
                queried_dates=queried_dates,
                payload_sha256_by_date=payload_shas,
            )
            if result.night_session_usable:
                for status in date_statuses:
                    if status.query_date == result.source_date:
                        status.result = "verified_pair"
                        status.verified_products = [
                            item.product for item in result.observations
                        ]
                result.date_statuses = list(date_statuses)
                result.expected_latest_session_date = calendar_expected_date
                intervening_errors = any(
                    item.result == "fetch_error"
                    and result.source_date is not None
                    and result.source_date < item.query_date < run_date
                    for item in date_statuses
                )
                if intervening_errors:
                    result.session_freshness = "unverified"
                elif result.source_date == result.expected_latest_session_date:
                    result.session_freshness = "fresh"
                else:
                    result.session_freshness = "stale"
                if result.session_freshness != "fresh":
                    skipped_warnings.append(
                        "verified night-futures pair is older than the latest completed "
                        "session evidence"
                    )
                result.warnings = skipped_warnings + result.warnings
                return result
            if row_count:
                skipped_warnings.append(
                    f"{target_date}: rows present but no verified NIGHT/preceding-DAY pair"
                )
    aggregate = parse_krx_futures_payloads(
        payloads,
        fetched_at=fetched_at,
        queried_dates=queried_dates,
        payload_sha256_by_date=payload_shas,
    )
    if aggregate.row_count:
        aggregate.status = "unavailable"
        aggregate.expected_latest_session_date = calendar_expected_date
        aggregate.date_statuses = date_statuses
        aggregate.reason = "no_recent_verified_night_reference_pair"
        aggregate.warnings = skipped_warnings + aggregate.warnings
        return aggregate
    if successful_response_count == 0 and last_fetch_error is not None:
        return KrxNightFuturesProbeResult(
            status="unavailable",
            fetched_at=fetched_at,
            queried_dates=queried_dates,
            date_statuses=date_statuses,
            reason=last_fetch_error,
            warnings=skipped_warnings,
        )
    return KrxNightFuturesProbeResult(
        status="unavailable",
        fetched_at=fetched_at,
        queried_dates=queried_dates,
        date_statuses=date_statuses,
        reason="no_recent_business_date_data",
        warnings=skipped_warnings,
    )


def _report(result: KrxNightFuturesProbeResult) -> str:
    observation_lines = "\n".join(
        f"- {item.product}: {item.contract_code}, {item.maturity}, "
        f"{item.reference_date} DAY {item.regular_close:g}, "
        f"{item.session_date} NIGHT {item.night_close:g}, "
        f"{item.point_change:+g} ({item.change_pct:+.4f}%)"
        for item in result.observations
    ) or "- No verified same-contract NIGHT/preceding-DAY observation."
    date_status_lines = "\n".join(
        f"- {item.query_date}: {item.result}, rows={item.row_count}, "
        f"verified={','.join(item.verified_products) or 'none'}"
        for item in result.date_statuses
    ) or "- No date-level diagnostics."
    recommendation = "production enabled" if result.night_session_usable else "not enabled"
    return f"""# KRX Night Futures Feasibility

## Source

- Official service: KRX Open API 선물 일별매매정보 (주식선물外)
- Endpoint identifier: `{KRX_SERVICE_NAME}`
- Authentication: `AUTH_KEY` request header only
- Source URL stored without credentials: `{KRX_FUTURES_DAILY_URL}`

## Probe Result

- Status: `{result.status}`
- Queried dates: {', '.join(str(item) for item in result.queried_dates) or 'none'}
- Source date: `{result.source_date or 'unavailable'}`
- Expected latest completed session: `{result.expected_latest_session_date or 'unavailable'}`
- Session freshness: `{result.session_freshness}`
- Rows: {result.row_count}
- Session values: {', '.join(result.session_values) or 'unavailable'}
- Field names: {', '.join(result.field_names) or 'unavailable'}
- Night/day separation usable: `{str(result.night_session_usable).lower()}`

### Date Evidence

{date_status_lines}

## Contract Evidence

{observation_lines}

Only a NIGHT row and the preceding calendar day's DAY row with explicit session
metadata, the same contract code, and an interpretable maturity were paired. A DAY row
with the same `BAS_DD` occurs after that NIGHT session and is never used as its
reference. Spot-index comparisons, cross-expiry comparisons, row-order inference, and
volume-based front-month inference were not used.

## Production Decision

**{recommendation}**

Reason: `{result.reason or 'verified explicit session and contract semantics'}`
"""


async def main() -> None:
    parser = argparse.ArgumentParser(description="Probe official KRX night-futures semantics.")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.fixture:
        try:
            payload = json.loads(args.fixture.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            result = KrxNightFuturesProbeResult(
                status="unavailable",
                fetched_at=datetime.now(timezone.utc),
                reason=f"fixture_load_failed:{type(exc).__name__}",
            )
        else:
            result = parse_krx_futures_payload(payload)
    elif args.live:
        result = await fetch_live_probe()
    else:
        result = KrxNightFuturesProbeResult(
            status="not_configured",
            fetched_at=datetime.now(timezone.utc),
            reason="Use --live or --fixture",
        )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(_report(result), encoding="utf-8")
    print(json.dumps(result.compact_summary(), ensure_ascii=False, default=str))


if __name__ == "__main__":
    asyncio.run(main())
