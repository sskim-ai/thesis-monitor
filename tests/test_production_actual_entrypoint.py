"""Actual launcher qualification; fakes are limited to wire, clock and temp state."""
import asyncio
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

from tests.production_entrypoint_wire_fixture import (
    FixtureClock, RawWire, deploy_native, install_boundaries, make_settings,
)


CASES = list(range(1, 16))
STAGES = ["MARKET", "CORE", "A", "B", "B2", "VALIDATE", "RENDER", "DELIVER"]
REQUIRED_RUNTIME = {
    ("app.jobs.unified_market_snapshot", "main"),
    ("app.services.production_adapter_factory", "build_production_adapter"),
    ("app.services.production_source_backend", "collect"),
    ("app.services.production_source_backend", "project"),
    ("app.services.production_source_plan", "build_request_plan"),
    ("app.services.production_source_plan", "admit_request_plan"),
    ("app.services.production_source_seal", "seal_collection"),
    ("app.services.production_source_projection", "replay_source_owners"),
    ("app.services.production_monitoring_session", "build"),
    ("app.services.production_model_transport", "request"),
    ("app.services.production_b2_execution", "authorize_b2"),
    ("app.services.production_b2_execution", "execute_b2"),
    ("app.services.production_message_renderer", "stock_message"),
    ("app.services.production_delivery", "deliver"),
}


def read(path):
    return json.loads(path.read_bytes())


def fingerprint(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def save_receipt(receipt, market, case):
    if path := os.environ.get("REV63D_RECEIPT_DIRECTORY"):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        (path / f"{market}-{case:02d}.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False))


@pytest.mark.parametrize("market", ["us", "kr"])
@pytest.mark.parametrize("case", CASES, ids=lambda case: f"case{case:02d}")
def test_actual_launcher_composition(tmp_path, monkeypatch, market, case):
    if market == "us" and case == 13:
        reason = "KIS production preflight is KR-only; US sources do not require KIS."
        save_receipt(dict(status="PROVEN_NOT_APPLICABLE", market=market, case=case,
            reason=reason, external_network_calls=0), market, case)
        return
    root = tmp_path.resolve()
    clock = FixtureClock(market, case)
    native = deploy_native(root)
    settings = make_settings(root, native, monkeypatch, market, case)
    wire = RawWire(clock)
    launcher, trace, calls, exceptions = install_boundaries(monkeypatch, settings, clock, wire)
    argv = ["unified_market_snapshot", "--market", market]
    monkeypatch.setattr(sys, "argv", argv)
    run = root / "data/unified-snapshot-runs" / f"snapshot-{market}-{clock.now().date()}"
    receipt = dict(market=market, case=case, root=str(root), status="FAIL",
        launcher="app.jobs.unified_market_snapshot.main", launcher_request=argv,
        adapter="production-v1:build_production_adapter:CanonicalProductionSourceBackend",
        external_network_calls=0, permitted_fake_boundaries=["raw_wire", "model_wire", "clock", "temp_state"])
    trace.start()
    try:
        exit_code = 0
        try:
            asyncio.run(launcher.main())
        except SystemExit as exc:
            exit_code = exc.code
        terminal = read(run / "terminal.json")
        expected = "FAILED" if case in {5, 13, 14} else "SKIPPED" if case == 6 else "SUCCESS"
        assert terminal["status"] == expected, (exceptions, terminal.get("error_chain"))
        assert exit_code == (1 if expected == "FAILED" else 0)
        assert terminal["normal_messages_sent"] is False
        attempts = terminal["attempts"]
        assert len([a for a in attempts if "attempt_id" in a]) == {
            2: 2, 3: 3, 4: 2, 5: 3, 6: 0, 13: 0, 14: 3}.get(case, 1)
        if case == 4:
            assert [a["status"] for a in attempts] == ["INCOMPLETE", "WINDOW_MISSED", "ELIGIBLE"]
            assert not any(":15:" in value for value in clock.waits)
            first, missed, final = attempts
            first_start = datetime.fromisoformat(first["started_at"])
            first_end = datetime.fromisoformat(first["completed_at"])
            final_start = datetime.fromisoformat(final["started_at"])
            assert first_end - first_start == timedelta(minutes=6)
            assert first_start < datetime.fromisoformat(missed["slot"]) < first_end < final_start
            assert final_start == first_start + timedelta(minutes=10)
            assert clock.waits == [first_start.isoformat(), final_start.isoformat()]
            assert first["errors"] == ["collection_exception"]
            assert first["error_type"] == "ValueError"
            assert first["attempt_id"].endswith("-attempt-1")
            assert final["attempt_id"].endswith("-attempt-3")
            assert not any("attempt-2" in p.name for p in run.iterdir())
            assert wire.crossed_slot_denials
            assert all(row["http_status"] == 400 for row in wire.crossed_slot_denials)
            assert len(wire.child_launches) == 2
            assert len({row["pid"] for row in wire.child_launches}) == 2
            assert [row["attempt_id"] for row in wire.child_launches] == [first["attempt_id"], final["attempt_id"]]
            assert all(not row["already_live_native_pids"] for row in wire.child_launches)
            assert [row["at"] for row in wire.child_launches] == [first_start.isoformat(), final_start.isoformat()]
            assert wire.model_launches and all(datetime.fromisoformat(at) >= final_start
                                               for at in wire.model_launches)
            assert all(p.returncode is not None for p in wire.native_processes)
            receipt["crossed_slot"] = dict(cycle_id=terminal["run_id"], initial_slot=first["slot"],
                first_attempt=first, missed_window=missed, third_attempt=final,
                missed_slot_count=1, max_concurrent_market_attempts=1,
                concurrency_proof="Disjoint real attempt receipts plus no surviving native worker at next spawn",
                no_immediate_catch_up=True, next_permitted_slot=final["slot"],
                next_actual_attempt_time=final["started_at"], child_launches=wire.child_launches,
                raw_nontransient_denials=wire.crossed_slot_denials,
                model_wire_start_times=wire.model_launches, token_failure_used=False,
                common_incomplete_owner="UnifiedMarketRun.run existing collection_exception -> INCOMPLETE",
                external_calls=0)
        if case in {5, 13, 14}:
            assert len(list(run.glob("failure-notification-intent.json"))) == 1
            assert not (run / "render").exists()
        if case in {6, 13, 14}:
            assert not wire.calls
        if case == 14:
            assert len(wire.plan_denials) == 3
            assert all(row["reason"] == "undeclared_provider_or_route"
                       and row["wire_calls_at_rejection"] == 0 for row in wire.plan_denials)
            receipt["negative_provider_preflight"] = dict(provider="alpha_vantage",
                status="REJECTED_BEFORE_DISPATCH", wire_calls=0, real_key_used=False,
                rejections=wire.plan_denials)
        if expected == "SUCCESS":
            assert [s["stage"] for s in terminal["stage_receipts"]] == STAGES
            assert all(s["status"] == "PASS" for s in terminal["stage_receipts"])
            assert terminal["delivery_receipt"]["mode"] == "DRY_RUN"
            delivered = terminal["delivery_receipt"]["receipts"]
            assert len(delivered) == (15 if market == "us" else 9)
            assert all(d["status"] == "DRY_RUN_NOT_SENT" for d in delivered)
            assert len({d["dedup_sha256"] for d in delivered}) == len(delivered)
            accepted = [read(p) for p in run.glob("b2/*/accepted.json")]
            assert len(accepted) == (14 if market == "us" else 8)
            outputs = [row["output"]["new_buyer_shadow"] for row in accepted]
            b2_inputs = [read(p)["provider_request"]["input"] for p in run.glob("b2/*/request.json")]
            snapshot = read(run / "snapshot.json")
            envelope = snapshot["collection"]["production_envelope"]
            assert {d["generation_id"] for d in delivered} == {envelope["generation_id"]}
            assert {r["generation_id"] for r in accepted} == {envelope["generation_id"]}
            if case in {7, 8}:
                night = [r["owner_result"]["canonical_optional_ownership"] for r in envelope["resolutions"]
                         if "canonical_optional_ownership" in r["owner_result"]]
                assert len(night) == 1
                assert night[0]["coverage_resolved"] and night[0]["current_consumer_eligible_count"] == 0
                assert night[0]["state"].startswith("UNAVAILABLE_")
                receipt["optional_night"] = night[0]
            if case == 9:
                evaluations = [i["valuation_evaluability"] for i in b2_inputs]
                assert any(v["blocked_metric_refs"] and v["usable_valuation_metric_refs"]
                           and v["evaluability_state"] == "EVALUABLE" for v in evaluations)
                assert all(not set(v["blocked_metric_refs"]) & set(v["usable_valuation_metric_refs"])
                           for v in evaluations)
                receipt["valuation_evaluability"] = evaluations
            if case == 10:
                assert all(o["valuation_context"]["state"] == "UNRESOLVED" for o in outputs)
                assert all(o["valuation_context"]["all_metrics_unusable_proof_ref"] for o in outputs)
            if case == 11:
                assert all(o["new_buyer"] == "AVOID" and o["active_risk_refs"] for o in outputs)
            if case == 12:
                timing_state = "UNRESOLVED" if market == "us" else "WAIT_FOR_ZONE"
                source_stocks = snapshot["collection"]["packet"]["monitoring_input"]["stocks"]
                ownership = {}
                if market == "us":
                    assert len(source_stocks) == 14
                    for ticker, stock in source_stocks.items():
                        price = stock["completed_session_current_price"]
                        technical = stock["packet"]["stocks"][0]["technical_context"]
                        assert price["source_role"] == "usa20590_completed_daily"
                        assert price["adjustment_basis"] == "regular_close"
                        assert price["generation_id"] == envelope["generation_id"]
                        assert not price["technical_compatibility"]["technical_target_injection_allowed"]
                        assert technical["last_completed_bar"]["D"] < price["target_session"]
                        assert not technical["quality"]["D"]["usable_for_current_reasoning"]
                        ownership[ticker] = dict(current_price_owner=price["source_role"],
                            target_session=price["target_session"],
                            last_completed_technical_bar=technical["last_completed_bar"]["D"],
                            newest_unconfirmed_row_not_promoted=True)
                subject_outputs = {p.parent.name: read(p)["output"]["new_buyer_shadow"]
                                   for p in run.glob("b2/*/accepted.json")}
                pairs = {ticker: value for ticker, value in subject_outputs.items()
                         if value["new_buyer"] == "ATTRACTIVE"
                         and value["timing_context"]["state"] == timing_state}
                assert pairs, {t: (o["new_buyer"], o["timing_context"]) for t, o in subject_outputs.items()}
                messages = {m["message_id"]: m for m in read(run / "render/response.json")["output"]["messages"]}
                for ticker, value in pairs.items():
                    text = messages[ticker]["text"]
                    assert "신규 매수자: ATTRACTIVE" in text
                    assert "진입 시점: " + timing_state in text
                    if market == "us":
                        assert value["timing_context"]["reason"] in {
                            "PRICE_ZONE_IDENTITY_BASIS_OR_VALUE_UNRESOLVED", "NO_ELIGIBLE_SELECTED_CANDIDATE"}
                    else:
                        assert value["timing_context"]["reason"] == "EXACT_SELECTED_ZONE_RELATION"
                        assert value["timing_context"]["evidence_refs"]
                        evidence = {e["ref_id"]: e for e in source_stocks[ticker]["evidence_packet"]["evidence"]}
                        zones = [evidence[ref] for ref in value["timing_context"]["evidence_refs"]
                                 if evidence[ref]["label"] == "chart_support_zone"]
                        assert zones
                        assert all(z["source_ref"].startswith("stock.fact_catalog.chart:structure:") for z in zones)
                        ownership[ticker] = dict(derived_zone_refs=[z["ref_id"] for z in zones],
                            derived_zone_sha256=[hashlib.sha256(json.dumps(z, sort_keys=True).encode()).hexdigest()
                                                for z in zones], user_price_rule_promoted=False)
                receipt["timing_capability"] = dict(semantic_applicability=True,
                    classification="TIMING_APPLICABLE_TYPED_UNRESOLVED_SUPPORTED" if market == "us"
                        else "TIMING_APPLICABLE_RESOLVED_AND_UNRESOLVED_SUPPORTED",
                    accepted_pairs={t: dict(new_buyer=o["new_buyer"], timing=o["timing_context"],
                        rendered_content_sha256=hashlib.sha256(messages[t]["text"].encode()).hexdigest())
                        for t, o in pairs.items()}, no_new_buyer_downgrade=True,
                    current_price_authority="usa20590" if market == "us" else "accepted_KR_adjusted_close",
                    source_ownership=ownership, new_source_role=False)
            messages = read(run / "render/response.json")["output"]["messages"]
            assert not any(heading in m["text"] for m in messages for heading in
                           ("기존 등록 가격 규칙", "데이터 주의", "다음 확인", "미확인"))
            if case == 15:
                before = {str(p.relative_to(run)): fingerprint(p) for p in run.rglob("*") if p.is_file()}
                wire_before = list(wire.calls)
                asyncio.run(launcher.main())
                assert wire.calls == wire_before
                assert {str(p.relative_to(run)): fingerprint(p) for p in run.rglob("*") if p.is_file()} == before
            receipt["dry_run_delivery"] = terminal["delivery_receipt"]
        receipt.update(status="PASS_VALID_TYPED_UNRESOLVED" if case == 12 and market == "us" else "PASS",
            terminal_state=terminal["status"], waits=clock.waits,
            stage_receipts=terminal["stage_receipts"], terminal=fingerprint(run / "terminal.json"))
    finally:
        trace.stop()
        missing_runtime = sorted(REQUIRED_RUNTIME - calls) if receipt.get('terminal_state') == 'SUCCESS' else []
        forbidden_runtime = sorted((module, function) for module, function in calls
                                   if 'blind' in module or 'rev59' in module)
        receipt['dynamic_closure'] = dict(missing=missing_runtime, forbidden=forbidden_runtime)
        if missing_runtime or forbidden_runtime:
            receipt['status'] = 'FAIL'
        receipt.update(wire=wire.calls, executed=sorted(calls), exceptions=exceptions,
            wire_fixture=fingerprint(Path(__file__).with_name("production_entrypoint_wire_fixture.py")),
            source_plan_files={str(p.relative_to(run)): fingerprint(p)
                               for p in run.glob("*/source/production-frozen-source-plan.json")},
            source_seal_files={str(p.relative_to(run)): fingerprint(p) for p in run.glob("*/source-seal.json")},
            timing_top=sorted(trace.timings, key=lambda row: row["total_seconds"], reverse=True)[:30],
            artifacts={str(p.relative_to(run)): fingerprint(p) for p in run.rglob("*") if p.is_file()})
        save_receipt(receipt, market, case)
    if receipt["terminal_state"] == "SUCCESS":
        assert REQUIRED_RUNTIME <= calls, REQUIRED_RUNTIME - calls
    assert not any("blind" in module or "rev59" in module for module, _ in calls)
