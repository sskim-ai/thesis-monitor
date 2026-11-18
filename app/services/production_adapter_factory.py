"""Closed production adapter registry; no arbitrary dotted-path plug-ins."""
import json
from pathlib import Path
import subprocess

from app.services.production_delivery import ProductionDelivery, destination_fingerprint
from app.services.production_model_transport import OfficialProductionModelTransport
from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
from app.services.production_source_backend import CanonicalProductionSourceBackend, runtime_code_identity
from app.services.unified_market_run import Clock
from app.services.unified_run_artifacts import SECRET_KEY, sha256_bytes
from app.services.unified_snapshot_contract import digest

ROOT = Path(__file__).resolve().parents[2]


def build_research_adapter(*, enabled=False, **kwargs):
    """Manual alias for the same explicitly admitted production child."""
    if enabled is not True:
        raise ValueError('research_no_send_factory_disabled')
    settings = kwargs.pop('settings')
    return build_production_adapter(settings, **kwargs)


def _configuration(path, expected):
    if not path or not expected:
        raise RuntimeError("production_full_source_backend_not_qualified:explicit_configuration_missing")
    path = Path(path)
    if (not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents))
            or {"Reports", "tests", "fixtures"}.intersection(path.parts)):
        raise ValueError("production_configuration_not_deployed")
    raw = path.read_bytes()
    if sha256_bytes(raw) != expected:
        raise ValueError("production_configuration_hash_mismatch")
    return json.loads(raw)


def build_production_adapter(settings, *, clock=None, source_transport=None, model_transport=None, notifier=None,
                             child=None, binding=None, runtime_root=None, journal_path=None,
                             approved_max_invocations=None, approved_plan_sha256=None, run_ledger=None,
                             market_origin=None, artifact_budget=None, retained_kr_ecos_body=None,
                             timeout_retry_cap=0):
    if child is not None:
        from app.services.research_no_send_run import build_research_no_send_adapter

        if any(port is not None for port in (source_transport, model_transport, notifier)):
            raise ValueError('prepared_cycle_no_alternate_source_model_or_delivery_port')
        return build_research_no_send_adapter(enabled=True, child=child, settings=settings, binding=binding,
            runtime_root=runtime_root, journal_path=journal_path, approved_max_invocations=approved_max_invocations,
            approved_plan_sha256=approved_plan_sha256, clock=clock or Clock(), run_ledger=run_ledger,
            market_origin=market_origin, artifact_budget=artifact_budget, retained_kr_ecos_body=retained_kr_ecos_body,
            timeout_retry_cap=timeout_retry_cap)
    if any(value is not None for value in (binding, runtime_root, journal_path, approved_max_invocations,
            approved_plan_sha256, run_ledger, market_origin, artifact_budget, retained_kr_ecos_body)) or timeout_retry_cap:
        raise ValueError('prepared_cycle_original_child_required')
    if not settings.unified_snapshot_enabled or settings.unified_snapshot_runtime_contract != "unified-query-time-snapshot-v2":
        raise ValueError("production_adapter_disabled_or_wrong_version")
    source_config = _configuration(settings.unified_snapshot_source_configuration,
                                   settings.unified_snapshot_source_configuration_sha256)
    model_binding = _configuration(settings.unified_snapshot_model_binding,
                                   settings.unified_snapshot_model_binding_sha256)
    if not settings.unified_snapshot_model_runtime_root:
        raise ValueError("production_model_runtime_root_missing")
    clock = clock or Clock()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    secrets = tuple(value.get_secret_value() if hasattr(value, "get_secret_value") else str(value)
        for key, value in settings.model_dump().items() if value and SECRET_KEY.search(key))
    sources = CanonicalProductionSourceBackend(settings=settings, configuration=source_config,
        implementation_sha=head, clock=clock, transport=source_transport)
    model = model_transport or OfficialProductionModelTransport(binding=model_binding,
        runtime_root=settings.unified_snapshot_model_runtime_root, secrets=secrets)
    if notifier is None:
        from app.services.notification_service import TelegramNotifier
        notifier = TelegramNotifier()
        # Uncertain send outcomes cannot be retried below the durable intent.
        notifier.settings = settings.model_copy(update={"telegram_retry_attempts": 1})
    if settings.notification_dry_run and (not settings.telegram_bot_token or not settings.telegram_chat_id):
        fingerprint = digest({"destination": "DRY_RUN_NO_RECIPIENT", "configuration": sources.configuration_identity})
    else:
        fingerprint = destination_fingerprint(recipient=settings.telegram_chat_id, token=settings.telegram_bot_token)
    delivery = ProductionDelivery(root=Path(settings.data_dir) / "production-delivery", fingerprint=fingerprint,
        dry_run=settings.notification_dry_run, live_authorized=settings.unified_snapshot_live_delivery_authorized,
        notifier=notifier)
    adapter = ProductionRuntimeBridgeV1(settings=settings, sources=sources, model=model, delivery=delivery, clock=clock)
    adapter.repository_commit = head
    adapter.adapter_fingerprint = digest({"contract": "production-runtime-bridge-v1",
        "source_configuration": sources.configuration_identity, "code": runtime_code_identity(),
        "model_binding": settings.unified_snapshot_model_binding_sha256})
    return adapter
