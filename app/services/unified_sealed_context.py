"""Replay publication context from explicit sealed bytes, without acquisition."""
import asyncio
from datetime import datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
from pydantic import TypeAdapter
from sqlmodel import SQLModel, Session, create_engine

from app.jobs.probe_krx_night_futures import fetch_live_probe, KST, KRX_FUTURES_DAILY_URL
from app.macro.providers.base import MacroProviderResult
from app.macro.providers.krx import materialize_night_probe
from app.services.unified_class_c_owners import project_canonical_catalog
from app.services.unified_persisted_owner_bridge import MODELS, project
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest


def replay_publications(*, documents, hashes, cutoff, policy):
    if set(documents) != set(hashes):
        raise ValueError("publication_exact_version_set_required")
    output = {}
    for name, raw in sorted(documents.items()):
        if sha256_bytes(raw) != hashes[name]:
            raise ValueError("publication_source_hash_mismatch")
        original = json.loads(raw)
        if original.get('contract') != 'unified-class-c-owner-projection-v1':
            raise ValueError("publication_projection_contract_required")
        role = original["role"]
        if role == 'canonical_cashflow_working_capital':
            current = project_canonical_catalog([r["record"] for r in original["records"]],
                cutoff=cutoff, policy=policy)
        else:
            engine = create_engine("sqlite://")
            try:
                SQLModel.metadata.create_all(engine, tables=[m.__table__ for m in MODELS.values()])
                with Session(engine) as session:
                    seen = set()
                    for row in original["records"]:
                        table, rid, record = row["table"], row["record_id"], row["record"]
                        if table not in MODELS or str(record.get("id")) != rid or (table, rid) in seen:
                            raise ValueError("publication_record_identity_mismatch")
                        seen.add((table, rid))
                        policy.check_lineage(record)
                        if "raw_payload" in record:
                            policy.check_lineage(json.loads(record["raw_payload"]))
                        session.add(MODELS[table].model_validate(record))
                    session.commit()
                    ticker = original.get('ticker') or (
                        original["records"][0]["record"].get("ticker", "*") if original["records"] else "*")
                    current = project(session, role=role, ticker=ticker, cutoff=cutoff, policy=policy)
            finally:
                engine.dispose()
        # Raw rows, original timestamps and denial reasons stay with the owner.
        if current != original:
            raise ValueError("publication_current_owner_replay_mismatch:" + name)
        output[name] = {"source_sha256": hashes[name], "projection": current}
    return output


def replay_night(*, receipts, bodies, body_hashes, observed_at, run_id, acquisition_id,
                 expected_value_sha256, policy, run_started_at, acquisition_cutoff,
                 history_receipts=None):
    policy.require("krx_night_futures")
    if not receipts or set(bodies) != set(body_hashes):
        raise ValueError("night_exact_source_set_required")
    if any(sha256_bytes(b) != body_hashes[n] for n, b in bodies.items()):
        raise ValueError("night_source_hash_mismatch")
    used = set()
    history_receipts = history_receipts or []
    history_dates = []
    for row in [*history_receipts, *receipts]:
        if (row['run_id'] != run_id or row['acquisition_id'] != acquisition_id
                or row['provider'] != 'krx_night_futures'
                or row['outcome'] != 'HTTP_RESPONSE' or row['http_status'] != 200
                or row['artifact_sha256'] != body_hashes[row['artifact']]
                or row['artifact'] in used):
            raise ValueError("night_original_receipt_mismatch")
        used.add(row['artifact'])
        request = row['request']
        if (request['method'] != 'GET' or request['route'] != KRX_FUTURES_DAILY_URL
                or set(request['params']) != {'basDd'}):
            raise ValueError('night_original_request_mismatch')
        query_date = datetime.strptime(request['params']['basDd'], '%Y%m%d').date()
        if query_date > observed_at.astimezone(KST).date():
            raise ValueError('night_future_query_date')
        if row in history_receipts:
            history_dates.append(query_date)
        start, end = (datetime.fromisoformat(row[k]) for k in ('requested_at', 'received_at'))
        if (any(t.utcoffset() is None for t in (start, end, observed_at, run_started_at, acquisition_cutoff))
                or not run_started_at <= observed_at <= acquisition_cutoff
                or not run_started_at <= start <= end <= acquisition_cutoff):
            raise ValueError("night_original_receipt_time_mismatch")
    if used != set(bodies):
        raise ValueError("night_unused_source_body")
    probe_dates = [datetime.strptime(r['request']['params']['basDd'], '%Y%m%d').date() for r in receipts]
    if history_dates and (history_dates != sorted(set(history_dates)) or max(history_dates) >= min(probe_dates)):
        raise ValueError('night_history_order_or_probe_overlap')

    class CapturedTransport(httpx.AsyncBaseTransport):
        index = 0

        async def handle_async_request(self, request):
            if self.index >= len(receipts):
                raise ValueError("night_undeclared_request")
            row = receipts[self.index]
            self.index += 1
            if (request.method != row['request']['method'] or request.method != 'GET'
                    or str(request.url.copy_with(query=None)) != row['request']['route']
                    or row['request']['route'] != KRX_FUTURES_DAILY_URL
                    or dict(request.url.params) != row['request']['params']):
                raise ValueError("night_original_request_mismatch")
            return httpx.Response(row['http_status'], content=bodies[row['artifact']], request=request)

    async def run():
        transport = CapturedTransport()
        probe = await fetch_live_probe(run_date=observed_at.astimezone(KST).date(),
            observation_time=observed_at, api_key="offline-no-credential",
            transport=transport, max_lookback_days=7)
        if transport.index != len(receipts):
            raise ValueError("night_receipts_not_fully_consumed")
        # live_source describes verified original acquisition, not this replay.
        probe.live_source = True
        with TemporaryDirectory(prefix="sealed-night-replay-") as tmp:
            from app.services.krx_night_history_service import persist_krx_response
            for row in history_receipts:
                persist_krx_response(root=Path(tmp),
                    query_date=datetime.strptime(row['request']['params']['basDd'], '%Y%m%d').date(),
                    fetched_at=datetime.fromisoformat(row['received_at']), http_status=row['http_status'],
                    raw_body=bodies[row['artifact']])
            result = TypeAdapter(MacroProviderResult).dump_python(
                materialize_night_probe(probe, history_directory=Path(tmp)), mode="json")
        if digest(result) != expected_value_sha256:
            raise ValueError("night_owner_value_mismatch")
        output = {"value": result, "value_sha256": digest(result),
            "original_receipts": receipts, "source_hashes": body_hashes,
            "original_run_id": run_id, "original_acquisition_id": acquisition_id,
            "observed_at": observed_at.isoformat(), "network_calls": 0}
        if history_receipts:
            output['history_receipts'] = history_receipts
        return output
    return asyncio.run(run())
