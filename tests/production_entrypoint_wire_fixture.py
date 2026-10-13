"""Synthetic wire/configuration only; canonical production owners are not replaced."""
from dataclasses import asdict
import asyncio
import builtins
import cProfile
from datetime import datetime, timedelta, timezone
import functools
import json
import math
import os
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import threading
import tarfile
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import httpx
from sqlmodel import Session, SQLModel, create_engine

from app.config import Settings
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.services.unified_run_artifacts import durable_bytes, durable_json, sha256_bytes
from app.services.unified_stock_acquisition import UNIVERSE
from tests.completed_price_fixtures import official_spec
from tests.test_official_codex_shadow_transport import invocation

REPO = Path(__file__).resolve().parents[1]
REAL_DATETIME = datetime
KST = ZoneInfo("Asia/Seoul")


def freeze_import_clock(monkeypatch, clock_type):
    """Replace only the allowed clock boundary, including late function imports."""
    original_import = builtins.__import__
    def import_with_clock(name, globals=None, locals=None, fromlist=(), level=0):
        module = original_import(name, globals, locals, fromlist, level)
        if name == "datetime" and (globals or {}).get("__name__", "").startswith(("app.", "scripts.")):
            return SimpleNamespace(**{**vars(module), "datetime": clock_type})
        return module
    monkeypatch.setattr(builtins, "__import__", import_with_clock)
    for name, module in list(sys.modules.items()):
        if name.startswith(("app.", "scripts.")) and getattr(module, "datetime", None) is REAL_DATETIME:
            monkeypatch.setattr(module, "datetime", clock_type)


class RuntimeCallProfile:
    def __init__(self, monkeypatch, calls):
        self.calls, self.profiles = calls, []
        # Closure uses Python code objects only; built-in C call rows are unused.
        self.main = cProfile.Profile(builtins=False)
        self.timings = []
        self.clock_type = None
        original_run = threading.Thread.run
        def run(thread):
            profile = cProfile.Profile(builtins=False)
            self.profiles.append(profile)
            profile.enable()
            try:
                return original_run(thread)
            finally:
                profile.disable()
        monkeypatch.setattr(threading.Thread, "run", run)

    def start(self):
        self.main.enable()

    def stop(self):
        self.main.disable()
        for profile in [self.main, *self.profiles]:
            for row in profile.getstats():
                code = row.code
                if not isinstance(code, str):
                    self.timings.append(dict(file=code.co_filename, function=code.co_name,
                        calls=row.callcount, total_seconds=row.totaltime, own_seconds=row.inlinetime))
                    try:
                        relative = Path(code.co_filename).relative_to(REPO).with_suffix("")
                    except ValueError:
                        continue
                    if relative.parts[0] in {"app", "scripts"}:
                        self.calls.add((".".join(relative.parts), code.co_name))
        # Modules imported after fixture setup must not retain a previous case's clock.
        for name, module in list(sys.modules.items()):
            if name.startswith(("app.", "scripts.")) and getattr(module, "datetime", None) is self.clock_type:
                module.datetime = REAL_DATETIME


def raw_schema_response(schema):
    """Build a synthetic wire object without duplicating closed evidence refs."""
    from app.services.canonical_subject_preflight import synthetic_shape_probe
    if "const" in schema or "enum" in schema:
        return synthetic_shape_probe(schema)
    if "anyOf" in schema:
        return raw_schema_response(schema["anyOf"][0])
    if schema.get("type") == "object":
        return {key: raw_schema_response(value) for key, value in schema["properties"].items()}
    if schema.get("type") == "array":
        count = schema.get("minItems", 0)
        if "enum" in schema["items"]:
            values = schema["items"]["enum"]
            assert count <= len(values)
            return values[:count]
        return [raw_schema_response(schema["items"]) for _ in range(count)]
    return synthetic_shape_probe(schema)


class FixtureClock:
    def __init__(self, market, case=1):
        self.value = datetime(2026, 10, 8, 8 if market == "us" else 16, 10, tzinfo=KST)
        self.case = case
        if case == 6:
            self.value = self.value.replace(day=11)
        self.last_allowed_slot = self.value + timedelta(minutes=10 if case in {2, 3, 4, 5, 14} else 0)
        self.waits = []

    def now(self):
        return self.value

    async def wait_until(self, value):
        if value > self.last_allowed_slot:
            raise AssertionError("FIRST_COMPLETE_CASE_ENTERED_RETRY_SLOT")
        self.waits.append(value.isoformat())
        self.value = max(self.value, value)


def synthetic_securities():
    rows = {}
    for market, tickers in UNIVERSE.items():
        for ticker in tickers:
            ordinal = len(rows) + 1
            foreign = ticker in {"TSM", "WRD", "SKHY"}
            rows[ticker] = SecurityMaster(ticker=ticker, company_name="Synthetic " + ticker,
                canonical_company_id="synthetic-issuer-" + ticker, canonical_security_id="security-" + ticker,
                exchange="NASDAQ" if market == "us" else "KRX", country=market.upper(),
                cik=str(ordinal) if market == "us" else None,
                corp_code=str(ordinal).zfill(8) if market == "kr" else None,
                issuer_type="adr" if ticker == "SKHY" else "foreign_private_issuer" if foreign else
                    "domestic_us" if market == "us" else "domestic_kr",
                security_type="ads" if ticker == "SKHY" else "common_stock",
                identity_provider="sec_edgar" if market == "us" else "opendart",
                identity_quality="verified", updated_at=datetime(2026, 8, 1, tzinfo=timezone.utc))
    return rows


def static_protocols(root):
    from app.services.official_security_identity_service import OfficialSecurityIdentityEvidence
    from tests.test_kis_output3_protocol_owner import fixture, protocol
    from tests.test_kis_exact_action_guard import docs as action_docs
    from tests.test_kis_current_fy1_owner import docs as price_docs
    from scripts.kis_estimate_capability_probe import STAGE_A

    root.mkdir()
    securities = synthetic_securities()
    raw = official_spec()
    if not isinstance(raw, bytes):
        raise AssertionError("exact official documentation bytes required")
    durable_bytes(root / "completed-close.json", raw, exclusive=True)
    cik = securities["SKHY"].cik
    accession = f"{int(cik):010d}-26-000001"
    identity = OfficialSecurityIdentityEvidence(ticker="SKHY", issuer_name="Synthetic issuer",
        security_title="American Depositary Shares", security_type="ads", issuer_type="adr", exchange="NASDAQ",
        source_url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/prospectus.htm",
        source_form="424(b)(4)", filing_accession=accession, as_of_date="2026-06-01",
        source_reference="SYNTHETIC STATIC IDENTITY, NOT LIVE", cik=securities["SKHY"].cik,
        ordinary_share_identifier="000660").to_payload()
    durable_json(root / "issuer.json", identity, exclusive=True)
    durable_json(root / "listing.json", {"list": [dict(code=t, marketCode="0") for t in UNIVERSE["kr"]]}, exclusive=True)
    f = fixture()
    kis = root / "kis"
    kis.mkdir()
    durable_bytes(kis / "estimate-docs.json", f["docs"].evidence.raw, exclusive=True)
    durable_json(kis / "protocol.json", protocol(f), exclusive=True)
    for target, source in zip(STAGE_A, f["codes"], strict=True):
        durable_bytes(kis / (target + ".body"), f["sources"][source].raw, exclusive=True)
    durable_json(kis / "action-docs.json", action_docs(), exclusive=True)
    durable_json(kis / "price-docs.json", price_docs(), exclusive=True)

    def item(path, purpose="PUBLIC_PROTOCOL"):
        return dict(path=str(path), sha256=sha256_bytes(path.read_bytes()), purpose=purpose)

    return dict(completed_close=item(root / "completed-close.json"), issuer_identity=item(root / "issuer.json"),
        kr_listing_routing=item(root / "listing.json", "IDENTITY_ROUTING_ONLY"),
        kis_protocols={p.name: item(p, "PROTOCOL_CONTROL") for p in kis.iterdir()})


def make_settings(root, native, monkeypatch, market, case=1):
    # This is synthetic current registration state, not a collected/owned packet.
    (root / "debug").mkdir()
    database = root / "registered.db"
    engine = create_engine("sqlite:///" + str(database))
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for security in synthetic_securities().values():
            session.add(security)
            session.add(WatchlistItem(ticker=security.ticker, company_name=security.company_name,
                exchange=security.exchange, created_at=security.updated_at, activated_at=security.updated_at,
                registration_requested_at=security.updated_at))
            session.add(InvestmentThesis(ticker=security.ticker, version=1,
                core_thesis="Synthetic configured business", created_at=security.updated_at,
                price_rules=json.dumps({"currency": "USD" if security.country == "US" else "KRW",
                    "basis": "close", "support_zone_low": 90, "support_zone_high": 95} if case == 12 else {})))
        session.add(WatchlistItem(ticker="NVDA", company_name="Inactive", active=False))
        session.commit()
    engine.dispose()
    runtime = root / "python-runtime"
    (runtime / "bin").mkdir(parents=True)
    shutil.copyfile(Path(sys.executable).resolve(), runtime / "bin/python")
    (runtime / "bin/python").chmod(0o700)
    durable_bytes(runtime / "pyvenv.cfg", ("home = " + str(Path(sys.base_prefix) / "bin") +
        "\ninclude-system-site-packages = false\nversion = " + sys.version.split()[0] + "\n").encode(), exclusive=True)
    site = runtime / f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    site.mkdir(parents=True)
    durable_bytes(site / "dependencies.pth", (str(Path(sys.prefix) / site.relative_to(runtime)) + "\n").encode(), exclusive=True)
    config = dict(database_path=str(database), native_owner_root=str(native),
        native_python=str(runtime / "bin/python" if sys.platform == "darwin" else Path(sys.executable).resolve()),
        **static_protocols(root / "protocol"))
    durable_json(root / "source-configuration.json", config, exclusive=True)
    install_root = root / "model-install"
    install_root.mkdir()
    installation = invocation.__wrapped__(install_root, monkeypatch)
    binding = json.loads(json.dumps(asdict(installation["official_shadow"].binding), default=str))
    durable_json(root / "model-binding.json", binding, exclusive=True)
    return Settings(_env_file=None, data_dir=str(root / "data"), database_url="sqlite://",
        kiwoom_app_key="synthetic-key", kiwoom_secret_key="synthetic-secret", sec_user_agent="synthetic@example.invalid",
        opendart_api_key="synthetic-dart", fred_api_key="synthetic-fred", eia_api_key="synthetic-eia",
        ecos_api_key="synthetic-ecos", krx_open_api_key="synthetic-krx", finnhub_api_key="synthetic-finnhub",
        naver_client_id="synthetic-naver", naver_client_secret="synthetic-naver-secret",
        kis_app_key=None if case == 13 else "synthetic-kis", kis_app_secret="synthetic-kis-secret",
        kiwoom_rest_request_interval_seconds=0, notification_dry_run=True, telegram_bot_token=None,
        telegram_chat_id=None, unified_snapshot_enabled=True, unified_snapshot_adapter_version="production-v1",
        unified_snapshot_runtime_contract="unified-query-time-snapshot-v2",
        unified_snapshot_source_configuration=str(root / "source-configuration.json"),
        unified_snapshot_source_configuration_sha256=sha256_bytes((root / "source-configuration.json").read_bytes()),
        unified_snapshot_model_binding=str(root / "model-binding.json"),
        unified_snapshot_model_binding_sha256=sha256_bytes((root / "model-binding.json").read_bytes()),
        unified_snapshot_model_runtime_root=str(root / "model-wire"),
        unified_snapshot_debug_destination=str(root / "debug"))


def deploy_native(root):
    native = root / "native-owner"
    fixture = REPO / "tests/fixtures/native-owner-code.tar.gz"
    identity = json.loads(fixture.with_suffix("").with_suffix(".json").read_bytes())
    assert sha256_bytes(fixture.read_bytes()) == identity["archive_sha256"]
    native.mkdir()
    with tarfile.open(fixture) as archive:
        for member in archive:
            path = Path(member.name)
            assert not path.is_absolute() and ".." not in path.parts
            assert member.isdir() or member.isfile()
            target = native / path
            if member.isdir():
                target.mkdir(exist_ok=True, parents=True)
            else:
                target.parent.mkdir(exist_ok=True, parents=True)
                target.write_bytes(archive.extractfile(member).read())
                target.chmod(member.mode)
    env = dict(os.environ, GIT_AUTHOR_DATE="2026-10-08T00:00:00Z", GIT_COMMITTER_DATE="2026-10-08T00:00:00Z")
    for command in (["init", "--quiet"], ["add", "."],
                    ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                     "-c", "core.hooksPath=/dev/null", "commit", "--quiet", "-m", "Exact native code fixture"]):
        subprocess.run(["git", *command], cwd=native, env=env, check=True, capture_output=True)
    durable_bytes(native / ".env", ("KIWOOM_APP_KEY=synthetic-key\nKIWOOM_SECRET_KEY=synthetic-secret\n"
        "KIWOOM_ENV=real\nKIWOOM_BASE_URL_REAL=https://api.kiwoom.com\nENABLE_LIVE_PROVIDER=true\n"
        "KIWOOM_REQUEST_INTERVAL_SECONDS=0\nKIWOOM_STOCK_LIST_INTERVAL_SECONDS=0\n"
        "KIWOOM_MAX_RETRIES=0\n").encode(), exclusive=True)
    return native


class RawWire:
    def __init__(self, clock):
        self.clock, self.calls = clock, []
        self.plan_denials = []
        self.crossed_slot_denials = []
        self.native_processes = []
        self.child_launches = []
        self.model_launches = []

    def __call__(self, request):
        self.calls.append(dict(method=request.method, host=request.url.host, path=request.url.path,
            api_id=request.headers.get("api-id"), at=self.clock.now().isoformat(), request_sha256=sha256_bytes(request.content)))
        failed_slots = {2: {10}, 3: {10, 15}, 5: {10, 15, 20}}.get(self.clock.case, set())
        if request.url.path.endswith("/token") and self.clock.now().minute in failed_slots:
            return httpx.Response(503, json={"return_code": 1, "return_msg": "Synthetic wire unavailable"})
        if (self.clock.case == 4 and request.headers.get("api-id")
                and self.clock.now() < self.clock.last_allowed_slot):
            # Keep a non-transient raw source denial throughout attempt one.
            # The real runtime, not this fixture, owns incomplete/missed states.
            requested_at = self.clock.now()
            if not self.crossed_slot_denials:
                self.clock.value += timedelta(minutes=6)
            self.crossed_slot_denials.append(dict(requested_at=requested_at.isoformat(),
                received_at=self.clock.now().isoformat(), api_id=request.headers["api-id"],
                http_status=400, request_sha256=sha256_bytes(request.content)))
            return httpx.Response(400, json={"return_code": 1, "return_msg": "Synthetic source unavailable"})
        if request.url.host == "openapi.koreainvestment.com":
            return self.kis(request)
        if request.url.path.endswith("/token"):
            return httpx.Response(200, json=dict(return_code=0, token="synthetic-token", expires_dt="20990101000000"))
        body = json.loads(request.content) if request.content else {}
        api = request.headers.get("api-id", "")
        market = "us" if api.startswith("usa") else "kr"
        target = self.clock.now().date() - timedelta(days=1 if market == "us" else 0)
        if api in {"usa06012", "usa06013", "usa06014", "ka10081", "ka10082", "ka10083"}:
            from app.services.market_session import _exchange_calendar
            period = {"usa06012": 1, "usa06013": 7, "usa06014": 30, "ka10081": 1, "ka10082": 7, "ka10083": 30}[api]
            calendar = _exchange_calendar("XNYS" if market == "us" else "XKRX")
            rows = []
            day = target
            count = 300 if period == 30 else 700
            while len(rows) < count:
                if calendar.is_session(day) if period == 1 else day.weekday() < 5:
                    price = 100 + (800 - len(rows)) * 0.01
                    if self.clock.case == 12 and market == "kr":
                        # Raw cyclical prices, not a pivot/zone fixture. The real
                        # structure algorithm must discover any usable support.
                        price = round(99 + 9 * math.cos(2 * math.pi * len(rows) / 40), 4)
                    rows.append(dict(dt=day.strftime("%Y%m%d"), open_pric=str(price), high_pric=str(price + 1),
                        low_pric=str(price - 1), cur_prc=str(price), trde_qty="10000", trde_prica="1000000"))
                if period == 30:
                    day = day.replace(day=1) - timedelta(days=1)
                    while day.weekday() >= 5:
                        day -= timedelta(days=1)
                else:
                    day -= timedelta(days=period)
            return httpx.Response(200, json=dict(return_code=0, result_list=rows, output=rows),
                headers={"cont-yn": "N", "next-key": ""})
        if api == "usa20590":
            return httpx.Response(200, json=dict(return_code=0, result_list=[dict(dt=body["base_dt"],
                open_pric="108", high_pric="109", low_pric="107", cur_prc="108")]))
        if api == "usa10099":
            from app.macro.providers.market import MARKET_SYMBOLS
            rows = [dict(stk_cd=t, stk_nm=t, stk_enm=t, stex_tp="ND") for t in sorted(set(UNIVERSE["us"]) | set(MARKET_SYMBOLS))]
            return httpx.Response(200, json=dict(return_code=0, list=rows if body["stex_tp"] == "ND" else []))
        if api == "ka10099":
            return httpx.Response(200, json=dict(return_code=0, list=[dict(code=t,
                name="Synthetic " + t, marketCode="0", marketName="KOSPI") for t in UNIVERSE["kr"]]))
        if api == "ka10001":
            return httpx.Response(200, json=dict(return_code=0, stk_cd=body["stk_cd"],
                stk_nm="Synthetic " + body["stk_cd"], per="" if self.clock.case in {9, 10} else "12.3",
                pbr="" if self.clock.case == 10 else "1.5", eps="100", bps="900", cur_prc="108"))
        if api.startswith("ka"):
            from tests.test_kiwoom_rest_market_context import _current, _handler
            if api == "ka20009":
                row = _current(body["inds_cd"])
                return httpx.Response(200, json=dict(return_code=0, inds_cur_prc_daly_rept=[dict(
                    dt_n=target.strftime("%Y%m%d"), cur_prc_n=row["cur_prc"], flu_rt_n=row["flu_rt"])]))
            return _handler([]).handle_request(request)
        if request.url.host in {"data.sec.gov", "www.sec.gov"}:
            return self.sec(request)
        if request.url.host == "opendart.fss.or.kr":
            return self.dart(request)
        if request.url.host == "finnhub.io":
            ticker = request.url.params["symbol"]
            if request.url.path.endswith("profile2"):
                return httpx.Response(200, json=dict(ticker=ticker, exchange="NASDAQ", country="US", currency="USD"))
            metrics = {} if self.clock.case == 10 else dict(peTTM=None if self.clock.case == 9 else 12.3, pbQuarterly=1.5, forwardPE=7)
            return httpx.Response(200, json=dict(symbol=ticker, metric=metrics))
        if request.url.host == "api.stlouisfed.org":
            return httpx.Response(200, json=dict(observations=[dict(date="2026-10-07", value="4.0"),
                dict(date="2026-10-06", value="3.9")]))
        if request.url.host == "api.eia.gov":
            return httpx.Response(200, json=dict(response=dict(data=[dict(period="2026-10-02", value=100, units="Thousand Barrels")])) )
        if request.url.host == "ecos.bok.or.kr":
            from app.macro.providers.ecos import KEY_STAT_NAMES
            return httpx.Response(200, json=dict(KeyStatisticList=dict(row=[dict(KEYSTAT_NAME=sorted(names)[0],
                DATA_VALUE="1300" if key == "USDKRW" else "3.0", CYCLE="20261007", UNIT_NAME="test")
                for key, names in KEY_STAT_NAMES.items()])))
        if request.url.host == "data-dbg.krx.co.kr":
            if self.clock.case == 8:
                from tests.test_krx_night_futures_probe import _row
                row = _row("KOSPI 200 선물", "야간", "A016C000", "코스피200 F 202612 야간",
                    "123", "20260901", "1")
                row.update(TDD_OPNPRC="122", TDD_HGPRC="124", TDD_LWPRC="121")
                return httpx.Response(200, json={"OutBlock_1": [row]})
            return httpx.Response(200, json={"OutBlock_1": []})
        if request.url.host == "news.google.com":
            return httpx.Response(200, text='<rss version="2.0"><channel><title>Synthetic empty feed</title></channel></rss>')
        if request.url.host == "openapi.naver.com":
            return httpx.Response(200, json=dict(total=0, start=1, display=0, items=[]))
        raise AssertionError("UNHANDLED_SYNTHETIC_WIRE:" + request.url.path + ":" + str(request.headers.get("api-id")))

    def kis(self, request):
        from tests.test_kis_output3_protocol_owner import fixture
        from scripts.kis_estimate_capability_probe import DATA_PATH
        from scripts.kis_protocol_stage_b_probe import IDENTITY_PATH
        from scripts.kis_current_fy1_owner import PRICE_PATH

        headers = {"tr_cont": "D"}
        if request.url.path == "/oauth2/tokenP":
            return httpx.Response(200, json=dict(access_token="synthetic-kis-token", token_type="Bearer",
                expires_in=86400, access_token_token_expired="2099-01-01 00:00:00"))
        f = fixture()
        if request.url.path == DATA_PATH:
            code = request.url.params["SHT_CD"]
            raw = f["sources"][f["codes"][0]].payload()
            raw["output1"] = dict(sht_cd="A" + code, estdate="20260701")
            raw["output4"] = [dict(dt=p) for p in ("2023.12", "2024.12", "2025.12", "2026.12E", "2027.12E")]
            if self.clock.case == 10:
                from scripts import kis_no_estimate_owner as empty_owner
                raw = dict(output1=empty_owner.EMPTY_OUTPUT1, output2=[], output3=[], output4=[],
                    rt_cd="0", msg_cd="MCA00000", msg1="normal response")
                headers = {"tr_id": empty_owner.TR_ID, "tr_cont": ""}
        elif request.url.path == IDENTITY_PATH:
            code = request.url.params["PDNO"]
            raw = f["identities"][f["codes"][0]].payload()
            raw["output"].update(pdno="00000A" + code, shtn_pdno=code, std_pdno="KR7" + code + "007")
        elif request.url.path == PRICE_PATH:
            raw = dict(rt_cd="0", output=[dict(stck_bsop_date=self.clock.now().strftime("%Y%m%d"),
                stck_clpr="108", stck_oprc="108", stck_hgpr="109", stck_lwpr="107")])
        elif request.url.path.startswith("/uapi/domestic-stock/v1/ksdinfo/"):
            raw = dict(rt_cd="0", output1=[], output=[], ctx_area_fk="", ctx_area_nk="")
        else:
            raise AssertionError("UNHANDLED_SYNTHETIC_KIS_WIRE:" + request.url.path)
        return httpx.Response(200, json=raw, headers=headers)

    def sec(self, request):
        from tests.test_bounded_financial_acquisition import filing, submission
        from tests.test_external_api_accuracy import _companyfact_entry, _companyfacts_payload
        from tests.test_residual_financial_semantics import html_statement
        path = request.url.path
        securities = synthetic_securities()
        if "/submissions/" in path or "/companyfacts/" in path:
            cik = int(path.split("CIK")[-1].split(".")[0])
        else:
            cik = int(path.split("/data/")[-1].split("/")[0])
        security = next(s for s in securities.values() if s.cik and int(s.cik) == cik)
        foreign = security.ticker in {"TSM", "WRD", "SKHY"}
        f = filing("6-K" if foreign else "10-Q")
        f["accessionNumber"] = f"{cik:010d}-26-000001"
        if "/submissions/" in path:
            return httpx.Response(200, json={**submission([f]), "cik": cik})
        if "/companyfacts/" in path:
            row = {**_companyfact_entry(30, fp="Q2", start="2026-04-01", end="2026-06-30", filed="2026-08-01"),
                   "accn": f["accessionNumber"]}
            pair = [row, dict(row, start="2025-04-01", end="2025-06-30", val=20)]
            if self.clock.case == 11:
                pair[0]["val"] = -20
            facts = _companyfacts_payload("us-gaap", {"Revenues": [dict(r, val=100 if r["start"].startswith("2026") else 80)
                for r in pair], "OperatingIncomeLoss": pair})
            return httpx.Response(200, json={**facts, "cik": cik})
        if path.endswith("index.json"):
            return httpx.Response(200, json={"directory": {"item": [{"name": "primary.htm"}]}})
        # This issuer's declared bridge uses the separately collected DART source.
        # Supplying a second native comparative table would correctly conflict.
        statement = html_statement()
        if self.clock.case == 11:
            statement = statement.replace("<td>30</td>", "<td>-20</td>")
        return httpx.Response(200, text=statement if foreign and security.ticker != "SKHY"
            else "<html>Synthetic nonfinancial filing</html>")

    def dart(self, request):
        corp = request.url.params["corp_code"]
        security = next(s for s in synthetic_securities().values() if s.corp_code == corp)
        if request.url.path.endswith("list.json"):
            return httpx.Response(200, json=dict(status="000", page_no=1, total_page=1, total_count=2, list=[dict(
                corp_code=corp, stock_code=security.ticker, corp_name=security.company_name,
                report_nm=name, rcept_no=number, rcept_dt=day) for name, number, day in [
                    ("반기보고서 (2026.06)", "20260814000001", "20260814"),
                    ("사업보고서 (2025.12)", "20260320000001", "20260320")]]))
        rows = []
        for i, (account, label, amount, prior) in enumerate([
            ("ifrs-full_Revenue", "매출액", 100, 80), ("dart_OperatingIncomeLoss", "영업이익", 20, 15),
            ("ifrs-full_ProfitLoss", "당기순이익", 10, 8)]):
            if self.clock.case == 11 and account == "dart_OperatingIncomeLoss":
                amount = -20
            rows.append(dict(corp_code=corp, rcept_no="20260814000001", bsns_year="2026", reprt_code="11012",
                fs_div="CFS", sj_div="CIS", account_id=account, account_nm=label, account_detail="-", ord=str(i + 1),
                currency="KRW", thstrm_amount=str(amount), frmtrm_q_amount=str(prior),
                thstrm_nm="제 1 기 반기", frmtrm_q_nm="제 0 기 반기"))
        return httpx.Response(200, json=dict(status="000", list=rows if request.url.params.get("fs_div") == "CFS" else []))


def install_boundaries(monkeypatch, settings, clock, wire):
    from app.jobs import unified_market_snapshot as launcher
    from app.services import production_adapter_factory as factory
    from app.services import unified_market_run as runtime
    from app.services.production_model_transport import OfficialProductionModelTransport

    class ClockDateTime(REAL_DATETIME):
        @classmethod
        def __get_pydantic_core_schema__(cls, source, handler):
            return handler.generate_schema(REAL_DATETIME)

        @classmethod
        def now(cls, tz=None):
            value = clock.now()
            return value.astimezone(tz) if tz else value.astimezone().replace(tzinfo=None)

    def no_network(*args, **kwargs):
        raise AssertionError("REV63D_EXTERNAL_NETWORK_DENIED")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket.socket, "connect_ex", no_network)
    monkeypatch.setattr(socket, "getaddrinfo", no_network)
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", lambda **_: httpx.MockTransport(wire))
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", lambda self, request: wire(request))
    monkeypatch.setattr(launcher, "get_settings", lambda: settings)
    monkeypatch.setattr(launcher, "datetime", ClockDateTime)
    monkeypatch.setattr(runtime.Clock, "now", lambda self: clock.now())
    monkeypatch.setattr(runtime.Clock, "until", lambda self, value: clock.wait_until(value))
    if clock.case == 14:
        from app.services import production_source_context as source_context
        from app.services.production_source_plan import ProductionRequestPlan
        original_plan = source_context.build_request_plan

        def invalid_provider_plan(**kwargs):
            result = original_plan(**kwargs)
            raw = result["plan"].model_dump(mode="json")
            raw["descriptors"][0]["provider"] = "alpha_vantage"
            # Negative-only authorization: validate an invalid plan in memory.
            # Do not dispatch it or substitute an accepted source/owner graph.
            try:
                ProductionRequestPlan.model_validate(raw)
            except ValueError as exc:
                assert "undeclared_provider_or_route" in str(exc)
                wire.plan_denials.append(dict(reason="undeclared_provider_or_route",
                    generation_id=raw["generation_id"], wire_calls_at_rejection=len(wire.calls),
                    invalid_plan_sha256=sha256_bytes(json.dumps(raw, sort_keys=True).encode())))
                raise
            raise AssertionError("ALPHA_VANTAGE_PREFLIGHT_DID_NOT_REJECT")

        monkeypatch.setattr(source_context, "build_request_plan", invalid_provider_plan)
    freeze_import_clock(monkeypatch, ClockDateTime)
    original_spawn = asyncio.create_subprocess_exec

    async def spawn(*args, **kwargs):
        native_call = "scripts.r9_rev11_native_worker" in args
        native_input = args[args.index("--input") + 1] if native_call else None
        live_native = [p.pid for p in wire.native_processes if p.returncode is None]
        if "app.jobs.production_kis_worker" in args:
            index = args.index("-m")
            args = (*args[:index], "-c", "from tests.production_entrypoint_wire_fixture import run_kis_wire_worker; run_kis_wire_worker()",
                    clock.now().isoformat(), str(clock.case), *args[index + 2:])
        if "scripts.r9_rev11_native_worker" in args:
            index = args.index("-m")
            bootstrap = '''import builtins, datetime, runpy, sys, types
Real = datetime.datetime
at = Real.fromisoformat(sys.argv.pop(1))
class ClockDateTime(Real):
    @classmethod
    def now(cls, tz=None):
        return at.astimezone(tz) if tz else at.replace(tzinfo=None)
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        return handler.generate_schema(Real)
original_import = builtins.__import__
def import_clock(name, globals=None, locals=None, fromlist=(), level=0):
    module = original_import(name, globals, locals, fromlist, level)
    if name == 'datetime' and (globals or {}).get('__name__', '').startswith(('app.', 'scripts.')):
        return types.SimpleNamespace(**{**vars(module), 'datetime': ClockDateTime})
    return module
builtins.__import__ = import_clock
runpy.run_module('scripts.r9_rev11_native_worker', run_name='__main__')
'''
            args = (*args[:index], "-c", bootstrap, clock.now().isoformat(), *args[index + 2:])
        process = await original_spawn(*args, **kwargs)
        if native_call:
            wire.child_launches.append(dict(pid=process.pid, at=clock.now().isoformat(),
                attempt_id=Path(native_input).parent.parent.name,
                already_live_native_pids=live_native))
            wire.native_processes.append(process)
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)

    async def model_wire(*args, **kwargs):
        wire.model_launches.append(clock.now().isoformat())
        return SyntheticModelProcess(clock.case)

    monkeypatch.setattr(factory, "OfficialProductionModelTransport",
        functools.partial(OfficialProductionModelTransport, worker_factory=model_wire))
    exceptions, calls = [], set()
    from scripts import r2b_r2_contract as contract
    original_require = contract._require
    def observe_require(condition, message):
        if not condition:
            exceptions.append(dict(function="r2b_r2_contract._require", message=message))
        return original_require(condition, message)
    monkeypatch.setattr(contract, "_require", observe_require)
    trace = RuntimeCallProfile(monkeypatch, calls)
    trace.clock_type = ClockDateTime
    return launcher, trace, calls, exceptions


class SyntheticModelProcess:
    """Raw wire response only; the real production adapter owns every validator."""
    returncode = None

    def __init__(self, case=1):
        self.case = case

    async def communicate(self, raw_frame):
        frame = json.loads(raw_frame)
        root = Path(frame["directory"])
        schema = json.loads((root / "approved-input/provider-wire-schema.json").read_bytes())
        definitions = schema.get("$defs", {})
        def dereference(value):
            if isinstance(value, dict):
                if "$ref" in value:
                    return dereference(definitions[value["$ref"].removeprefix("#/$defs/")])
                return {k: dereference(v) for k, v in value.items() if k != "$defs"}
            return [dereference(v) for v in value] if isinstance(value, list) else value
        schema = dereference(schema)
        prompt = (root / "approved-input/prompt.txt").read_text()
        context = json.loads(prompt.rsplit("\nFROZEN_CONTEXT:\n", 1)[1])
        stage = json.loads((root / "production-authorization.json").read_bytes())["stage"]
        if stage == "CORE":
            from scripts.m12ds_r3_policy import ADVERSE
            response = dict(cores={ticker: dict(claims=[dict(effect=observation["effect"],
                text="Synthetic source interpretation.", evidence_refs=[observation["source_ref"]],
                observation_ids=[key], materiality="ACTIVE_MATERIAL_RISK"
                    if self.case == 11 and observation["effect"] in ADVERSE else "CONTEXT_ONLY")
                for key, observation in list(item["observed_propositions"].items())[:8]])
                for ticker, item in context.items()})
        else:
            if stage == "B":
                for subject in schema["properties"]["decisions"]["properties"].values():
                    branches = subject["properties"]["overall"]["anyOf"]
                    owned = [b for b in branches if b["properties"]["supporting_refs"].get("minItems", 0)]
                    if owned:
                        subject["properties"]["overall"]["anyOf"] = owned
            response = raw_schema_response(schema)
        durable_json(root / "raw-output.json", response, exclusive=True)
        durable_json(root / "transport-receipt.json", dict(status="PASS", synthetic_wire=True,
            request_id=frame["request_id"], prompt_sha256=frame["prompt_sha256"],
            schema_sha256=frame["schema_sha256"]), exclusive=True)
        self.returncode = 0
        return b"", b""

    async def wait(self):
        return self.returncode


def run_kis_wire_worker():
    """Child-side external HTTP/clock boundary; execute the unchanged worker."""
    import io
    import runpy

    clock = FixtureClock("kr")
    clock.value = REAL_DATETIME.fromisoformat(sys.argv.pop(1))
    clock.case = int(sys.argv.pop(1))
    wire = RawWire(clock)
    raw = sys.stdin.buffer.read()
    root = Path(json.loads(raw)["root"])
    sys.stdin = io.TextIOWrapper(io.BytesIO(raw))
    def denied(*args, **kwargs):
        raise AssertionError("REV63D_KIS_CHILD_EXTERNAL_NETWORK_DENIED")
    socket.socket.connect = socket.socket.connect_ex = socket.getaddrinfo = denied
    httpx.HTTPTransport.handle_request = lambda self, request: wire(request)
    class ClockDateTime(REAL_DATETIME):
        @classmethod
        def now(cls, tz=None):
            value = clock.now()
            return value.astimezone(tz) if tz else value.replace(tzinfo=None)
        @classmethod
        def __get_pydantic_core_schema__(cls, source, handler):
            return handler.generate_schema(REAL_DATETIME)
    import pytest
    patches = pytest.MonkeyPatch()
    freeze_import_clock(patches, ClockDateTime)
    try:
        runpy.run_module("app.jobs.production_kis_worker", run_name="__main__")
    finally:
        patches.undo()
        durable_json(root.parent / "kis-wire-test-receipt.json", dict(wire=wire.calls,
            external_network_calls=0), exclusive=True)
