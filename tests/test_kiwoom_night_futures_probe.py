import asyncio
from datetime import date
import json

import httpx

from app.jobs.probe_kiwoom_night_futures import (
    GATEWAY_CAPABILITY_PATH,
    KiwoomFinalNightClose,
    documented_capability,
    fetch_gateway_capability,
    parse_gateway_capability_payload,
    reconcile_with_krx,
)
from app.jobs.probe_krx_night_futures import KrxNightFutureObservation
from app.macro.providers.registry import macro_provider_statuses


def _final_observation(
    product: str = "KOSPI200",
    *,
    contract_code: str = "KR4101V60003",
    night_close: float = 429.0,
    regular_close: float = 428.0,
    final_price_semantics: str = "session_final_event",
    session: str = "night",
    status: str = "final",
) -> dict[str, object]:
    point_change = night_close - regular_close
    return {
        "product": product,
        "vendor_symbol": "vendor-front-month-symbol",
        "contract_code": contract_code,
        "contract_month": "2026-09",
        "expiry": "2026-09-10",
        "session_date": "2026-08-13",
        "session": session,
        "status": status,
        "final_price_semantics": final_price_semantics,
        "observed_at": "2026-08-14T05:59:58+09:00",
        "regular_close": regular_close,
        "night_close": night_close,
        "point_change": point_change,
        "change_pct": point_change / regular_close * 100,
        "tick_size": 0.05,
        "volume": 12345,
        "subscription_started_at": "2026-08-13T17:58:00+09:00",
        "first_tick_at": "2026-08-13T18:00:00+09:00",
        "last_tick_at": "2026-08-14T05:59:58+09:00",
        "session_finalized_at": "2026-08-14T06:00:03+09:00",
        "persisted_at": "2026-08-14T06:00:04+09:00",
        "available_for_digest_at": "2026-08-14T06:00:04+09:00",
        "digest_deadline_at": "2026-08-14T07:50:00+09:00",
    }


def _krx_observation(**updates: object) -> KrxNightFutureObservation:
    regular_close = float(updates.get("regular_close", 428.0))
    night_close = float(updates.get("night_close", 429.0))
    point_change = night_close - regular_close
    values: dict[str, object] = {
        "product": "KOSPI200",
        "contract_code": "KR4101V60003",
        "contract_name": "코스피200 F 202609 야간",
        "maturity": "2026-09",
        "source_date": date(2026, 8, 13),
        "session_date": date(2026, 8, 13),
        "reference_date": date(2026, 8, 12),
        "regular_close": regular_close,
        "night_close": night_close,
        "reference_price": regular_close,
        "current_session_price": night_close,
        "point_change": point_change,
        "change_pct": point_change / regular_close * 100,
        "night_source_record_id": "2026-08-13:NIGHT:KR4101V60003",
        "reference_source_record_id": "2026-08-12:DAY:KR4101V60003",
    }
    values.update(updates)
    return KrxNightFutureObservation.model_validate(values)


def _product_evidence(
    product: str,
    *,
    supported: bool = True,
    observation: dict[str, object] | None = None,
) -> dict[str, object]:
    if not supported:
        return {
            "product": product,
            "product_supported": False,
        }
    return {
        "product": product,
        "product_supported": True,
        "symbol_discovery": True,
        "recent_month_identified": True,
        "realtime_subscription": True,
        "night_session_ticks": True,
        "closing_phase_ticks": True,
        "final_close_determined": True,
        "session_identity_verified": True,
        "contract_identity_verified": True,
        "observation": observation or _final_observation(product),
    }


def _payload(products: list[dict[str, object]]) -> dict[str, object]:
    return {
        "contract_version": "1",
        "api_family": "openapi_plus",
        "platform": "Windows OCX gateway",
        "captured_at": "2026-08-14T06:00:05+09:00",
        "products": products,
    }


def test_documented_capability_is_fail_closed_by_product() -> None:
    result = documented_capability()
    products = {item.product: item for item in result.products}

    assert products["KOSPI200"].capability == "partial"
    assert products["KOSDAQ150"].capability == "unsupported"
    assert result.production_primary_enabled is False
    assert result.production_decision == "not_enabled"


def test_gateway_capability_is_evaluated_independently_for_each_product() -> None:
    result = parse_gateway_capability_payload(
        _payload(
            [
                _product_evidence("KOSPI200"),
                _product_evidence("KOSDAQ150", supported=False),
            ]
        )
    )
    products = {item.product: item for item in result.products}

    assert products["KOSPI200"].capability == "supported"
    assert products["KOSDAQ150"].capability == "unsupported"
    assert result.production_primary_enabled is False
    assert result.production_decision == "shadow_candidate"


def test_missing_product_evidence_is_unknown_not_inferred_from_other_product() -> None:
    result = parse_gateway_capability_payload(_payload([_product_evidence("KOSPI200")]))
    products = {item.product: item for item in result.products}

    assert products["KOSPI200"].capability == "supported"
    assert products["KOSDAQ150"].capability == "unknown"


def test_rest_gateway_cannot_override_official_derivatives_product_scope() -> None:
    payload = _payload([_product_evidence("KOSPI200")])
    payload["api_family"] = "rest"

    result = parse_gateway_capability_payload(payload)

    assert {item.capability for item in result.products} == {"unsupported"}
    assert result.production_decision == "not_enabled"


def test_regular_session_or_unverified_last_tick_cannot_be_final_close() -> None:
    regular = _final_observation(session="regular")
    last_tick = _final_observation(final_price_semantics="last_tick")

    regular_result = parse_gateway_capability_payload(
        _payload([_product_evidence("KOSPI200", observation=regular)])
    )
    last_tick_result = parse_gateway_capability_payload(
        _payload([_product_evidence("KOSPI200", observation=last_tick)])
    )

    assert regular_result.status == "ok"
    assert last_tick_result.status == "ok"
    assert regular_result.products[0].capability == "partial"
    assert last_tick_result.products[0].capability == "partial"
    assert regular_result.production_primary_enabled is False
    assert last_tick_result.production_primary_enabled is False


def test_invalid_product_evidence_does_not_discard_other_verified_product() -> None:
    invalid_kosdaq = _final_observation("KOSDAQ150", session="regular")

    result = parse_gateway_capability_payload(
        _payload(
            [
                _product_evidence("KOSPI200"),
                _product_evidence("KOSDAQ150", observation=invalid_kosdaq),
            ]
        )
    )
    products = {item.product: item for item in result.products}

    assert products["KOSPI200"].capability == "supported"
    assert products["KOSDAQ150"].capability == "partial"


def test_observation_for_different_product_cannot_prove_support() -> None:
    wrong_observation = _final_observation("KOSDAQ150")

    result = parse_gateway_capability_payload(
        _payload([_product_evidence("KOSPI200", observation=wrong_observation)])
    )

    assert result.products[0].product == "KOSPI200"
    assert result.products[0].capability == "partial"


def test_expired_or_mismatched_contract_is_rejected() -> None:
    observation = _final_observation()
    observation["contract_month"] = "2026-12"

    result = parse_gateway_capability_payload(
        _payload([_product_evidence("KOSPI200", observation=observation)])
    )

    assert result.status == "ok"
    assert result.products[0].capability == "partial"

    expired = _final_observation()
    expired["contract_month"] = "2026-07"
    expired["expiry"] = "2026-07-09"
    expired_result = parse_gateway_capability_payload(
        _payload([_product_evidence("KOSPI200", observation=expired)])
    )

    assert expired_result.products[0].capability == "partial"


def test_close_that_is_not_persisted_before_digest_deadline_is_rejected() -> None:
    observation = _final_observation()
    observation["digest_deadline_at"] = "2026-08-14T05:59:00+09:00"

    result = parse_gateway_capability_payload(
        _payload([_product_evidence("KOSPI200", observation=observation)])
    )

    assert result.status == "ok"
    assert result.products[0].capability == "partial"
    assert result.production_primary_enabled is False


def test_gateway_probe_fetches_once_without_authentication_or_query_secrets() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_payload([_product_evidence("KOSPI200")]))

    result = asyncio.run(
        fetch_gateway_capability(
            "http://127.0.0.1:9911",
            transport=httpx.MockTransport(handler),
        )
    )

    assert result.status == "ok"
    assert len(requests) == 1
    assert requests[0].url.path == GATEWAY_CAPABILITY_PATH
    assert not requests[0].url.query
    assert "authorization" not in requests[0].headers


def test_gateway_url_rejects_embedded_credentials_and_query_strings() -> None:
    credentials = asyncio.run(fetch_gateway_capability("http://user:pass@localhost:9911"))
    query = asyncio.run(fetch_gateway_capability("http://localhost:9911?token=secret"))

    assert credentials.status == "unavailable"
    assert query.status == "unavailable"
    assert credentials.production_primary_enabled is False
    assert query.production_primary_enabled is False


def test_sensitive_gateway_fields_are_rejected_without_value_leakage() -> None:
    secret = "must-never-be-reported"
    payload = _payload([_product_evidence("KOSPI200")])
    payload["access_token"] = secret

    result = parse_gateway_capability_payload(payload)
    rendered = json.dumps(result.model_dump(mode="json"), ensure_ascii=False)

    assert result.status == "unavailable"
    assert result.reason == "gateway_payload_contains_sensitive_fields"
    assert secret not in rendered


def test_reconciliation_requires_same_product_contract_maturity_and_session() -> None:
    kiwoom = KiwoomFinalNightClose.model_validate(_final_observation())
    krx = _krx_observation(contract_code="DIFFERENT")

    result = reconcile_with_krx(kiwoom, krx)

    assert result.result == "not_comparable"
    assert result.close_difference is None


def test_reconciliation_uses_contract_tick_size_tolerance() -> None:
    kiwoom = KiwoomFinalNightClose.model_validate(_final_observation())
    within_tick = _krx_observation(night_close=429.05)
    mismatch = within_tick.model_copy(
        update={"night_close": 429.2, "point_change": 1.2, "change_pct": 1.2 / 428 * 100}
    )

    assert reconcile_with_krx(kiwoom, within_tick).result == "within_tick"
    assert reconcile_with_krx(kiwoom, mismatch).result == "mismatch"


def test_reconciliation_rejects_regular_close_basis_mismatch() -> None:
    kiwoom = KiwoomFinalNightClose.model_validate(_final_observation())
    krx = _krx_observation(regular_close=427.0)

    assert reconcile_with_krx(kiwoom, krx).result == "mismatch"


def test_kiwoom_is_not_registered_as_a_production_macro_provider() -> None:
    names = {item.name for item in macro_provider_statuses()}

    assert "kiwoom_night_futures" not in names
