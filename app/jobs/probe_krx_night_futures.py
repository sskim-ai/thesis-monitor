import argparse
import asyncio
from datetime import date, datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re

import httpx
from pydantic import BaseModel, Field

from app.config import get_settings


KRX_FUTURES_DAILY_URL = "https://data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd"
KRX_SERVICE_NAME = "fut_bydd_trd"
USER_AGENT = "thesis-monitor/KRX-night-futures-probe"
TARGET_PRODUCTS = ("KOSPI200", "KOSDAQ150")

_MATURITY_YYYYMM_RE = re.compile(r"(?<!\d)(20\d{2})[./\- ]?(0[1-9]|1[0-2])(?!\d)")
_MATURITY_YYMM_RE = re.compile(r"(?<!\d)(\d{2})[./\- ]?(0[1-9]|1[0-2])(?!\d)")


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
    regular_close: float
    night_close: float
    point_change: float
    change_pct: float | None = None
    session_evidence: str = "MKT_NM:정규/야간"


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
    if not all((business_date, product, session, contract_code, contract_name)) or close is None:
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


def parse_krx_futures_payload(
    payload: object,
    *,
    fetched_at: datetime | None = None,
    queried_dates: list[date] | None = None,
) -> KrxNightFuturesProbeResult:
    fetched_at = fetched_at or datetime.now(timezone.utc)
    raw_rows = _rows(payload)
    field_names = sorted({key for row in raw_rows for key in row})
    session_values = sorted(
        {str(row.get("MKT_NM") or "").strip() for row in raw_rows if row.get("MKT_NM")}
    )
    result = KrxNightFuturesProbeResult(
        status="ok" if raw_rows else "unavailable",
        fetched_at=fetched_at,
        queried_dates=queried_dates or [],
        field_names=field_names,
        row_count=len(raw_rows),
        session_values=session_values,
        reason=None if raw_rows else "empty_response",
    )
    parsed = [row for item in raw_rows if (row := _parse_row(item)) is not None]
    if not parsed:
        if raw_rows:
            result.reason = "no_unambiguous_target_contract_rows"
        return result

    source_date = max(row.business_date for row in parsed)
    result.source_date = source_date
    source_rows = [row for row in parsed if row.business_date == source_date]
    for product in TARGET_PRODUCTS:
        product_rows = [row for row in source_rows if row.product == product]
        by_contract: dict[str, list[KrxFuturesRow]] = {}
        for row in product_rows:
            by_contract.setdefault(row.contract_code, []).append(row)
        candidates: list[tuple[tuple[int, int], KrxFuturesRow, KrxFuturesRow]] = []
        for contract_rows in by_contract.values():
            regular = [row for row in contract_rows if row.session == "regular"]
            night = [row for row in contract_rows if row.session == "night"]
            maturities = {row.maturity for row in contract_rows if row.maturity}
            if len(regular) != 1 or len(night) != 1 or len(maturities) != 1:
                continue
            maturity = next(iter(maturities))
            if maturity is None:
                continue
            if _maturity_key(maturity) < (source_date.year, source_date.month):
                continue
            candidates.append((_maturity_key(maturity), regular[0], night[0]))
        if not candidates:
            if product_rows:
                result.warnings.append(
                    f"{product}:same-contract regular/night pair with maturity unavailable"
                )
            continue
        _, regular, night = min(candidates, key=lambda item: item[0])
        point_change = night.close - regular.close
        result.observations.append(
            KrxNightFutureObservation(
                product=product,
                contract_code=regular.contract_code,
                contract_name=regular.contract_name,
                maturity=regular.maturity or "",
                source_date=source_date,
                regular_close=regular.close,
                night_close=night.close,
                point_change=round(point_change, 8),
                change_pct=(
                    round(point_change / regular.close * 100, 8)
                    if regular.close != 0
                    else None
                ),
            )
        )
    result.night_session_usable = bool(result.observations)
    if not result.night_session_usable:
        result.reason = "night_session_or_contract_identity_not_verifiable"
    return result


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
    latest_nonempty: KrxNightFuturesProbeResult | None = None
    last_fetch_error: str | None = None
    successful_response_count = 0
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
                skipped_warnings.append(
                    f"{target_date}: fetch failed ({type(exc).__name__})"
                )
                continue
            successful_response_count += 1
            result = parse_krx_futures_payload(
                payload,
                fetched_at=fetched_at,
                queried_dates=queried_dates,
            )
            if result.night_session_usable:
                result.warnings = skipped_warnings + result.warnings
                return result
            if result.row_count:
                if latest_nonempty is None:
                    latest_nonempty = result
                skipped_warnings.append(
                    f"{target_date}: rows present but no verified regular/night pair"
                )
    if latest_nonempty is not None:
        latest_nonempty.status = "unavailable"
        latest_nonempty.reason = "no_recent_verified_night_pair"
        latest_nonempty.queried_dates = queried_dates
        latest_nonempty.warnings = skipped_warnings + latest_nonempty.warnings
        return latest_nonempty
    if successful_response_count == 0 and last_fetch_error is not None:
        return KrxNightFuturesProbeResult(
            status="unavailable",
            fetched_at=fetched_at,
            queried_dates=queried_dates,
            reason=last_fetch_error,
            warnings=skipped_warnings,
        )
    return KrxNightFuturesProbeResult(
        status="unavailable",
        fetched_at=fetched_at,
        queried_dates=queried_dates,
        reason="no_recent_business_date_data",
        warnings=skipped_warnings,
    )


def _report(result: KrxNightFuturesProbeResult) -> str:
    observation_lines = "\n".join(
        f"- {item.product}: {item.contract_code}, {item.maturity}, regular "
        f"{item.regular_close:g}, night {item.night_close:g}, "
        f"{item.point_change:+g} ({item.change_pct:+.4f}%)"
        for item in result.observations
    ) or "- No verified same-contract regular/night observation."
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
- Rows: {result.row_count}
- Session values: {', '.join(result.session_values) or 'unavailable'}
- Field names: {', '.join(result.field_names) or 'unavailable'}
- Night/day separation usable: `{str(result.night_session_usable).lower()}`

## Contract Evidence

{observation_lines}

Only rows with explicit regular/night session metadata, the same contract code, and an
interpretable maturity were paired. Spot-index comparisons, cross-expiry comparisons,
row-order inference, and volume-based front-month inference were not used.

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
