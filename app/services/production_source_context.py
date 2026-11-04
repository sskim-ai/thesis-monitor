"""Freeze current registered inputs and canonical request slots per attempt."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

from sqlmodel import select

from app.models.security import SecurityMaster
from app.services.fresh_source_run_contract import validate_local_seed, MAX_KR_REQUEST_PAGES
from app.services.market_session import korea_market_session
from app.services.onboarding_readiness_service import production_universe_snapshot
from app.services.ohlcv_client import PERIOD_COUNTS, PRICE_STRUCTURE_PERIOD_COUNTS, OHLCV_PROVIDER_REQUEST_LIMIT
from app.services.production_local_snapshot import readonly_local_snapshot
from app.services.production_runtime_preflight import kis_binding
from app.services.production_source_configuration import ProductionSourceConfiguration
from app.services.production_source_plan import build_request_plan
from app.services.provider_native_valuation_acquisition import routing_markets
from app.services.unified_class_c_owners import project_local_seed
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE, ROLES, make_reads
from app.services.unified_stock_event_input import make_read

ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = frozenset({"local", "local+openfigi", "canonical_local", "kiwoom", "kiwoom_rest",
    "ohlcv_analyst", "sec_edgar", "sec_companyfacts", "sec_foreign_filing", "sec_official_identity",
    "opendart", "fred", "eia", "ecos", "krx_night_futures", "google_news_rss", "naver_news", "finnhub"})
POLICY = UnifiedSourcePolicy(PROVIDERS)


def credential_binding(settings, market):
    result = dict(kiwoom=[settings.kiwoom_app_key, settings.kiwoom_secret_key],
        sec_edgar=[settings.sec_user_agent], opendart=[settings.opendart_api_key],
        fred=[settings.fred_api_key], eia=[settings.eia_api_key], ecos=[settings.ecos_api_key],
        krx_night_futures=[settings.krx_open_api_key], google_news_rss=["NO_CREDENTIAL_REQUIRED"],
        naver_news=[settings.naver_client_id, settings.naver_client_secret], finnhub=[settings.finnhub_api_key])
    if market == "kr":
        result = {k: v for k, v in result.items() if k in {"kiwoom", "opendart", "ecos", "krx_night_futures", "naver_news"}}
        kis_binding(settings, required=True)
        secret = settings.kis_app_secret or settings.kis_secret_app_key
        result["kis"] = [settings.kis_app_key.get_secret_value(), secret.get_secret_value()]
    else:
        result.pop("naver_news")
    if not all(all(isinstance(v, str) and v.strip() for v in values) for values in result.values()):
        raise ValueError("production_source_credential_missing")
    return result


def inspect_native(config, root):
    output = root / "native-owner.json"
    result = subprocess.run([config.native_python, "-B", str(ROOT / "scripts/unified_stock_source_worker.py"),
        "inspect", "--owner-root", config.native_owner_root, "--output", str(output)],
        cwd=config.native_owner_root, capture_output=True, timeout=60, check=False)
    if result.returncode != 0:
        raise ValueError("production_native_inspection_failed")
    value = json.loads(output.read_bytes())
    if (not value["owner_clean"] or not value["credentials_present"] or not value["live_provider"]
            or value["environment"] != "real" or value["base_url"] != "https://api.kiwoom.com"):
        raise ValueError("production_native_owner_not_qualified")
    return value


def freeze_current_context(*, request, directory, settings, configuration, implementation_sha,
                           native_inspector=inspect_native):
    configuration = ProductionSourceConfiguration.model_validate(configuration)
    market, run_id, attempt = (request[k] for k in ("market", "run_id", "attempt_id"))
    at = datetime.fromisoformat(request["started_at"])
    if at.utcoffset() is None or not attempt.startswith(run_id + "-attempt-"):
        raise ValueError("production_source_request_identity")
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    credentials = credential_binding(settings, market)
    static = configuration.seal_protocols(root, market)
    native = native_inspector(configuration, root)
    selected = {market: UNIVERSE[market]}
    enabled = settings.us_price_structure_v3_enabled if market == "us" else settings.kr_price_structure_v3_enabled
    configured = PRICE_STRUCTURE_PERIOD_COUNTS if enabled else PERIOD_COUNTS
    counts = {market: {role: PERIOD_COUNTS["weekly"] if not adjusted else
        max(min(configured[period], OHLCV_PROVIDER_REQUEST_LIMIT), 300 if period == "monthly" else 700)
        for role, (period, adjusted) in ROLES.items()}}
    with readonly_local_snapshot(configuration.database_path, temporary_parent=root) as (session, db_identity):
        universe = production_universe_snapshot(session, market, cutoff=at, session_key="daily_" + market).to_dict()
        if tuple(universe["eligible_subjects"]) != UNIVERSE[market]:
            raise ValueError("production_registered_active_universe_drift")
        all_records = [r.model_dump(mode="json") for r in session.exec(select(SecurityMaster)).all()]
        records = [r for r in all_records if r["ticker"] in selected[market]]
        identities = {r["ticker"]: r for r in records}
        if len(records) != len(identities) or set(identities) != set(selected[market]):
            raise ValueError("production_security_identity_coverage")
        auxiliary = [r for r in all_records if r["ticker"] == "000660"] if market == "us" else []
        if market == "us" and len(auxiliary) != 1:
            raise ValueError("production_auxiliary_issuer_identity")
        stock = StockPlan(run_id=attempt, acquisition_id=attempt + ":stock", frozen_at=at,
            contract="one-shot-us14-source-acquisition-v1" if market == "us" else "one-shot-kr8-source-acquisition-v1",
            instruction_sha=implementation_sha, implementation_sha=implementation_sha,
            universe_sha256=digest({market: universe}),
            reads=make_reads({market: universe}, identities, at=at, counts=counts, us_only=market == "us", kr_only=market == "kr"),
            **{k: native[k] for k in ("owner_head", "owner_files", "settings_sha256", "request_environment_sha256")})
        target = next(r.latest_completed_session for r in stock.reads)
        if target != request["target_session"]:
            raise ValueError("production_completed_session_drift")
        local = project_local_seed(session, market=market, session_key=target, cutoff=at, policy=POLICY)
        validate_local_seed(local)
        durable_json(root / ("class-c/local-" + market + ".json"), local, exclusive=True)
        from sqlalchemy import text
        official_identities = {}
        for ticker in identities:
            cached = session.exec(text("SELECT payload FROM providerresponsecache WHERE ticker=:ticker "
                "AND provider='official_security_identity' AND data_type='identity_evidence' AND status='success'")
                .bindparams(ticker=ticker)).all()
            if len(cached) == 1:
                official_identities[ticker] = json.loads(cached[0][0]).get("evidence_payload")
    official = json.loads((root / "static/official-security-identity.json").read_bytes())
    listing = json.loads((root / "static/kr-list-routing.json").read_bytes())["list"] if market == "kr" else []
    valuation_markets = routing_markets(identities, listing_rows=listing)
    hashes = {k: digest(v) for k, v in credentials.items()}
    news = [make_read(security=identities[t], market=market, run_id=attempt,
        lookback_days=settings.monitor_lookback_days, security_records=records) for t in selected[market]]
    compiler = dict(stock=stock, identities=identities, news_reads=news, config_identities=hashes,
        configured_kr_pages=settings.kiwoom_rest_max_pages, kr_post_acquisition_completeness_approved=True,
        exact_financial_owner=True, valuation_market_types=valuation_markets,
        auxiliary_security=auxiliary[0] if auxiliary else None,
        auxiliary_identity_sha256=digest(official) if auxiliary else None)
    kis_plan = None
    if market == "kr":
        from app.services.canonical_source_plan import compile_slots
        from scripts.kr8_kis_integration import build_plan
        candidate = compile_slots(**compiler)["candidate"]
        securities = {t: dict(r, corp_code=candidate["financial_plans"][t]["issuer"], currency="KRW")
                      for t, r in identities.items()}
        kis_plan = build_plan(generation=attempt, as_of=at.isoformat(), securities=securities,
            static_hashes={n: p.sha256 for n, p in configuration.kis_protocols.items()})
    result = build_request_plan(market=market, run_id=run_id, attempt_id=attempt,
        compiler_args=compiler, kis_plan=kis_plan)
    plan = result.pop("plan")
    from app.macro.providers.market import MARKET_SYMBOLS
    symbols = list(MARKET_SYMBOLS) if market == "us" else []
    market_reads = [dict(role="us_market:" + symbol, symbol=symbol, market="us", provider="ohlcv_analyst",
        response_provider="kiwoom", period="daily", adjusted=True, session_date=target, max_requests=1,
        params=dict(symbol=symbol, market="US", periods="daily", count=2, include_indicators="false",
                    indicator_limit=0, adjusted="true")) for symbol in symbols]
    frozen = dict(**result, generation_id=attempt, frozen_at=at.isoformat(), scope="US14_ONLY" if market == "us" else "KR8_ONLY",
        query_kst_date=at.astimezone(ZoneInfo("Asia/Seoul")).date().isoformat(), plan=plan.model_dump(mode="json"),
        stock_plan=stock.model_dump(mode="json"), security_records=records, native_owner=native,
        native_owner_root=configuration.native_owner_root, us_market_symbols=symbols, us_market_reads=market_reads,
        sessions={market: target}, kr_local_cap=min(settings.kiwoom_rest_max_pages, MAX_KR_REQUEST_PAGES),
        ohlcv_source_url=settings.ohlcv_base_url.rstrip("/") + "/ohlcv", config_identities=hashes,
        settings_sha256=digest(settings.model_dump(mode="json")), provider_native_valuation=True,
        valuation_official_identities=official_identities,
        valuation_routing_reference=dict(sha256=configuration.kr_listing_routing.sha256,
            role="ROUTING_REFERENCE_ONLY_CURRENT_IDENTITY_REQUIRES_FRESH_LIST", mutable_current_values_reused=False)
            if market == "kr" else None,
        completed_close_documentation=dict(path="static/completed-close-documentation.json",
            sha256=configuration.completed_close.sha256) if market == "us" else None,
        runtime_envelope_contract="production-source-configuration-v1", execution_purpose="PRODUCTION_MONITORING",
        configuration_sha256=configuration.identity, local_snapshot_identity=db_identity,
        protocol_inputs=static, protected_input_hashes={str(p.relative_to(root)): sha256_bytes(p.read_bytes())
            for p in root.rglob("*.json")})
    if market == "us":
        frozen["context_sessions"] = {"kr_fx": korea_market_session(at).latest_completed_regular_session_date.isoformat()}
    durable_json(root / "production-frozen-source-plan.json", frozen, exclusive=True)
    if kis_plan is not None:
        durable_json(root / "kis-plan.json", kis_plan, exclusive=True)
    return frozen, compiler, kis_plan, credentials
