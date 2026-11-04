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


def build_production_adapter(settings, *, clock=None, source_transport=None, model_transport=None, notifier=None):
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
