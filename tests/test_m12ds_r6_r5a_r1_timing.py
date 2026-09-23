import asyncio
from datetime import date, datetime, timedelta
import json
from types import SimpleNamespace

import httpx
import pytest

from scripts import m12ds_r6_r5_cutoff_observer as observer
from scripts.m12ds_r6_r4_kiwoom_finality import cutoff_attempt
from tests.test_m12ds_r6_r4_kiwoom_finality import daily, mutate_payload, universe
from tests.test_m12ds_r6_r5_close_ownership import sample_three

SLOT = datetime.fromisoformat("2026-09-25T08:05:00+09:00")


def install_clock(monkeypatch, at, *, early_returns=(), suspend=False, stall=False):
    state = SimpleNamespace(now=at, elapsed=0.0, sleeps=[], early=list(early_returns))

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return state.now.astimezone(tz)

    async def sleep(seconds):
        assert 0 < seconds <= 1.0
        state.sleeps.append(seconds)
        state.elapsed += seconds
        target = state.now + timedelta(seconds=seconds)
        if stall:
            return
        if state.early and target >= SLOT:
            state.now = SLOT - timedelta(milliseconds=state.early.pop(0))
        elif suspend and target >= SLOT and state.now < SLOT:
            state.now = SLOT + timedelta(minutes=1, milliseconds=1)
        else:
            state.now = target

    monkeypatch.setattr(observer, "datetime", Clock)
    monkeypatch.setattr(observer, "monotonic", lambda: state.elapsed)
    monkeypatch.setattr(observer.asyncio, "sleep", sleep)
    return state


@pytest.mark.parametrize("early", [(3,), (1, 1, 1, 1)])
def test_early_wake_rechecks_before_first_request(monkeypatch, tmp_path, early):
    state = install_clock(monkeypatch, SLOT - timedelta(seconds=1), early_returns=early)
    calls = []

    async def fetch(client, token, item):
        assert state.now >= SLOT
        calls.append(state.now)
        return daily(at=state.now.isoformat())

    monkeypatch.setattr(observer, "fetch", fetch)

    async def run():
        assert await observer.wait_until_slot(SLOT)
        assert not calls
        return await observer.sample(
            None, None, [dict(symbol="SPY", mode="adjusted")], tmp_path, cutoff=SLOT
        )

    collected, errors = asyncio.run(run())
    assert not errors and len(collected) == len(calls) == 1
    assert calls[0] == SLOT
    assert len(state.sleeps) == len(early) + 2  # Initial wait, rechecks, unchanged pacing.
    assert state.sleeps[-1] == 0.6


@pytest.mark.parametrize(
    "offset, expected", [(0, True), (30, True), (59.999, True), (60, False), (61, False)]
)
def test_arrival_has_no_tolerance_or_backfill(monkeypatch, offset, expected):
    state = install_clock(monkeypatch, SLOT + timedelta(seconds=offset))
    assert asyncio.run(observer.wait_until_slot(SLOT)) is expected
    assert not state.sleeps


def test_suspend_past_minute_does_not_collect(monkeypatch):
    state = install_clock(monkeypatch, SLOT - timedelta(seconds=1), suspend=True)
    assert asyncio.run(observer.wait_until_slot(SLOT)) is False
    assert state.now > SLOT + timedelta(minutes=1)


def test_stalled_wall_clock_has_finite_wait_budget(monkeypatch):
    state = install_clock(monkeypatch, SLOT - timedelta(seconds=1), stall=True)
    assert asyncio.run(observer.wait_until_slot(SLOT)) is False
    assert sum(state.sleeps) == 61


def test_response_crossing_minute_still_fails_strict_validation():
    routes, envelopes = universe()
    for symbol in envelopes:
        envelopes[symbol] = daily(symbol, at="2026-09-23T08:05:59+09:00")
    envelopes["SPY"]["received_at"] = "2026-09-23T08:06:00+09:00"
    with pytest.raises(ValueError, match="not_actual_configured_minute"):
        cutoff_attempt(envelopes, routes, cutoff="2026-09-23T08:05:00+09:00")


@pytest.mark.parametrize("scenario", ["normal", "suspend", "provider_failure", "post_wait_suspend"])
def test_four_window_loop_keeps_exact_requests_and_no_retry(monkeypatch, tmp_path, scenario):
    import app.config
    import app.providers.kiwoom_rest_client

    state = install_clock(
        monkeypatch,
        SLOT - timedelta(minutes=1),
        early_returns=(3, 1, 1),
        suspend=scenario == "suspend",
    )
    routes, _ = universe()
    frozen = observer.plan(date(2026, 9, 25), routes)
    calls, auth, timeouts = [], [], []

    class Client:
        def __init__(self, **kwargs):
            timeouts.append(kwargs)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    class Owner:
        def __init__(self, **kwargs):
            assert kwargs["max_retries"] == 0
            self.base_url = "https://api.kiwoom.com"

        async def _access_token(self, client):
            auth.append(1)
            return "synthetic-only"

    async def fetch(client, token, item):
        assert state.now.hour == 8 and state.now.minute in (5, 10, 15, 20)
        calls.append((state.now, item))
        if scenario == "provider_failure" and len(calls) == 1:
            raise httpx.ReadTimeout("synthetic-only failure")
        q, raw, adj = sample_three(item["symbol"], at=state.now.isoformat(), older=True)
        for e in (raw, adj):
            mutate_payload(
                e,
                lambda p: [
                    r.update(dt=d)
                    for r, d in zip(p["result_list"], ("20260924", "20260923"), strict=True)
                ],
            )
        return dict(quote=q, raw=raw, adjusted=adj)[item["mode"]]

    monkeypatch.setattr(
        app.config,
        "Settings",
        lambda **kw: SimpleNamespace(
            kiwoom_app_key="synthetic",
            kiwoom_secret_key="synthetic",
            kiwoom_rest_base_url="https://api.kiwoom.com",
        ),
    )
    monkeypatch.setattr(app.providers.kiwoom_rest_client, "KiwoomRestClient", Owner)
    monkeypatch.setattr(observer.httpx, "AsyncClient", Client)
    monkeypatch.setattr(observer, "fetch", fetch)
    if scenario == "post_wait_suspend":
        original_wait = observer.wait_until_slot

        async def suspended_wait(slot):
            ready = await original_wait(slot)
            if slot == SLOT:
                state.now = SLOT + timedelta(minutes=1)
            return ready

        monkeypatch.setattr(observer, "wait_until_slot", suspended_wait)
    output = tmp_path / "observed"
    asyncio.run(
        observer.observe(
            date(2026, 9, 25),
            routes,
            output,
            mode="cutoff",
            env_file=tmp_path / "absent",
            frozen_plan=frozen,
        )
    )
    result = json.loads((output / "result.json").read_text())
    assert len(result["receipts"]) == 4 and len(auth) == 1
    assert result["retries"] == result["model_calls"] == 0
    assert timeouts == [dict(base_url="https://api.kiwoom.com", timeout=10, trust_env=False)]
    missed = scenario in ("suspend", "post_wait_suspend")
    assert len(calls) == (84 if missed else 112)
    for minute in (5, 10, 15, 20):
        items = [item for at, item in calls if at.minute == minute]
        assert items == ([] if missed and minute == 5 else frozen["requests"])
    first = result["receipts"][0]
    if missed:
        assert first["status"] == "MISSED_NOT_BACKFILLED"
        assert json.loads((output / "0805-receipt.json").read_text()) == first
    elif scenario == "provider_failure":
        assert first["status"] == "INCOMPLETE" and first["collected"] == 27
        assert sum(r["collected"] for r in result["receipts"]) == 111
    else:
        assert all(r["collected"] == 28 for r in result["receipts"])
        assert all(r["review"]["availability"]["count"] == 22 for r in result["receipts"])
        assert all(r["review"]["final_decision"] is None for r in result["receipts"])
