from copy import deepcopy
from datetime import date, timedelta
import json

import pytest

from app.services.completed_session_current_price import project_completed_price, validate_completed_price
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_run_artifacts import sha256_bytes
from tests.rev10_cohort_fixtures import plan_and_securities


def price_inputs(ticker="CORZ", later=None, old=None):
    plan, securities = plan_and_securities()
    read = next(r for r in plan.reads if r.subject == ticker and r.role == "adjusted_daily")
    security = next(s for s in securities[read.market] if s["ticker"] == ticker)
    target = date.fromisoformat(read.latest_completed_session)
    row = dict(date=str(target), open=100, high=110, low=90, close=105, volume=10)
    rows = [row]
    if old is not None:
        rows.insert(0, dict(row, date=str(target - timedelta(days=1)), **old))
    if later is not None:
        rows.append(dict(row, date=str(target + timedelta(days=1)), **later))
    request = dict(method="POST", route=read.route, api_id=read.api_id,
        payload=dict(stk_cd=ticker, upd_stkpc_tp="1", stex_tp=read.exchange))
    receipt = dict(run_id=plan.run_id, acquisition_id=plan.acquisition_id,
        plan_sha256=digest(plan.model_dump(mode="json")), entry=read.model_dump(mode="json"),
        started_at=plan.frozen_at.isoformat(), completed_at=plan.frozen_at.isoformat(), status="CAPTURED",
        pages=[dict(provider="kiwoom", entry_id=read.entry_id, page_ordinal=1, request=request,
            request_sha256=digest(request), requested_at=plan.frozen_at.isoformat(),
            received_at=plan.frozen_at.isoformat(), artifact="raw", http_status=200)],
        normalized_artifact="rows")
    inputs = dict(plan=plan, read=read, receipt=receipt, security=security,
                  currency="USD" if read.market == "us" else "KRW")
    return bind_rows(inputs, rows)


def bind_rows(inputs, rows):
    artifacts = {"raw": encoded(dict(return_code=0, result_list=rows)), "rows": encoded(rows)}
    inputs["receipt"]["pages"][0]["source_sha256"] = sha256_bytes(artifacts["raw"])
    inputs["receipt"]["normalized_sha256"] = sha256_bytes(artifacts["rows"])

    def artifact(path, sha):
        assert sha256_bytes(artifacts[path]) == sha
        return artifacts[path]

    return dict(inputs, artifact_reader=artifact)


@pytest.mark.parametrize("ticker", ["CORZ", "000660"])
@pytest.mark.parametrize("later", [{}, {"high": 101}, {"low": 108}])
def test_exact_target_ignores_only_out_of_dependency_rows(ticker, later):
    inputs = price_inputs(ticker, later, {"high": 98})
    before = deepcopy(inputs["receipt"])
    projection = project_completed_price(**inputs)
    assert projection.availability == "AVAILABLE"
    assert projection.current_price == 105
    assert projection.price_as_of == inputs["read"].latest_completed_session
    assert not projection.source_integrity["valid"]
    assert projection.target_integrity["valid"]
    assert [r["scope"] for r in projection.out_of_scope_rows] == ["OUT_OF_SCOPE_HISTORICAL_SESSION", "OUT_OF_SCOPE_LATER_SESSION"]
    assert projection.out_of_scope_rows[-1]["anomalies"]
    assert inputs["receipt"] == before
    assert validate_completed_price(projection.model_dump(mode="json"), **inputs) == projection


@pytest.mark.parametrize("mutation,reason", [
    ("missing", "TARGET_ROW_MISSING"), ("duplicate", "TARGET_ROW_DUPLICATE_OR_CONFLICT"),
    ("conflict", "TARGET_ROW_DUPLICATE_OR_CONFLICT"), ("invalid", "TARGET_ROW_INTEGRITY_FAILED"),
    ("unknown_scope", "UNKNOWN_ROW_SESSION_SCOPE"),
])
def test_fail_closed_no_older_fallback(mutation, reason):
    inputs = price_inputs(old={})
    rows = json.loads(inputs["artifact_reader"]("rows", inputs["receipt"]["normalized_sha256"]))
    if mutation == "missing":
        rows.pop()
    elif mutation in {"duplicate", "conflict"}:
        rows.append(dict(rows[-1], close=101 if mutation == "conflict" else 105))
    elif mutation == "invalid":
        rows[-1]["high"] = 99
    else:
        rows[0]["date"] = "unknown"
    p = project_completed_price(**bind_rows(inputs, rows))
    assert p.availability == "UNAVAILABLE" and reason in p.denial_reasons
    assert p.current_price is p.price_as_of is p.selected_row is None


@pytest.mark.parametrize("field,value", [("ticker", "IBM"), ("canonical_security_id", "wrong"), ("exchange", "NYSE")])
def test_wrong_security_rejected(field, value):
    inputs = price_inputs()
    inputs["security"][field] = value
    with pytest.raises(ValueError, match="security_currency_basis"):
        project_completed_price(**inputs)


@pytest.mark.parametrize("key,value", [("currency", "KRW"), ("adjustment_basis", "unadjusted")])
def test_wrong_currency_basis_rejected(key, value):
    inputs = price_inputs()
    inputs[key] = value
    with pytest.raises(ValueError, match="security_currency_basis"):
        project_completed_price(**inputs)


def test_wrong_generation_or_target_and_date_relabel_rejected():
    inputs = price_inputs()
    inputs["receipt"]["run_id"] = "different"
    with pytest.raises(ValueError, match="prior_run"):
        project_completed_price(**inputs)
    inputs = price_inputs()
    read = inputs["read"].model_copy(update={"latest_completed_session": "2026-09-21"})
    inputs["plan"] = inputs["plan"].model_copy(update={"reads": tuple(read if r == inputs["read"] else r for r in inputs["plan"].reads)})
    inputs["read"] = read
    with pytest.raises(ValueError, match="frozen_calendar_target"):
        project_completed_price(**inputs)
    inputs = price_inputs()
    p = project_completed_price(**inputs).model_dump(mode="json")
    p["price_as_of"] = "2026-09-23"
    p["projection_sha256"] = digest({k: v for k, v in p.items() if k != "projection_sha256"})
    with pytest.raises(ValueError, match="inconsistent|source_binding"):
        validate_completed_price(p, **inputs)


def test_later_bad_row_never_restores_technical_features(tmp_path):
    from tests.rev8_source_fixtures import fresh_inputs
    from app.services.fresh_financial_stock_owner import assemble_fresh_stock
    from app.services.unified_stock_anomaly_scope import materialize_source_components
    from tests.test_unified_stock_owner import freeze_hashes
    plan, _ = plan_and_securities()
    item = fresh_inputs(tmp_path, "CORZ", plan=plan, completed_price=False)
    tech = item["technical_inputs"]
    roles = {r: json.loads(tech["artifacts"][r + ".json"]) for r in tech["receipts"]}
    target = roles["adjusted_daily"][-1]
    roles["adjusted_daily"].append(dict(target, date="2026-09-23", high=1))
    role = "adjusted_daily"
    raw, normalized = encoded(dict(return_code=0, result_list=roles[role])), encoded(roles[role])
    tech["artifacts"].update({role + ".body": raw, role + ".json": normalized})
    tech["receipts"][role]["normalized_sha256"] = sha256_bytes(normalized)
    tech["receipts"][role]["pages"][0]["source_sha256"] = sha256_bytes(raw)
    components = materialize_source_components(ticker="CORZ", market="us", cutoff=date(2026, 9, 22),
        observed_at=plan.frozen_at.isoformat(), roles=roles)
    tech["components"] = components
    from tests.completed_price_fixtures import source
    from app.services.completed_price_state import bind_source
    security = item['financial_inputs']['plan']['security']
    close_source, artifacts = source(plan, security, value=target['close'])
    item["technical_inputs"] = bind_source(freeze_hashes(tech), source=close_source,
        artifacts=artifacts, security=security)
    before = digest(components)
    result = assemble_fresh_stock(**item)
    assert result["status"] == "PASS"
    assert result["completed_session_current_price"]["current_price"] == target["close"]
    stock = result["packet"]["stocks"][0]
    assert stock["current_price_context"]["as_of_date"] == "2026-09-22"
    assert stock["current_valuation_view"]["price_session"] == "2026-09-22"
    assert not stock["technical_context"]["features"]["daily"]["facts"]
    assert digest(components) == before
