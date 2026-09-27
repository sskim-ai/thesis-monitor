"""Explicit REV8 source-only controller. Never registered as a production job."""

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
from zoneinfo import ZoneInfo

import httpx
from pydantic import TypeAdapter

from app.config import Settings
from app.macro.providers.base import MacroProviderResult
from app.macro.providers.market import MARKET_SYMBOLS, OhlcvMarketProvider
from app.macro.providers.krx import KrxNightFuturesProvider
from app.jobs.probe_krx_night_futures import KRX_FUTURES_DAILY_URL, expected_latest_completed_krx_session
from app.providers.kiwoom_rest_client import KiwoomRestClient
from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService, kiwoom_market_reads
from app.services.market_session import korea_market_session, us_market_session
from app.services.unified_kiwoom_observer import KiwoomReceiptObserver
from app.services.unified_live_source_transport import BoundedTransport, LiveAsyncTransport, SourceSafetyStop
from app.services.unified_run_acquisition import RunRead, RunAcquisitionObserver
from app.services.unified_run_artifacts import durable_json, durable_bytes, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_observer import OhlcvRead, OhlcvReceiptObserver
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE, ROLES, make_reads
from app.services.ohlcv_client import PERIOD_COUNTS, PRICE_STRUCTURE_PERIOD_COUNTS, OHLCV_PROVIDER_REQUEST_LIMIT
from scripts.unified_adapter_preflight import current_universe
from scripts.unified_stock_source_plan import state
from scripts.unified_stock_owner_proof import capture as capture_class_c


ROOT = Path(__file__).resolve().parents[1]
POLICY = UnifiedSourcePolicy(frozenset({"ohlcv_analyst", "kiwoom", "kiwoom_rest", "krx_night_futures"}))
REV7_SHA = "a3ec25f9ac7a610755aad11c172166332f937d47eb5cc3e952823d902653f323"


def read(path):
    return json.loads(path.read_bytes())


def save(out, name, value):
    durable_json(out / name, value, exclusive=True)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def freeze(args):
    from app.services.fpi_discovered_exhibit_phase2 import sealed_source
    parent = sealed_source(args.rev7, REV7_SHA)
    before = state(ROOT, args.operating)
    if not before["clean"] or not before["operating_clean"]:
        raise ValueError("clean_instruction_implementation_and_operating_required")
    at = datetime.now(timezone.utc)
    at_kst = at.astimezone(ZoneInfo("Asia/Seoul"))
    # This controller deliberately has no scheduled multi-attempt implementation.
    if ((at_kst.hour == 8 and 10 <= at_kst.minute <= 20) or
            (at_kst.hour == 16 and at_kst.minute <= 10)):
        raise ValueError("scheduled_window_requires_existing_attempt_orchestrator")
    owner_path = args.output / "native-owner.json"
    subprocess.run([sys.executable, str(ROOT / "scripts/unified_stock_source_worker.py"), "inspect",
        "--owner-root", str(args.native_owner), "--output", str(owner_path)], check=True)
    native = read(owner_path)
    if not native["owner_clean"] or not native["credentials_present"] or not native["live_provider"]:
        raise ValueError("native_owner_unavailable")
    settings = Settings(_env_file=args.operating / ".env")
    db = args.operating / "data/thesis_monitor.sqlite3"
    universe = current_universe(db, at)
    with sqlite3.connect(f"{db.as_uri()}?mode=ro", uri=True) as conn:
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        identities = {r["ticker"]: dict(r) for r in conn.execute(
            "SELECT ticker,canonical_security_id,exchange FROM securitymaster")}
    counts = {}
    for market in UNIVERSE:
        enabled = settings.us_price_structure_v3_enabled if market == "us" else settings.kr_price_structure_v3_enabled
        configured = PRICE_STRUCTURE_PERIOD_COUNTS if enabled else PERIOD_COUNTS
        counts[market] = {role: PERIOD_COUNTS["weekly"] if not adjusted else
            max(min(configured[period], OHLCV_PROVIDER_REQUEST_LIMIT), 300 if period == "monthly" else 700)
            for role, (period, adjusted) in ROLES.items()}
    run = "rev8-live-" + at.strftime("%Y%m%dT%H%M%SZ")
    stock = StockPlan(run_id=run, acquisition_id=run + ":stock-wire",
        frozen_at=at, instruction_sha=args.instruction_sha, implementation_sha=before["head"],
        universe_sha256=digest(universe), reads=make_reads(universe, identities, at=at, counts=counts),
        **{k: native[k] for k in ("owner_head", "owner_files", "settings_sha256", "request_environment_sha256")})
    us_session = us_market_session(at).latest_completed_regular_session_date
    kr_session = korea_market_session(at).latest_completed_regular_session_date
    us = [OhlcvRead(role="us_market:" + symbol, symbol=symbol, market="us", provider="ohlcv_analyst",
        period="daily", adjusted=True, session_date=us_session, max_requests=1,
        params={"symbol": symbol, "market": "US", "periods": "daily", "count": 2,
                "include_indicators": "false", "indicator_limit": 0, "adjusted": "true"}).model_dump(mode="json")
        for symbol in MARKET_SYMBOLS]
    kr = [r.model_dump(mode="json") for r in kiwoom_market_reads(session_date=kr_session,
        max_pages=settings.kiwoom_rest_max_pages, max_requests_per_page=1)]
    night = [RunRead(key="night:" + (at_kst.date() - timedelta(days=i)).isoformat(), route=KRX_FUTURES_DAILY_URL,
        params={"basDd": (at_kst.date() - timedelta(days=i)).strftime("%Y%m%d")}, max_requests=1).model_dump(mode="json")
        for i in range(7)]
    names = subprocess.check_output(["git", "ls-files", "app", "scripts"], cwd=ROOT, text=True).splitlines()
    code = {str(ROOT / name): sha256_bytes((ROOT / name).read_bytes()) for name in names if name.endswith(".py")}
    inventory = read(ROOT / "docs/operations/UNIFIED_ACQUISITION_CLASSES.json")
    stock_max = sum(r.max_pages for r in stock.reads) + 1
    kr_max = sum(r["max_pages"] for r in kr) + 1
    maxima = {"stock_wire": stock_max, "us_market_wire": len(us) * 2 + 3 + 1,
              "kr_market_wire": kr_max, "night_wire": len(night)}
    budgets = {k: {"maximum_logical": n, "maximum_HTTP_attempts": 3 * n,
                  "timeout_seconds": 600, "transient_retries": 2, "semantic_retries": 0}
               for k, n in maxima.items()}
    capture_class_c(db, args.output, stock)
    versions = {str(p.relative_to(args.output)): sha256_bytes(p.read_bytes())
                for p in sorted((args.output / "class-c").glob("*.json"))}
    denials = {role: {"status": "OPTIONAL_UNAVAILABLE", "value": None,
        "reason": "NO_LIVE_REFRESH_PLANNED_EXISTING_TYPED_SOURCE_REQUIRED"}
        for role in ("news_and_filing_events", "earnings_calendar", "us_exchange_breadth")}
    plan = {"contract": "live-full-source-cohort-proof-v1", "proof_mode": "AD_HOC_LIVE_SOURCE_PROOF",
        "scope": "LIVE_SOURCE_ADAPTER_PROOF_NOT_PRODUCTION_DECISION", "proof_run_id": run,
        "started_at": at.isoformat(), "instruction_sha": args.instruction_sha,
        "implementation_sha": before["head"], "code_files": code, "config": before["config"],
        "native_owner": native, "stock_plan": stock.model_dump(mode="json"),
        "market_attempts": {m: run + ":" + m + ":A1" for m in UNIVERSE},
        "class_b_acquisition": run + ":night:B1", "universe": universe, "universe_sha256": digest(universe),
        "source_policy": sorted(POLICY.allowed_providers), "source_policy_sha256": digest(sorted(POLICY.allowed_providers)),
        "inventory": inventory, "inventory_sha256": digest(inventory),
        "class_c_versions": versions, "class_c_version_set_sha256": digest(versions),
        "us_market_reads": us, "us_market_registry_sha256": digest(MARKET_SYMBOLS),
        "US_MARKET_SYMBOL_COUNT": len(us), "kr_market_reads": kr,
        "kr_max_pages": settings.kiwoom_rest_max_pages, "night_reads": night,
        "sessions": {"us": us_session.isoformat(), "kr": kr_session.isoformat(),
                     "night_expected": expected_latest_completed_krx_session(at_kst.date()).isoformat()},
        "budgets": budgets, "optional_denials": denials,
        "us_market_dispatch": "EXISTING_NATIVE_OHLCV_OWNER_IN_PRIVATE_WORKER_REAL_KIWOOM_NOT_SYNTHETIC",
        "us_market_wire_templates": {"chart": {"route": "/api/us/chart", "api_id": "usa06012",
            "symbols": list(MARKET_SYMBOLS), "exchanges": ["ND", "NY", "NA"], "pages_per_symbol": 2,
            "body": {"stk_cd": "DECLARED_SYMBOL", "stex_tp": "OWNER_RESOLVED_EXCHANGE", "strt_dt": "",
                     "upd_stkpc_tp": "1", "exrt_appl_tp": "0"}},
            "discovery": {"route": "/api/us/stkinfo", "api_id": "usa10099",
                          "bodies": [{"stex_tp": e} for e in ("ND", "NY", "NA")], "maximum_each": 1}},
        "prohibited": {k: 0 for k in ("alpha_vantage", "massive", "mock", "fallback", "model", "render", "send", "production_write")}}
    save(args.output, "state-before.json", before)
    save(args.output, "REV7-identity.json", {"sha256": REV7_SHA, "manifest_entries": len(parent["files"])})
    save(args.output, "canonical-identities.json", {t: identities[t] for ts in UNIVERSE.values() for t in ts})
    save(args.output, "class-c-version-set.json", {"cutoff": at.isoformat(), "versions": versions,
        "version_set_sha256": digest(versions), "selection": "EXISTING_OWNER_READONLY_PROJECTION"})
    save(args.output, "provider-budget-before.json", budgets)
    save(args.output, "rev8-full-source-acquisition-plan.json", plan)
    path = args.output / "rev8-full-source-acquisition-plan.json"
    durable_bytes(path.with_suffix(".json.sha256"), (sha256_bytes(path.read_bytes()) + "  " + path.name + "\n").encode(), exclusive=True)
    print(json.dumps({"run": run, "stock_roles": len(stock.reads), "US_MARKET_SYMBOL_COUNT": len(us),
                      "budgets": budgets, "sessions": plan["sessions"]}), flush=True)


def verify(args):
    path = args.output / "rev8-full-source-acquisition-plan.json"
    expected = path.with_suffix(".json.sha256").read_text().split()[0]
    if sha256_bytes(path.read_bytes()) != expected:
        raise SourceSafetyStop("plan_drift")
    plan = read(path)
    def guard():
        if sha256_bytes(path.read_bytes()) != expected:
            raise SourceSafetyStop("plan_drift")
        for name, sha in plan["code_files"].items():
            if sha256_bytes(Path(name).read_bytes()) != sha:
                raise SourceSafetyStop("code_drift")
        if state(ROOT, args.operating)["config"] != plan["config"]:
            raise SourceSafetyStop("configuration_drift")
        for name, sha in plan["class_c_versions"].items():
            if sha256_bytes((args.output / name).read_bytes()) != sha:
                raise SourceSafetyStop("class_c_drift")
    guard()
    return plan, guard, expected


class NativeMarketTransport(httpx.AsyncBaseTransport):
    def __init__(self, args, plan, expected):
        self.args, self.plan, self.expected = args, plan, expected
        self.process = None

    async def handle_async_request(self, request):
        if request.method != "GET" or request.url.path != "/ohlcv":
            raise SourceSafetyStop("non_market_native_route")
        params = dict(request.url.params)
        for k in ("count", "indicator_limit"):
            params[k] = int(params[k])
        if params not in [r["params"] for r in self.plan["us_market_reads"]]:
            raise SourceSafetyStop("undeclared_native_market_request")
        if self.process is None:
            self.process = await asyncio.create_subprocess_exec(*worker_command(self.args, "market", self.expected),
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
        self.process.stdin.write((json.dumps(params) + "\n").encode())
        await self.process.stdin.drain()
        line = await self.process.stdout.readline()
        if not line:
            await self.process.wait()
            raise SourceSafetyStop("native_market_worker_stopped")
        result = json.loads(line)
        return httpx.Response(result["status"], content=json.dumps(result["body"], ensure_ascii=False).encode(), request=request)

    async def aclose(self):
        if self.process is not None:
            if self.process.returncode is None:
                self.process.stdin.write(b'{"close":true}\n')
                await self.process.stdin.drain()
            _, error = await self.process.communicate()
            if error:
                save(self.args.output, "native-market-stderr-hash.json", {"sha256": sha256_bytes(error), "bytes": len(error)})
            if self.process.returncode:
                raise SourceSafetyStop("native_market_worker_failed")


def worker_command(args, mode, expected):
    return [sys.executable, str(ROOT / "scripts/unified_live_native_worker.py"), mode,
        "--owner-root", str(args.native_owner), "--plan", str(args.output / "rev8-full-source-acquisition-plan.json"),
        "--sha256", expected, "--output", str(args.output / ("stock-acquisition" if mode == "stocks" else "us-market-native"))]


async def acquire(args):
    plan, guard, expected = verify(args)
    save(args.output, "live-dispatch-once.json", {"started_at": stamp(), "plan_sha256": expected})
    settings = Settings(_env_file=args.operating / ".env")
    # All overrides are local to this short-lived source proof process.
    import app.config as config
    proof_settings = settings.model_copy(update={"macro_provider_timeout_seconds": 600, "ohlcv_timeout_seconds": 600})
    config.get_settings = lambda: proof_settings
    import app.macro.providers.market as market_module
    import app.jobs.probe_krx_night_futures as night_module
    market_module.get_settings = night_module.get_settings = lambda: proof_settings
    results, counters = {}, {}
    try:
        stock_root = args.output / "stock-acquisition"
        stock_root.mkdir(mode=0o700)
        child = await asyncio.create_subprocess_exec(*worker_command(args, "stocks", expected))
        rc = await child.wait()
        if rc:
            raise SourceSafetyStop("stock_worker_failed")
        results["stocks"] = {"status": "CAPTURE_COMPLETE_NOT_QUALIFICATION"}
        guard()
        native = NativeMarketTransport(args, plan, expected)
        observer = OhlcvReceiptObserver(root=args.output / "us-market", run_id=plan["proof_run_id"],
            attempt_id=plan["market_attempts"]["us"], reads=tuple(OhlcvRead.model_validate(r) for r in plan["us_market_reads"]), policy=POLICY)
        provider = OhlcvMarketProvider(transport=native, source_observer=observer)
        us = await provider.collect(datetime.now(timezone.utc))
        results["us_market"] = TypeAdapter(MacroProviderResult).dump_python(us, mode="json")
        save(args.output, "us-market-owner.json", results["us_market"])
        guard()
        reads = tuple(__import__("app.services.unified_kiwoom_observer", fromlist=["KiwoomRead"]).KiwoomRead.model_validate(r)
                      for r in plan["kr_market_reads"])
        seen_auth = 0
        def kr_authorize(request):
            nonlocal seen_auth
            if request.url.host != "api.kiwoom.com" or request.url.scheme != "https" or request.method != "POST":
                raise SourceSafetyStop("kr_provider_route_drift")
            if request.url.path == "/oauth2/token":
                seen_auth += 1
                if seen_auth > 1:
                    raise SourceSafetyStop("kr_auth_budget_exhausted")
            elif not any((r.endpoint, r.api_id, r.body) == (request.url.path, request.headers.get("api-id"),
                        json.loads(request.content)) for r in reads):
                raise SourceSafetyStop("kr_request_not_planned")
        recorder = BoundedTransport(root=args.output / "kr-wire", maximum_logical=plan["budgets"]["kr_market_wire"]["maximum_logical"],
            guard=guard, secrets=(settings.kiwoom_app_key, settings.kiwoom_secret_key))
        observer = KiwoomReceiptObserver(root=args.output / "kr-market", run_id=plan["proof_run_id"],
            attempt_id=plan["market_attempts"]["kr"], session_date=datetime.fromisoformat(plan["sessions"]["kr"]).date(),
            reads=reads, policy=POLICY)
        client = KiwoomRestClient(app_key=settings.kiwoom_app_key, secret_key=settings.kiwoom_secret_key,
            base_url=settings.kiwoom_rest_base_url, timeout_seconds=600, max_retries=0,
            request_interval_seconds=settings.kiwoom_rest_request_interval_seconds,
            transport=LiveAsyncTransport(recorder=recorder, authorize=kr_authorize), source_observer=observer)
        try:
            kr = await KiwoomKrMarketContextService(client, max_pages=plan["kr_max_pages"]).collect(
                session_date=observer.session_date, observed_at=datetime.now(timezone.utc))
            results["kr_market"] = {"status": "OWNER_RETURNED", "cross_section": kr.cross_section.model_dump(mode="json"),
                                    "audit": kr.audit.model_dump(mode="json")}
        except Exception as exc:
            results["kr_market"] = {"status": "FAILED", "error_class": type(exc).__name__, "error": str(exc)}
        finally:
            counters["kr"] = recorder.counts()
            await client.transport.shutdown()
        save(args.output, "kr-market-owner.json", results["kr_market"])
        guard()
        night_reads = tuple(RunRead.model_validate(r) for r in plan["night_reads"])
        def night_authorize(request):
            if request.method != "GET" or not any(str(request.url.copy_with(query=None)) == r.route and
                    dict(request.url.params) == r.params for r in night_reads):
                raise SourceSafetyStop("night_request_not_planned")
        recorder = BoundedTransport(root=args.output / "night-wire", maximum_logical=len(night_reads),
            guard=guard, secrets=(settings.krx_open_api_key,))
        observer = RunAcquisitionObserver(root=args.output / "night", run_id=plan["proof_run_id"],
            acquisition_id=plan["class_b_acquisition"], provider="krx_night_futures", role="night_and_publication_context",
            reads=night_reads, policy=POLICY)
        night_transport = LiveAsyncTransport(recorder=recorder, authorize=night_authorize)
        try:
            result = await KrxNightFuturesProvider(source_observer=observer,
                transport=night_transport,
                history_directory=args.output / "private-night-history").collect(datetime.now(timezone.utc))
            results["night"] = TypeAdapter(MacroProviderResult).dump_python(result, mode="json")
        except Exception as exc:
            results["night"] = {"status": "FAILED", "error_class": type(exc).__name__}
        finally:
            await night_transport.shutdown()
        counters["night"] = recorder.counts()
        save(args.output, "night-owner.json", results["night"])
    except SourceSafetyStop as exc:
        results["systemic_stop"] = str(exc)
    finally:
        save(args.output, "acquisition-outcome.json", {"completed_at": stamp(), "results": results, "counters": counters,
            "model": 0, "render": 0, "send": 0, "production_db_write": 0, "scheduler_mutation": 0})
    print(json.dumps({"roles": list(results), "systemic_stop": results.get("systemic_stop")}), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("freeze", "acquire"))
    for name in ("output", "operating", "native-owner", "rev7"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--instruction-sha", required=True)
    args = p.parse_args()
    if args.mode == "freeze":
        def denied(*unused, **kw):
            raise RuntimeError("freeze_network_denied")
        socket.socket.connect = socket.socket.connect_ex = socket.getaddrinfo = denied
        freeze(args)
    else:
        asyncio.run(acquire(args))


if __name__ == "__main__":
    main()
