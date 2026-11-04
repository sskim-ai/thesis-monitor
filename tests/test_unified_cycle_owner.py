"""Synthetic backend events, never historical real registration certification."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from importlib.metadata import version

import pytest
from sqlalchemy import MetaData
from sqlmodel import Session, create_engine

from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.services.unified_cycle_owner import (
    CycleOwner,
    apply_cycle_owner,
    load_pinned_cycle_owner,
    policy_fingerprints,
    require_generation,
    revoke_cycle_owner,
)
from app.services.unified_local_seed_bridge import admit_pinned_local_seed
from app.services.unified_persisted_projection import project_local_seed
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_source_policy import UnifiedSourcePolicy

POLICY = UnifiedSourcePolicy(frozenset({"canonical_local", "sec_edgar", "local"}))
SOURCES = {}


def sample(
    market="us",
    ticker="UNSEEN",
    security_type="common_stock",
    *,
    at=None,
    cycle=None,
    activation_seconds=-900,
    cutoff_seconds=60,
    created_seconds=None,
):
    slot = datetime.fromisoformat(
        at or ("2026-09-26T08:10:00+09:00" if market == "us" else "2026-09-23T16:10:00+09:00")
    )
    cutoff = slot + timedelta(seconds=cutoff_seconds)
    activation = (slot + timedelta(seconds=activation_seconds)).astimezone(timezone.utc)
    target = (slot - timedelta(days=1)).date() if market == "us" else slot.date()
    first = cycle or slot.date()
    venue = "NASDAQ" if market == "us" else "KOSPI"
    engine = create_engine("sqlite://")
    schema = MetaData()
    for model in (Company, SecurityMaster, InvestmentThesis, WatchlistItem):
        table = model.__table__.to_metadata(schema)
        if model is WatchlistItem:
            table.c.registration_requested_at.nullable = True
    schema.create_all(engine)
    with Session(engine) as session:
        session.add(
            WatchlistItem(
                ticker=ticker,
                company_name="Fictional",
                exchange=venue,
                activated_at=activation,
                created_at=(
                    activation
                    if created_seconds is None
                    else (slot + timedelta(seconds=created_seconds)).astimezone(timezone.utc)
                ),
                first_eligible_session=first,
            )
        )
        session.add(
            SecurityMaster(
                ticker=ticker,
                company_name="Fictional",
                exchange=venue,
                country="US" if market == "us" else "KR",
                canonical_company_id="issuer:fictional",
                canonical_security_id="security:" + ticker,
                issuer_type=(
                    "foreign_private_issuer"
                    if security_type in {"adr", "ads"}
                    else "domestic_us"
                    if market == "us"
                    else "krx"
                ),
                security_type=security_type,
                identity_provider="sec_edgar" if market == "us" else "local",
                updated_at=activation,
                cik="1234" if market == "us" else None,
            )
        )
        session.add(
            InvestmentThesis(
                ticker=ticker,
                version=1,
                core_thesis="Synthetic configuration only",
                created_at=activation,
            )
        )
        session.add(
            Company(ticker=ticker, company_name="Fictional", exchange=venue, created_at=activation)
        )
        session.commit()
        # SQLite can retain a legacy NULL; never invent registration time.
        session.connection().exec_driver_sql(
            "UPDATE watchlistitem SET registration_requested_at=NULL"
        )
        session.commit()
        doc = project_local_seed(
            session, market=market, session_key=target.isoformat(), cutoff=cutoff, policy=POLICY
        )
        from app.services.minimal_class_c_export import COLUMNS

        source_rows = {
            table: [
                dict(row)
                for row in session.connection()
                .exec_driver_sql(
                    "SELECT " + ",".join('"' + c + '"' for c in columns) + ' FROM "' + table + '"'
                )
                .mappings()
            ]
            for table, columns in COLUMNS.items()
        }
    engine.dispose()
    SOURCES[digest(source_rows)] = encoded(source_rows)
    records = {r["table"]: r for role in doc["roles"].values() for r in role["records"]}
    event = dict(
        ticker=ticker,
        security_id="security:" + ticker,
        thesis_version=1,
        record_hashes={k: v["original_record_sha256"] for k, v in records.items()},
        original_cycle=first.isoformat(),
        mode="RECONCILER_DEFAULT",
        writer_at=activation.isoformat(),
        original_writer_event_sha256=digest("SYNTHETIC_ORIGINAL_WRITER_EVENT"),
    )
    freeze = dict(
        contract="class-c-cycle-run-session-owner-v1",
        generation_id="test-cycle-generation",
        source_generation_id="test-source-generation",
        source_export_sha256=digest(source_rows),
        source_projection_sha256=digest(doc),
        identity_policy_sha256=digest(sorted(POLICY.allowed_providers)),
        calendar_version=version("exchange-calendars"),
        target_session=target.isoformat(),
        source_cutoff=cutoff.isoformat(),
        cutoff=cutoff.isoformat(),
        market=market,
        scheduled_at=slot.isoformat(),
        scheduled_run_event_sha256=digest("SYNTHETIC_RUN_EVENT"),
        policy_fingerprints=policy_fingerprints(),
        events=[event],
    )
    return doc, freeze


def owner(freeze):
    return load_pinned_cycle_owner(
        encoded(freeze),
        expected_sha256=digest(freeze),
        source_rows=SOURCES[freeze["source_export_sha256"]],
        source_generation_id="test-source-generation",
        execution_generation_id="test-cycle-generation",
        policy=POLICY,
    )


def applied(doc, freeze):
    handle = owner(freeze)
    result = apply_cycle_owner(doc, original=doc, owner=handle)
    return handle, result


def admit(doc, handle):
    return admit_pinned_local_seed(
        encoded(doc),
        expected_sha256=digest(doc),
        market=doc["market"],
        session_key=doc["session"],
        cutoff=datetime.fromisoformat(doc["cutoff"]),
        subjects=doc["universe"]["eligible_subjects"],
        policy=POLICY,
        cycle_owner=handle,
    )


@pytest.mark.parametrize(
    "market,ticker,kind",
    [
        ("us", "NEWUS", "common_stock"),
        ("kr", "999999", "common_stock"),
        ("us", "NEWADS", "ads"),
        ("us", "NVDA", "common_stock"),
        ("kr", "035420", "common_stock"),
    ],
)
def test_same_contract_actual_projection_owner_and_canonical(market, ticker, kind, tmp_path):
    from types import SimpleNamespace
    from app.services.canonical_source_replay import current_local_seed

    doc, freeze = sample(market, ticker, kind)
    assert doc["roles"]["universe"]["eligible"] is False
    handle, result = applied(doc, freeze)
    assert result["denials"] == []
    assert result["cycle_owner_receipt"]["approved"] == [ticker]
    assert result["production_seed_qualified"] is False
    assert admit(result, handle) == result
    assert admit(result, handle) == result  # Same live invocation is idempotent.
    (tmp_path / "class-c").mkdir()
    (tmp_path / f"class-c/local-{market}.json").write_bytes(encoded(result))
    frozen = dict(
        generation_id=freeze["generation_id"],
        frozen_at=doc["cutoff"],
        sessions={market: doc["session"]},
        protected_input_hashes={f"class-c/local-{market}.json": digest(result)},
    )
    plan = SimpleNamespace(
        run_id=freeze["generation_id"],
        frozen_at=datetime.fromisoformat(doc["cutoff"]),
        reads=[SimpleNamespace(market=market, latest_completed_session=doc["session"])],
        universe={market: [ticker]},
    )
    assert current_local_seed(tmp_path, frozen, plan, market, POLICY, cycle_owner=handle) == result
    plan.run_id = frozen["generation_id"] = "different-generation"
    with pytest.raises(ValueError, match="execution_generation"):
        current_local_seed(tmp_path, frozen, plan, market, POLICY, cycle_owner=handle)


def test_activation_after_price_close_is_not_after_run_cutoff():
    doc, freeze = sample()
    _, result = applied(doc, freeze)
    close = datetime.fromisoformat(result["cycle_owner_receipt"]["calendar"]["completed_close"])
    watch = result["roles"]["universe"]["records"][0]["record"]
    assert (
        close
        < datetime.fromisoformat(watch["activated_at"]).replace(tzinfo=close.tzinfo)
        < datetime.fromisoformat(doc["cutoff"])
    )
    assert watch["first_eligible_session"] != doc["session"]
    assert result["roles"]["universe"]["eligible"]


@pytest.mark.parametrize(
    "market,instant,expected",
    [
        ("kr", "2026-09-23T16:04:59+09:00", "2026-09-23"),
        ("kr", "2026-09-23T16:05:00+09:00", "2026-09-24"),
        ("us", "2026-09-26T08:04:59+09:00", "2026-09-26"),
        ("us", "2026-09-26T08:05:00+09:00", "2026-09-27"),
        ("kr", "2026-09-23T23:59:59+09:00", "2026-09-24"),
        ("kr", "2026-09-24T00:00:00+09:00", "2026-09-24"),
    ],
)
def test_original_writer_boundaries_are_not_exchange_calendar(market, instant, expected):
    from app.services.onboarding_reconciler_service import _next_cycle_date

    assert _next_cycle_date(market, datetime.fromisoformat(instant)).isoformat() == expected


@pytest.mark.parametrize(
    "case",
    [
        "pin",
        "policy",
        "source_asof",
        "writer_future",
        "default_override",
        "default_date",
        "override_missing",
        "rows",
        "duplicate",
        "unissued",
        "revoked",
        "generation",
        "receipt",
        "lost_owner",
        "slot",
        "future_slot",
        "market",
        "session",
        "calendar_unavailable",
        "original_row",
        "security",
        "thesis",
        "cycle",
        "missing_event",
        "missing_thesis",
    ],
)
def test_actual_owner_fail_closed(case, monkeypatch):
    doc, freeze = sample()
    pin = digest(freeze)
    if case == "pin":
        freeze["events"][0]["security_id"] = "forged"
        with pytest.raises(ValueError, match="freeze_pin"):
            load_pinned_cycle_owner(
                encoded(freeze),
                expected_sha256=pin,
                source_rows=SOURCES[freeze["source_export_sha256"]],
                source_generation_id="test-source-generation",
                execution_generation_id="test-cycle-generation",
                policy=POLICY,
            )
        return
    if case in {
        "policy",
        "source_asof",
        "writer_future",
        "default_override",
        "default_date",
        "override_missing",
        "rows",
        "duplicate",
    }:
        event = freeze["events"][0]
        if case == "policy":
            freeze["policy_fingerprints"]["app/services/unified_runtime_v2.py"] = "0" * 64
        if case == "source_asof":
            freeze["source_cutoff"] = "2000-01-01T00:00:00+00:00"
        if case == "writer_future":
            event["writer_at"] = "2030-01-01T00:00:00+00:00"
        if case == "default_override":
            event["explicit_override"] = event["original_cycle"]
        if case == "default_date":
            event["original_cycle"] = "2000-01-01"
        if case == "override_missing":
            event["mode"] = "RECONCILER_EXPLICIT_OVERRIDE"
        if case == "rows":
            event["record_hashes"].pop("company")
        if case == "duplicate":
            freeze["events"] *= 2
        with pytest.raises(ValueError):
            owner(freeze)
        return
    if case == "slot":
        freeze["scheduled_at"] = "2026-09-26T08:05:00+09:00"
    if case == "future_slot":
        freeze["scheduled_at"] = "2026-09-26T08:15:00+09:00"
    if case == "missing_event":
        freeze["events"] = []
    handle = owner(freeze)
    if case == "unissued":
        handle = CycleOwner()
    if case == "revoked":
        revoke_cycle_owner(handle)
    if case == "generation":
        with pytest.raises(ValueError, match="generation"):
            require_generation(handle, "other")
        return
    if case == "calendar_unavailable":
        monkeypatch.setattr(
            "app.services.unified_cycle_owner._exchange_calendar",
            lambda _: (_ for _ in ()).throw(ValueError("unavailable")),
        )
    if case in {"receipt", "lost_owner"}:
        result = apply_cycle_owner(doc, original=doc, owner=handle)
        if case == "receipt":
            result["cycle_owner_receipt"]["source_export_sha256"] = "0" * 64
        with pytest.raises(ValueError):
            admit(result, handle if case == "receipt" else None)
        return
    original = deepcopy(doc)
    if case == "market":
        doc["market"] = "kr"
    if case == "session":
        doc["session"] = "2026-09-24"
    if case in {"original_row", "security", "thesis", "cycle", "missing_thesis"}:
        if case == "original_row":
            original["roles"]["universe"]["records"][0]["original_record_sha256"] = "0" * 64
        if case == "security":
            original["roles"]["security_identity"]["records"][0]["record"][
                "canonical_security_id"
            ] = "other"
        if case == "thesis":
            original["roles"]["stored_thesis_and_business_metadata"]["records"][0]["record"][
                "version"
            ] = 2
        if case == "cycle":
            original["roles"]["universe"]["records"][0]["record"]["first_eligible_session"] = (
                "2026-09-27"
            )
        if case == "missing_thesis":
            original["roles"]["stored_thesis_and_business_metadata"]["records"] = []
        for role in original["roles"].values():
            role["version"] = digest(role["records"])
    if case == "missing_event":
        result = apply_cycle_owner(doc, original=original, owner=handle)
        assert not result["roles"]["universe"]["eligible"]
        with pytest.raises(ValueError):
            admit(result, handle)
    else:
        with pytest.raises(ValueError):
            apply_cycle_owner(doc, original=original, owner=handle)


def test_documented_explicit_override_is_separate_from_default():
    doc, freeze = sample()
    freeze["events"][0].update(
        mode="RECONCILER_EXPLICIT_OVERRIDE", explicit_override=freeze["events"][0]["original_cycle"]
    )
    handle, result = applied(doc, freeze)
    assert admit(result, handle) == result


@pytest.mark.parametrize(
    "market,slot,session,close",
    [
        ("us", "2026-03-10T08:10:00+09:00", "2026-03-09", "20:00:00+00:00"),
        ("us", "2026-11-28T08:10:00+09:00", "2026-11-27", "18:00:00+00:00"),
        ("kr", "2026-03-03T16:10:00+09:00", "2026-03-03", "06:30:00+00:00"),
    ],
)
def test_dst_early_close_and_after_substitute_holiday(market, slot, session, close):
    doc, freeze = sample(market, at=slot)
    _, result = applied(doc, freeze)
    assert result["cycle_owner_receipt"]["calendar"]["target"] == session
    assert result["cycle_owner_receipt"]["calendar"]["completed_close"].endswith(close)


@pytest.mark.parametrize(
    "market,slot",
    [
        ("us", "2026-09-27T08:10:00+09:00"),
        ("us", "2026-11-27T08:10:00+09:00"),
        ("kr", "2026-03-02T16:10:00+09:00"),
        ("kr", "2026-09-25T16:10:00+09:00"),
    ],
)
def test_closed_day_is_not_a_new_scheduled_price_session(market, slot):
    from app.services.unified_market_run import target_session

    assert target_session(market, datetime.fromisoformat(slot)) is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("active", False),
        ("monitoring_requested", False),
        ("production_eligible", False),
        ("onboarding_state", "PENDING_ONBOARDING"),
        ("activated_at", None),
        ("activated_at", "2027-01-01T00:00:00+00:00"),
    ],
)
def test_config_only_new_subject_or_changed_activation_stays_denied(field, value):
    doc, freeze = sample(ticker="NVDA")
    watch = doc["roles"]["universe"]["records"][0]
    watch["record"][field] = value
    watch["original_record_sha256"] = digest(watch["record"])
    doc["roles"]["universe"]["version"] = digest(doc["roles"]["universe"]["records"])
    freeze["events"][0]["record_hashes"]["watchlistitem"] = watch["original_record_sha256"]
    with pytest.raises(ValueError, match="authenticated_original_records"):
        applied(doc, freeze)


@pytest.mark.parametrize(
    "field",
    [
        "source_generation_id",
        "generation_id",
        "calendar_version",
        "identity_policy_sha256",
        "source_projection_sha256",
    ],
)
def test_pinned_freeze_still_requires_backend_identity_and_dependency(field):
    _, freeze = sample()
    freeze[field] = "0" * 64
    with pytest.raises(ValueError):
        owner(freeze)


def test_actual_source_bytes_not_labels_or_original_equals_document():
    doc, freeze = sample()
    handle = owner(freeze)
    changed = deepcopy(doc)
    changed["roles"]["universe"]["records"][0]["record"]["activated_at"] = "2000-01-01T00:00:00"
    changed["roles"]["universe"]["version"] = digest(changed["roles"]["universe"]["records"])
    with pytest.raises(ValueError, match="authenticated_original_records"):
        apply_cycle_owner(changed, original=changed, owner=handle)
    with pytest.raises(ValueError, match="export_digest"):
        load_pinned_cycle_owner(
            encoded(freeze),
            expected_sha256=digest(freeze),
            source_rows=b"{}",
            source_generation_id="test-source-generation",
            execution_generation_id="test-cycle-generation",
            policy=POLICY,
        )


def test_stock_owner_repeated_local_consumption_requires_live_capability():
    from app.services.unified_stock_owner import _local

    doc, freeze = sample()
    handle, result = applied(doc, freeze)
    args = dict(
        market="us",
        session_key=doc["session"],
        cutoff=datetime.fromisoformat(doc["cutoff"]),
        ticker="UNSEEN",
        policy=POLICY,
    )
    assert _local(result, **args, cycle_owner=handle)["watchlistitem"]["ticker"] == "UNSEEN"
    assert _local(result, **args, cycle_owner=handle)["watchlistitem"]["ticker"] == "UNSEEN"
    with pytest.raises(ValueError, match="live_backend"):
        _local(result, **args)
    revoke_cycle_owner(handle)
    with pytest.raises(ValueError, match="live_backend"):
        _local(result, **args, cycle_owner=handle)


def test_membership_cutoff_not_scheduled_start_is_explicit_inherited_contract():
    doc, freeze = sample(activation_seconds=30)
    freeze["events"][0].update(
        mode="RECONCILER_EXPLICIT_OVERRIDE", explicit_override=freeze["events"][0]["original_cycle"]
    )
    handle, result = applied(doc, freeze)
    assert admit(result, handle) == result
    assert result["cycle_owner_receipt"]["membership_as_of"] == "FROZEN_RUN_CUTOFF"


def test_mixed_provenance_never_promotes_missing_subjects():
    import json
    from app.services.minimal_class_c_export import project_authorized_rows

    _, left = sample(ticker="FIRST")
    _, right = sample(ticker="SECOND")
    rows = json.loads(SOURCES[left["source_export_sha256"]])
    more = json.loads(SOURCES[right["source_export_sha256"]])
    for table, values in more.items():
        for record in values:
            record["id"] = 2
            rows[table].append(record)
    raw = encoded(rows)
    SOURCES[digest(rows)] = raw
    doc = project_authorized_rows(
        rows,
        market="us",
        session_key=left["target_session"],
        cutoff=datetime.fromisoformat(left["cutoff"]),
        policy=POLICY,
    )
    left.update(source_export_sha256=digest(rows), source_projection_sha256=digest(doc))
    handle, result = applied(doc, left)
    assert result["cycle_owner_receipt"]["approved"] == ["FIRST"]
    assert result["cycle_owner_receipt"]["denied"][0]["ticker"] == "SECOND"
    assert result["roles"]["universe"]["eligible"] is False
    with pytest.raises(ValueError):
        admit(result, handle)


def test_caller_cannot_erase_authenticated_noncycle_denial():
    doc, freeze = sample(created_seconds=120)
    handle = owner(freeze)
    assert any(d["reason"] == "universe_record_after_cutoff" for d in doc["denials"])
    doc["denials"] = [d for d in doc["denials"] if d["reason"] != "universe_record_after_cutoff"]
    doc["roles"]["universe"]["eligible"] = True
    result = apply_cycle_owner(doc, original=doc, owner=handle)
    assert any(d["reason"] == "universe_record_after_cutoff" for d in result["denials"])
    assert result["roles"]["universe"]["eligible"] is False
    with pytest.raises(ValueError):
        admit(result, handle)


def test_cross_midnight_membership_uses_frozen_cutoff_date():
    from datetime import date

    doc, freeze = sample(cutoff_seconds=57600, cycle=date(2026, 9, 27))
    freeze["events"][0].update(
        mode="RECONCILER_EXPLICIT_OVERRIDE", explicit_override=freeze["events"][0]["original_cycle"]
    )
    handle, result = applied(doc, freeze)
    assert result["cycle_owner_receipt"]["approved"] == ["UNSEEN"]
    assert result["cycle_owner_receipt"]["membership_as_of"] == "FROZEN_RUN_CUTOFF"
    assert admit(result, handle) == result
