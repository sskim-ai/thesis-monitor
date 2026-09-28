"""Declared historical KRX bytes -> existing probe/history owner, offline only.

The transitive receipt uses original KRX receipt children, not fabricated HTTP
receipts. The live aggregate verifier intentionally cannot admit this graph.
"""

from datetime import date, datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

import httpx
from pydantic import Field, TypeAdapter, model_validator

from app.jobs.probe_krx_night_futures import KRX_FUTURES_DAILY_URL, KST, _rows, fetch_live_probe
from app.macro.providers.base import MacroProviderResult
from app.macro.providers.krx import materialize_night_probe
from app.services.krx_night_history_service import KrxNightRawResponseReceipt, persist_krx_response
from app.services.unified_aggregate_receipt import AggregateReceipt, ArtifactBinding
from app.services.unified_persisted_projection import _fingerprints
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_source_replay import read_bound_artifact
from app.services.night_futures_product_scope import PRODUCTS


OWNER = "krx-declared-history-offline-replay-v1"


class HistoricalKrxChild(ContractModel):
    child_id: str
    purpose: Literal["history", "probe"]
    query_date: date
    receipt: ArtifactBinding
    body: ArtifactBinding


class HistoricalKrxPlan(ContractModel):
    contract: Literal["krx-declared-history-offline-replay-v1"] = OWNER
    mode: Literal["HISTORICAL_OFFLINE_ONLY"] = "HISTORICAL_OFFLINE_ONLY"
    run_id: str = Field(min_length=1)
    source_archive_id: str = Field(min_length=1)
    source_manifest: ArtifactBinding
    source_manifest_generation_id: str
    source_probe: ArtifactBinding
    source_candidate: ArtifactBinding
    owner_fingerprint: str
    observed_at: datetime
    session_date: date
    products: tuple[str, ...] = PRODUCTS
    children: tuple[HistoricalKrxChild, ...]

    @model_validator(mode="after")
    def validate_identity(self):
        if self.products != PRODUCTS:
            raise ValueError("krx_configured_products_required")
        if self.observed_at.utcoffset() is None:
            raise ValueError("krx_aware_observation_required")
        ids = tuple(c.child_id for c in self.children)
        if not ids or len(set(ids)) != len(ids):
            raise ValueError("krx_duplicate_or_missing_child")
        identities = [(c.purpose, c.query_date) for c in self.children]
        if len(set(identities)) != len(identities):
            raise ValueError("krx_duplicate_child_date")
        history = [c.query_date for c in self.children if c.purpose == "history"]
        probes = [c.query_date for c in self.children if c.purpose == "probe"]
        if not history or not probes or history != sorted(history) or probes != sorted(probes, reverse=True):
            raise ValueError("krx_ordered_history_and_probe_required")
        if max(history) >= min(probes):
            raise ValueError("krx_history_probe_overlap")
        if tuple(c.purpose for c in self.children) != ("history",) * len(history) + ("probe",) * len(probes):
            raise ValueError("krx_history_before_probe_required")
        return self


def krx_replay_fingerprint() -> str:
    return digest(_fingerprints("app/services/unified_krx_history_replay.py",
        "app/jobs/probe_krx_night_futures.py", "app/macro/providers/krx.py",
        "app/services/night_futures_product_scope.py",
        "app/services/krx_night_history_service.py", "app/services/market_session.py"))


def _read(root, binding):
    return read_bound_artifact(root, binding.path, binding.sha256)


def native_candidate_projection(document: dict) -> dict:
    """Typed timestamp canonicalization; archive acquisition audit is not owner output."""
    if set(document) != {"provider", "observations", "events", "warnings", "telemetry"} or document["events"]:
        raise ValueError("krx_unowned_candidate_fields")
    value = TypeAdapter(MacroProviderResult).dump_python(
        TypeAdapter(MacroProviderResult).validate_python(document), mode="json")
    value["telemetry"].pop("month_history", None)
    return value


def _validate_inputs(root: Path, receipt: AggregateReceipt, plan: HistoricalKrxPlan):
    if (receipt.acquisition_class != "RUN_FRESH_ONCE" or receipt.attempt_id is not None
            or receipt.acquisition_id != "historical-replay-not-live"):
        raise ValueError("krx_offline_acquisition_identity_required")
    if (receipt.owner, receipt.provider, receipt.role, receipt.market, receipt.symbol,
            receipt.basis, receipt.session, receipt.run_id, receipt.validator_contract) != (
            OWNER, "krx_night_futures", "night_and_publication_context", "us", "*",
            "same_contract_night_dwm", plan.session_date.isoformat(), plan.run_id, OWNER):
        raise ValueError("krx_aggregate_identity_mismatch")
    if receipt.coverage != {"mode": plan.mode, "products": list(PRODUCTS), "live_qualified": False}:
        raise ValueError("krx_offline_receipt_required")
    if receipt.received_at != plan.observed_at or receipt.requested_at != plan.observed_at:
        raise ValueError("krx_aggregate_observation_mismatch")
    if plan.owner_fingerprint != krx_replay_fingerprint():
        raise ValueError("krx_owner_changed")
    manifest = json.loads(_read(root, plan.source_manifest))
    if (manifest.get("generation_id") != plan.source_manifest_generation_id
            or plan.source_archive_id != plan.source_manifest.sha256):
        raise ValueError("krx_source_generation_mismatch")
    if tuple(c.child_id for c in plan.children) != receipt.expected_child_ids:
        raise ValueError("krx_exact_history_set_required")
    original_probe = json.loads(_read(root, plan.source_probe))
    if (original_probe.get("live_source") is not True
            or datetime.fromisoformat(original_probe["fetched_at"]) != plan.observed_at
            or original_probe.get("source_date") != plan.session_date.isoformat()):
        raise ValueError("krx_original_probe_identity_mismatch")
    originals = []
    for child, aggregate_child in zip(plan.children, receipt.children, strict=True):
        if (child.receipt != aggregate_child.receipt or aggregate_child.normalization
                or aggregate_child.accepted_page):
            raise ValueError("krx_child_binding_mismatch")
        original = KrxNightRawResponseReceipt.model_validate_json(_read(root, child.receipt))
        body = _read(root, child.body)
        rows = _rows(json.loads(body))
        if (original.source_url != KRX_FUTURES_DAILY_URL or original.service != "fut_bydd_trd"
                or original.query_date != child.query_date or original.http_status != 200
                or original.raw_payload_sha256 != child.body.sha256
                or original.raw_size_bytes != len(body)
                or original.row_count != len(rows)
                or original.field_names != tuple(sorted({key for row in rows for key in row}))
                or original.raw_relative_path != f"raw/{child.query_date:%Y/%m/%d}/{child.body.sha256}.json"
                or original.fetched_at.utcoffset() is None or original.fetched_at > plan.observed_at):
            raise ValueError("krx_original_receipt_mismatch")
        if child.purpose == "probe":
            # Raw-store receipts retain their first acquisition time. The bound
            # probe independently records a later read of exactly those bytes.
            statuses = [s for s in original_probe["date_statuses"] if s["query_date"] == child.query_date.isoformat()]
            if len(statuses) != 1 or statuses[0]["raw_payload_sha256"] != child.body.sha256:
                raise ValueError("krx_cross_probe_acquisition")
        originals.append((child, original, body))
    probes = [c.query_date.isoformat() for c in plan.children if c.purpose == "probe"]
    if probes != original_probe.get("queried_dates"):
        raise ValueError("krx_probe_date_set_mismatch")
    return original_probe, originals


async def replay_krx_history_aggregate(*, root: Path, receipt: AggregateReceipt,
                                       expected_plan_sha256: str) -> dict:
    """Independently pinned plan required; no output-derived live authority."""
    receipt = AggregateReceipt.model_validate(receipt.model_dump(mode="json"))
    if receipt.plan.sha256 != expected_plan_sha256:
        raise ValueError("krx_frozen_plan_changed")
    plan = HistoricalKrxPlan.model_validate_json(_read(root, receipt.plan))
    expected_probe, originals = _validate_inputs(root, receipt, plan)
    expected = json.loads(read_bound_artifact(root, receipt.artifact, receipt.artifact_sha256))
    source_candidate = json.loads(_read(root, plan.source_candidate))
    if native_candidate_projection(source_candidate) != expected:
        raise ValueError("krx_expected_projection_mismatch")
    if digest(expected) != receipt.normalized_sha256:
        raise ValueError("krx_normalized_hash_mismatch")
    probes = [(c, r, b) for c, r, b in originals if c.purpose == "probe"]

    class DeclaredBytesTransport(httpx.AsyncBaseTransport):
        index = 0

        async def handle_async_request(self, request):
            if self.index >= len(probes):
                raise ValueError("krx_undeclared_probe_read")
            child, original, body = probes[self.index]
            if (request.method != "GET" or str(request.url.copy_with(query=None)) != KRX_FUTURES_DAILY_URL
                    or dict(request.url.params) != {"basDd": child.query_date.strftime("%Y%m%d")}):
                raise ValueError("krx_probe_request_order_mismatch")
            self.index += 1
            return httpx.Response(original.http_status, content=body, request=request)

    transport = DeclaredBytesTransport()
    probe = await fetch_live_probe(run_date=plan.observed_at.astimezone(KST).date(),
        observation_time=plan.observed_at, api_key="offline-no-credential", transport=transport,
        max_lookback_days=len(probes))
    if transport.index != len(probes):
        raise ValueError("krx_unconsumed_probe_child")
    # This flag means original source bytes exist, not that replay called a provider.
    probe.live_source = expected_probe["live_source"]
    if {**probe.model_dump(mode="json"), "live_source": probe.live_source} != expected_probe:
        raise ValueError("krx_probe_not_reproduced")
    if tuple(o.product for o in probe.observations) != PRODUCTS:
        raise ValueError("krx_configured_products_required")
    with TemporaryDirectory(prefix="krx-offline-replay-") as temporary:
        storage = Path(temporary)
        for child, original, body in originals:
            if child.purpose != "history":
                continue
            reproduced, _normalized, _stored = persist_krx_response(root=storage,
                query_date=child.query_date, fetched_at=original.fetched_at,
                http_status=original.http_status, raw_body=body)
            if reproduced != original:
                raise ValueError("krx_history_receipt_not_reproduced")
        result = TypeAdapter(MacroProviderResult).dump_python(
            materialize_night_probe(probe, history_directory=storage), mode="json")
    if digest(result) != receipt.normalized_sha256 or result != expected:
        raise ValueError("krx_owner_output_not_reproduced")
    products = []
    for observation in result["observations"]:
        context = observation["raw_payload"]
        timeframes = context.get("night_timeframes")
        if (not timeframes or timeframes["instrument_root"] != context["product"]
                or timeframes["reference_date"] != plan.session_date.isoformat()):
            raise ValueError("krx_dwm_required")
        for name in ("daily", "weekly", "monthly"):
            frame = timeframes[name]
            if (frame["missing_dates"] or not frame["source_fact_ids"]
                    or frame["contract_code"] != context["contract_code"]):
                raise ValueError("krx_same_contract_history_incomplete")
            if not set(frame["source_raw_sha256"]) <= {c.body.sha256 for c in plan.children}:
                raise ValueError("krx_unbound_history_dependency")
        products.append({"product": context["product"], "contract_code": context["contract_code"],
            "reference_date": context["reference_date"], "timeframes": timeframes})
    annotation = source_candidate.get("telemetry", {}).get("month_history")
    if annotation is not None:
        coverage = [{"product": p["product"], "contract_code": p["contract_code"],
            "reference_date": p["timeframes"]["reference_date"],
            "expected_dates": [d for d in p["timeframes"]["monthly"]["expected_dates"] if d <= plan.session_date.isoformat()],
            "included_dates": p["timeframes"]["monthly"]["included_dates"],
            "missing_dates": p["timeframes"]["monthly"]["missing_dates"]} for p in products]
        if annotation.get("coverage") != coverage:
            raise ValueError("krx_archive_history_coverage_mismatch")
    return {"contract": OWNER, "mode": plan.mode, "source_archive_id": plan.source_archive_id,
        "run_id": plan.run_id, "plan_sha256": expected_plan_sha256,
        "aggregate_sha256": receipt.aggregate_sha256, "owner_output_sha256": digest(result),
        "source_child_count": len(originals), "probe_source_opens": len(probes),
        "history_source_opens": len(originals) - len(probes), "products": products,
        "status": "PASS", "external_provider_calls": 0, "production_writes": 0,
        "source_candidate_sha256": plan.source_candidate.sha256,
        "candidate_projection": "TYPED_NATIVE_OWNER_EXCLUDES_ARCHIVE_MONTH_ACQUISITION_AUDIT",
        "archive_month_audit_recreated_as_new_calls": False,
        "private_storage_removed": True, "complete_source_adapter_qualified": False}
