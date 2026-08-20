from __future__ import annotations

import copy
import json
from datetime import date, datetime, UTC
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.jobs.ai_review import _launch_terminal_canaries
from app.services.cash_flow_capital_efficiency_service import (
    CapexScope,
    EligibilityStatus,
    FactType,
    FinancialFact,
    Metric,
    PeriodIdentity,
    PeriodType,
)
from app.services.cash_flow_runtime_shadow_canary_service import (
    CanaryLaunchResult,
    canary_identity,
    launch_cash_flow_runtime_shadow_canary,
    run_cash_flow_runtime_shadow_canary,
)
from app.services.cash_flow_shadow_consumption_service import (
    ShadowNumericClaim,
    ShadowReasoning,
)


PACKET_ID = "2026-08-21-us-run-30-test"
NOW = datetime(2026, 8, 21, 0, 1, tzinfo=UTC)


def _fact(
    ticker: str,
    metric: Metric,
    value: str,
    *,
    suffix: str = "current",
    filing_date: date = date(2026, 7, 20),
    input_fact_ids: tuple[str, ...] = (),
) -> FinancialFact:
    fact_id = f"{ticker}:{metric.value}:{suffix}"
    return FinancialFact(
        fact_id=fact_id,
        issuer_id=f"issuer:{ticker}",
        metric=metric,
        value=Decimal(value),
        currency="USD",
        unit="USD",
        period=PeriodIdentity(
            start=date(2026, 1, 1),
            end=date(2026, 6, 30),
            period_type=PeriodType.YTD,
            fiscal_year=2026,
            fiscal_quarter=2,
        ),
        entity_scope="consolidated",
        statement_basis="CFS",
        reported_or_derived=(
            "derived_metric" if metric == Metric.FCF else "reported"
        ),
        source_provider="sec_companyfacts",
        source_document_id=f"doc:{ticker}",
        filing_date=filing_date,
        source_occurrence_id=f"occ:{fact_id}",
        raw_payload_sha256="a" * 64,
        semantic_mapping=(
            "OCF_MINUS_PPE_CAPEX_CASH_OUTFLOW"
            if metric == Metric.FCF
            else metric.value
        ),
        fact_type=(
            FactType.DERIVED_METRIC if metric == Metric.FCF else FactType.REPORTED
        ),
        source_semantic=metric.value,
        source_reported_value=(None if metric == Metric.FCF else Decimal(value)),
        source_reported_unit="USD",
        source_sign=(
            "positive_payment_magnitude"
            if metric == Metric.CAPEX
            else "economic_signed"
        ),
        capex_scope=CapexScope.PPE_ONLY if metric == Metric.CAPEX else None,
        derivation_formula=(
            "OCF_MINUS_PPE_CAPEX_CASH_OUTFLOW" if metric == Metric.FCF else None
        ),
        derivation_version=(
            "cash-flow-capital-efficiency-v1" if metric == Metric.FCF else None
        ),
        input_fact_ids=input_fact_ids,
        quality="REPORTED_VERIFIED",
        eligibility=EligibilityStatus.ELIGIBLE,
    )


def _full_facts(ticker: str, *, negative: bool = False) -> list[FinancialFact]:
    ocf = _fact(ticker, Metric.OCF, "30" if negative else "100")
    capex = _fact(ticker, Metric.CAPEX, "70" if negative else "40")
    fcf = _fact(
        ticker,
        Metric.FCF,
        "-40" if negative else "60",
        input_fact_ids=(ocf.fact_id, capex.fact_id),
    )
    return [ocf, capex, fcf]


def _packet() -> dict[str, object]:
    stocks = [
        {
            "ticker": "GOOGL",
            "industry": "Information Technology Services",
            "sector": "Technology",
            "unknowns": ["OCF·CAPEX·FCF가 미확인입니다."],
            "industry_reasoning_plan": {"next_confirmation": "cloud cash flow"},
            "fact_catalog": [
                {"fact_type": "financial_quality", "as_of_date": "2026-06-30"}
            ],
        },
        {
            "ticker": "HUT",
            "industry": "Data Center",
            "sector": "Technology",
            "unknowns": ["FCF impact is unknown"],
            "industry_reasoning_plan": {"next_confirmation": "lease billing"},
            "fact_catalog": [
                {"fact_type": "financial_quality", "as_of_date": "2026-06-30"}
            ],
        },
        {
            "ticker": "RXRX",
            "industry": "Biotechnology",
            "sector": "Healthcare",
            "unknowns": ["현금소진이 미확인입니다."],
            "industry_reasoning_plan": {"next_confirmation": "milestone cash flow"},
            "fact_catalog": [
                {"fact_type": "financial_quality", "as_of_date": "2026-06-30"}
            ],
        },
        {
            "ticker": "TSM",
            "industry": "Semiconductors",
            "sector": "Technology",
            "unknowns": ["FCF impact is unknown"],
            "industry_reasoning_plan": {"next_confirmation": "wafer margin capex"},
            "fact_catalog": [
                {"fact_type": "financial_quality", "as_of_date": "2026-06-30"}
            ],
        },
    ]
    return {
        "packet_id": PACKET_ID,
        "assessment_date": "2026-08-21",
        "market": "us",
        "generated_at": "2026-08-20T23:20:00+00:00",
        "source_monitor_run_id": "30",
        "analysis_policy_version": "daily-review-v3.10",
        "output_schema_version": "4",
        "stocks": stocks,
    }


def _delivery(mode: str = "ai_assisted") -> dict[str, object]:
    return {
        "packet_id": PACKET_ID,
        "delivery_mode": mode,
        "status": "sent",
        "delivery_count": 5,
        "sent_count": 5,
        "pending_count": 0,
        "dispatched_at": "2026-08-21T00:00:00+00:00",
    }


def _runtime_inputs():
    googl = _full_facts("GOOGL")
    hut = [_fact("HUT", Metric.OCF, "25")]
    rxrx = _full_facts("RXRX", negative=True)
    tsm = _full_facts("TSM")
    facts_by_ticker = {"GOOGL": googl, "HUT": hut, "RXRX": rxrx, "TSM": tsm}
    facts_by_id = {
        fact.fact_id: fact
        for facts in facts_by_ticker.values()
        for fact in facts
    }
    records = {
        "GOOGL": {
            "cash_flow_core_status": "ELIGIBLE",
            "metrics": {"fcf": {"fact_id": googl[-1].fact_id}},
        },
        "HUT": {
            "cash_flow_core_status": "PARTIAL",
            "metrics": {"fcf": {"fact_id": None}},
        },
        "RXRX": {
            "cash_flow_core_status": "ELIGIBLE",
            "metrics": {"fcf": {"fact_id": rxrx[-1].fact_id}},
        },
        "TSM": {
            "cash_flow_core_status": "ELIGIBLE",
            "metrics": {"fcf": {"fact_id": tsm[-1].fact_id}},
        },
    }
    formal = {ticker: date(2026, 6, 30) for ticker in records}
    preliminary = {"TSM": date(2026, 7, 31)}
    industries = {
        "GOOGL": "cloud_platform_software",
        "HUT": "hpc_data_center",
        "RXRX": "biotech",
        "TSM": "memory_semiconductor",
    }
    financial_types = {ticker: "non_financial" for ticker in records}
    return (
        records,
        facts_by_ticker,
        facts_by_id,
        formal,
        preliminary,
        industries,
        financial_types,
        "b" * 64,
        "c" * 64,
    )


@pytest.fixture
def canary_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from app.services import cash_flow_runtime_shadow_canary_service as service

    data_root = tmp_path / "data"
    packet = _packet()
    packet_path = data_root / "ai_review" / "inbox" / f"{PACKET_ID}.json"
    packet_path.parent.mkdir(parents=True)
    packet_path.write_text(json.dumps(packet), encoding="utf-8")
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
    monkeypatch.setattr(service, "_load_runtime_inputs", lambda packet: _runtime_inputs())
    monkeypatch.setattr(
        service,
        "get_settings",
        lambda: SimpleNamespace(cash_flow_runtime_shadow_canary_enabled=True),
    )
    return data_root, archive, packet_path, delivery_path


def _sha(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _receipt_path(archive: Path) -> Path:
    root = archive / "cash-flow-shadow-canary" / canary_identity(PACKET_ID)
    receipts = list(root.glob("attempts/*/canary-receipt.json"))
    assert len(receipts) == 1
    return receipts[0]


def test_runtime_canary_passes_and_is_idempotent_without_touching_production(
    canary_environment,
) -> None:
    _data_root, archive, packet_path, delivery_path = canary_environment
    packet_before = _sha(packet_path)
    delivery_before = _sha(delivery_path)

    first = run_cash_flow_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="ai_assisted",
        expected_delivery_sha256=delivery_before,
        now=NOW,
    )
    second = run_cash_flow_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="ai_assisted",
        expected_delivery_sha256=delivery_before,
        now=NOW,
    )

    assert first.status == "COMPLETE_PASS"
    assert second.status == "DUPLICATE_SKIPPED"
    assert _sha(packet_path) == packet_before
    assert _sha(delivery_path) == delivery_before
    root = archive / "cash-flow-shadow-canary" / canary_identity(PACKET_ID)
    assert (root / "canary-complete.json").exists()
    assert len(list(root.glob("attempts/*"))) == 1
    receipt = json.loads(_receipt_path(archive).read_text())
    assert receipt["production_influence_count"] == 0
    assert receipt["telegram_delivery_count"] == 0
    assert receipt["numeric_binding"] == {
        "automatic": 3,
        "manual": 0,
        "rejected": 0,
        "unresolved": 0,
    }
    attempt = _receipt_path(archive).parent
    sidecar = json.loads((attempt / "cash-flow-sidecar.json").read_text())
    assert sidecar["subjects"]["TSM"]["usage_mode"] == "LATEST_FORMAL_CONTEXT_ONLY"
    assert sidecar["subjects"]["TSM"]["shadow_used"] is False
    assert sidecar["subjects"]["HUT"]["usage_mode"] == "OCF_ONLY_CONTEXT"
    raw = json.loads((attempt / "raw-shadow-output.json").read_text())
    assert raw["subjects"]["TSM"] is None
    assert "runway" in raw["subjects"]["RXRX"]["text"]


def test_ai_generation_failure_has_separate_receipt_and_no_production_effect(
    canary_environment,
) -> None:
    _data_root, archive, packet_path, delivery_path = canary_environment
    before = (_sha(packet_path), _sha(delivery_path))

    def fail(*_args):
        raise TimeoutError("shadow generation timeout")

    result = run_cash_flow_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="ai_assisted",
        expected_delivery_sha256=_sha(delivery_path),
        generator=fail,
        now=NOW,
    )

    assert result.status == "AI_GENERATION_FAILED"
    assert (_sha(packet_path), _sha(delivery_path)) == before
    receipt = json.loads(_receipt_path(archive).read_text())
    assert receipt["status"] == "AI_GENERATION_FAILED"
    assert receipt["production_influence_count"] == 0


def test_numeric_validator_failure_is_canary_only(canary_environment) -> None:
    _data_root, archive, _packet_path, delivery_path = canary_environment

    def invalid(contexts, facts, industries, source_texts):
        fact = next(item for item in facts.values() if item.metric == Metric.FCF)
        return {
            ticker: (
                ShadowReasoning(
                    text="잉여현금흐름은 $999입니다.",
                    fact_ids=(fact.fact_id,),
                    numeric_claims=(
                        ShadowNumericClaim(
                            fact_id=fact.fact_id,
                            semantic_type=fact.metric.value,
                            value="999",
                            display="$999",
                            currency=fact.currency,
                            unit=fact.unit,
                        ),
                    ),
                )
                if ticker == "GOOGL"
                else None
            )
            for ticker in contexts
        }

    result = run_cash_flow_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="ai_assisted",
        expected_delivery_sha256=_sha(delivery_path),
        generator=invalid,
        now=NOW,
    )

    assert result.status == "NUMERIC_BINDING_FAILED"
    assert not (
        archive
        / "cash-flow-shadow-canary"
        / canary_identity(PACKET_ID)
        / "canary-complete.json"
    ).exists()
    receipt = json.loads(_receipt_path(archive).read_text())
    assert receipt["numeric_binding"]["rejected"] == 1
    assert receipt["production_influence_count"] == 0


def test_semantic_validator_failure_is_canary_only(canary_environment) -> None:
    _data_root, archive, _packet_path, delivery_path = canary_environment

    def stale_as_current(contexts, facts, industries, source_texts):
        fact = next(
            item
            for item in facts.values()
            if item.fact_id.startswith("TSM:") and item.metric == Metric.FCF
        )
        return {
            ticker: (
                ShadowReasoning(
                    text="현재 잉여현금흐름은 $60입니다.",
                    fact_ids=(fact.fact_id,),
                    numeric_claims=(
                        ShadowNumericClaim(
                            fact_id=fact.fact_id,
                            semantic_type=fact.metric.value,
                            value="60",
                            display="$60",
                            currency=fact.currency,
                            unit=fact.unit,
                        ),
                    ),
                )
                if ticker == "TSM"
                else None
            )
            for ticker in contexts
        }

    result = run_cash_flow_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="ai_assisted",
        expected_delivery_sha256=_sha(delivery_path),
        generator=stale_as_current,
        now=NOW,
    )

    assert result.status == "SEMANTIC_VALIDATION_FAILED"
    receipt = json.loads(_receipt_path(archive).read_text())
    assert receipt["numeric_binding"]["rejected"] == 0
    assert receipt["semantic_error_count"] > 0
    assert receipt["production_influence_count"] == 0


def test_archive_failure_cannot_escape_to_production(
    canary_environment, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services import cash_flow_runtime_shadow_canary_service as service

    _data_root, archive, _packet_path, delivery_path = canary_environment
    original = service._write_json_once

    def fail_one(path: Path, payload: object) -> None:
        if path.name == "raw-shadow-output.json":
            raise OSError("archive unavailable")
        original(path, payload)

    monkeypatch.setattr(service, "_write_json_once", fail_one)
    result = run_cash_flow_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="ai_assisted",
        expected_delivery_sha256=_sha(delivery_path),
        now=NOW,
    )

    assert result.status == "ARCHIVE_WRITE_FAILED"
    receipt = json.loads(_receipt_path(archive).read_text())
    assert receipt["status"] == "ARCHIVE_WRITE_FAILED"
    assert receipt["production_influence_count"] == 0


def test_launcher_detaches_only_after_terminal_delivery(canary_environment) -> None:
    _data_root, _archive, _packet_path, _delivery_path = canary_environment
    calls: list[tuple[list[str], dict[str, object]]] = []

    class Process:
        pid = 42

    def popen(command, **kwargs):
        calls.append((command, kwargs))
        return Process()

    production = _delivery()
    original = copy.deepcopy(production)
    launched = launch_cash_flow_runtime_shadow_canary(production, popen=popen)
    pending = launch_cash_flow_runtime_shadow_canary(
        {**production, "status": "pending", "pending_count": 1, "sent_count": 4},
        popen=popen,
    )

    assert launched == CanaryLaunchResult(
        status="launched",
        packet_id=PACKET_ID,
        canary_id=canary_identity(PACKET_ID),
        process_id=42,
    )
    assert pending.status == "not_terminal"
    assert production == original
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command[1:3] == ["-m", "app.jobs.cash_flow_shadow_canary"]
    assert kwargs["start_new_session"] is True
    assert kwargs["stdin"] is not None
    assert kwargs["stdout"] is not None
    assert kwargs["stderr"] is not None


def test_launcher_failure_and_job_wrapper_never_change_exit_path(
    canary_environment, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.jobs.ai_review as job

    _data_root, archive, _packet_path, _delivery_path = canary_environment
    production = _delivery("deterministic_fallback")
    delivery_path = archive / "delivery-result.json"
    delivery_path.write_text(json.dumps(production), encoding="utf-8")

    def fail_popen(*_args, **_kwargs):
        raise OSError("cannot spawn")

    result = launch_cash_flow_runtime_shadow_canary(production, popen=fail_popen)
    assert result.status == "launch_failed"
    receipt = json.loads(_receipt_path(archive).read_text())
    assert receipt["status"] == "LAUNCH_FAILED"
    assert receipt["production_influence_count"] == 0

    original = copy.deepcopy(production)
    monkeypatch.setattr(
        job,
        "launch_cash_flow_runtime_shadow_canary",
        lambda _value: (_ for _ in ()).throw(RuntimeError("canary failed")),
    )
    _launch_terminal_canaries([production])
    assert production == original


def test_fallback_canary_is_exactly_once_and_never_imports_telegram(
    canary_environment,
) -> None:
    _data_root, archive, packet_path, delivery_path = canary_environment
    fallback = _delivery("deterministic_fallback")
    delivery_path.write_text(json.dumps(fallback), encoding="utf-8")
    before = (_sha(packet_path), _sha(delivery_path))

    first = run_cash_flow_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="deterministic_fallback",
        expected_delivery_sha256=_sha(delivery_path),
        now=NOW,
    )
    second = run_cash_flow_runtime_shadow_canary(
        PACKET_ID,
        delivery_mode="deterministic_fallback",
        expected_delivery_sha256=_sha(delivery_path),
        now=NOW,
    )

    assert first.status == "COMPLETE_PASS"
    assert second.status == "DUPLICATE_SKIPPED"
    assert (_sha(packet_path), _sha(delivery_path)) == before
    root = archive / "cash-flow-shadow-canary" / canary_identity(PACKET_ID)
    assert len(list(root.glob("attempts/*"))) == 1
    source = Path(
        "app/services/cash_flow_runtime_shadow_canary_service.py"
    ).read_text(encoding="utf-8")
    assert "notification_service" not in source
    assert "TelegramNotifier" not in source
