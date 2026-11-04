"""Default-OFF scoped canonical planning, not production or source-use admission.

No StockPlan impersonation, collector, credential lookup or native dispatch. The
sealed static routing owner and current source authority are separate gates.
"""
from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from typing import Literal

import httpx
from pydantic import Field, model_validator

from app.macro.providers.market import MARKET_SYMBOLS
from app.services.canonical_source_plan import kiwoom_request
from app.services.kiwoom_kr_market_context_service import kiwoom_market_reads
from app.services.market_session import (
    korea_market_session, preceding_exchange_session_date, us_market_session,
)
from app.services.scoped_routing_identity import DetachedRoutingBinding, ScopedSubject, SealedRoutingCatalog
from app.services.sealed_chart_slots import chart_slots
from app.services.sealed_fresh_dispatch import FreshRequestDescriptor, RequestPlan, wire_identity
from app.services.sealed_response_binding import ResponseBinding, binding_owner_hash
from app.services.unified_snapshot_contract import ContractModel, digest, encoded
from app.services.unified_stock_acquisition import API_IDS, ROLES, stock_read_fields

ROOT = Path(__file__).resolve().parents[2]
SHA = r"^[a-f0-9]{64}$"
CONTRACT = "r22-scoped-source-plan-v1"
OWNER_FILES = (
    "app/services/scoped_source_plan.py", "app/services/scoped_routing_identity.py",
    "app/services/canonical_source_plan.py", "app/services/unified_stock_acquisition.py",
    "app/services/kiwoom_kr_market_context_service.py", "app/macro/providers/market.py",
    "app/services/sealed_source_transport.py", "app/services/sealed_chart_slots.py",
    "app/services/kiwoom_completed_close_owner.py",
    "app/services/completed_session_current_price.py",
    "app/services/market_session.py",
)


class HistoryCounts(ContractModel):
    adjusted_daily: int = Field(ge=2, le=1000)
    adjusted_weekly: int = Field(ge=2, le=1000)
    adjusted_monthly: int = Field(ge=2, le=1000)
    unadjusted_weekly_valuation: int = Field(ge=2, le=1000)


class ScopedCaptureSelection(ContractModel):
    """Explicit source-only subset; omitted roles never become complete coverage."""
    contract: Literal["scoped-capture-selection-v1"] = "scoped-capture-selection-v1"
    stock_markets: tuple[Literal["kr", "us"], ...] = ("kr", "us")
    stock_roles: tuple[Literal["adjusted_daily", "adjusted_weekly", "adjusted_monthly", "unadjusted_weekly_valuation"], ...] = tuple(ROLES)
    market_contexts: tuple[Literal["kr", "us"], ...] = ("kr", "us")
    us_completed_closes: bool = True

    @model_validator(mode="after")
    def unique_selection(self):
        for values in (self.stock_markets, self.stock_roles, self.market_contexts):
            if len(set(values)) != len(values):
                raise ValueError("scoped_duplicate_capture_selection")
        if not self.market_contexts and not (self.stock_markets and self.stock_roles):
            raise ValueError("scoped_empty_capture_selection")
        return self


class ScopedCaptureSelectionV2(ScopedCaptureSelection):
    """Narrow chart capture by registered security, never registration authority.

    Completed-close selection retains its separate existing contract. V1 bytes
    and defaults are unchanged; callers must explicitly select this version.
    """
    contract: Literal["scoped-capture-selection-v2"]
    stock_security_ids: tuple[str, ...] = Field(min_length=1, max_length=22)

    @model_validator(mode="after")
    def unique_security_selection(self):
        if (len(set(self.stock_security_ids)) != len(self.stock_security_ids)
                or any(not s.strip() or s != s.strip() for s in self.stock_security_ids)
                or not self.stock_roles or not self.stock_markets):
            raise ValueError("scoped_invalid_security_selection")
        return self


class ScopedPriceCaptureSelection(ContractModel):
    """Explicit price-only subset, with no chart or Market coverage claim."""
    contract: Literal["scoped-price-capture-selection-v1"]
    close_security_ids: tuple[str, ...] = Field(min_length=1, max_length=14)
    stock_markets: tuple[()] = ()
    stock_roles: tuple[()] = ()
    market_contexts: tuple[()] = ()
    us_completed_closes: Literal[True] = True

    @model_validator(mode="after")
    def unique_close_selection(self):
        if (len(set(self.close_security_ids)) != len(self.close_security_ids)
                or any(not s.strip() or s != s.strip() for s in self.close_security_ids)):
            raise ValueError("scoped_invalid_close_selection")
        return self


def selected_independent_closes(config):
    """Registered subjects only; legacy V1 still depends on its chart reads."""
    selection = config.capture_selection
    if isinstance(selection, ScopedPriceCaptureSelection):
        return tuple(s for s in config.subjects if s.security_id in selection.close_security_ids)
    if isinstance(selection, ScopedCaptureSelectionV2) and selection.us_completed_closes:
        return tuple(s for s in config.subjects if s.market == "us")
    return ()


class ScopedConfig(ContractModel):
    subjects: tuple[ScopedSubject, ...] = Field(min_length=1, max_length=22)
    kr_history: HistoryCounts
    us_history: HistoryCounts
    kr_max_pages: int = Field(ge=1, le=20)
    market_dependencies: Literal["KR10_AND_FULL_US_MARKET_SET"] = "KR10_AND_FULL_US_MARKET_SET"
    capture_selection: ScopedPriceCaptureSelection | ScopedCaptureSelectionV2 | ScopedCaptureSelection | None = None

    @model_validator(mode="after")
    def distinct(self):
        if len({s.ticker for s in self.subjects}) != len(self.subjects):
            raise ValueError("scoped_duplicate_subject")
        if len({s.security_id for s in self.subjects}) != len(self.subjects):
            raise ValueError("scoped_duplicate_security")
        if isinstance(self.capture_selection, ScopedCaptureSelectionV2):
            eligible = {s.security_id for s in self.subjects
                        if s.market in self.capture_selection.stock_markets}
            if not set(self.capture_selection.stock_security_ids) <= eligible:
                raise ValueError("scoped_selected_security_outside_registration_or_market")
        if isinstance(self.capture_selection, ScopedPriceCaptureSelection):
            eligible = {s.security_id for s in self.subjects if s.market == "us"}
            if not set(self.capture_selection.close_security_ids) <= eligible:
                raise ValueError("scoped_close_security_outside_us_registration")
        return self


class SessionPair(ContractModel):
    market: Literal["kr", "us"]
    calendar: Literal["XKRX", "XNYS"]
    target: date
    prior: date

    @model_validator(mode="after")
    def exact_pair(self):
        if self.calendar != {"kr": "XKRX", "us": "XNYS"}[self.market]:
            raise ValueError("scoped_calendar_market_mismatch")
        if self.prior != preceding_exchange_session_date(self.calendar, self.target):
            raise ValueError("scoped_nonadjacent_session_pair")
        return self


class ScopedStockRead(ContractModel):
    """Same per-read wire semantics, independent from historical cohort membership."""
    entry_id: str
    market: Literal["us", "kr"]
    subject: str
    canonical_security_id: str
    provider: Literal["kiwoom"] = "kiwoom"
    owner: Literal["ohlcv_analyst.KiwoomProvider.get_bars"] = "ohlcv_analyst.KiwoomProvider.get_bars"
    exchange: str
    route: str
    api_id: str
    role: str
    timeframe: Literal["daily", "weekly", "monthly"]
    adjusted: bool
    count: int = Field(ge=2, le=1000)
    max_pages: int = Field(ge=1, le=12)
    query_date: str
    latest_completed_session: str
    market_state: str
    query_semantics: Literal["LATEST_AVAILABLE_SOURCE_ROWS_NO_DATE_RELABEL"] = "LATEST_AVAILABLE_SOURCE_ROWS_NO_DATE_RELABEL"

    @model_validator(mode="after")
    def per_read_contract(self):
        if (self.entry_id != f"{self.market}:{self.subject}:{self.role}"
                or ROLES.get(self.role) != (self.timeframe, self.adjusted)
                or self.api_id != API_IDS[self.market][self.timeframe]
                or self.route != ("/api/us/chart" if self.market == "us" else "/api/dostk/chart")
                or self.exchange not in ({"ND", "NY", "NA"} if self.market == "us" else {"KRX", "KOSPI", "KOSDAQ"})
                or self.max_pages != (min(12, self.count // 100 + 2) if self.market == "us" else min(10, self.count // 200 + 2))):
            raise ValueError("scoped_stock_read_contract")
        return self


class PricePairRequirement(ContractModel):
    role: str
    instrument_kind: Literal["INDEX", "STOCK", "ETF_PROXY"]
    market: Literal["kr", "us"]
    symbol: str
    security_ref: str
    currency: Literal["KRW", "USD", "INDEX_POINTS"]
    target: date
    prior: date
    descriptor_id: str
    source_api: Literal["ka20009", "ka10081", "usa20590", "usa06012"]
    normalization_owner: str
    basis: Literal["INDEX_CLOSE", "ADJUSTED_STOCK_CHART", "REGULAR_STOCK_CLOSE", "ADJUSTED_ETF_RETURN"]
    usage: Literal["REQUIRED_CURRENT_AND_PRIOR_OWNER_PROOF"] = "REQUIRED_CURRENT_AND_PRIOR_OWNER_PROOF"
    available: Literal[False] = False
    source_use_grant: Literal["NOT_ISSUED"] = "NOT_ISSUED"


class R22ScopedSourcePlanV1(ContractModel):
    contract: Literal["r22-scoped-source-plan-v1"] = CONTRACT
    purpose: Literal["OFFLINE_SCOPED_CANONICAL_PLANNING"] = "OFFLINE_SCOPED_CANONICAL_PLANNING"
    config: ScopedConfig
    identities: tuple[DetachedRoutingBinding, ...]
    sessions: tuple[SessionPair, ...]
    stock_reads: tuple[ScopedStockRead, ...]
    kr_market_reads_json: str
    us_market_symbols: tuple[str, ...]
    request_plan: RequestPlan
    price_pairs: tuple[PricePairRequirement, ...]
    owner_files_json: str
    catalog_sha256: str = Field(pattern=SHA)
    config_sha256: str = Field(pattern=SHA)
    current_identity_authority: Literal[False] = False
    dispatch_allowed: Literal[False] = False
    production_universe_mutated: Literal[False] = False
    native_source_use: Literal["NOT_ADMITTED"] = "NOT_ADMITTED"

    @property
    def plan_sha256(self):
        return digest(self.model_dump(mode="json"))


def _sessions(at):
    if at.utcoffset() is None:
        raise ValueError("scoped_timezone_required")
    states = {"kr": korea_market_session(at), "us": us_market_session(at)}
    pairs = tuple(SessionPair(market=m, calendar=cal,
        target=states[m].latest_completed_regular_session_date,
        prior=preceding_exchange_session_date(cal, states[m].latest_completed_regular_session_date))
        for m, cal in (("kr", "XKRX"), ("us", "XNYS")))
    return states, pairs


def compile_scoped_source_plan(*, config: ScopedConfig, catalog: SealedRoutingCatalog,
                              generation_id: str, at: datetime, code_sha: str,
                              provider_config_sha256: str, enabled: bool = False):
    if enabled is not True:
        raise ValueError("scoped_source_feature_off")
    config = ScopedConfig.model_validate(config)
    bindings = tuple(catalog.bind(s, at=at) for s in config.subjects)
    identities = {b.subject.ticker: catalog.record(b, at=at) for b in bindings}
    wire = compile_scoped_wire_contract(config=config, identities=identities,
        generation_id=generation_id, at=at, code_sha=code_sha,
        provider_config_sha256=provider_config_sha256)
    return R22ScopedSourcePlanV1(config=config, identities=bindings, **wire,
        catalog_sha256=catalog.catalog_sha256,
        config_sha256=digest(config.model_dump(mode="json")))


def compile_scoped_wire_contract(*, config, identities, generation_id, at,
                                code_sha, provider_config_sha256, retries=2):
    """Pure original wire construction, never registration or dispatch authority.

    Current callers must independently authenticate every identity and obtain a
    live source-only parent. Legacy offline planning retains its false flags.
    """
    config = ScopedConfig.model_validate(config)
    if type(retries) is not int or not 0 <= retries <= 2:
        raise ValueError("scoped_retry_bound")
    if set(identities) != {s.ticker for s in config.subjects}:
        raise ValueError("scoped_wire_identity_coverage")
    states, pairs = _sessions(at)
    selection = config.capture_selection or ScopedCaptureSelection()
    sessions = {p.market: p for p in pairs}
    reads = []
    for s in config.subjects:
        if s.market not in selection.stock_markets:
            continue
        if (isinstance(selection, ScopedCaptureSelectionV2)
                and s.security_id not in selection.stock_security_ids):
            continue
        identity = identities[s.ticker]
        counts = getattr(config, s.market + "_history").model_dump()
        for role, count in counts.items():
            if role not in selection.stock_roles:
                continue
            reads.append(ScopedStockRead(**stock_read_fields(subject=s.ticker,
                identity=identity, market=s.market, role=role, count=count, at=at, state=states[s.market])))
    owners = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
              for name in OWNER_FILES}
    descriptors = []

    def add(key, market, subject, api, route, body, *, role=None, pages=1, mandatory=True, binding=None):
        owner = "app/services/sealed_source_transport.py"
        d = FreshRequestDescriptor(generation_id=generation_id, logical_request_id=key,
            provider="kiwoom", source_family=(role or key).split(":")[0], role_id=role or key,
            market=market, subject=subject, endpoint_operation=api,
            request_json=wire_identity(kiwoom_request(api, route, body), ("PLAN_CREDENTIAL",)),
            target_period=str(sessions[market].target) if market in sessions else at.date().isoformat(),
            mandatory=mandatory, group_id=key, page_ordinal=1, max_pages=pages,
            document_ordinal=1, max_documents=1, timeout_seconds=600, transient_retry_max=retries,
            raw_path=f"raw/{key}/source.body", normalizer=owner, consumer_role=role or key,
            owner_sha256=owners[owner], config_identity_sha256=provider_config_sha256,
            response_binding=binding)
        descriptors.extend(chart_slots(d, maximum_pages=pages) if pages > 1 else (d,))
        return key

    # Same credential-exchange descriptor as the inherited compiler; no credential read.
    auth_request = httpx.Request("POST", "https://api.kiwoom.com/oauth2/token",
        headers={"Content-Type": "application/json;charset=UTF-8"},
        json={"grant_type": "client_credentials", "appkey": "PLAN_CREDENTIAL", "secretkey": "PLAN_CREDENTIAL"})
    auth = FreshRequestDescriptor(generation_id=generation_id, logical_request_id="kiwoom:auth",
        provider="kiwoom", source_family="kiwoom", role_id="kiwoom:credential_exchange",
        market="global", subject="run", endpoint_operation="credential_exchange",
        request_json=wire_identity(auth_request, ("PLAN_CREDENTIAL",)), target_period=at.date().isoformat(),
        mandatory=True, group_id="kiwoom:auth", page_ordinal=1, max_pages=1, document_ordinal=1,
        max_documents=1, timeout_seconds=600, transient_retry_max=retries, raw_path="raw/kiwoom:auth/source.body",
        normalizer="app/services/sealed_source_transport.py", consumer_role="kiwoom:credential_exchange",
        owner_sha256=owners["app/services/sealed_source_transport.py"], config_identity_sha256=provider_config_sha256)
    descriptors.append(auth)
    for r in reads:
        body = dict(stk_cd=r.subject, upd_stkpc_tp=str(int(r.adjusted)))
        body.update(dict(stex_tp=r.exchange, strt_dt="", exrt_appl_tp="0") if r.market == "us"
                    else dict(base_dt=r.query_date))
        if r.market == "kr" and r.max_pages > config.kr_max_pages:
            raise ValueError("scoped_kr_page_budget_insufficient")
        add(r.entry_id + ":page1", r.market, r.subject, r.api_id, r.route, body,
            pages=r.max_pages, role="stock:" + r.entry_id)
        if r.market == "us" and r.role == "adjusted_daily" and selection.us_completed_closes:
            add("completed_close:" + r.subject, "us", r.subject, "usa20590", "/api/us/mrkcond",
                dict(stex_tp=r.exchange, stk_cd=r.subject, base_dt=r.latest_completed_session.replace("-", "")))

    close_subjects = selected_independent_closes(config)
    if close_subjects:
        existing_closes = {d.subject for d in descriptors if d.endpoint_operation == "usa20590"}
        for s in close_subjects:
            if s.ticker not in existing_closes:
                route = stock_read_fields(subject=s.ticker, identity=identities[s.ticker],
                    market="us", role="adjusted_daily", count=config.us_history.adjusted_daily,
                    at=at, state=states["us"])
                add("completed_close:" + s.ticker, "us", s.ticker, "usa20590", "/api/us/mrkcond",
                    dict(stex_tp=route["exchange"], stk_cd=s.ticker,
                         base_dt=sessions["us"].target.strftime("%Y%m%d")))

    discovery = tuple(add("us_market:discovery:" + exchange, "us", "*", "usa10099", "/api/us/stkinfo",
        {"stex_tp": exchange}, role="us_market:exchange_discovery") for exchange in (("ND", "NY", "NA") if "us" in selection.market_contexts else ()))
    for symbol in (MARKET_SYMBOLS if "us" in selection.market_contexts else ()):
        policy = dict(rule="native_exact_symbol_in_exchange_list", symbol=symbol,
            exchange_order=["ND", "NY", "NA"], row_keys=["list", "result_list", "output", "data"])
        binding = ResponseBinding(kind="KIWOOM_US_EXCHANGE", parents=discovery,
            policy_json=encoded(policy).decode(), policy_sha256=digest(policy))
        add("us_market:" + symbol, "us", symbol, "usa06012", "/api/us/chart",
            dict(stex_tp="ND", stk_cd=symbol, strt_dt="", upd_stkpc_tp="1", exrt_appl_tp="0"),
            pages=2, binding=binding)
    kr_reads = kiwoom_market_reads(session_date=sessions["kr"].target,
        max_pages=config.kr_max_pages, max_requests_per_page=1) if "kr" in selection.market_contexts else ()
    for r in kr_reads:
        add("kr_market:" + r.key, "kr", r.key.split(":")[0], r.api_id, r.endpoint,
            r.body, pages=r.max_pages, mandatory=r.mandatory)

    requirements = []
    def requirement(symbol, market, kind, security, descriptor, api, basis, owner):
        p = sessions[market]
        requirements.append(PricePairRequirement(role=f"{market}:{kind}:{symbol}", symbol=symbol,
            market=market, instrument_kind=kind, security_ref=security,
            currency="INDEX_POINTS" if kind=="INDEX" else "KRW" if market=="kr" else "USD",
            target=p.target, prior=p.prior, descriptor_id=descriptor, source_api=api,
            basis=basis, normalization_owner=owner))
    for r in kr_reads:
        if r.api_id == "ka20009":
            symbol = r.key.split(":")[0]
            requirement(symbol,"kr","INDEX","index:"+r.body["inds_cd"],"kr_market:"+r.key,
                "ka20009","INDEX_CLOSE","app.services.kiwoom_kr_market_context_service")
    for s in config.subjects:
        independent_close = s in close_subjects
        if not independent_close and not any(r.subject == s.ticker and r.role == "adjusted_daily" for r in reads):
            continue
        if s.market == "us" and not selection.us_completed_closes:
            continue
        requirement(s.ticker,s.market,"STOCK",s.security_id,
            "completed_close:"+s.ticker if s.market=="us" else f"kr:{s.ticker}:adjusted_daily:page1",
            "usa20590" if s.market=="us" else "ka10081",
            "REGULAR_STOCK_CLOSE" if s.market=="us" else "ADJUSTED_STOCK_CHART",
            "app.services.kiwoom_completed_close_owner" if s.market=="us" else "app.services.completed_session_current_price")
    for symbol in (("SPY","QQQ") if "us" in selection.market_contexts else ()):
        requirement(symbol,"us","ETF_PROXY","market-proxy:"+symbol,"us_market:"+symbol,
            "usa06012","ADJUSTED_ETF_RETURN","app.macro.providers.market.normalize_market_observation")
    request_plan = RequestPlan(generation_id=generation_id, code_sha=code_sha,
        policy_schema_sha256=digest(dict(contract=CONTRACT,schema=R22ScopedSourcePlanV1.model_json_schema())),
        frozen_at=at, descriptors=tuple(descriptors),
        mandatory_roles=tuple(dict.fromkeys(d.consumer_role for d in descriptors if d.mandatory)),
        binding_owner_sha256=binding_owner_hash())
    return dict(sessions=pairs,
        stock_reads=tuple(reads), kr_market_reads_json=encoded([r.model_dump(mode="json") for r in kr_reads]).decode(),
        us_market_symbols=tuple(MARKET_SYMBOLS) if "us" in selection.market_contexts else (), request_plan=request_plan, price_pairs=tuple(requirements),
        owner_files_json=encoded(owners).decode())


def validate_scoped_structure(plan, *, config, catalog, generation_id, at, code_sha,
                              provider_config_sha256, enabled=False):
    """Replay trusted compilation inputs; a self-rehashed caller plan grants nothing."""
    plan = R22ScopedSourcePlanV1.model_validate(plan)
    rebuilt = compile_scoped_source_plan(config=config,catalog=catalog,generation_id=generation_id,
        at=at,code_sha=code_sha,provider_config_sha256=provider_config_sha256,enabled=enabled)
    if plan != rebuilt:
        raise ValueError("scoped_canonical_replay_mismatch")
    return dict(contract=CONTRACT, structural_status="PASS", plan_sha256=plan.plan_sha256,
        static_binding="VERIFIED_SEALED_STATIC_BINDING", current_identity_authority="NOT_ADMITTED",
        live_dispatch_allowed=False, source_use="NOT_ADMITTED",
        owner_requirements=["CURRENT_SECURITY_AND_ETF_IDENTITY", "SIX_PAIR_SOURCE_OWNER_QUALIFICATION",
            "SCOPED_NATIVE_CAPTURE_ADAPTER", "RESOURCE_AND_PROVIDER_ADMISSION"],
        price_pairs_required=len(plan.price_pairs), price_pairs_available=0,
        descriptor_slots=len(plan.request_plan.descriptors),
        maximum_transport_attempts=sum(d.max_transport_attempts for d in plan.request_plan.descriptors),
        kr_logical_reads=len(json.loads(plan.kr_market_reads_json)),
        us_market_dependency_instruments=len(plan.us_market_symbols),
        optional_kr_flow_unavailable_does_not_qualify_or_deny_unrelated_roles=True)


def require_scoped_current_authority(plan):
    R22ScopedSourcePlanV1.model_validate(plan)
    raise ValueError("SCOPED_CURRENT_IDENTITY_AND_SOURCE_OWNER_NOT_ADMITTED")
