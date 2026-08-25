from __future__ import annotations

import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from app.config import get_settings
from app.providers.kiwoom_rest_client import (
    KiwoomRestClient,
    KiwoomRestError,
    KiwoomRestResponse,
    payload_sha256,
)
from app.services.market_cross_section_service import (
    MarketBreadth,
    MarketCrossSection,
    MarketCrossSectionQuality,
    MarketFlowFact,
    MarketIndexFact,
    MarketScopedBreadth,
    MarketSectorFact,
)
from app.services.market_session import korea_market_session
from app.services.structured_market_context_service import (
    StructuredMarketContextEnvelope,
    load_structured_market_context,
    persist_structured_market_context,
)


CONTRACT_VERSION = "kiwoom-kr-market-context-v1"
RECONCILIATION_VERSION = "kr-market-flow-reconciliation-v1"
CONCENTRATION_VERSION = "kr-market-flow-concentration-v1"
KST = ZoneInfo("Asia/Seoul")

SECTOR_ENDPOINT = "/api/dostk/sect"
MARKET_CONDITION_ENDPOINT = "/api/dostk/mrkcond"
KA10051_AMOUNT_UNIT_KRW = 100_000_000
KA10066_AMOUNT_UNIT_KRW = 1_000_000

MARKETS = {
    "KOSPI": {"ka20001_market": "0", "ka10051_market": "0", "ka10066_market": "001", "code": "001"},
    "KOSDAQ": {"ka20001_market": "1", "ka10051_market": "1", "ka10066_market": "101", "code": "101"},
}
FLOW_FIELDS = {
    "foreign": ("frgnr_netprps", "frgnr_invsr"),
    "institution": ("orgn_netprps", "orgn"),
    "retail": ("ind_netprps", "ind_invsr"),
}


class KiwoomFlowReconciliation(BaseModel):
    market: Literal["KOSPI", "KOSDAQ"]
    actor: Literal["foreign", "institution", "retail"]
    aggregate_amount_krw: int
    paginated_amount_krw: int | None
    difference_krw: int | None
    classification: Literal[
        "EXACT",
        "WITHIN_AGGREGATE_RESOLUTION",
        "PAGINATION_INCOMPLETE",
        "DUPLICATE_IDENTITY",
        "UNRESOLVED_BASIS_OR_TAXONOMY",
    ]
    aggregate_ref: str
    paginated_ref: str | None = None


class KiwoomFlowConcentration(BaseModel):
    market: Literal["KOSPI", "KOSDAQ"]
    actor: Literal["foreign", "institution", "retail"]
    direction: Literal["net_buy", "net_sell"]
    top_n: int
    numerator_krw: int
    denominator_krw: int
    ratio: float
    unit: Literal["KRW"] = "KRW"
    formula: Literal[
        "top_n_same_direction_abs / all_same_direction_abs"
    ] = "top_n_same_direction_abs / all_same_direction_abs"
    input_refs: list[str]


class KiwoomCollectionAudit(BaseModel):
    contract_version: Literal["kiwoom-kr-market-context-v1"] = CONTRACT_VERSION
    session_date: date
    observed_at: datetime
    session_identity: dict[str, str]
    pagination: dict[str, dict[str, object]]
    unit_contract: dict[str, object]
    reconciliation: list[KiwoomFlowReconciliation]
    concentration: list[KiwoomFlowConcentration] = Field(default_factory=list)
    blocked_concentration_markets: dict[str, list[str]] = Field(default_factory=dict)
    provider_calls: dict[str, int]
    warnings: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class KiwoomMarketContextCollection:
    cross_section: MarketCrossSection
    audit: KiwoomCollectionAudit
    sanitized_archive: dict[str, object]


@dataclass(frozen=True)
class _PageSet:
    rows: list[dict[str, object]]
    pages: int
    complete: bool
    response_hashes: list[str]
    duplicate_identities: list[str]

    @property
    def combined_sha256(self) -> str:
        return payload_sha256(self.response_hashes)


def _signed_int(value: object) -> int:
    text = str(value or "").replace(",", "").strip()
    if not text:
        raise ValueError("required Kiwoom integer is missing")
    return int(text)


def _signed_float(value: object) -> float:
    text = str(value or "").replace(",", "").strip()
    if not text:
        raise ValueError("required Kiwoom number is missing")
    return float(text)


def _absolute_float(value: object) -> float:
    return abs(_signed_float(value))


def _normalized_security_code(value: object) -> str:
    code = str(value or "").strip()
    for suffix in ("_AL", "_NX"):
        if code.endswith(suffix):
            return code[: -len(suffix)]
    return code


def _breadth(payload: dict[str, object], *, listed_count: int | None) -> MarketBreadth:
    advance = _signed_int(payload.get("rising"))
    decline = _signed_int(payload.get("fall"))
    unchanged = _signed_int(payload.get("stdns"))
    eligible = advance + decline + unchanged
    directional = advance + decline
    return MarketBreadth(
        eligible_count=eligible,
        advance_count=advance,
        decline_count=decline,
        unchanged_count=unchanged,
        advance_ratio=advance / directional if directional else None,
        ad_ratio=advance / decline if decline else None,
        median_return_pct=None,
        equal_weight_return_pct=None,
        positive_return_pct=advance / eligible * 100 if eligible else None,
        negative_return_pct=decline / eligible * 100 if eligible else None,
        total_trading_volume=None,
        total_trading_value=None,
        listed_count=listed_count,
        limit_up_count=_signed_int(payload.get("upl")),
        limit_down_count=_signed_int(payload.get("lst")),
    )


def _merge_breadth(values: list[MarketBreadth]) -> MarketBreadth:
    advance = sum(item.advance_count for item in values)
    decline = sum(item.decline_count for item in values)
    unchanged = sum(item.unchanged_count for item in values)
    eligible = advance + decline + unchanged
    directional = advance + decline
    listed_values = [item.listed_count for item in values]
    return MarketBreadth(
        eligible_count=eligible,
        advance_count=advance,
        decline_count=decline,
        unchanged_count=unchanged,
        advance_ratio=advance / directional if directional else None,
        ad_ratio=advance / decline if decline else None,
        median_return_pct=None,
        equal_weight_return_pct=None,
        positive_return_pct=advance / eligible * 100 if eligible else None,
        negative_return_pct=decline / eligible * 100 if eligible else None,
        total_trading_volume=None,
        total_trading_value=None,
        listed_count=(
            sum(int(value) for value in listed_values if value is not None)
            if all(value is not None for value in listed_values)
            else None
        ),
        limit_up_count=sum(item.limit_up_count or 0 for item in values),
        limit_down_count=sum(item.limit_down_count or 0 for item in values),
    )


def _aggregate_row(
    payload: dict[str, object], *, market: str, code: str
) -> dict[str, object]:
    rows = payload.get("inds_netprps")
    if not isinstance(rows, list):
        raise ValueError(f"ka10051 rows are missing: {market}")
    code_matches = [
        row
        for row in rows
        if isinstance(row, dict)
        and str(row.get("inds_cd") or "").removesuffix("_AL") == code
    ]
    if len(code_matches) == 1:
        return code_matches[0]
    expected_names = {"KOSPI": "종합(KOSPI)", "KOSDAQ": "종합(KOSDAQ)"}
    matches = [
        row
        for row in rows
        if isinstance(row, dict)
        and str(row.get("inds_nm") or "").strip() == expected_names[market]
    ]
    if len(matches) != 1:
        raise ValueError(f"ka10051 aggregate identity is not unique: {market}")
    return matches[0]


def _classify_reconciliation(
    *,
    aggregate: int,
    paginated: int | None,
    complete: bool,
    duplicates: list[str],
) -> tuple[str, int | None]:
    if not complete:
        return "PAGINATION_INCOMPLETE", None
    if duplicates:
        return "DUPLICATE_IDENTITY", None
    if paginated is None:
        return "PAGINATION_INCOMPLETE", None
    difference = aggregate - paginated
    if difference == 0:
        return "EXACT", difference
    if abs(difference) < KA10051_AMOUNT_UNIT_KRW:
        return "WITHIN_AGGREGATE_RESOLUTION", difference
    return "UNRESOLVED_BASIS_OR_TAXONOMY", difference


def _flow_concentration(
    *,
    market: str,
    actor: str,
    aggregate_amount: int,
    rows: list[dict[str, object]],
    page_ref: str,
) -> KiwoomFlowConcentration | None:
    if aggregate_amount == 0:
        return None
    source_field = FLOW_FIELDS[actor][1]
    direction = 1 if aggregate_amount > 0 else -1
    aligned = sorted(
        (
            (
                abs(_signed_int(row.get(source_field)) * KA10066_AMOUNT_UNIT_KRW),
                _normalized_security_code(row.get("stk_cd")),
            )
            for row in rows
            if _signed_int(row.get(source_field)) * direction > 0
        ),
        reverse=True,
    )
    denominator = sum(amount for amount, _code in aligned)
    if denominator <= 0:
        return None
    top = aligned[:5]
    numerator = sum(amount for amount, _code in top)
    refs = [page_ref, *[f"kiwoom:ka10066:{market}:{code}:{actor}" for _amount, code in top]]
    return KiwoomFlowConcentration(
        market=market,
        actor=actor,
        direction="net_buy" if direction > 0 else "net_sell",
        top_n=len(top),
        numerator_krw=numerator,
        denominator_krw=denominator,
        ratio=numerator / denominator,
        input_refs=refs,
    )


class KiwoomKrMarketContextService:
    def __init__(
        self,
        client: KiwoomRestClient,
        *,
        max_pages: int | None = None,
    ) -> None:
        self.client = client
        self.max_pages = max_pages or get_settings().kiwoom_rest_max_pages
        self._archive_rows: list[dict[str, object]] = []

    async def _request(
        self,
        *,
        api_id: str,
        endpoint: str,
        body: dict[str, str],
        page: int = 1,
        continuation: bool = False,
        next_key: str = "",
    ) -> KiwoomRestResponse:
        response = await self.client.request(
            endpoint=endpoint,
            api_id=api_id,
            body=body,
            continuation=continuation,
            next_key=next_key,
        )
        self._archive_rows.append(
            {
                "api_id": api_id,
                "request": body,
                "page": page,
                "continuation": response.continuation,
                "payload_sha256": response.payload_sha256,
                "payload": response.payload,
            }
        )
        return response

    async def _ka10066_pages(self, *, market_code: str) -> _PageSet:
        rows: list[dict[str, object]] = []
        hashes: list[str] = []
        continuation = False
        next_key = ""
        for page in range(1, self.max_pages + 1):
            response = await self._request(
                api_id="ka10066",
                endpoint=MARKET_CONDITION_ENDPOINT,
                body={
                    "mrkt_tp": market_code,
                    "amt_qty_tp": "1",
                    "trde_tp": "0",
                    "stex_tp": "3",
                },
                page=page,
                continuation=continuation,
                next_key=next_key,
            )
            raw_rows = response.payload.get("opaf_invsr_trde")
            if not isinstance(raw_rows, list) or any(
                not isinstance(row, dict) for row in raw_rows
            ):
                raise ValueError("ka10066 response rows are invalid")
            rows.extend(row for row in raw_rows if isinstance(row, dict))
            hashes.append(response.payload_sha256)
            if not response.continuation:
                complete = True
                break
            continuation = True
            next_key = response.next_key
        else:
            complete = False
            page = self.max_pages
        identities = [_normalized_security_code(row.get("stk_cd")) for row in rows]
        identity_counts = Counter(identity for identity in identities if identity)
        duplicate_identities = sorted(
            identity for identity, count in identity_counts.items() if count > 1
        )
        return _PageSet(
            rows=rows,
            pages=page,
            complete=complete,
            response_hashes=hashes,
            duplicate_identities=duplicate_identities,
        )

    @staticmethod
    def _validate_session_identity(
        *,
        session_date: date,
        observed_at: datetime,
        current: dict[str, object],
        sectors: dict[str, object],
        history: dict[str, object],
        market: str,
        code: str,
    ) -> None:
        observed_kst = observed_at.astimezone(KST)
        session_state = korea_market_session(observed_kst)
        if session_state.latest_completed_regular_session_date != session_date:
            raise ValueError("current-only Kiwoom TR is outside the completed target session")
        history_rows = history.get("inds_cur_prc_daly_rept")
        matching_history = [
            row
            for row in history_rows or []
            if isinstance(row, dict)
            and str(row.get("dt_n") or "") == session_date.strftime("%Y%m%d")
        ]
        if len(matching_history) != 1:
            raise ValueError(f"Kiwoom historical session identity is missing: {market}")
        all_rows = sectors.get("all_inds_idex")
        composite = [
            row
            for row in all_rows or []
            if isinstance(row, dict) and str(row.get("stk_cd") or "") == code
        ]
        if len(composite) != 1:
            raise ValueError(f"Kiwoom composite index identity is not unique: {market}")
        current_close = _absolute_float(current.get("cur_prc"))
        current_return = _signed_float(current.get("flu_rt"))
        for source in (matching_history[0], composite[0]):
            close_key = "cur_prc_n" if "cur_prc_n" in source else "cur_prc"
            return_key = "flu_rt_n" if "flu_rt_n" in source else "flu_rt"
            if (
                _absolute_float(source.get(close_key)) != current_close
                or _signed_float(source.get(return_key)) != current_return
            ):
                raise ValueError(f"Kiwoom current/historical index mismatch: {market}")

    async def collect(
        self,
        *,
        session_date: date,
        observed_at: datetime,
    ) -> KiwoomMarketContextCollection:
        if observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        current_payloads: dict[str, dict[str, object]] = {}
        sector_payloads: dict[str, dict[str, object]] = {}
        aggregate_payloads: dict[str, dict[str, object]] = {}
        aggregate_rows: dict[str, dict[str, object]] = {}

        for market, spec in MARKETS.items():
            current = await self._request(
                api_id="ka20001",
                endpoint=SECTOR_ENDPOINT,
                body={
                    "mrkt_tp": spec["ka20001_market"],
                    "inds_cd": spec["code"],
                },
            )
            sectors = await self._request(
                api_id="ka20003",
                endpoint=SECTOR_ENDPOINT,
                body={"inds_cd": spec["code"]},
            )
            history = await self._request(
                api_id="ka20009",
                endpoint=SECTOR_ENDPOINT,
                body={
                    "mrkt_tp": spec["ka20001_market"],
                    "inds_cd": spec["code"],
                },
            )
            aggregate = await self._request(
                api_id="ka10051",
                endpoint=SECTOR_ENDPOINT,
                body={
                    "mrkt_tp": spec["ka10051_market"],
                    "amt_qty_tp": "0",
                    "base_dt": session_date.strftime("%Y%m%d"),
                    "stex_tp": "3",
                },
            )
            self._validate_session_identity(
                session_date=session_date,
                observed_at=observed_at,
                current=current.payload,
                sectors=sectors.payload,
                history=history.payload,
                market=market,
                code=spec["code"],
            )
            current_payloads[market] = current.payload
            sector_payloads[market] = sectors.payload
            aggregate_payloads[market] = aggregate.payload
            aggregate_rows[market] = _aggregate_row(
                aggregate.payload,
                market=market,
                code=spec["code"],
            )

        page_sets: dict[str, _PageSet] = {}
        page_errors: dict[str, str] = {}
        for market, spec in MARKETS.items():
            try:
                page_sets[market] = await self._ka10066_pages(
                    market_code=spec["ka10066_market"]
                )
            except (KiwoomRestError, TypeError, ValueError) as exc:
                page_errors[market] = type(exc).__name__

        scoped_breadth: list[MarketScopedBreadth] = []
        indices: list[MarketIndexFact] = []
        sectors: list[MarketSectorFact] = []
        market_flows: list[MarketFlowFact] = []
        reconciliation: list[KiwoomFlowReconciliation] = []
        concentration: list[KiwoomFlowConcentration] = []
        blocked_concentration: dict[str, list[str]] = {}

        for market, spec in MARKETS.items():
            sector_rows = sector_payloads[market].get("all_inds_idex")
            if not isinstance(sector_rows, list):
                raise ValueError(f"ka20003 rows are missing: {market}")
            composite = next(
                row
                for row in sector_rows
                if isinstance(row, dict) and str(row.get("stk_cd") or "") == spec["code"]
            )
            listed_count = _signed_int(composite.get("flo_stk_num"))
            breadth = _breadth(current_payloads[market], listed_count=listed_count)
            scoped_breadth.append(MarketScopedBreadth(scope=market, breadth=breadth))
            indices.append(
                MarketIndexFact(
                    symbol=market,
                    label=str(composite.get("stk_nm") or market),
                    close=_absolute_float(current_payloads[market].get("cur_prc")),
                    return_pct=_signed_float(current_payloads[market].get("flu_rt")),
                    source_ref=f"kiwoom:ka20001:{market}:{session_date.isoformat()}",
                )
            )
            for row in sector_rows:
                if not isinstance(row, dict) or str(row.get("stk_cd") or "") == spec["code"]:
                    continue
                advance = _signed_int(row.get("rising"))
                decline = _signed_int(row.get("fall"))
                unchanged = _signed_int(row.get("stdns"))
                sectors.append(
                    MarketSectorFact(
                        sector=str(row.get("stk_nm") or ""),
                        taxonomy="kiwoom-sector-index-v1",
                        metric_role="actual_sector_breadth",
                        return_pct=_signed_float(row.get("flu_rt")),
                        advance_ratio=(
                            advance / (advance + decline)
                            if advance + decline
                            else None
                        ),
                        sector_code=str(row.get("stk_cd") or ""),
                        market_scope=market,
                        listed_count=_signed_int(row.get("flo_stk_num")),
                        advance_count=advance,
                        decline_count=decline,
                        unchanged_count=unchanged,
                        limit_up_count=_signed_int(row.get("upl")),
                        limit_down_count=_signed_int(row.get("lst")),
                        source_ref=(
                            f"kiwoom:ka20003:{market}:{row.get('stk_cd')}:{session_date.isoformat()}"
                        ),
                    )
                )

            page_set = page_sets.get(market)
            for actor, (aggregate_field, stock_field) in FLOW_FIELDS.items():
                source_value = _signed_int(aggregate_rows[market].get(aggregate_field))
                aggregate_amount = source_value * KA10051_AMOUNT_UNIT_KRW
                market_flows.append(
                    MarketFlowFact(
                        actor=actor,
                        net_buy_amount=aggregate_amount,
                        currency="KRW",
                        market=market,
                        exchange_basis="KRX_NXT_INTEGRATED",
                        source_unit="100M_KRW",
                        source_unit_scale_krw=KA10051_AMOUNT_UNIT_KRW,
                        source_ref=f"kiwoom:ka10051:{market}:{actor}:{session_date.isoformat()}",
                    )
                )
                paginated_amount = (
                    sum(_signed_int(row.get(stock_field)) for row in page_set.rows)
                    * KA10066_AMOUNT_UNIT_KRW
                    if page_set is not None and page_set.complete
                    else None
                )
                classification, difference = _classify_reconciliation(
                    aggregate=aggregate_amount,
                    paginated=paginated_amount,
                    complete=bool(page_set and page_set.complete),
                    duplicates=page_set.duplicate_identities if page_set else [],
                )
                reconciliation.append(
                    KiwoomFlowReconciliation(
                        market=market,
                        actor=actor,
                        aggregate_amount_krw=aggregate_amount,
                        paginated_amount_krw=paginated_amount,
                        difference_krw=difference,
                        classification=classification,
                        aggregate_ref=f"kiwoom:ka10051:{market}:{actor}:{session_date.isoformat()}",
                        paginated_ref=(
                            f"kiwoom:ka10066:{market}:all-pages:{page_set.combined_sha256}"
                            if page_set
                            else None
                        ),
                    )
                )

            market_reconciliation = [
                item for item in reconciliation if item.market == market
            ]
            blocking = [
                item.classification
                for item in market_reconciliation
                if item.classification
                not in {"EXACT", "WITHIN_AGGREGATE_RESOLUTION"}
            ]
            if page_set is None:
                blocking.append(page_errors.get(market, "PAGINATION_UNAVAILABLE"))
            if blocking:
                blocked_concentration[market] = sorted(set(blocking))
            elif page_set is not None:
                for item in market_reconciliation:
                    relation = _flow_concentration(
                        market=market,
                        actor=item.actor,
                        aggregate_amount=item.aggregate_amount_krw,
                        rows=page_set.rows,
                        page_ref=str(item.paginated_ref),
                    )
                    if relation is not None:
                        concentration.append(relation)

        breadth_values = [item.breadth for item in scoped_breadth]
        overall_breadth = _merge_breadth(breadth_values)
        stats = asdict(self.client.stats)
        warnings = [
            f"concentration_blocked:{market}:{','.join(reasons)}"
            for market, reasons in sorted(blocked_concentration.items())
        ]
        audit = KiwoomCollectionAudit(
            session_date=session_date,
            observed_at=observed_at,
            session_identity={
                market: "ka20001_ka20003_matched_ka20009_target_date"
                for market in MARKETS
            },
            pagination={
                market: {
                    "pages": page_set.pages,
                    "rows": len(page_set.rows),
                    "complete": page_set.complete,
                    "duplicate_identities": page_set.duplicate_identities,
                    "combined_sha256": page_set.combined_sha256,
                }
                for market, page_set in page_sets.items()
            }
            | {
                market: {
                    "pages": 0,
                    "rows": 0,
                    "complete": False,
                    "error": error,
                }
                for market, error in page_errors.items()
            },
            unit_contract={
                "ka10051": {
                    "request_amount_mode": "0",
                    "source_unit": "100M_KRW",
                    "scale_krw": KA10051_AMOUNT_UNIT_KRW,
                },
                "ka10066": {
                    "request_amount_mode": "1",
                    "source_unit": "1M_KRW",
                    "scale_krw": KA10066_AMOUNT_UNIT_KRW,
                },
                "verification": "2026-08-25_cross_tr_empirical_reconciliation",
            },
            reconciliation=reconciliation,
            concentration=concentration,
            blocked_concentration_markets=blocked_concentration,
            provider_calls=stats,
            warnings=warnings,
        )
        source_sha = payload_sha256(
            [row["payload_sha256"] for row in self._archive_rows]
        )
        cross_section = MarketCrossSection(
            market="KR",
            session_date=session_date,
            as_of=observed_at,
            indices=indices,
            breadth=overall_breadth,
            breadth_by_scope=scoped_breadth,
            concentration={
                "contract_version": CONCENTRATION_VERSION,
                "relations": [item.model_dump(mode="json") for item in concentration],
                "blocked_markets": blocked_concentration,
            },
            sectors=sectors,
            market_flows=market_flows,
            quality=MarketCrossSectionQuality(
                provider="KIWOOM_REST",
                provider_role="official_primary_supplemental",
                coverage="full",
                freshness="fresh",
                universe_version="kiwoom-integrated-market-v1",
                raw_count=overall_breadth.listed_count or overall_breadth.eligible_count,
                eligible_count=overall_breadth.eligible_count,
                excluded_count=(
                    (overall_breadth.listed_count or overall_breadth.eligible_count)
                    - overall_breadth.eligible_count
                ),
                warnings=warnings,
                volume_semantics="unknown",
                trading_value_semantics="unknown",
            ),
            source_payload_sha256=source_sha,
        )
        archive = {
            "contract_version": CONTRACT_VERSION,
            "session_date": session_date.isoformat(),
            "observed_at": observed_at.isoformat(),
            "source_payload_sha256": source_sha,
            "responses": self._archive_rows,
            "audit": audit.model_dump(mode="json"),
        }
        return KiwoomMarketContextCollection(
            cross_section=cross_section,
            audit=audit,
            sanitized_archive=archive,
        )


def persist_kiwoom_market_archive(
    collection: KiwoomMarketContextCollection,
    *,
    directory: Path | None = None,
) -> Path:
    root = directory or (
        Path(get_settings().data_dir) / "market-context" / "kiwoom" / "raw"
    )
    source_sha = collection.cross_section.source_payload_sha256
    path = root / collection.cross_section.session_date.isoformat() / f"{source_sha}.json"
    encoded = json.dumps(
        collection.sanitized_archive,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(encoded, encoding="utf-8")
    os.replace(temporary, path)
    return path


async def collect_and_persist_kiwoom_market_context(
    *,
    session_date: date,
    observed_at: datetime,
) -> dict[str, object]:
    """Best-effort production acquisition; failure never blocks the KR packet."""
    settings = get_settings()
    if not settings.kiwoom_kr_market_context_enabled:
        return {"status": "NOT_ENABLED", "packet_continues": True}
    client = KiwoomRestClient()
    if not client.configured:
        return {
            "status": "NOT_CONFIGURED",
            "packet_continues": True,
            "reason": "kiwoom_credentials_missing",
        }
    try:
        previous = load_structured_market_context(
            "KR",
            session_date,
            cutoff=observed_at,
        )
    except (OSError, TypeError, ValueError):
        previous = None
    try:
        collection = await KiwoomKrMarketContextService(client).collect(
            session_date=session_date,
            observed_at=observed_at,
        )
        archive_path = persist_kiwoom_market_archive(collection)
        previous_state = previous.publication_state if previous is not None else "NOT_OBSERVED"
        envelope = StructuredMarketContextEnvelope(
            market="KR",
            session_date=session_date,
            retrieved_at=observed_at,
            provider="KIWOOM_REST",
            publication_state="AVAILABLE_CURRENT",
            source_refs=[
                f"kiwoom-archive:{archive_path.relative_to(Path(settings.data_dir))}",
                "kiwoom:ka20001",
                "kiwoom:ka20003",
                "kiwoom:ka10051",
                "kiwoom:ka10066",
            ],
            source_payload_sha256=collection.cross_section.source_payload_sha256,
            cross_section=collection.cross_section,
            data_gaps=[
                *collection.audit.warnings,
                f"krx_telemetry_independent_state:{previous_state}",
            ],
        )
        context_path = persist_structured_market_context(envelope)
    except (KiwoomRestError, OSError, RuntimeError, TypeError, ValueError) as exc:
        return {
            "status": "UNAVAILABLE",
            "packet_continues": True,
            "reason": type(exc).__name__,
            "provider_calls": asdict(client.stats),
        }
    return {
        "status": "AVAILABLE_CURRENT",
        "packet_continues": True,
        "provider": "KIWOOM_REST",
        "context_path": str(context_path),
        "archive_path": str(archive_path),
        "source_payload_sha256": collection.cross_section.source_payload_sha256,
        "provider_calls": collection.audit.provider_calls,
        "pagination": collection.audit.pagination,
        "concentration_relations": len(collection.audit.concentration),
        "warnings": collection.audit.warnings,
    }
