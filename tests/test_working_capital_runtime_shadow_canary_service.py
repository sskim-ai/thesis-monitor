from __future__ import annotations

import copy
import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.cash_flow_capital_efficiency_service import (
    EligibilityStatus,
    FactType,
    FinancialFact,
    Metric,
    PeriodIdentity,
    PeriodType,
)
from app.services.working_capital_core_service import (
    WorkingCapitalCoreSnapshot,
    build_working_capital_core_snapshot,
)
from app.services.working_capital_runtime_shadow_canary_service import (
    CanaryLaunchResult,
    _runtime_scope,
    canary_identity,
    launch_working_capital_runtime_shadow_canary,
    run_working_capital_runtime_shadow_canary,
)


PACKET_ID = "2026-08-21-kr-run-31-test"
CURRENT = date(2026, 6, 30)
PRIOR = date(2025, 6, 30)
AVAILABLE = date(2026, 8, 1)
NOW = datetime(2026, 8, 21, 8, 0, tzinfo=UTC)


def _fact(
    ticker: str,
    metric: Metric,
    value: str,
    *,
    period_end: date,
    semantic: str,
    available: date,
    balance_scope: str | None = None,
) -> FinancialFact:
    is_balance = metric in {
        Metric.INVENTORY,
        Metric.TRADE_AR,
        Metric.BROAD_AR,
        Metric.TRADE_AP,
        Metric.BROAD_AP,
    }
    token = hashlib.sha256(
        f"{ticker}|{metric.value}|{value}|{period_end}|{semantic}".encode()
    ).hexdigest()[:20]
    fiscal_year = period_end.year
    return FinancialFact(
        fact_id=f"fact:{token}",
        issuer_id=f"issuer:{ticker}",
        metric=metric,
        value=Decimal(value),
        currency="KRW",
        unit="KRW",
        period=PeriodIdentity(
            start=period_end if is_balance else date(fiscal_year, 1, 1),
            end=period_end,
            period_type=PeriodType.POINT_IN_TIME if is_balance else PeriodType.YTD,
            fiscal_year=fiscal_year,
            fiscal_quarter=2,
        ),
        entity_scope="consolidated",
        statement_basis="official_filing_statement",
        reported_or_derived="reported",
        source_provider="opendart",
        source_document_id=f"doc:{token}",
        filing_date=available,
        source_occurrence_id=f"occ:{token}",
        raw_payload_sha256=hashlib.sha256(token.encode()).hexdigest(),
        semantic_mapping=semantic,
        fact_type=FactType.REPORTED,
        source_semantic=semantic,
        quality="REPORTED_VERIFIED",
        eligibility=EligibilityStatus.ELIGIBLE,
        as_of_date=available,
        source_available_at=available,
        balance_scope=balance_scope,
        net_gross_scope="net" if balance_scope else None,
    )


def _balance_pair(ticker: str, metric: Metric) -> list[FinancialFact]:
    semantic = {
        Metric.INVENTORY: "ifrs-full:Inventories",
        Metric.TRADE_AR: "ifrs-full:TradeReceivables",
        Metric.BROAD_AR: "us-gaap:AccountsReceivableNetCurrent",
        Metric.TRADE_AP: "ifrs-full:TradePayables",
        Metric.BROAD_AP: "us-gaap:AccountsPayableAndAccruedLiabilitiesCurrent",
    }[metric]
    scope = "total" if metric == Metric.INVENTORY else "current"
    return [
        _fact(
            ticker,
            metric,
            "125",
            period_end=CURRENT,
            semantic=semantic,
            available=AVAILABLE,
            balance_scope=scope,
        ),
        _fact(
            ticker,
            metric,
            "100",
            period_end=PRIOR,
            semantic=semantic,
            available=date(2025, 8, 1),
            balance_scope=scope,
        ),
    ]


def _flow_pair(ticker: str, metric: Metric, semantic: str) -> list[FinancialFact]:
    return [
        _fact(
            ticker,
            metric,
            "220",
            period_end=CURRENT,
            semantic=semantic,
            available=AVAILABLE,
        ),
        _fact(
            ticker,
            metric,
            "200",
            period_end=PRIOR,
            semantic=semantic,
            available=date(2025, 8, 1),
        ),
    ]


def _snapshot(
    ticker: str,
    metric: Metric,
    *,
    industry: str,
    financial_type: str = "non_financial",
) -> WorkingCapitalCoreSnapshot:
    return build_working_capital_core_snapshot(
        (
            *_balance_pair(ticker, metric),
            *_flow_pair(ticker, Metric.REVENUE, "ifrs-full:Revenue"),
            *_flow_pair(ticker, Metric.COGS, "ifrs-full:CostOfSales"),
        ),
        issuer_id=f"issuer:{ticker}",
        industry=industry,
        financial_type=financial_type,
        as_of_date=date(2026, 8, 21),
    )


def _packet() -> dict[str, object]:
    return {
        "packet_id": PACKET_ID,
        "assessment_date": "2026-08-21",
        "market": "kr",
        "generated_at": "2026-08-21T07:40:00+00:00",
        "stocks": [
            {"ticker": "INV", "unknowns": ["재고 전환을 확인해야 합니다."]},
            {"ticker": "AR", "unknowns": ["매출채권 회수를 확인해야 합니다."]},
            {"ticker": "BROAD", "unknowns": ["매출채권 회수를 확인해야 합니다."]},
            {"ticker": "AP", "unknowns": ["매입채무를 확인해야 합니다."]},
        ],
    }


def _delivery(mode: str = "ai_assisted") -> dict[str, object]:
    return {
        "packet_id": PACKET_ID,
        "delivery_mode": mode,
        "status": "sent",
        "delivery_count": 4,
        "sent_count": 4,
        "pending_count": 0,
    }


def _runtime_inputs(packet: dict[str, object]):
    del packet
    originals = {
        "INV": _snapshot("INV", Metric.INVENTORY, industry="memory_semiconductor"),
        "AR": _snapshot("AR", Metric.TRADE_AR, industry="industrial_epc"),
        "BROAD": _snapshot(
            "BROAD", Metric.BROAD_AR, industry="cloud_platform_software"
        ),
        "AP": _snapshot("AP", Metric.TRADE_AP, industry="industrial_epc"),
    }
    snapshots = {ticker: _runtime_scope(item) for ticker, item in originals.items()}
    records = {
        "INV": {"industry": "memory_semiconductor", "market": "KR"},
        "AR": {"industry": "industrial_epc", "market": "KR"},
        "BROAD": {"industry": "cloud_platform_software", "market": "KR"},
        "AP": {"industry": "industrial_epc", "market": "KR"},
    }
    return snapshots, records, {"INV": CURRENT}, "a" * 64


@pytest.fixture
def canary_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from app.services import working_capital_runtime_shadow_canary_service as service

    data_root = tmp_path / "data"
    packet_path = data_root / "ai_review" / "inbox" / f"{PACKET_ID}.json"
    packet_path.parent.mkdir(parents=True)
    packet_path.write_text(json.dumps(_packet()), encoding="utf-8")
    archive = (
        data_root
        / "ai_review"
        / "pilot"
        / "history"
        / "2026"
        / "08"
        / PACKET_ID
    )
    archive.mkdir(parents=True)
    delivery_path = archive / "delivery-result.json"
    delivery_path.write_text(json.dumps(_delivery()), encoding="utf-8")
    monkeypatch.setattr(service, "_data_root", lambda: data_root)
    monkeypatch.setattr(service, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(service, "_load_runtime_inputs", _runtime_inputs)
    monkeypatch.setattr(service, "_latest_preliminary_periods", lambda *_args: {})
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(working_capital_runtime_shadow_canary_enabled=True),
    )
    return data_root, archive, packet_path, delivery_path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _receipt_path(archive: Path) -> Path:
    root = archive / "working-capital-shadow-canary" / canary_identity(PACKET_ID)
    paths = list(root.glob("attempts/*/canary-receipt.json"))
    assert len(paths) == 1
    return paths[0]


def test_runtime_scope_excludes_broad_ar_and_all_ap() -> None:
    broad = _runtime_scope(
        _snapshot("BROAD", Metric.BROAD_AR, industry="cloud_platform_software")
    )
    ap = _runtime_scope(_snapshot("AP", Metric.TRADE_AP, industry="industrial_epc"))
    inventory = _runtime_scope(
        _snapshot("INV", Metric.INVENTORY, industry="memory_semiconductor")
    )
    trade_ar = _runtime_scope(
        _snapshot("AR", Metric.TRADE_AR, industry="industrial_epc")
    )

    assert broad.metric_states == () and broad.relations == ()
    assert ap.metric_states == () and ap.relations == ()
    assert {item.balance_metric for item in inventory.relations} == {Metric.INVENTORY}
    assert {item.balance_metric for item in trade_ar.relations} == {Metric.TRADE_AR}


def test_runtime_canary_selects_only_inventory_and_trade_ar_and_is_idempotent(
    canary_environment,
) -> None:
    _data_root, archive, packet_path, delivery_path = canary_environment
    before = (_sha(packet_path), _sha(delivery_path))

    first = run_working_capital_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="ai_assisted",
        expected_delivery_sha256=_sha(delivery_path),
        now=NOW,
    )
    second = run_working_capital_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="ai_assisted",
        expected_delivery_sha256=_sha(delivery_path),
        now=NOW,
    )

    assert first.status == "COMPLETE_PASS"
    assert second.status == "DUPLICATE_SKIPPED"
    assert (_sha(packet_path), _sha(delivery_path)) == before
    receipt = json.loads(_receipt_path(archive).read_text())
    assert receipt["selected_subjects"] == ["INV", "AR"]
    assert receipt["selected_metric_families"] == {
        "INV": "inventory",
        "AR": "trade_accounts_receivable",
    }
    assert receipt["numeric_binding"] == {
        "automatic": 2,
        "manual": 0,
        "rejected": 0,
        "unresolved": 0,
    }
    assert receipt["production_influence_count"] == 0
    assert receipt["cash_flow_cross_link_count"] == 1
    assert (
        archive
        / "working-capital-shadow-canary"
        / canary_identity(PACKET_ID)
        / "canary-complete.json"
    ).exists()


def test_validation_failure_is_archived_without_production_effect(
    canary_environment, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services import working_capital_runtime_shadow_canary_service as service

    _data_root, archive, packet_path, delivery_path = canary_environment
    before = (_sha(packet_path), _sha(delivery_path))
    monkeypatch.setattr(
        service,
        "validate_working_capital_reasoning",
        lambda *_args, **_kwargs: ("unsupported_causal_overclaim",),
    )

    result = run_working_capital_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="ai_assisted",
        expected_delivery_sha256=_sha(delivery_path),
        now=NOW,
    )

    assert result.status == "FAILED_VALIDATION"
    assert (_sha(packet_path), _sha(delivery_path)) == before
    receipt = json.loads(_receipt_path(archive).read_text())
    assert receipt["semantic_error_count"] == 4
    assert receipt["production_influence_count"] == 0


def test_newer_packet_formal_period_suppresses_older_static_relation(
    canary_environment,
) -> None:
    _data_root, archive, packet_path, delivery_path = canary_environment
    packet = json.loads(packet_path.read_text())
    packet["stocks"][0]["valuation"] = {
        "financial_quality": {
            "source_snapshot": {
                "source_type": "full_statement",
                "period": "2026-09-30",
            }
        }
    }
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

    result = run_working_capital_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="ai_assisted",
        expected_delivery_sha256=_sha(delivery_path),
        now=NOW,
    )

    assert result.status == "COMPLETE_PASS"
    receipt = json.loads(_receipt_path(archive).read_text())
    assert receipt["selected_subjects"] == ["AR"]
    sidecar = json.loads(
        (_receipt_path(archive).parent / "working-capital-sidecar.json").read_text()
    )
    assert sidecar["subjects"]["INV"]["shadow_used"] is False
    assert any(
        item["reason"] == "relation_not_latest_formal_balance"
        for item in sidecar["subjects"]["INV"]["point_in_time_exclusions"]
    )


def test_launcher_is_detached_and_only_accepts_terminal_delivery(
    canary_environment,
) -> None:
    _data_root, _archive, _packet_path, _delivery_path = canary_environment
    calls: list[tuple[list[str], dict[str, object]]] = []

    class Process:
        pid = 91

    def popen(command, **kwargs):
        calls.append((command, kwargs))
        return Process()

    production = _delivery()
    original = copy.deepcopy(production)
    launched = launch_working_capital_runtime_shadow_canary(production, popen=popen)
    pending = launch_working_capital_runtime_shadow_canary(
        {**production, "status": "pending", "sent_count": 3, "pending_count": 1},
        popen=popen,
    )

    assert launched == CanaryLaunchResult(
        "launched", PACKET_ID, canary_identity(PACKET_ID), 91
    )
    assert pending.status == "not_terminal"
    assert production == original
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command[1:3] == ["-m", "app.jobs.working_capital_shadow_canary"]
    assert kwargs["start_new_session"] is True


def test_fallback_delivery_has_separate_canary_and_no_telegram_import(
    canary_environment,
) -> None:
    _data_root, archive, packet_path, delivery_path = canary_environment
    fallback = _delivery("deterministic_fallback")
    delivery_path.write_text(json.dumps(fallback), encoding="utf-8")
    before = (_sha(packet_path), _sha(delivery_path))

    result = run_working_capital_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="deterministic_fallback",
        expected_delivery_sha256=_sha(delivery_path),
        now=NOW,
    )

    assert result.status == "COMPLETE_PASS"
    assert (_sha(packet_path), _sha(delivery_path)) == before
    source = Path(
        "app/services/working_capital_runtime_shadow_canary_service.py"
    ).read_text(encoding="utf-8")
    assert "notification_service" not in source
    assert "TelegramNotifier" not in source
