"""Concrete offline aggregate callbacks. Unimplemented owners remain blocked."""

import asyncio
from collections import Counter
from datetime import date, datetime
import hashlib
import json
from math import isfinite

from pydantic import TypeAdapter

from app.macro.providers.base import MacroProviderResult
from app.macro.providers.market import MARKET_SYMBOLS, normalize_market_observation
from app.services.market_session import us_market_session
from app.services.unified_aggregate_receipt import VerifiedAggregate
from app.services.unified_persisted_projection import _fingerprints
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_composition import OwnerAdapter, OwnerProjection, SourceRole
from app.services.unified_source_observer import OhlcvRead
from app.services.unified_source_policy import UnifiedSourcePolicy


def us_market_aggregate_owner(*, role: SourceRole, source_url: str,
                              policy: UnifiedSourcePolicy) -> OwnerAdapter:
    if (role.market, role.provider, role.acquisition_class, role.basis) != (
            "us", "ohlcv_analyst", "ATTEMPT_FRESH", "adjusted_close"):
        raise ValueError("us_market_owner_role_mismatch")
    if not source_url.endswith("/ohlcv") or "?" in source_url or "@" in source_url:
        raise ValueError("us_market_source_url_invalid")

    def replay(graph: VerifiedAggregate, cutoff: datetime) -> OwnerProjection:
        receipt = graph.receipt
        if (receipt.owner, receipt.role, receipt.provider, receipt.market, receipt.symbol,
                receipt.basis, receipt.session) != (
                role.owner, role.key, role.provider, role.market, role.symbol, role.basis, role.session):
            raise ValueError("us_market_aggregate_identity_mismatch")
        if cutoff.utcoffset() is None or receipt.received_at > cutoff:
            raise ValueError("us_market_cutoff_mismatch")
        session = us_market_session(cutoff).latest_completed_regular_session_date
        plan = json.loads(graph.plan)
        reads = [OhlcvRead.model_validate(r) for r in plan.get("reads", [])]
        if (tuple(r.symbol for r in reads) != tuple(MARKET_SYMBOLS)
                or len(graph.child_receipts) != len(reads) or len(graph.child_bodies) != len(reads)
                or role.session != session.isoformat()):
            raise ValueError("whole_us_market_plan_required")
        observations = []
        for read, child, body in zip(reads, graph.child_receipts, graph.child_bodies, strict=True):
            if (read.market, read.provider, read.period, read.adjusted, read.session_date) != (
                    "us", "ohlcv_analyst", "daily", True, session):
                raise ValueError("us_market_read_basis_mismatch")
            if child.get("request") != {"method": "GET", "route": "/ohlcv", "params": read.params}:
                raise ValueError("us_market_child_outside_plan")
            if (child.get("provider") != role.provider or child.get("read") != read.model_dump(mode="json")
                    or child.get("role") != read.role or child.get("symbol") != read.symbol
                    or child.get("outcome") != "HTTP_RESPONSE" or body is None
                    or not 200 <= child.get("http_status", 0) < 300):
                raise ValueError("us_market_successful_child_required")
            payload = json.loads(body)
            policy.check_lineage(payload)
            if (payload.get("resolved_symbol", {}).get("code") != read.symbol
                    or payload.get("meta", {}).get("provider") != (read.response_provider or role.provider)
                    or payload.get("meta", {}).get("adjusted") is not True):
                raise ValueError("us_market_response_identity_mismatch")
            observation = normalize_market_observation(payload, symbol=read.symbol, source_url=source_url)
            if (observation is None or not isfinite(observation.value) or observation.value <= 0
                    or observation.observed_at.date() != session or observation.observed_at > cutoff):
                raise ValueError("us_market_observation_ineligible")
            observations.append(observation)
        value = TypeAdapter(MacroProviderResult).dump_python(
            MacroProviderResult(provider=role.provider, observations=observations), mode="json")
        return OwnerProjection(value, role.provider, role.market, role.symbol, role.basis,
                               role.session, True, None, receipt.received_at)

    def reject_single(_raw, _cutoff):
        raise ValueError("market_requires_transitive_receipt")

    return OwnerAdapter("us-market-child-replay-v1", digest({"files": _fingerprints(
        "app/services/unified_aggregate_owners.py", "app/macro/providers/market.py",
        "app/services/market_session.py"), "source_url": source_url,
        "role": role.model_dump(mode="json")}), reject_single, replay)


def kiwoom_aggregate_owner(*, role: SourceRole, observed_at: datetime, max_pages: int,
                           max_requests_per_page: int, policy: UnifiedSourcePolicy,
                           consumer_complete: bool = False) -> OwnerAdapter:
    from app.providers.kiwoom_rest_client import KiwoomCallStats, KiwoomRestResponse, payload_sha256
    from app.services.kiwoom_kr_market_context_service import (
        KiwoomKrMarketContextService, kiwoom_market_reads,
    )

    if (role.market, role.provider, role.acquisition_class) != ("kr", "kiwoom_rest", "ATTEMPT_FRESH"):
        raise ValueError("kiwoom_aggregate_role_mismatch")
    session = date.fromisoformat(role.session)
    reads = kiwoom_market_reads(session_date=session, max_pages=max_pages,
                               max_requests_per_page=max_requests_per_page)
    if observed_at.utcoffset() is None:
        raise ValueError("source_timezone_required")
    if consumer_complete and role.key != "kr_local_indices_sectors_breadth":
        raise ValueError("consumed_page_owner_scope_mismatch")

    def replay(graph: VerifiedAggregate, cutoff: datetime) -> OwnerProjection:
        receipt = graph.receipt
        if (receipt.owner, receipt.role, receipt.market, receipt.provider, receipt.symbol,
                receipt.basis, receipt.session) != (
                role.owner, role.key, role.market, role.provider, role.symbol, role.basis, role.session):
            raise ValueError("kiwoom_aggregate_identity_mismatch")
        if cutoff.utcoffset() is None or not observed_at <= receipt.requested_at <= receipt.received_at <= cutoff:
            raise ValueError("kiwoom_aggregate_observation_time_mismatch")
        plan = json.loads(graph.plan)
        if plan.get("reads") != [r.model_dump(mode="json") for r in reads] or plan.get("session") != role.session:
            raise ValueError("kiwoom_whole_owner_plan_required")
        if not len(graph.child_receipts) == len(graph.child_bodies) == len(graph.accepted_pages):
            raise ValueError("kiwoom_exact_page_artifacts_required")
        counts = Counter()
        for child, body, page in zip(graph.child_receipts, graph.child_bodies, graph.accepted_pages, strict=True):
            matches = [r for r in reads if r.key == child.get("read_key")]
            if len(matches) != 1 or page is None or body is None:
                raise ValueError("kiwoom_page_not_planned_or_accepted")
            read = matches[0]
            counts[read.key] += 1
            request = child["request"]
            if ((request.get("method"), request.get("route"), request.get("api_id"), request.get("body"))
                    != ("POST", read.endpoint, read.api_id, read.body)
                    or child.get("provider") != "kiwoom_rest" or child.get("role") != read.role
                    or child.get("session") != role.session or counts[read.key] > read.max_pages
                    or child.get("outcome") != "HTTP_RESPONSE" or not 200 <= child.get("http_status", 0) < 300):
                raise ValueError("kiwoom_child_request_mismatch")
            policy.check_lineage(json.loads(body))
        if set(counts) != {r.key for r in reads}:
            raise ValueError("kiwoom_required_read_set_missing")
        if consumer_complete:
            from app.services.kiwoom_consumed_page_contract import qualify
            qualify(graph, observed_at=observed_at)

        class ReplayClient:
            source_observer = None
            stats = KiwoomCallStats(requests=0, successes=0, failures=0, retries=0)

            def __init__(self):
                self.index = 0

            async def request(self, *, endpoint, api_id, body, continuation=False, next_key=""):
                if self.index >= len(graph.child_receipts):
                    raise ValueError("kiwoom_owner_extra_read")
                original = graph.child_receipts[self.index]["request"]
                page = graph.accepted_pages[self.index]
                payload = json.loads(graph.child_bodies[self.index])
                # Cursor hashes already form a verified chain. Opaque replay
                # handles carry those hashes without reconstructing a secret.
                cursor = next_key or hashlib.sha256(b"").hexdigest()
                if ((endpoint, api_id, body, continuation, cursor) != (
                    original["route"], original["api_id"], original["body"],
                    original["continuation"], original["cursor_sha256"])):
                    raise ValueError("kiwoom_owner_read_order_or_cursor_mismatch")
                if int(payload.get("return_code", 0)) != 0:
                    raise ValueError("kiwoom_provider_failure")
                self.index += 1
                return KiwoomRestResponse(api_id, payload, page["continuation"],
                    page["next_cursor_sha256"] if page["continuation"] else "", payload_sha256(payload))

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise ValueError("offline_sync_replay_required")
        client = ReplayClient()
        result = asyncio.run(KiwoomKrMarketContextService(client, max_pages=max_pages,
            completed_session_only=plan.get("completed_session_only", False)).collect(
            session_date=session, observed_at=observed_at))
        if client.index != len(graph.child_receipts):
            raise ValueError("kiwoom_owner_unconsumed_children")
        value = result.cross_section.model_dump(mode="json")
        if role.key == "kr_local_indices_sectors_breadth":
            value = {k: value[k] for k in ("indices", "sectors", "breadth", "breadth_by_scope")}
        elif role.key == "kr_market_investor_flows" and not result.audit.blocked_concentration_markets:
            value = {k: value[k] for k in ("market_flows", "concentration")}
        else:
            raise ValueError("kiwoom_role_output_ineligible")
        return OwnerProjection(value, role.provider, role.market, role.symbol, role.basis,
                               role.session, True, None, observed_at)

    def reject_single(_raw, _cutoff):
        raise ValueError("kiwoom_requires_transitive_receipt")

    fingerprint = digest({"files": _fingerprints("app/services/unified_aggregate_owners.py",
        "app/services/kiwoom_kr_market_context_service.py", "app/providers/kiwoom_rest_client.py"),
        "observed_at": observed_at.isoformat(), "reads": [r.model_dump(mode="json") for r in reads]})
    if consumer_complete:
        from app.services.kiwoom_consumed_page_contract import CONTRACT
        fingerprint = digest({"base": fingerprint, "completion": _fingerprints(
            "app/services/kiwoom_consumed_page_contract.py")})
        return OwnerAdapter(CONTRACT, fingerprint, reject_single, replay, observed_at)
    return OwnerAdapter("kiwoom-child-owner-replay-v1", fingerprint, reject_single, replay)
