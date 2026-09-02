import argparse
import asyncio
import hashlib
import json
import math
import re
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import httpx
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.market_session import preceding_exchange_session_date
from app.services.night_futures_session_mapping_service import (
    KST,
    US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT,
    classify_provider_reference_date,
    resolve_us_morning_night_reference_date,
)


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
    """Return the US morning digest's previous valid XKRX reference date."""
    mapping = resolve_us_morning_night_reference_date(
        datetime.combine(run_date, time(8, 0), tzinfo=KST)
    )
    return mapping.expected_reference_date if mapping is not None else None


class KrxFuturesRow(BaseModel):
    business_date: date
    product: str
    session: str
    contract_code: str
    contract_name: str
    maturity: str | None = None
    close: float
    provider_change_point: float | None = None
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
    provider_change_point: float | None = None
    provider_change_match: bool | None = None
    comparison_semantic: str = NIGHT_COMPARISON_SEMANTIC
    night_source_record_id: str
    reference_source_record_id: str
    night_source_payload_sha256: str | None = None
    reference_source_payload_sha256: str | None = None
    session_evidence: str = "MKT_NM:정규/야간"
    expected_reference_date: date | None = None
    provider_raw_bas_dd: date | None = None
    reference_date_match: bool = False
    reference_date_relation: str = "UNVERIFIED"
    finality_valid: bool = False


class KrxProbeDateStatus(BaseModel):
    query_date: date
    row_count: int = 0
    verified_products: list[str] = Field(default_factory=list)
    http_status: int | None = None
    returned_business_dates: list[date] = Field(default_factory=list)
    returned_night_business_dates: list[date] = Field(default_factory=list)
    raw_payload_sha256: str | None = None
    result: str


class KrxProbeProductStatus(BaseModel):
    product: str
    expected_night_bas_dd: date | None = None
    returned_night_bas_dd: date | None = None
    matched_day_bas_dd: date | None = None
    contract_code: str | None = None
    maturity: str | None = None
    row_state: str
    readiness: str
    rejection_reason: str | None = None
    provider_change_crosscheck_status: str = "NOT_OBSERVED"
    expected_reference_date: date | None = None
    provider_raw_bas_dd: date | None = None
    reference_date_match: bool = False
    reference_date_relation: str = "UNVERIFIED"
    finality_valid: bool = False


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
    returned_business_dates: list[date] = Field(default_factory=list)
    returned_night_session_dates: list[date] = Field(default_factory=list)
    product_statuses: list[KrxProbeProductStatus] = Field(default_factory=list)
    parsed_row_count: int = 0
    parser_status: str = "NOT_OBSERVED"
    canonicalization_status: str = "NOT_OBSERVED"
    provider_change_crosscheck_status: str = "NOT_OBSERVED"
    expected_latest_session_date: date | None = None
    reference_date_contract: str = US_MORNING_NIGHT_REFERENCE_DATE_CONTRACT
    expected_reference_date: date | None = None
    provider_raw_bas_dd: date | None = None
    reference_date_match_count: int = 0
    finality_valid: bool = False
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
            "reference_date_contract": self.reference_date_contract,
            "expected_reference_date": self.expected_reference_date,
            "provider_raw_bas_dd": self.provider_raw_bas_dd,
            "reference_date_match_count": self.reference_date_match_count,
            "finality_valid": self.finality_valid,
            "session_freshness": self.session_freshness,
            "date_statuses": [item.model_dump(mode="json") for item in self.date_statuses],
            "returned_business_dates": self.returned_business_dates,
            "returned_night_session_dates": self.returned_night_session_dates,
            "product_statuses": [
                item.model_dump(mode="json") for item in self.product_statuses
            ],
            "parsed_row_count": self.parsed_row_count,
            "parser_status": self.parser_status,
            "canonicalization_status": self.canonicalization_status,
            "provider_change_crosscheck_status": (
                self.provider_change_crosscheck_status
            ),
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
        provider_change_point=_number(item.get("CMPPREVDD_PRC")),
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
    """Pair a NIGHT close with the preceding eligible XKRX DAY close.

    KRX assigns the trading day from the night session's 06:00 end time. A
    NIGHT row for T+1 therefore cannot be compared with the DAY row carrying
    the same BAS_DD; that DAY session occurs later. Weekends and exchange
    holidays are traversed with the XKRX calendar. Both source dates and the
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
    result.parsed_row_count = len(parsed)
    result.parser_status = (
        "PASS" if parsed or not raw_rows else "PARSER_ERROR"
    )
    result.returned_business_dates = sorted(
        {row.business_date for row in parsed}
    )
    result.returned_night_session_dates = sorted(
        {row.business_date for row in parsed if row.session == "night"}
    )
    night_dates = sorted(
        {row.business_date for row in parsed if row.session == "night"},
        reverse=True,
    )
    for session_date in night_dates:
        reference_date = preceding_exchange_session_date("XKRX", session_date)
        if reference_date is None:
            result.warnings.append(
                f"{session_date}:preceding eligible XKRX DAY session unavailable"
            )
            continue
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
                derived_change = night.close - regular[0].close
                if night.provider_change_point is not None and not math.isclose(
                    night.provider_change_point,
                    derived_change,
                    rel_tol=0,
                    abs_tol=1e-8,
                ):
                    result.warnings.append(
                        f"{product}:{session_date}:provider change conflicts with "
                        "verified NIGHT/preceding-DAY prices"
                    )
                    continue
                candidates.append((_maturity_key(night.maturity), regular[0], night))
            if not candidates:
                if nights:
                    result.warnings.append(
                        f"{product}:preceding-eligible same-contract DAY reference unavailable"
                    )
                continue
            _, regular, night = min(candidates, key=lambda item: item[0])
            point_change = night.close - regular.close
            provider_change_match = (
                None if night.provider_change_point is None else True
            )
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
                    provider_change_point=night.provider_change_point,
                    provider_change_match=provider_change_match,
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
            result.canonicalization_status = "PASS"
            result.provider_change_crosscheck_status = "PASS"
            result.reason = None
            return result
    if parsed:
        result.canonicalization_status = "BLOCKED"
        result.provider_change_crosscheck_status = (
            "FAILED"
            if any("provider change conflicts" in item for item in result.warnings)
            else "NOT_OBSERVED"
        )
        result.reason = "night_reference_session_or_contract_identity_not_verifiable"
    return result


def _product_statuses(
    payloads: dict[date, object],
    expected_session: date | None,
    result: KrxNightFuturesProbeResult,
    *,
    finality_valid: bool,
) -> list[KrxProbeProductStatus]:
    parsed = [
        row
        for payload in payloads.values()
        for item in _rows(payload)
        if (row := _parse_row(item)) is not None
    ]
    reference_date = (
        preceding_exchange_session_date("XKRX", expected_session)
        if expected_session
        else None
    )
    ready = {item.product: item for item in result.observations}
    statuses: list[KrxProbeProductStatus] = []
    for product in TARGET_PRODUCTS:
        nights = [
            row for row in parsed if row.product == product and row.session == "night"
        ]
        expected_rows = [
            row for row in nights if row.business_date == expected_session
        ]
        latest = max(nights, key=lambda item: item.business_date, default=None)
        observation = ready.get(product)
        returned_date = (
            observation.session_date
            if observation is not None
            else latest.business_date
            if latest is not None
            else None
        )
        date_relation = classify_provider_reference_date(
            returned_date,
            expected_session,
        )
        common = {
            "expected_reference_date": expected_session,
            "provider_raw_bas_dd": returned_date,
            "reference_date_match": date_relation == "DATE_MATCH",
            "reference_date_relation": date_relation,
            "finality_valid": finality_valid,
        }
        if (
            observation is not None
            and observation.session_date == expected_session
            and finality_valid
        ):
            statuses.append(
                KrxProbeProductStatus(
                    product=product,
                    expected_night_bas_dd=expected_session,
                    returned_night_bas_dd=observation.session_date,
                    matched_day_bas_dd=observation.reference_date,
                    contract_code=observation.contract_code,
                    maturity=observation.maturity,
                    row_state="EXPECTED_SESSION_PRESENT",
                    readiness="READY",
                    provider_change_crosscheck_status=(
                        "PASS"
                        if observation.provider_change_match is not False
                        else "FAILED"
                    ),
                    **common,
                )
            )
            continue
        if not expected_rows:
            statuses.append(
                KrxProbeProductStatus(
                    product=product,
                    expected_night_bas_dd=expected_session,
                    returned_night_bas_dd=(latest.business_date if latest else None),
                    contract_code=(latest.contract_code if latest else None),
                    maturity=(latest.maturity if latest else None),
                    row_state=(
                        "STALE_PRIOR_REFERENCE"
                        if date_relation == "STALE_PRIOR_REFERENCE"
                        else "UNEXPECTED_FUTURE_REFERENCE"
                        if date_relation == "UNEXPECTED_FUTURE_REFERENCE"
                        else "NO_NIGHT_ROW"
                    ),
                    readiness="NOT_READY",
                    rejection_reason=(
                        "stale_prior_reference"
                        if date_relation == "STALE_PRIOR_REFERENCE"
                        else "unexpected_future_reference"
                        if date_relation == "UNEXPECTED_FUTURE_REFERENCE"
                        else "expected_reference_absent"
                        if latest is not None
                        else "night_rows_absent"
                    ),
                    **common,
                )
            )
            continue
        if observation is not None and observation.session_date == expected_session:
            statuses.append(
                KrxProbeProductStatus(
                    product=product,
                    expected_night_bas_dd=expected_session,
                    returned_night_bas_dd=observation.session_date,
                    matched_day_bas_dd=observation.reference_date,
                    contract_code=observation.contract_code,
                    maturity=observation.maturity,
                    row_state="EXPECTED_REFERENCE_PRESENT_UNFINALIZED",
                    readiness="NOT_READY",
                    rejection_reason="session_not_final",
                    provider_change_crosscheck_status=(
                        "PASS"
                        if observation.provider_change_match is not False
                        else "FAILED"
                    ),
                    **common,
                )
            )
            continue
        selected = expected_rows[0]
        matching_day = [
            row
            for row in parsed
            if row.product == product
            and row.session == "regular"
            and row.business_date == reference_date
            and row.contract_code == selected.contract_code
            and row.maturity == selected.maturity
        ]
        other_day_contracts = [
            row
            for row in parsed
            if row.product == product
            and row.session == "regular"
            and row.business_date == reference_date
        ]
        conflict = bool(
            matching_day
            and selected.provider_change_point is not None
            and not math.isclose(
                selected.provider_change_point,
                selected.close - matching_day[0].close,
                rel_tol=0,
                abs_tol=1e-8,
            )
        )
        statuses.append(
            KrxProbeProductStatus(
                product=product,
                expected_night_bas_dd=expected_session,
                returned_night_bas_dd=selected.business_date,
                matched_day_bas_dd=(matching_day[0].business_date if matching_day else None),
                contract_code=selected.contract_code,
                maturity=selected.maturity,
                row_state="EXPECTED_SESSION_PRESENT",
                readiness="NOT_READY",
                rejection_reason=(
                    "provider_change_conflict"
                    if conflict
                    else (
                        "contract_or_maturity_mismatch"
                        if other_day_contracts
                        else "matching_preceding_day_contract_unavailable"
                    )
                ),
                provider_change_crosscheck_status=(
                    "FAILED" if conflict else "NOT_OBSERVED"
                ),
                **common,
            )
        )
    return statuses


def _attach_fetch_telemetry(
    result: KrxNightFuturesProbeResult,
    *,
    payloads: dict[date, object],
    expected_session: date | None,
    observation_time: datetime | None = None,
) -> KrxNightFuturesProbeResult:
    observed = observation_time or result.fetched_at
    observed_kst = (
        observed.replace(tzinfo=KST)
        if observed.tzinfo is None
        else observed.astimezone(KST)
    )
    finality_valid = observed_kst.timetz().replace(tzinfo=None) >= time(6, 0)
    result.expected_latest_session_date = expected_session
    result.expected_reference_date = expected_session
    result.provider_raw_bas_dd = result.source_date
    result.finality_valid = finality_valid
    result.product_statuses = _product_statuses(
        payloads,
        expected_session,
        result,
        finality_valid=finality_valid,
    )
    for item in result.observations:
        relation = classify_provider_reference_date(
            item.session_date,
            expected_session,
        )
        item.expected_reference_date = expected_session
        item.provider_raw_bas_dd = item.session_date
        item.reference_date_match = relation == "DATE_MATCH"
        item.reference_date_relation = relation
        item.finality_valid = finality_valid
    result.reference_date_match_count = sum(
        item.reference_date_match and item.finality_valid
        for item in result.observations
    )
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
    observation_time: datetime | None = None,
    api_key: str | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
    max_lookback_days: int = 7,
) -> KrxNightFuturesProbeResult:
    run_date = run_date or date.today()
    api_key = api_key if api_key is not None else get_settings().krx_open_api_key
    observed = observation_time or datetime.now(timezone.utc)
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=KST)
    fetched_at = observed.astimezone(timezone.utc)
    if not api_key:
        return _attach_fetch_telemetry(
            KrxNightFuturesProbeResult(
            status="not_configured",
            fetched_at=fetched_at,
            reason="KRX_OPEN_API_KEY is not configured",
            ),
            payloads={},
            expected_session=expected_latest_completed_krx_session(run_date),
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
                response = getattr(exc, "response", None)
                date_statuses.append(
                    KrxProbeDateStatus(
                        query_date=target_date,
                        http_status=(
                            response.status_code if response is not None else None
                        ),
                        result="fetch_error",
                    )
                )
                skipped_warnings.append(
                    f"{target_date}: fetch failed ({type(exc).__name__})"
                )
                continue
            successful_response_count += 1
            payloads[target_date] = payload
            payload_shas[target_date] = hashlib.sha256(response.content).hexdigest()
            raw_rows = _rows(payload)
            row_count = len(raw_rows)
            parsed_rows = [
                row for item in raw_rows if (row := _parse_row(item)) is not None
            ]
            date_statuses.append(
                KrxProbeDateStatus(
                    query_date=target_date,
                    row_count=row_count,
                    http_status=response.status_code,
                    returned_business_dates=sorted(
                        {row.business_date for row in parsed_rows}
                    ),
                    returned_night_business_dates=sorted(
                        {
                            row.business_date
                            for row in parsed_rows
                            if row.session == "night"
                        }
                    ),
                    raw_payload_sha256=payload_shas[target_date],
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
                source_pending_warning = (
                    f"{result.source_date}: rows present but no verified "
                    "NIGHT/preceding-DAY pair"
                )
                skipped_warnings = [
                    item for item in skipped_warnings if item != source_pending_warning
                ]
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
                elif not (
                    fetched_at.astimezone(KST).timetz().replace(tzinfo=None)
                    >= time(6, 0)
                ):
                    result.session_freshness = "unfinalized"
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
                return _attach_fetch_telemetry(
                    result,
                    payloads=payloads,
                    expected_session=calendar_expected_date,
                )
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
        return _attach_fetch_telemetry(
            aggregate,
            payloads=payloads,
            expected_session=calendar_expected_date,
        )
    if successful_response_count == 0 and last_fetch_error is not None:
        return _attach_fetch_telemetry(
            KrxNightFuturesProbeResult(
                status="unavailable",
                fetched_at=fetched_at,
                queried_dates=queried_dates,
                date_statuses=date_statuses,
                reason=last_fetch_error,
                warnings=skipped_warnings,
            ),
            payloads=payloads,
            expected_session=calendar_expected_date,
        )
    return _attach_fetch_telemetry(
        KrxNightFuturesProbeResult(
            status="unavailable",
            fetched_at=fetched_at,
            queried_dates=queried_dates,
            date_statuses=date_statuses,
            reason="no_recent_business_date_data",
            warnings=skipped_warnings,
        ),
        payloads=payloads,
        expected_session=calendar_expected_date,
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

Only a NIGHT row and the preceding eligible XKRX DAY row with explicit session metadata,
the same contract code, and an interpretable maturity were paired. Weekends and exchange
holidays are traversed by the exchange calendar. A DAY row with the same `BAS_DD` occurs
after that NIGHT session and is never used as its reference. Spot-index comparisons,
cross-expiry comparisons, row-order inference, and volume-based front-month inference
were not used.

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
