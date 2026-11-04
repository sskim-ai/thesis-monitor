"""Original Class-C issuers over newly created TEST_ONLY_SYNTHETIC rows.

No live consent is represented. These are ordinary process-local issuer handles
used in an isolated test simulation, not a separate production test-grant type.
The caller must keep its permitted clock and finite I/O boundary installed for
the entire downstream use of the returned handles. Nothing is patched here.
"""

from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.services import minimal_class_c_export as exporter
from app.services import prospective_class_c_owner as prospective
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_stock_acquisition import UNIVERSE


TEST_ONLY = "TEST_ONLY_SYNTHETIC"
DIRECTORY = "ng20-test-only-class-c"


def _require(condition, reason):
    if not condition:
        raise ValueError("ng20_class_c_fixture_" + reason)


def _clock(cutoff):
    _require(isinstance(cutoff, datetime) and cutoff.utcoffset() is not None,
             "aware_cutoff_required")
    _require(exporter.datetime.now(timezone.utc) == cutoff
             and prospective._now() == cutoff, "caller_installed_capture_and_owner_clock_required")


def synthetic_security_records(cutoff):
    """Generic fictional identities, not assertions about the enrolled issuers.

Main may supply its own synthetic SecurityMaster records instead. Build source
plans from the returned fixture's persisted securities to retain exact identity.
"""
    return {
        ticker: SecurityMaster(
            ticker=ticker, company_name="Synthetic " + ticker,
            legal_name=TEST_ONLY + " " + ticker,
            canonical_company_id="synthetic-issuer-" + ticker,
            canonical_security_id="security-" + ticker,
            exchange="NASDAQ" if market == "us" else "KRX",
            country="US" if market == "us" else "KR",
            cik="1234" if market == "us" else None,
            corp_code="00123456" if market == "kr" else None,
            issuer_type="domestic_us" if market == "us" else "domestic_kr",
            security_type="common_stock", identity_quality="verified",
            identity_provider="sec_edgar" if market == "us" else "opendart",
            updated_at=cutoff,
        ).model_dump(mode="json")
        for market, tickers in UNIVERSE.items() for ticker in tickers
    }


def _new_database(tmp_path, securities, cutoff, clocks):
    root = Path(tmp_path)
    _require(root.is_absolute() and ".." not in root.parts, "absolute_temp_path_required")
    _require(not any(part.startswith(".env") or part.lower() in {
        ".git", "credentials", "secrets"} for part in root.parts), "protected_path_denied")
    _require(any(part in {"tmp", "temp"} or part.startswith("pytest-")
                 for part in root.parts), "caller_admitted_temp_directory_required")
    _require(not any(path.is_symlink() for path in (root, *root.parents)), "symlink_denied")
    _require(root.is_dir(), "existing_temp_directory_required")
    directory = root / DIRECTORY
    directory.mkdir(mode=0o700)  # Exclusive: never reopen a previous fixture DB.
    path = directory / (TEST_ONLY + ".sqlite3")
    with path.open("xb"):
        pass
    path.chmod(0o600)
    engine = create_engine("sqlite:///" + str(path))
    try:
        SQLModel.metadata.create_all(engine, tables=[m.__table__ for m in exporter.MODELS.values()])
        with Session(engine) as session:
            for market, tickers in UNIVERSE.items():
                for ticker in tickers:
                    security = securities[ticker]
                    session.add(security)
                    session.add(WatchlistItem(
                        ticker=ticker, company_name=security.company_name,
                        exchange=security.exchange, notes=TEST_ONLY,
                        active=True, monitoring_requested=True, onboarding_state="ACTIVE",
                        production_eligible=True, created_at=cutoff,
                        registration_requested_at=cutoff, activated_at=cutoff,
                        first_eligible_session=date.fromisoformat(clocks[market]["target"]),
                    ))
                    session.add(Company(
                        ticker=ticker, company_name=security.company_name,
                        exchange=security.exchange, industry=TEST_ONLY, created_at=cutoff,
                    ))
                    session.add(InvestmentThesis(
                        ticker=ticker, version=1, status="active", source=TEST_ONLY,
                        core_thesis=TEST_ONLY + ": configured business membership, not investment advice",
                        created_at=cutoff,
                    ))
            session.commit()
    finally:
        engine.dispose()
    identity = path.stat()
    _require(identity.st_nlink == 1, "database_hardlink_denied")
    return path, identity


def build_class_c_fixture(tmp_path, *, generation_id, source_generation_id, cutoff,
                          policy, securities=None):
    """Return one raw capture and original KR/US prospective projections.

``tmp_path`` must be a fresh caller-admitted test-temp directory. The caller
sets ``minimal_class_c_export.datetime.now`` and ``prospective_class_c_owner._now``
to this exact aware cutoff. This helper never adjusts clocks or receipt dates.
``securities`` is an optional exact-22 mapping of visibly synthetic records;
fresh DB primary keys replace supplied IDs, while canonical identities remain.
The returned raw/capture/handles and DB are test-local, not public artifacts.
Original issuer exceptions propagate without being converted into success.
"""
    _clock(cutoff)
    _require(isinstance(generation_id, str) and bool(generation_id)
             and isinstance(source_generation_id, str) and bool(source_generation_id),
             "explicit_generation_ids_required")
    subjects = tuple(t for tickers in UNIVERSE.values() for t in tickers)
    _require(len(subjects) == len(set(subjects)) == 22
             and len(UNIVERSE["kr"]) == 8 and len(UNIVERSE["us"]) == 14,
             "fixed_22_cohort_required")
    provided = synthetic_security_records(cutoff) if securities is None else securities
    _require(isinstance(provided, dict) and set(provided) == set(subjects), "exact_security_cohort_required")
    models = {}
    policy.require("canonical_local")
    for ticker in subjects:
        record = provided[ticker]
        record = record.model_dump() if isinstance(record, SecurityMaster) else dict(record)
        security = SecurityMaster.model_validate({**record, "id": None})
        _require(security.ticker == ticker and security.company_name.startswith(("Synthetic ", TEST_ONLY)),
                 "synthetic_security_identity_required")
        at = security.updated_at
        _require(at is not None and (at.replace(tzinfo=timezone.utc) if at.tzinfo is None else at) <= cutoff,
                 "security_after_cutoff")
        policy.require(security.identity_provider)
        models[ticker] = security
    clocks = {market: prospective.completed_clock(market, cutoff) for market in UNIVERSE}
    path, identity = _new_database(tmp_path, models, cutoff, clocks)
    event_id = TEST_ONLY + ":NG20:" + generation_id
    permission = exporter.ExportPermission(
        event_id=event_id, approved=True, database=path,
        device=identity.st_dev, inode=identity.st_ino, subjects=subjects,
    )
    simulated_message = dict(
        kind=TEST_ONLY, event_id=event_id, source_generation_id=source_generation_id,
        generation_id=generation_id, subjects=list(subjects),
        statement="Isolated test simulation for a newly created synthetic DB only; no actual operator consent, private read, model dispatch, or production grant.",
    )
    decision = prospective.ApprovalDecision(
        event_id=event_id, user_message_sha256=digest(simulated_message), approved=True,
        effective_at=cutoff - timedelta(seconds=1), expires_at=cutoff + timedelta(minutes=50),
        subjects=subjects,
    )
    approval = prospective.record_backend_approval(decision)
    try:
        before_sha = sha256(path.read_bytes()).hexdigest()
        capture = exporter.capture_authorized_class_c(permission)
        raw, receipt = exporter.captured_private_snapshot(capture)
        _require(sha256(path.read_bytes()).hexdigest() == before_sha, "capture_changed_database")
        _require(datetime.fromisoformat(receipt["cutoff"]) == cutoff, "capture_clock_mismatch")
        rows = json.loads(raw)
        _require(set(rows) == set(exporter.MODELS) and all(
            len(values) == 22 and {row["ticker"] for row in values} == set(subjects)
            for values in rows.values()), "incomplete_original_capture")
        _require(receipt["total_changes"] == 0 and not receipt["denied_queries"]
                 and receipt["query_only"] is True and receipt["sqlite_mode"] == "ro",
                 "original_readonly_capture_required")
        owners, projections, originals, projection_bytes = {}, {}, {}, {}
        for market, tickers in UNIVERSE.items():
            originals[market] = exporter.project_captured_export(
                capture, market=market, session_key=clocks[market]["target"], policy=policy)
            owner, document = prospective.issue_prospective_owner(
                approval=approval, capture=capture, market=market,
                source_generation_id=source_generation_id, generation_id=generation_id,
                policy=policy, purpose=prospective.SCOPE,
            )
            _require(set(document["universe"]["eligible_subjects"]) == set(tickers)
                     and not document["denials"] and all(r["eligible"] for r in document["roles"].values()),
                     "original_owner_projection_ineligible:" + market)
            _require(document["production_seed_qualified"] is False, "production_seed_unexpected")
            owners[market], projections[market] = owner, document
            projection_bytes[market] = encoded(document)
        _clock(cutoff)
    except BaseException:
        prospective.revoke_approval(approval)
        raise
    return dict(
        kind=TEST_ONLY, permission=permission, approval=approval, approval_decision=decision,
        simulated_approval_event=simulated_message, capture=capture, raw=raw, capture_receipt=receipt,
        owners=owners, projections=projections, original_projections=originals,
        projection_bytes=projection_bytes,
        protected_input_hashes={"class-c/local-" + m + ".json": sha256(b).hexdigest()
                                for m, b in projection_bytes.items()},
        securities={r["ticker"]: r for r in rows["securitymaster"]},
        sessions={m: c["target"] for m, c in clocks.items()},
        diagnostics=dict(
            kind=TEST_ONLY, class_c_issuance={m: "ISSUED" for m in owners},
            table_counts={t: len(v) for t, v in rows.items()},
            raw_sha256=sha256(raw).hexdigest(), capture_receipt_sha256=digest(receipt),
            approval_event=event_id, scope="MEMBERSHIP_ONLY_NOT_D01_D02",
            native_manual_positive="NOT_ATTEMPTED", production_authority=False,
            clock="CALLER_INSTALLED_EXACT_CAPTURE_AND_OWNER_CLOCK", B2="OFF",
        ),
    )
