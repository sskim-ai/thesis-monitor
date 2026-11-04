"""Current configuration/DB binding probes; not full adapter qualification."""
from datetime import datetime
from pathlib import Path

import pytest
from sqlmodel import SQLModel, Session, create_engine

from app.config import Settings
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.services.production_source_configuration import ProductionSourceConfiguration
from app.services.production_source_context import freeze_current_context
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import UNIVERSE
from tests.test_r9_rev11_full_plan import compiled


def context_setup(tmp_path, market):
    stock, args, _ = compiled()
    database = tmp_path / "current.db"
    engine = create_engine("sqlite:///" + str(database))
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for row in args["identities"].values():
            session.add(SecurityMaster.model_validate({**row, "updated_at": stock.frozen_at}))
            session.add(WatchlistItem(ticker=row["ticker"], company_name=row["company_name"], exchange=row["exchange"], created_at=stock.frozen_at))
            session.add(InvestmentThesis(ticker=row["ticker"], version=1, core_thesis="Synthetic test thesis", created_at=stock.frozen_at))
        session.add(WatchlistItem(ticker="NVDA", company_name="inactive", active=False))
        session.commit()
    engine.dispose()
    protocol = tmp_path / "protocol.json"
    durable_json(protocol, {})
    item = dict(path=str(protocol), sha256=sha256_bytes(protocol.read_bytes()), purpose="PUBLIC_PROTOCOL")
    config = ProductionSourceConfiguration(database_path=str(database), native_owner_root=str(tmp_path),
        native_python=str(tmp_path / "python"), completed_close=item, issuer_identity=item,
        kr_listing_routing={**item, "purpose": "IDENTITY_ROUTING_ONLY"}, kis_protocols={"probe.json": item})
    settings = Settings(_env_file=None, kiwoom_app_key="synthetic-key", kiwoom_secret_key="synthetic-secret",
        sec_user_agent="test@example.invalid", opendart_api_key="synthetic-dart", fred_api_key="synthetic-fred",
        eia_api_key="synthetic-eia", ecos_api_key="synthetic-ecos", krx_open_api_key="synthetic-krx",
        naver_client_id="synthetic-naver", naver_client_secret="synthetic-naver-secret", finnhub_api_key="synthetic-finnhub",
        kis_app_key="synthetic-kis", kis_app_secret="synthetic-kis-secret")
    request = dict(market=market, run_id="current", attempt_id="current-attempt-1",
        started_at=stock.frozen_at.isoformat(), target_session=next(r.latest_completed_session for r in stock.reads if r.market == market))
    return config, settings, request, stock, database


@pytest.mark.parametrize("market", ["us", "kr"])
def test_current_db_and_fresh_plan_before_transport(tmp_path, monkeypatch, market):
    config, settings, request, stock, database = context_setup(tmp_path, market)
    before = sha256_bytes(database.read_bytes())

    def static_probe(self, root, market):
        # Protocol validation has separate tests; synthetic content cannot claim
        # qualification as the real pinned documentation.
        durable_json(root / "static/official-security-identity.json", {})
        durable_json(root / "static/kr-list-routing.json", {"list": [dict(code=t, marketCode="0") for t in UNIVERSE["kr"]]})
        return {"probe": {"scope": "SYNTHETIC_PROTOCOL_ONLY"}}

    monkeypatch.setattr(ProductionSourceConfiguration, "seal_protocols", static_probe)
    calls = []

    def inspector(configuration, root):
        calls.append("inspection")
        return {k: getattr(stock, k) for k in ("owner_head", "owner_files", "settings_sha256", "request_environment_sha256")}

    root = tmp_path / "source"
    frozen, compiler, kis, credentials = freeze_current_context(request=request, directory=root,
        settings=settings, configuration=config, implementation_sha="a" * 40, native_inspector=inspector)
    assert calls == ["inspection"]
    assert frozen["generation_id"] == request["attempt_id"]
    assert frozen["plan"]["run_id"] == request["run_id"]
    assert "NVDA" not in frozen["plan"]["subjects"]
    assert frozen["plan"]["alpha_vantage_planned_calls"] == 0
    assert sha256_bytes(database.read_bytes()) == before
    assert not Path(str(database) + "-wal").exists()
    assert not Path(str(database) + "-shm").exists()
    assert all("synthetic-secret" not in p.read_text() for p in root.rglob("*.json"))
    assert digest(kis) == frozen["plan"]["kis_plan_sha256"] if kis else market == "us"
    assert compiler["stock"].run_id == request["attempt_id"]
    assert credentials and datetime.fromisoformat(frozen["frozen_at"]).utcoffset() is not None
    from app.services.canonical_source_replay import current_local_seed
    from app.services.production_source_context import POLICY
    admitted = current_local_seed(root, frozen, compiler["stock"], market, POLICY)
    assert admitted["universe"]["eligible_subjects"] == list(UNIVERSE[market])
    assert admitted["production_seed_qualified"] is False


def test_kis_missing_binding_precedes_native_inspection(tmp_path):
    config, settings, request, _, _ = context_setup(tmp_path, "kr")
    settings.kis_app_key = None
    with pytest.raises(ValueError, match="kis_required_active_binding_missing"):
        freeze_current_context(request=request, directory=tmp_path / "source", settings=settings,
            configuration=config, implementation_sha="a" * 40,
            native_inspector=lambda *_: pytest.fail("native inspection must not start"))
