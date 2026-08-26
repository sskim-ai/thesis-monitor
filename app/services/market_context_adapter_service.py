from __future__ import annotations

import math
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.services.market_cross_section_service import MarketCrossSection
from app.services.market_session import korea_market_session, us_market_session


MARKET_CONTEXT_ADAPTER_VERSION = "market-context-adapter-v1"
MarketCode = Literal["KR", "US"]
Availability = Literal["AVAILABLE", "PARTIAL", "UNKNOWN"]


class AdapterIndex(BaseModel):
    symbol: str
    name: str
    close: float | None = None
    return_pct: float | None = None
    basis: str
    as_of_date: date
    source_ref: str


class AdapterBreadth(BaseModel):
    availability: Availability
    advancers: int | None = None
    decliners: int | None = None
    unchanged: int | None = None
    eligible_count: int | None = None
    breadth_ratio: float | None = None
    source_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_counts(self) -> "AdapterBreadth":
        counts = (self.advancers, self.decliners, self.unchanged)
        if any(value is None for value in counts):
            if self.availability == "AVAILABLE":
                raise ValueError("available breadth requires all counts")
            return self
        total = sum(int(value) for value in counts if value is not None)
        if self.eligible_count != total:
            raise ValueError("breadth counts do not reconcile")
        return self


class AdapterScopedBreadth(BaseModel):
    scope: str
    breadth: AdapterBreadth


class AdapterSector(BaseModel):
    name: str
    level: float | None = None
    return_pct: float | None = None
    state: Literal[
        "CURRENT_DIRECTIONAL",
        "CURRENT_LEVEL_ONLY",
        "PUBLICATION_PENDING",
        "SOURCE_UNAVAILABLE",
    ]
    basis: Literal["actual_sector_breadth", "sector_price_proxy"]
    source_ref: str


class AdapterSizeContext(BaseModel):
    name: str
    level: float | None = None
    return_pct: float | None = None
    state: Literal[
        "CURRENT_DIRECTIONAL",
        "CURRENT_LEVEL_ONLY",
        "PUBLICATION_PENDING",
        "SOURCE_UNAVAILABLE",
    ]
    basis: str
    as_of_date: date
    source_ref: str


class AdapterMarketFlow(BaseModel):
    participant: Literal["foreign", "institution", "retail"]
    net_flow: float
    unit: str
    scope: str
    as_of_date: date
    source_ref: str


class DeterministicMarketRelation(BaseModel):
    metric: str
    formula: str
    input_refs: list[str]
    result: float
    unit: str
    scope: str
    as_of_date: date
    limitations: list[str] = Field(default_factory=list)


class AdapterSessionContext(BaseModel):
    role: Literal["pre_market", "regular", "after_hours", "closed"]
    assessment_state: Literal["provisional", "final"]
    market_date: date
    latest_completed_regular_session_date: date
    timezone: str
    market_calendar_ref: str = "existing_market_session_service"
    provider_publication_state: Literal[
        "PROVIDER_COMPLETE",
        "MARKET_COMPLETED_PROVIDER_PENDING",
        "PROVIDER_PARTIAL",
        "UNAVAILABLE",
        "UNKNOWN",
    ] = "UNKNOWN"


class NormalizedMarketContext(BaseModel):
    contract_version: Literal["market-context-adapter-v1"] = (
        MARKET_CONTEXT_ADAPTER_VERSION
    )
    market: MarketCode
    assessment_date: date
    session_date: date
    as_of: datetime
    cutoff: datetime
    indices: list[AdapterIndex] = Field(default_factory=list)
    breadth: AdapterBreadth
    breadth_by_scope: list[AdapterScopedBreadth] = Field(default_factory=list)
    size_context: list[AdapterSizeContext] = Field(default_factory=list)
    sectors: list[AdapterSector] = Field(default_factory=list)
    market_flows: list[AdapterMarketFlow] = Field(default_factory=list)
    concentration: list[DeterministicMarketRelation] = Field(default_factory=list)
    deterministic_relations: list[DeterministicMarketRelation] = Field(
        default_factory=list
    )
    session_context: AdapterSessionContext
    official_event_sources: list[str]
    data_gaps: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_context(self) -> "NormalizedMarketContext":
        if self.as_of.tzinfo is None or self.cutoff.tzinfo is None:
            raise ValueError("adapter timestamps must be timezone-aware")
        if self.as_of > self.cutoff:
            raise ValueError("market context cannot be after the cutoff")
        return self


def _facts(
    fact_catalog: list[dict[str, object]],
    *fact_types: str,
) -> list[dict[str, object]]:
    return [
        item
        for item in fact_catalog
        if isinstance(item, dict) and str(item.get("fact_type") or "") in fact_types
    ]


def _fields(fact: dict[str, object]) -> dict[str, object]:
    value = fact.get("fields")
    return value if isinstance(value, dict) else {}


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = float(value)
        return result if math.isfinite(result) else None
    return None


def _fact_date(fact: dict[str, object]) -> date | None:
    try:
        return date.fromisoformat(str(fact.get("as_of_date") or "")[:10])
    except ValueError:
        return None


def _structured_state(fields: dict[str, object]) -> str:
    state = str(fields.get("structured_state") or "")
    if state in {
        "CURRENT_DIRECTIONAL",
        "CURRENT_LEVEL_ONLY",
        "PUBLICATION_PENDING",
        "SOURCE_UNAVAILABLE",
    }:
        return state
    if _number(fields.get("return_pct")) is not None:
        return "CURRENT_DIRECTIONAL"
    if _number(fields.get("level")) is not None:
        return "CURRENT_LEVEL_ONLY"
    return "SOURCE_UNAVAILABLE"


def _point_in_time_facts(
    fact_catalog: list[dict[str, object]],
    assessment_date: date,
) -> tuple[list[dict[str, object]], list[str]]:
    eligible: list[dict[str, object]] = []
    gaps: list[str] = []
    for fact in fact_catalog:
        fact_id = str(fact.get("fact_id") or "")
        if not fact_id:
            gaps.append("fact_id_missing")
            continue
        as_of_date = _fact_date(fact)
        if as_of_date is None:
            gaps.append(f"fact_date_missing:{fact_id}")
            continue
        if as_of_date > assessment_date:
            gaps.append(f"future_fact_suppressed:{fact_id}")
            continue
        eligible.append(fact)
    return eligible, gaps


def _session_context(
    market: MarketCode,
    as_of: datetime,
    publication_state: str,
) -> AdapterSessionContext:
    state = korea_market_session(as_of) if market == "KR" else us_market_session(as_of)
    role = "regular" if state.session == "open" else state.session
    return AdapterSessionContext(
        role=role,
        assessment_state=state.assessment_state,
        market_date=state.market_date,
        latest_completed_regular_session_date=(
            state.latest_completed_regular_session_date
        ),
        timezone=state.timezone_name,
        provider_publication_state=publication_state,
    )


class MarketContextAdapter:
    market: MarketCode
    official_event_sources: tuple[str, ...]
    local_index_symbols: frozenset[str]

    def normalize(
        self,
        *,
        assessment_date: date,
        as_of: datetime,
        cutoff: datetime,
        fact_catalog: list[dict[str, object]],
        coverage: dict[str, object] | None = None,
        cross_section: MarketCrossSection | None = None,
        provider_publication_state: str = "UNKNOWN",
    ) -> NormalizedMarketContext:
        if as_of.tzinfo is None or cutoff.tzinfo is None:
            raise ValueError("adapter timestamps must be timezone-aware")
        if cross_section is not None and cross_section.market != self.market:
            raise ValueError("cross-section market mismatch")
        if cross_section is not None and (
            cross_section.as_of > cutoff
            or cross_section.session_date > assessment_date
        ):
            raise ValueError("cross-section is after the adapter cutoff")
        eligible_facts, temporal_gaps = _point_in_time_facts(
            fact_catalog,
            assessment_date,
        )
        indices = self.get_index_context(
            eligible_facts,
            cross_section=cross_section,
        )
        session_date = max(
            (item.as_of_date for item in indices),
            default=(
                cross_section.session_date
                if cross_section is not None
                else assessment_date
            ),
        )
        breadth, breadth_relations = self.get_breadth_context(
            eligible_facts,
            cross_section=cross_section,
        )
        breadth_by_scope = self.get_scoped_breadth_context(
            cross_section=cross_section,
        )
        sectors = self.get_sector_context(eligible_facts, cross_section=cross_section)
        size_context = self.get_size_context(
            eligible_facts,
            cross_section=cross_section,
        )
        market_flows = self.get_market_flow_context(
            eligible_facts,
            cross_section=cross_section,
        )
        concentration = self.get_concentration_context(cross_section=cross_section)
        relations = [
            *breadth_relations,
            *self.get_deterministic_relations(
                eligible_facts,
            ),
        ]
        gaps = list(temporal_gaps)
        if not indices:
            gaps.append("local_indices_unavailable")
        if breadth.availability == "UNKNOWN":
            gaps.append("breadth_unavailable")
        if not sectors:
            gaps.append("sector_context_unavailable")
        if not size_context:
            gaps.append("size_context_unavailable")
        if not market_flows:
            gaps.append(
                "us_participant_flow_not_supported"
                if self.market == "US"
                else "market_flow_unavailable"
            )
        if isinstance(coverage, dict):
            for name, value in coverage.items():
                if not isinstance(value, dict):
                    continue
                status = str(value.get("status") or "")
                if status == "unavailable":
                    gaps.append(
                        f"coverage:{name}:{value.get('reason') or 'unavailable'}"
                    )
        return NormalizedMarketContext(
            market=self.market,
            assessment_date=assessment_date,
            session_date=session_date,
            as_of=as_of,
            cutoff=cutoff,
            indices=indices,
            breadth=breadth,
            breadth_by_scope=breadth_by_scope,
            size_context=size_context,
            sectors=sectors,
            market_flows=market_flows,
            concentration=concentration,
            deterministic_relations=relations,
            session_context=_session_context(
                self.market,
                as_of,
                provider_publication_state,
            ),
            official_event_sources=list(self.official_event_sources),
            data_gaps=sorted(set(gaps)),
        )

    def get_scoped_breadth_context(
        self,
        *,
        cross_section: MarketCrossSection | None,
    ) -> list[AdapterScopedBreadth]:
        if cross_section is None:
            return []
        values: list[AdapterScopedBreadth] = []
        for item in cross_section.breadth_by_scope:
            breadth = item.breadth
            ratio = (
                breadth.advance_count
                / (breadth.advance_count + breadth.decline_count)
                if breadth.advance_count + breadth.decline_count
                else None
            )
            values.append(
                AdapterScopedBreadth(
                    scope=item.scope,
                    breadth=AdapterBreadth(
                        availability="AVAILABLE",
                        advancers=breadth.advance_count,
                        decliners=breadth.decline_count,
                        unchanged=breadth.unchanged_count,
                        eligible_count=breadth.eligible_count,
                        breadth_ratio=ratio,
                        source_refs=[
                            f"cross-section:{cross_section.quality.provider}:breadth:{item.scope}"
                        ],
                    ),
                )
            )
        return values

    def get_size_context(
        self,
        fact_catalog: list[dict[str, object]],
        *,
        cross_section: MarketCrossSection | None = None,
    ) -> list[AdapterSizeContext]:
        values: list[AdapterSizeContext] = []
        if self.market == "KR" and cross_section is not None:
            values.extend(
                AdapterSizeContext(
                    name=item.sector,
                    level=None,
                    return_pct=item.return_pct,
                    state="CURRENT_DIRECTIONAL",
                    basis="official_size_index",
                    as_of_date=cross_section.session_date,
                    source_ref=(
                        item.source_ref
                        or f"cross-section:size:{item.market_scope}:{item.sector_code}"
                    ),
                )
                for item in cross_section.sectors
                if item.market_scope == "KOSPI"
                and item.sector_code in {"002", "003", "004"}
            )
            return values
        if self.market != "US":
            return values
        for fact in _facts(fact_catalog, "market_style"):
            fields = _fields(fact)
            symbol = str(fields.get("series_code") or "")
            if symbol not in {"IWM", "RSP"}:
                continue
            values.append(
                AdapterSizeContext(
                    name=str(fields.get("label") or symbol),
                    level=_number(fields.get("level")),
                    return_pct=_number(fields.get("return_pct")),
                    state=_structured_state(fields),
                    basis=(
                        "equal_weight_price_proxy"
                        if symbol == "RSP"
                        else "small_cap_price_proxy"
                    ),
                    as_of_date=_fact_date(fact),
                    source_ref=str(fact.get("fact_id") or ""),
                )
            )
        return values

    def get_index_context(
        self,
        fact_catalog: list[dict[str, object]],
        *,
        cross_section: MarketCrossSection | None,
    ) -> list[AdapterIndex]:
        values: list[AdapterIndex] = []
        if cross_section is not None:
            values.extend(
                AdapterIndex(
                    symbol=item.symbol,
                    name=item.label,
                    close=item.close,
                    return_pct=item.return_pct,
                    basis="official_or_provider_index",
                    as_of_date=cross_section.session_date,
                    source_ref=item.source_ref or f"cross-section:{item.symbol}",
                )
                for item in cross_section.indices
            )
        for fact in _facts(
            fact_catalog,
            "market_index",
            "market_cross_section_index",
        ):
            fields = _fields(fact)
            symbol = str(fields.get("series_code") or fields.get("symbol") or "")
            if not symbol or symbol not in self.local_index_symbols:
                continue
            values.append(
                AdapterIndex(
                    symbol=symbol,
                    name=str(fields.get("label") or symbol),
                    close=_number(fields.get("close")),
                    return_pct=_number(fields.get("return_pct")),
                    basis=(
                        "local_market_proxy"
                        if fact.get("fact_type") == "market_index"
                        else "official_or_provider_index"
                    ),
                    as_of_date=_fact_date(fact),
                    source_ref=str(fact.get("fact_id") or ""),
                )
            )
        unique: dict[str, AdapterIndex] = {}
        for item in values:
            unique.setdefault(item.symbol, item)
        return list(unique.values())

    def get_breadth_context(
        self,
        fact_catalog: list[dict[str, object]],
        *,
        cross_section: MarketCrossSection | None,
    ) -> tuple[AdapterBreadth, list[DeterministicMarketRelation]]:
        if cross_section is not None and cross_section.breadth is not None:
            breadth = cross_section.breadth
            ref = f"cross-section:{cross_section.quality.provider}:breadth"
            ratio = (
                breadth.advance_count
                / (breadth.advance_count + breadth.decline_count)
                if breadth.advance_count + breadth.decline_count
                else None
            )
            relations = []
            if ratio is not None:
                relations.append(
                    DeterministicMarketRelation(
                        metric="advance_decline_participation_ratio",
                        formula="advancers / (advancers + decliners)",
                        input_refs=[ref],
                        result=ratio,
                        unit="ratio",
                        scope=self.market,
                        as_of_date=cross_section.session_date,
                    )
                )
            if self.market == "US":
                denominator = breadth.eligible_count
                relation_scope = next(
                    (
                        item.scope
                        for item in cross_section.breadth_by_scope
                        if item.breadth == breadth
                    ),
                    "US_BROAD",
                )
                relations.extend(
                    [
                        DeterministicMarketRelation(
                            metric="net_advances",
                            formula="advancers - decliners",
                            input_refs=[ref],
                            result=float(
                                breadth.advance_count - breadth.decline_count
                            ),
                            unit="issues",
                            scope=relation_scope,
                            as_of_date=cross_section.session_date,
                        ),
                        DeterministicMarketRelation(
                            metric="advance_share",
                            formula=(
                                "advancers / (advancers + decliners + unchanged)"
                            ),
                            input_refs=[ref],
                            result=breadth.advance_count / denominator,
                            unit="ratio",
                            scope=relation_scope,
                            as_of_date=cross_section.session_date,
                        ),
                        DeterministicMarketRelation(
                            metric="decline_share",
                            formula=(
                                "decliners / (advancers + decliners + unchanged)"
                            ),
                            input_refs=[ref],
                            result=breadth.decline_count / denominator,
                            unit="ratio",
                            scope=relation_scope,
                            as_of_date=cross_section.session_date,
                        ),
                    ]
                )
                if breadth.decline_count:
                    relations.append(
                        DeterministicMarketRelation(
                            metric="advance_decline_ratio",
                            formula="advancers / decliners",
                            input_refs=[ref],
                            result=breadth.advance_count / breadth.decline_count,
                            unit="ratio",
                            scope=relation_scope,
                            as_of_date=cross_section.session_date,
                        )
                    )
            return (
                AdapterBreadth(
                    availability="AVAILABLE",
                    advancers=breadth.advance_count,
                    decliners=breadth.decline_count,
                    unchanged=breadth.unchanged_count,
                    eligible_count=breadth.eligible_count,
                    breadth_ratio=ratio,
                    source_refs=[ref],
                ),
                relations,
            )
        counts = _facts(fact_catalog, "market_breadth_counts")
        if not counts:
            return AdapterBreadth(availability="UNKNOWN"), []
        fact = counts[-1]
        fields = _fields(fact)
        values = [fields.get(name) for name in ("advance_count", "decline_count", "unchanged_count")]
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in values):
            return AdapterBreadth(availability="PARTIAL"), []
        advance, decline, unchanged = (int(value) for value in values)
        total = advance + decline + unchanged
        ratio = advance / (advance + decline) if advance + decline else None
        ref = str(fact.get("fact_id") or "")
        relations = []
        if ratio is not None:
            relations.append(
                DeterministicMarketRelation(
                    metric="advance_decline_participation_ratio",
                    formula="advancers / (advancers + decliners)",
                    input_refs=[ref],
                    result=ratio,
                    unit="ratio",
                    scope=self.market,
                    as_of_date=_fact_date(fact),
                )
            )
        return (
            AdapterBreadth(
                availability="AVAILABLE",
                advancers=advance,
                decliners=decline,
                unchanged=unchanged,
                eligible_count=total,
                breadth_ratio=ratio,
                source_refs=[ref],
            ),
            relations,
        )

    def get_sector_context(
        self,
        fact_catalog: list[dict[str, object]],
        *,
        cross_section: MarketCrossSection | None,
    ) -> list[AdapterSector]:
        values: list[AdapterSector] = []
        if cross_section is not None:
            values.extend(
                AdapterSector(
                    name=item.sector,
                    level=None,
                    return_pct=item.return_pct,
                    state="CURRENT_DIRECTIONAL",
                    basis=item.metric_role,
                    source_ref=(
                        item.source_ref
                        or f"cross-section:sector:{item.taxonomy}:{item.sector}"
                    ),
                )
                for item in cross_section.sectors
                if not (
                    item.market_scope == "KOSPI"
                    and item.sector_code in {"002", "003", "004"}
                )
            )
        if self.market == "US":
            for fact in _facts(fact_catalog, "market_sector"):
                fields = _fields(fact)
                values.append(
                    AdapterSector(
                        name=str(fields.get("label") or fields.get("series_code") or ""),
                        level=_number(fields.get("level")),
                        return_pct=_number(fields.get("return_pct")),
                        state=_structured_state(fields),
                        basis="sector_price_proxy",
                        source_ref=str(fact.get("fact_id") or ""),
                    )
                )
        return [
            item
            for item in values
            if item.name and item.state != "SOURCE_UNAVAILABLE"
        ]

    def get_market_flow_context(
        self,
        fact_catalog: list[dict[str, object]],
        *,
        cross_section: MarketCrossSection | None,
    ) -> list[AdapterMarketFlow]:
        raw = list(cross_section.market_flows) if cross_section is not None else []
        if self.market == "US" and (raw or _facts(fact_catalog, "market_flow")):
            raise ValueError("US participant flow semantics are unsupported")
        if any(item.currency != "KRW" for item in raw):
            raise ValueError("KR market flow requires KRW monetary units")
        values = [
            AdapterMarketFlow(
                participant=item.actor,
                net_flow=item.net_buy_amount,
                unit=item.currency,
                scope=item.market,
                as_of_date=cross_section.session_date,
                source_ref=(
                    item.source_ref
                    or f"cross-section:flow:{item.market}:{item.actor}"
                ),
            )
            for item in raw
        ]
        for fact in _facts(fact_catalog, "market_flow"):
            fields = _fields(fact)
            actor = str(fields.get("actor") or "")
            amount = _number(fields.get("net_buy_amount"))
            currency = str(fields.get("currency") or "")
            if actor not in {"foreign", "institution", "retail"} or amount is None:
                continue
            if currency != "KRW":
                raise ValueError("KR market flow requires KRW monetary units")
            values.append(
                AdapterMarketFlow(
                    participant=actor,
                    net_flow=amount,
                    unit=currency,
                    scope=str(fields.get("market_scope") or "KR_MARKET"),
                    as_of_date=_fact_date(fact),
                    source_ref=str(
                        fields.get("source_ref") or fact.get("fact_id") or ""
                    ),
                )
            )
        return list(
            {
                (item.participant, item.scope, item.source_ref): item
                for item in values
            }.values()
        )

    def get_deterministic_relations(
        self,
        fact_catalog: list[dict[str, object]],
    ) -> list[DeterministicMarketRelation]:
        if self.market != "US":
            return []
        relations: list[DeterministicMarketRelation] = []
        facts_by_id = {
            str(fact.get("fact_id")): fact
            for fact in fact_catalog
            if fact.get("fact_id")
        }
        for fact in _facts(
            fact_catalog,
            "market_growth_relative",
            "market_sector_relative",
            "market_style_relative",
        ):
            fields = _fields(fact)
            result = _number(fields.get("relative_return_pct"))
            refs = fields.get("source_fact_ids")
            if result is None or not isinstance(refs, list) or len(refs) != 2:
                continue
            inputs = [facts_by_id.get(str(value)) for value in refs]
            if any(value is None for value in inputs):
                continue
            input_dates = {
                value.get("as_of_date")
                for value in inputs
                if isinstance(value, dict)
            }
            input_returns = [
                _number(_fields(value).get("return_pct"))
                for value in inputs
                if isinstance(value, dict)
            ]
            if (
                len(input_dates) != 1
                or len(input_returns) != 2
                or any(value is None for value in input_returns)
            ):
                continue
            expected = float(input_returns[0]) - float(input_returns[1])
            if not math.isclose(result, expected, rel_tol=0, abs_tol=1e-9):
                continue
            relations.append(
                DeterministicMarketRelation(
                    metric="relative_return",
                    formula="subject_return_pct - benchmark_return_pct",
                    input_refs=[str(value) for value in refs],
                    result=result,
                    unit="pct_point",
                    scope="US",
                    as_of_date=_fact_date(fact),
                )
            )
        return relations

    def get_concentration_context(
        self,
        *,
        cross_section: MarketCrossSection | None,
    ) -> list[DeterministicMarketRelation]:
        if cross_section is None:
            return []
        value = cross_section.concentration
        flow_relations = value.get("relations")
        if isinstance(flow_relations, list):
            relations: list[DeterministicMarketRelation] = []
            for raw in flow_relations:
                if not isinstance(raw, dict):
                    continue
                result = _number(raw.get("ratio"))
                input_refs = raw.get("input_refs")
                if result is None or not isinstance(input_refs, list) or not input_refs:
                    continue
                relations.append(
                    DeterministicMarketRelation(
                        metric="market_flow_same_direction_top_n_concentration",
                        formula=str(raw.get("formula") or ""),
                        input_refs=[str(item) for item in input_refs],
                        result=result,
                        unit="ratio",
                        scope=f"{raw.get('market')}:{raw.get('actor')}",
                        as_of_date=cross_section.session_date,
                        limitations=[
                            "Concentration is descriptive and does not establish causality."
                        ],
                    )
                )
            return relations
        result = _number(value.get("concentration_gap_pct"))
        proxy = _number(value.get("proxy_return_pct"))
        equal_weight = _number(value.get("equal_weight_return_pct"))
        if result is None or proxy is None or equal_weight is None:
            return []
        expected = proxy - equal_weight
        if not math.isclose(result, expected, rel_tol=0, abs_tol=1e-9):
            raise ValueError("concentration relation arithmetic mismatch")
        return [
            DeterministicMarketRelation(
                metric=str(value.get("metric_role") or "concentration_gap"),
                formula="proxy_return_pct - equal_weight_return_pct",
                input_refs=[
                    f"cross-section:index:{value.get('proxy_symbol') or 'proxy'}",
                    "cross-section:breadth:equal_weight_return_pct",
                ],
                result=result,
                unit="pct_point",
                scope=self.market,
                as_of_date=cross_section.session_date,
                limitations=[str(item) for item in value.get("limitations", [])],
            )
        ]


class KrMarketContextAdapter(MarketContextAdapter):
    market: Literal["KR"] = "KR"
    official_event_sources = ("KRX", "OpenDART", "company_ir", "regulator")
    local_index_symbols = frozenset({"KOSPI", "KOSDAQ"})


class UsMarketContextAdapter(MarketContextAdapter):
    market: Literal["US"] = "US"
    official_event_sources = (
        "SEC",
        "company_ir",
        "Federal_Reserve",
        "US_Treasury",
        "BLS",
        "BEA",
        "exchange_or_regulator",
    )
    local_index_symbols = frozenset({"SPY", "QQQ", "IWM", "SOXX"})


def market_context_adapter(market: str) -> MarketContextAdapter:
    normalized = market.strip().upper()
    if normalized == "KR":
        return KrMarketContextAdapter()
    if normalized == "US":
        return UsMarketContextAdapter()
    raise ValueError(f"unsupported market: {market}")


def event_time_eligible(
    *,
    market: str,
    event_at: datetime,
    claimed_session_role: str,
) -> bool:
    if event_at.tzinfo is None:
        return False
    state = korea_market_session(event_at) if market.upper() == "KR" else us_market_session(event_at)
    actual = "regular" if state.session == "open" else state.session
    return actual == claimed_session_role
